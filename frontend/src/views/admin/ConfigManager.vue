<!--
  ConfigManager.vue - 配置文件管理页面（管理员视角）
  
  页面作用：
    - 展示所有已上传的 Clash/代理配置文件列表（包含分组信息、普通用户可见性、定时更新策略及状态）
    - 自由独立分组管理：
      - 支持管理员独立新建分组、编辑分组信息（名称、描述、排序权重）和删除分组（关联配置安全迁移）
      - 提供专门的“分组管理”控制中心面板
      - 顶部支持按分组快速切换 Tab/Pill 筛选与实时统计
      - 上传/导入配置及单项/批量修改时可快速选择已有分组或点击快捷新建分组
    - 快速切换配置对普通用户的可见性 (is_public Switch 开关实时生效)
    - 针对移动端深度优化：
      - 移动端模式下自动采用触控友好的卡片流布局 (Mobile Cards)
      - 桌面端模式下保留完整的高密度管理表格 (Desktop Table)
    - 支持新建/上传配置文件（文件上传、订阅链接、粘贴 YAML）
    - 提供订阅配置的“立即同步”与“定时设置”调度策略修改
    - 提供进入在线代码编辑 (ConfigEditor) 和删除配置功能
-->
<template>
  <div class="manager-container">
    <!-- 顶部操作栏 -->
    <div class="header-actions">
      <div class="header-titles">
        <h2 class="page-title">配置管理</h2>
        <p class="page-subtitle">管理所有代理订阅配置文件、自由分组、普通用户可见性与定时自动同步调度策略。</p>
      </div>
      <div class="header-btns">
        <el-button 
          v-if="selectedRows.length > 0 && !deviceStore.isMobile" 
          type="warning" 
          plain 
          :icon="Folder" 
          @click="openBatchGroupDialog"
        >
          批量移动 ({{ selectedRows.length }})
        </el-button>
        <el-button 
          type="info" 
          plain 
          :icon="Operation" 
          @click="openGroupManageDialog"
        >
          分组管理
        </el-button>
        <el-button 
          type="success" 
          plain 
          :icon="Plus" 
          @click="openCreateGroupDialog"
        >
          新建分组
        </el-button>
        <el-button type="primary" @click="openUploadDialog" :icon="Upload" class="upload-top-btn">
          上传 / 导入配置
        </el-button>
      </div>
    </div>

    <!-- 分组过滤与搜索筛选工具栏 -->
    <div class="filter-toolbar">
      <!-- 左侧分组快速筛选 Tabs / Pills -->
      <div class="group-pills-wrapper">
        <div
          class="group-pill"
          :class="{ active: selectedGroup === 'all' }"
          @click="selectedGroup = 'all'"
        >
          <span>全部</span>
          <span class="pill-badge">{{ configStore.configList.length }}</span>
        </div>
        <div
          v-for="grp in groupStats"
          :key="grp.name"
          class="group-pill"
          :class="{ active: selectedGroup === grp.name }"
          @click="selectedGroup = grp.name"
        >
          <el-icon class="pill-icon"><Folder /></el-icon>
          <span>{{ grp.name }}</span>
          <span class="pill-badge">{{ grp.count }}</span>
        </div>

        <!-- 快速新建分组 Pill 按钮 -->
        <div class="group-pill add-group-pill" @click="openCreateGroupDialog">
          <el-icon><Plus /></el-icon>
          <span>新建分组</span>
        </div>
      </div>

      <!-- 右侧搜索输入框 -->
      <div class="filter-search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索配置名称、描述或分组..."
          clearable
          :prefix-icon="Search"
          class="search-input"
        />
      </div>
    </div>

    <!-- 1. 桌面端视图：完整数据表格 (Desktop Table) -->
    <el-table
      v-if="!deviceStore.isMobile"
      ref="tableRef"
      v-loading="configStore.loading"
      :data="filteredConfigs"
      class="custom-table"
      empty-text="暂无匹配的配置文件"
      @selection-change="handleSelectionChange"
    >
      <!-- 多选列 -->
      <el-table-column type="selection" width="45" align="center" />

      <!-- 配置名称（宽度自适应，内嵌订阅导入标签） -->
      <el-table-column prop="name" label="配置名称" min-width="200">
        <template #default="scope">
          <div class="name-cell">
            <span class="config-title">{{ scope.row.name }}</span>
            <el-tag v-if="scope.row.subscription_url" size="small" type="info" effect="plain" class="sub-link-tag">
              订阅导入
            </el-tag>
          </div>
        </template>
      </el-table-column>

      <!-- 所属分组列：展示分组标签与快捷修改 -->
      <el-table-column prop="group_name" label="所属分组" width="130">
        <template #default="scope">
          <div class="group-cell" @click="openChangeGroupDialog(scope.row)">
            <el-tag size="small" effect="plain" class="admin-group-tag">
              <el-icon><Folder /></el-icon>
              <span>{{ scope.row.group_name || '默认分组' }}</span>
            </el-tag>
            <el-tooltip content="修改分组" placement="top">
              <el-button link :icon="Edit" size="small" class="group-quick-edit-btn" />
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
      
      <!-- 配置描述 -->
      <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip />
      
      <!-- 普通用户可见性列：支持管理员一键快速切换 -->
      <el-table-column label="用户可见" width="100" align="center">
        <template #default="scope">
          <el-switch
            :model-value="scope.row.is_public"
            :loading="scope.row._switchingVisibility"
            inline-prompt
            active-text="公开"
            inactive-text="隐藏"
            @change="(val) => handleToggleVisibility(scope.row, val)"
          />
        </template>
      </el-table-column>

      <!-- 定时更新状态列 -->
      <el-table-column label="定时更新" width="115">
        <template #default="scope">
          <div v-if="scope.row.auto_update" class="schedule-cell">
            <el-tooltip placement="top" effect="dark">
              <template #content>
                <div class="schedule-tooltip-content">
                  <div><strong>更新策略:</strong> {{ formatScheduleTooltip(scope.row) }}</div>
                  <div v-if="scope.row.last_auto_update_at">
                    <strong>上次同步:</strong> {{ formatDate(scope.row.last_auto_update_at) }}
                  </div>
                  <div v-if="scope.row.last_auto_update_status">
                    <strong>同步状态:</strong> 
                    <span :style="{ color: scope.row.last_auto_update_status === 'success' ? '#67c23a' : '#f56c6c' }">
                      {{ scope.row.last_auto_update_status === 'success' ? '成功' : scope.row.last_auto_update_status }}
                    </span>
                  </div>
                </div>
              </template>
              <el-tag type="warning" size="small" effect="light" class="schedule-tag">
                <el-icon><Timer /></el-icon>
                <span>{{ formatScheduleText(scope.row) }}</span>
              </el-tag>
            </el-tooltip>
          </div>
          <div v-else class="schedule-cell">
            <el-tag type="info" size="small" effect="plain">未开启</el-tag>
          </div>
        </template>
      </el-table-column>

      <!-- 大小 -->
      <el-table-column prop="file_size" label="大小" width="75" align="right">
        <template #default="scope">
          {{ formatSize(scope.row.file_size) }}
        </template>
      </el-table-column>
      
      <!-- 最后修改 -->
      <el-table-column prop="updated_at" label="最后修改" width="135">
        <template #default="scope">
          {{ formatDate(scope.row.updated_at || scope.row.created_at) }}
        </template>
      </el-table-column>
      
      <!-- 操作列（右对齐展示完整功能按钮） -->
      <el-table-column label="操作" width="220" align="right">
        <template #default="scope">
          <div class="table-actions">
            <!-- 分组修改按钮 -->
            <el-tooltip content="调整配置所属分组" placement="top">
              <el-button 
                type="info" 
                link 
                :icon="Folder" 
                @click="openChangeGroupDialog(scope.row)"
              >
                分组
              </el-button>
            </el-tooltip>

            <!-- 若为订阅导入配置，提供立即同步和定时设置按钮 -->
            <template v-if="scope.row.subscription_url">
              <el-tooltip content="立即从原订阅链接同步更新" placement="top">
                <el-button 
                  type="success" 
                  link 
                  :icon="Refresh" 
                  :loading="scope.row._syncing" 
                  @click="handleSyncNow(scope.row)"
                >
                  同步
                </el-button>
              </el-tooltip>
              <el-tooltip content="配置定时自动更新策略" placement="top">
                <el-button 
                  type="warning" 
                  link 
                  :icon="Timer" 
                  @click="openScheduleDialog(scope.row)"
                >
                  定时
                </el-button>
              </el-tooltip>
            </template>
            
            <el-button
              type="primary"
              size="small"
              class="edit-action-btn"
              @click="editConfig(scope.row.id)"
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-button type="danger" link @click="confirmDelete(scope.row)" :icon="Delete">
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 2. 移动端专属视图：卡片列表流 (Mobile Card View) -->
    <div v-else class="mobile-config-list" v-loading="configStore.loading">
      <div v-if="filteredConfigs.length === 0" class="empty-box">
        <el-empty description="暂无匹配的配置文件" />
      </div>

      <div 
        v-for="item in filteredConfigs" 
        :key="item.id" 
        class="admin-config-card"
      >
        <!-- 卡片头部：名称与大小 -->
        <div class="card-top-row">
          <div class="card-title-group">
            <h4 class="card-name">{{ item.name }}</h4>
            <el-tag size="small" effect="plain" class="mobile-group-badge">
              <el-icon><Folder /></el-icon> {{ item.group_name || '默认分组' }}
            </el-tag>
            <el-tag v-if="item.subscription_url" size="small" type="info" effect="plain">
              订阅
            </el-tag>
          </div>
          <span class="card-size">{{ formatSize(item.file_size) }}</span>
        </div>

        <!-- 描述（若有） -->
        <p class="card-desc" v-if="item.description">{{ item.description }}</p>

        <!-- 属性与开关行 -->
        <div class="card-props-row">
          <div class="prop-item">
            <span class="prop-label">用户可见:</span>
            <el-switch
              :model-value="item.is_public"
              :loading="item._switchingVisibility"
              size="small"
              inline-prompt
              active-text="公开"
              inactive-text="隐藏"
              @change="(val) => handleToggleVisibility(item, val)"
            />
          </div>

          <!-- 定时更新状态 -->
          <div class="prop-item">
            <el-tag 
              v-if="item.auto_update" 
              type="warning" 
              size="small" 
              effect="light"
              class="mobile-schedule-tag"
            >
              <el-icon><Timer /></el-icon>
              <span>{{ formatScheduleText(item) }}</span>
            </el-tag>
            <span v-else class="no-schedule-tip">未开启定时</span>
          </div>
        </div>

        <!-- 卡片底部时间与操作按钮 -->
        <div class="card-bottom-row">
          <span class="card-date">{{ formatDate(item.updated_at || item.created_at) }}</span>
          
          <div class="card-actions">
            <!-- 调整分组按钮 -->
            <el-button
              type="info"
              size="small"
              plain
              :icon="Folder"
              @click="openChangeGroupDialog(item)"
              class="mobile-action-btn"
            >
              分组
            </el-button>

            <template v-if="item.subscription_url">
              <el-button 
                type="success" 
                size="small" 
                plain
                :icon="Refresh" 
                :loading="item._syncing" 
                @click="handleSyncNow(item)"
                class="mobile-action-btn"
              >
                同步
              </el-button>
              <el-button 
                type="warning" 
                size="small" 
                plain
                :icon="Timer" 
                @click="openScheduleDialog(item)"
                class="mobile-action-btn"
              >
                定时
              </el-button>
            </template>
            
            <el-button 
              type="primary" 
              size="small" 
              class="edit-action-btn mobile-action-btn"
              @click="editConfig(item.id)" 
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              plain 
              @click="confirmDelete(item)" 
              :icon="Delete"
              class="mobile-action-btn"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 1. 上传/导入配置弹窗 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传 / 导入配置文件"
      :width="deviceStore.isMobile ? '95%' : '560px'"
      class="custom-dialog"
      :destroy-on-close="true"
    >
      <el-form :model="uploadForm" ref="formRef" label-position="top">
        <el-form-item label="配置名称" required>
          <el-input v-model="uploadForm.name" placeholder="例如：优质节点订阅" />
        </el-form-item>

        <!-- 所属分组设置：支持从已有分组中选择，或直接输入新分组名称 -->
        <el-form-item label="所属分组" required>
          <div class="group-select-row">
            <el-select
              v-model="uploadForm.group_name"
              filterable
              allow-create
              default-first-option
              placeholder="选择已有分组或直接输入新分组"
              style="flex: 1;"
            >
              <el-option
                v-for="grp in configStore.groups"
                :key="grp"
                :label="grp"
                :value="grp"
              />
            </el-select>
            <el-button type="success" plain :icon="Plus" @click="openCreateGroupDialog">
              新建分组
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="配置描述">
          <el-input v-model="uploadForm.description" type="textarea" placeholder="选填描述信息..." :rows="2" />
        </el-form-item>

        <!-- 普通用户可见性设置 -->
        <el-form-item label="普通用户权限">
          <div class="visibility-setting-box">
            <el-switch
              v-model="uploadForm.is_public"
              active-text="对普通用户可见"
              inactive-text="仅管理员可见 (隐藏)"
            />
            <span class="setting-hint">关闭后，普通用户登录将无法在列表中查看到该配置。</span>
          </div>
        </el-form-item>

        <el-form-item label="导入方式">
          <el-radio-group v-model="uploadForm.method" :size="deviceStore.isMobile ? 'small' : 'default'">
            <el-radio-button value="file">文件上传</el-radio-button>
            <el-radio-button value="url">订阅链接</el-radio-button>
            <el-radio-button value="content">粘贴 YAML</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <!-- 方式 1: 上传本地 YAML 文件 -->
        <el-form-item v-if="uploadForm.method === 'file'" label="YAML 文件" required>
          <el-upload
            class="upload-area"
            drag
            action="#"
            :auto-upload="false"
            :limit="1"
            accept=".yaml,.yml"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖拽至此 或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">仅支持 .yaml 或 .yml 配置文件</div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 方式 2: 订阅链接导入（支持配置定时更新） -->
        <template v-if="uploadForm.method === 'url'">
          <el-form-item label="订阅链接 URL" required>
            <el-input v-model="uploadForm.url" placeholder="https://example.com/api/v1/client/subscribe?token=..." />
          </el-form-item>

          <!-- 可选定时更新选项 -->
          <div class="schedule-config-panel">
            <div class="panel-header">
              <span class="panel-title">
                <el-icon><Timer /></el-icon> 定时自动更新
              </span>
              <el-switch v-model="uploadForm.auto_update" />
            </div>
            
            <div v-if="uploadForm.auto_update" class="panel-body">
              <div class="form-row">
                <label class="sub-label">更新频率模式:</label>
                <el-radio-group v-model="uploadForm.update_interval_type" size="small">
                  <el-radio-button value="daily">每日定时时刻</el-radio-button>
                  <el-radio-button value="interval">固定时间间隔</el-radio-button>
                </el-radio-group>
              </div>

              <!-- 每日定时时刻选择 -->
              <div v-if="uploadForm.update_interval_type === 'daily'" class="form-row">
                <label class="sub-label">定时更新时间 (系统时间):</label>
                <el-time-select
                  v-model="uploadForm.update_time"
                  start="00:00"
                  step="00:30"
                  end="23:30"
                  placeholder="选择时间点"
                  class="time-picker-input"
                />
              </div>

              <!-- 间隔小时数选择 -->
              <div v-if="uploadForm.update_interval_type === 'interval'" class="form-row">
                <label class="sub-label">更新间隔时间:</label>
                <el-select v-model="uploadForm.update_time" placeholder="选择间隔" class="interval-select">
                  <el-option label="每 6 小时" value="6" />
                  <el-option label="每 12 小时" value="12" />
                  <el-option label="每 24 小时 (每天)" value="24" />
                  <el-option label="每 48 小时 (两天)" value="48" />
                </el-select>
              </div>

              <div class="schedule-tip">
                💡 开启后，系统后台调度器将在到达设定时间时自动重新拉取原订阅链接，并静默覆盖更新配置。
              </div>
            </div>
          </div>
        </template>

        <!-- 方式 3: 直接粘贴 YAML 内容 -->
        <el-form-item v-if="uploadForm.method === 'content'" label="YAML 内容" required>
          <el-input v-model="uploadForm.content" type="textarea" :rows="6" placeholder="请在此粘贴 YAML 配置内容..." style="font-family: monospace;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">
            确认添加
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 2. 定时自动更新策略修改弹窗 -->
    <el-dialog
      v-model="scheduleDialog.visible"
      :title="`定时更新设置 - ${scheduleDialog.config?.name || ''}`"
      :width="deviceStore.isMobile ? '95%' : '520px'"
      class="custom-dialog"
    >
      <el-form :model="scheduleDialog.form" label-position="top">
        <el-form-item label="订阅链接地址" required>
          <el-input v-model="scheduleDialog.form.subscription_url" placeholder="https://..." />
        </el-form-item>

        <el-form-item label="开启定时自动同步">
          <el-switch v-model="scheduleDialog.form.auto_update" active-text="启用" inactive-text="关闭" />
        </el-form-item>

        <template v-if="scheduleDialog.form.auto_update">
          <el-form-item label="更新频率模式">
            <el-radio-group v-model="scheduleDialog.form.update_interval_type" size="small">
              <el-radio-button value="daily">每日定时时刻</el-radio-button>
              <el-radio-button value="interval">固定时间间隔</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <!-- 每日定时时刻选择 -->
          <el-form-item v-if="scheduleDialog.form.update_interval_type === 'daily'" label="每日更新时刻 (系统时间)">
            <el-time-select
              v-model="scheduleDialog.form.update_time"
              start="00:00"
              step="00:30"
              end="23:30"
              placeholder="选择更新时间"
              class="time-picker-input"
            />
          </el-form-item>

          <!-- 间隔小时数选择 -->
          <el-form-item v-if="scheduleDialog.form.update_interval_type === 'interval'" label="间隔小时数">
            <el-select v-model="scheduleDialog.form.update_time" placeholder="选择间隔" style="width: 100%;">
              <el-option label="每 6 小时" value="6" />
              <el-option label="每 12 小时" value="12" />
              <el-option label="每 24 小时 (每天)" value="24" />
              <el-option label="每 48 小时 (两天)" value="48" />
            </el-select>
          </el-form-item>

          <div v-if="scheduleDialog.config?.last_auto_update_at" class="last-sync-info">
            上次同步时间: {{ formatDate(scheduleDialog.config.last_auto_update_at) }} 
            ({{ scheduleDialog.config.last_auto_update_status === 'success' ? '状态正常' : scheduleDialog.config.last_auto_update_status }})
          </div>
        </template>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="scheduleDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="submitScheduleUpdate" :loading="scheduleDialog.submitting">
            保存配置
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 3. 调整分组对话框 (支持单项与批量操作) -->
    <el-dialog
      v-model="groupDialog.visible"
      :title="groupDialog.isBatch ? `批量调整分组 (已选 ${groupDialog.selectedIds.length} 项)` : `调整所属分组 - ${groupDialog.config?.name || ''}`"
      :width="deviceStore.isMobile ? '95%' : '480px'"
      class="custom-dialog"
    >
      <el-form label-position="top">
        <el-form-item label="目标分组名称" required>
          <div class="group-select-row">
            <el-select
              v-model="groupDialog.group_name"
              filterable
              allow-create
              default-first-option
              placeholder="选择已有分组或输入新分组名称"
              style="flex: 1;"
            >
              <el-option
                v-for="grp in configStore.groups"
                :key="grp"
                :label="grp"
                :value="grp"
              />
            </el-select>
            <el-button type="success" plain :icon="Plus" @click="openCreateGroupDialog">
              新建
            </el-button>
          </div>
        </el-form-item>

        <!-- 快捷选择已有分组 -->
        <div class="preset-groups-box" v-if="configStore.groups.length > 0">
          <span class="preset-title">点击快速选取已有分组:</span>
          <div class="preset-tags">
            <el-tag
              v-for="grp in configStore.groups"
              :key="grp"
              size="small"
              :effect="groupDialog.group_name === grp ? 'dark' : 'plain'"
              class="clickable-preset-tag"
              @click="groupDialog.group_name = grp"
            >
              <el-icon><Folder /></el-icon>
              {{ grp }}
            </el-tag>
          </div>
        </div>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="groupDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="submitGroupChange" :loading="groupDialog.submitting">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 4. 新建分组对话框 (独立创建) -->
    <el-dialog
      v-model="createGroupDialog.visible"
      title="新建配置分组"
      :width="deviceStore.isMobile ? '95%' : '460px'"
      class="custom-dialog"
    >
      <el-form :model="createGroupDialog.form" label-position="top">
        <el-form-item label="分组名称" required>
          <el-input 
            v-model="createGroupDialog.form.name" 
            placeholder="例如：香港专线、VIP节点、自建节点" 
            maxlength="64"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="分组描述 (选填)">
          <el-input 
            v-model="createGroupDialog.form.description" 
            type="textarea" 
            placeholder="关于此分组节点的说明或备注..." 
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number 
            v-model="createGroupDialog.form.sort_order" 
            :min="0" 
            :max="999" 
            style="width: 100%;"
          />
          <span class="setting-hint">数字越小展示越靠前 (默认: 0)</span>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createGroupDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="submitCreateGroup" :loading="createGroupDialog.submitting">
            立即创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 5. 编辑分组对话框 -->
    <el-dialog
      v-model="editGroupDialog.visible"
      :title="`编辑分组 - ${editGroupDialog.group?.name || ''}`"
      :width="deviceStore.isMobile ? '95%' : '460px'"
      class="custom-dialog"
    >
      <el-form :model="editGroupDialog.form" label-position="top">
        <el-form-item label="分组名称" required>
          <el-input 
            v-model="editGroupDialog.form.name" 
            placeholder="请输入分组名称" 
            :disabled="editGroupDialog.group?.name === '默认分组'"
            maxlength="64"
            show-word-limit
          />
          <span class="setting-hint" v-if="editGroupDialog.group?.name === '默认分组'">
            系统默认分组不可修改名称
          </span>
          <span class="setting-hint" v-else>
            修改分组名称后，该分组下的所有已有配置将自动同步至新名称。
          </span>
        </el-form-item>
        <el-form-item label="分组描述">
          <el-input 
            v-model="editGroupDialog.form.description" 
            type="textarea" 
            placeholder="分组说明..." 
            :rows="3"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number 
            v-model="editGroupDialog.form.sort_order" 
            :min="0" 
            :max="999" 
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editGroupDialog.visible = false">取消</el-button>
          <el-button type="primary" @click="submitEditGroup" :loading="editGroupDialog.submitting">
            保存修改
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 6. 分组管理中心弹窗 -->
    <el-dialog
      v-model="groupManageDialog.visible"
      title="配置分组管理中心"
      :width="deviceStore.isMobile ? '95%' : '750px'"
      class="custom-dialog"
    >
      <div class="group-manage-header">
        <span class="group-manage-tip">
          共 {{ configStore.groupList.length }} 个独立分组，可自由添加、编辑或删除分组。
        </span>
        <el-button type="primary" size="small" :icon="Plus" @click="openCreateGroupDialog">
          新建分组
        </el-button>
      </div>

      <el-table :data="configStore.groupList" class="group-manage-table" empty-text="暂无分组">
        <el-table-column prop="name" label="分组名称" min-width="130">
          <template #default="scope">
            <div class="group-name-cell">
              <el-tag size="small" effect="plain" class="admin-group-tag">
                <el-icon><Folder /></el-icon>
                <span>{{ scope.row.name }}</span>
              </el-tag>
              <el-tag v-if="scope.row.name === '默认分组'" size="small" type="info">系统</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip>
          <template #default="scope">
            {{ scope.row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="count" label="配置数" width="90" align="center">
          <template #default="scope">
            <el-badge :value="scope.row.count" class="count-badge" type="primary" />
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        <el-table-column label="操作" width="140" align="right">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              class="edit-action-btn"
              :icon="Edit" 
              @click="openEditGroupDialog(scope.row)"
            >
              编辑
            </el-button>
            <el-button 
              type="danger" 
              link 
              size="small" 
              :icon="Delete" 
              :disabled="scope.row.name === '默认分组'"
              @click="confirmDeleteGroup(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="groupManageDialog.visible = false">完成</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 7. 删除配置确认对话框 -->
    <ConfirmDialog
      v-model:visible="deleteDialog.visible"
      title="删除配置"
      :message="`确定要删除配置“${deleteDialog.config?.name}”吗？此操作无法撤销。`"
      type="danger"
      confirm-text="删除"
      @confirm="handleDelete"
      @cancel="deleteDialog.visible = false"
    />

    <!-- 8. 删除分组确认对话框 -->
    <ConfirmDialog
      v-model:visible="groupDeleteDialog.visible"
      title="删除配置分组"
      :message="`确定要删除分组“${groupDeleteDialog.group?.name}”吗？该分组下的 ${groupDeleteDialog.group?.count || 0} 个配置将自动安全转移至【默认分组】。`"
      type="danger"
      confirm-text="删除分组"
      @confirm="handleDeleteGroup"
      @cancel="groupDeleteDialog.visible = false"
    />
  </div>
</template>

<script setup>
/**
 * 引入依赖与 API
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useConfigStore } from '../../stores/config'
import { useDeviceStore } from '../../stores/device'
import { 
  uploadConfig, 
  updateConfigVisibility, 
  updateConfigSchedule, 
  syncConfig,
  updateConfigGroup,
  batchUpdateConfigGroup
} from '../../api/configs'
import { ElMessage } from 'element-plus'
import { 
  Upload, 
  Edit, 
  Delete, 
  UploadFilled, 
  Timer, 
  Refresh, 
  Folder, 
  Search, 
  Plus, 
  Operation 
} from '@element-plus/icons-vue'
import ConfirmDialog from '../../components/common/ConfirmDialog.vue'

const router = useRouter()
const configStore = useConfigStore()
const deviceStore = useDeviceStore()

// 表格引用与多选状态
const tableRef = ref(null)
const selectedRows = ref([])

// 分组筛选与搜索状态
const selectedGroup = ref('all')
const searchKeyword = ref('')

// 上传弹窗状态
const showUploadDialog = ref(false)
const uploading = ref(false)
const selectedFile = ref(null)

// 上传表单响应式状态
const uploadForm = reactive({
  name: '',
  description: '',
  group_name: '默认分组',
  is_public: true,
  method: 'file',
  url: '',
  auto_update: false,
  update_interval_type: 'daily',
  update_time: '04:00',
  content: ''
})

// 定时更新设置弹窗状态
const scheduleDialog = reactive({
  visible: false,
  config: null,
  submitting: false,
  form: {
    auto_update: false,
    subscription_url: '',
    update_interval_type: 'daily',
    update_time: '04:00'
  }
})

// 分组修改弹窗状态（支持单项或批量）
const groupDialog = reactive({
  visible: false,
  config: null,
  isBatch: false,
  selectedIds: [],
  group_name: '默认分组',
  submitting: false
})

// 新建分组弹窗状态
const createGroupDialog = reactive({
  visible: false,
  submitting: false,
  form: {
    name: '',
    description: '',
    sort_order: 0
  }
})

// 编辑分组弹窗状态
const editGroupDialog = reactive({
  visible: false,
  group: null,
  submitting: false,
  form: {
    id: null,
    name: '',
    description: '',
    sort_order: 0
  }
})

// 分组管理中心面板状态
const groupManageDialog = reactive({
  visible: false
})

// 删除配置对话框状态
const deleteDialog = reactive({
  visible: false,
  config: null
})

// 删除分组对话框状态
const groupDeleteDialog = reactive({
  visible: false,
  group: null
})

/**
 * 计算各个分组的配置数量统计列表 (直接基于 store 中的 groupList 与 configList 综合计算)
 */
const groupStats = computed(() => {
  const map = {}
  
  // 1. 先统计已有配置的计数
  configStore.configList.forEach(item => {
    const grp = item.group_name || '默认分组'
    map[grp] = (map[grp] || 0) + 1
  })

  // 2. 将 groupList 中即使配置数量为 0 的分组也包含进来
  configStore.groupList.forEach(g => {
    if (g.name && map[g.name] === undefined) {
      map[g.name] = 0
    }
  })

  const list = Object.keys(map).map(name => ({
    name,
    count: map[name]
  }))
  
  list.sort((a, b) => {
    if (a.name === '默认分组') return -1
    if (b.name === '默认分组') return 1
    return a.name.localeCompare(b.name)
  })
  return list
})

/**
 * 响应式过滤后的配置文件列表（结合分组 Tab 筛选与关键词搜索）
 */
const filteredConfigs = computed(() => {
  let list = configStore.configList

  // 1. 分组筛选
  if (selectedGroup.value !== 'all') {
    list = list.filter(item => (item.group_name || '默认分组') === selectedGroup.value)
  }

  // 2. 关键词搜索
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter(item => {
      const nameMatch = item.name && item.name.toLowerCase().includes(kw)
      const descMatch = item.description && item.description.toLowerCase().includes(kw)
      const groupMatch = item.group_name && item.group_name.toLowerCase().includes(kw)
      return nameMatch || descMatch || groupMatch
    })
  }

  return list
})

/**
 * 表格多选发生变化
 */
const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

/**
 * 打开新建分组弹窗
 */
const openCreateGroupDialog = () => {
  createGroupDialog.form.name = ''
  createGroupDialog.form.description = ''
  createGroupDialog.form.sort_order = 0
  createGroupDialog.visible = true
}

/**
 * 提交新建分组
 */
const submitCreateGroup = async () => {
  const name = createGroupDialog.form.name.trim()
  if (!name) {
    ElMessage.warning('请输入分组名称')
    return
  }

  createGroupDialog.submitting = true
  try {
    const newGrp = await configStore.createNewGroup({
      name,
      description: createGroupDialog.form.description.trim() || undefined,
      sort_order: createGroupDialog.form.sort_order || 0
    })
    createGroupDialog.visible = false
    
    // 如果当前正在上传配置或调整分组弹窗中，自动选中新建的分组
    if (showUploadDialog.value) {
      uploadForm.group_name = newGrp.name
    }
    if (groupDialog.visible) {
      groupDialog.group_name = newGrp.name
    }
  } catch (error) {
    // 错误在 store 中已提示
  } finally {
    createGroupDialog.submitting = false
  }
}

/**
 * 打开分组管理对话框
 */
const openGroupManageDialog = () => {
  configStore.fetchGroups()
  groupManageDialog.visible = true
}

/**
 * 打开编辑分组对话框
 * @param {Object} group 分组对象
 */
const openEditGroupDialog = (group) => {
  editGroupDialog.group = group
  editGroupDialog.form.id = group.id
  editGroupDialog.form.name = group.name
  editGroupDialog.form.description = group.description || ''
  editGroupDialog.form.sort_order = group.sort_order || 0
  editGroupDialog.visible = true
}

/**
 * 提交编辑分组
 */
const submitEditGroup = async () => {
  if (!editGroupDialog.form.id) {
    ElMessage.warning('分组 ID 缺失')
    return
  }
  const name = editGroupDialog.form.name.trim()
  if (!name) {
    ElMessage.warning('分组名称不能为空')
    return
  }

  editGroupDialog.submitting = true
  try {
    await configStore.updateExistingGroup(editGroupDialog.form.id, {
      name,
      description: editGroupDialog.form.description.trim(),
      sort_order: editGroupDialog.form.sort_order || 0
    })
    editGroupDialog.visible = false
  } catch (error) {
    // 错误在 store 中已提示
  } finally {
    editGroupDialog.submitting = false
  }
}

/**
 * 打开删除分组确认弹窗
 * @param {Object} group 分组对象
 */
const confirmDeleteGroup = (group) => {
  if (group.name === '默认分组') {
    ElMessage.warning('系统【默认分组】不可删除')
    return
  }
  groupDeleteDialog.group = group
  groupDeleteDialog.visible = true
}

/**
 * 执行删除分组
 */
const handleDeleteGroup = async () => {
  if (!groupDeleteDialog.group?.id) return
  try {
    await configStore.removeGroup(groupDeleteDialog.group.id)
    groupDeleteDialog.visible = false
  } catch (error) {
    // 错误在 store 中已处理
  }
}

/**
 * 打开单项修改分组对话框
 * @param {Object} row 配置项
 */
const openChangeGroupDialog = (row) => {
  groupDialog.config = row
  groupDialog.isBatch = false
  groupDialog.selectedIds = []
  groupDialog.group_name = row.group_name || '默认分组'
  groupDialog.visible = true
}

/**
 * 打开批量修改分组对话框
 */
const openBatchGroupDialog = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先勾选需要移动分组的配置文件')
    return
  }
  groupDialog.config = null
  groupDialog.isBatch = true
  groupDialog.selectedIds = selectedRows.value.map(r => r.id)
  groupDialog.group_name = '默认分组'
  groupDialog.visible = true
}

/**
 * 提交修改分组（单项或批量）
 */
const submitGroupChange = async () => {
  const targetGroup = (groupDialog.group_name || '').trim() || '默认分组'
  groupDialog.submitting = true

  try {
    if (groupDialog.isBatch) {
      // 批量调整
      const res = await batchUpdateConfigGroup(groupDialog.selectedIds, targetGroup)
      ElMessage.success(`已成功将 ${res.data?.updated_count || groupDialog.selectedIds.length} 个配置移动至【${targetGroup}】`)
    } else if (groupDialog.config) {
      // 单项调整
      await updateConfigGroup(groupDialog.config.id, targetGroup)
      groupDialog.config.group_name = targetGroup
      ElMessage.success(`已将【${groupDialog.config.name}】调整为【${targetGroup}】`)
    }

    groupDialog.visible = false
    await configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改分组失败，请重试')
    console.error('Failed to update config group:', error)
  } finally {
    groupDialog.submitting = false
  }
}

/**
 * 打开上传配置弹窗并重置表单
 */
const openUploadDialog = () => {
  uploadForm.name = ''
  uploadForm.description = ''
  uploadForm.group_name = selectedGroup.value !== 'all' ? selectedGroup.value : '默认分组'
  uploadForm.is_public = true
  uploadForm.method = 'file'
  uploadForm.url = ''
  uploadForm.auto_update = false
  uploadForm.update_interval_type = 'daily'
  uploadForm.update_time = '04:00'
  uploadForm.content = ''
  selectedFile.value = null
  showUploadDialog.value = true
}

/**
 * 监听上传文件选择变动
 */
const handleFileChange = (file) => {
  selectedFile.value = file.raw
  if (!uploadForm.name) {
    const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "")
    uploadForm.name = nameWithoutExt
  }
}

/**
 * 移除已选文件
 */
const handleFileRemove = () => {
  selectedFile.value = null
}

/**
 * 提交上传配置表单
 */
const submitUpload = async () => {
  if (!uploadForm.name) {
    ElMessage.warning('请输入配置名称')
    return
  }
  
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('name', uploadForm.name)
    formData.append('description', uploadForm.description || '')
    formData.append('group_name', (uploadForm.group_name || '').trim() || '默认分组')
    formData.append('is_public', String(uploadForm.is_public))
    
    if (uploadForm.method === 'file') {
      if (!selectedFile.value) {
        ElMessage.warning('请选择一个 YAML 文件')
        uploading.value = false
        return
      }
      formData.append('file', selectedFile.value)
    } else if (uploadForm.method === 'url') {
      if (!uploadForm.url) {
        ElMessage.warning('请输入订阅链接')
        uploading.value = false
        return
      }
      formData.append('url', uploadForm.url)
      formData.append('auto_update', String(uploadForm.auto_update))
      if (uploadForm.auto_update) {
        formData.append('update_interval_type', uploadForm.update_interval_type)
        formData.append('update_time', uploadForm.update_time)
      }
    } else if (uploadForm.method === 'content') {
      if (!uploadForm.content) {
        ElMessage.warning('请输入 YAML 内容')
        uploading.value = false
        return
      }
      formData.append('content', uploadForm.content)
    }
    
    await uploadConfig(formData)
    ElMessage.success('配置添加成功')
    showUploadDialog.value = false
    await configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加配置失败')
  } finally {
    uploading.value = false
  }
}

/**
 * 管理员一键切换普通用户可见性
 * @param {Object} row 配置项
 * @param {boolean} newVal 新可见性值
 */
const handleToggleVisibility = async (row, newVal) => {
  row._switchingVisibility = true
  try {
    const res = await updateConfigVisibility(row.id, newVal)
    row.is_public = res.data?.is_public ?? newVal
    ElMessage.success(row.is_public ? `已设置【${row.name}】为公开可见` : `已设置【${row.name}】为隐藏（仅管理可见）`)
  } catch (error) {
    ElMessage.error('修改可见性失败，请重试')
    console.error('Failed to toggle visibility:', error)
  } finally {
    row._switchingVisibility = false
  }
}

/**
 * 打开定时自动同步策略设置对话框
 * @param {Object} row 配置项
 */
const openScheduleDialog = (row) => {
  scheduleDialog.config = row
  scheduleDialog.form.auto_update = Boolean(row.auto_update)
  scheduleDialog.form.subscription_url = row.subscription_url || ''
  scheduleDialog.form.update_interval_type = row.update_interval_type || 'daily'
  scheduleDialog.form.update_time = row.update_time || '04:00'
  scheduleDialog.visible = true
}

/**
 * 提交修改定时自动同步设置
 */
const submitScheduleUpdate = async () => {
  if (!scheduleDialog.config) return
  if (!scheduleDialog.form.subscription_url) {
    ElMessage.warning('订阅链接不能为空')
    return
  }

  scheduleDialog.submitting = true
  try {
    const payload = {
      auto_update: scheduleDialog.form.auto_update,
      subscription_url: scheduleDialog.form.subscription_url,
      update_interval_type: scheduleDialog.form.update_interval_type,
      update_time: scheduleDialog.form.update_time
    }
    await updateConfigSchedule(scheduleDialog.config.id, payload)
    ElMessage.success('定时自动更新配置已保存')
    scheduleDialog.visible = false
    await configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存定时设置失败')
  } finally {
    scheduleDialog.submitting = false
  }
}

/**
 * 管理员一键立即从原订阅链接同步最新内容
 * @param {Object} row 配置项
 */
const handleSyncNow = async (row) => {
  row._syncing = true
  try {
    const res = await syncConfig(row.id)
    ElMessage.success(res.data?.message || '同步完成')
    await configStore.fetchConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '立即同步失败，请检查原订阅地址是否可达')
  } finally {
    row._syncing = false
  }
}

/**
 * 格式化定时更新提示简写
 */
const formatScheduleText = (row) => {
  if (row.update_interval_type === 'interval') {
    return `每 ${row.update_time || 12}h`
  }
  return `每日 ${row.update_time || '04:00'}`
}

/**
 * 格式化定时更新悬浮详细说明
 */
const formatScheduleTooltip = (row) => {
  if (row.update_interval_type === 'interval') {
    return `每隔 ${row.update_time || 12} 小时自动从订阅源拉取更新`
  }
  return `每天 ${row.update_time || '04:00'} (系统时间) 自动从订阅源拉取更新`
}

/**
 * 跳转编辑页面
 */
const editConfig = (id) => {
  router.push(`/admin/configs/${id}/edit`)
}

/**
 * 打开删除确认弹窗
 */
const confirmDelete = (config) => {
  deleteDialog.config = config
  deleteDialog.visible = true
}

/**
 * 执行删除配置
 */
const handleDelete = async () => {
  if (!deleteDialog.config) return
  try {
    await configStore.removeConfig(deleteDialog.config.id)
    ElMessage.success('配置已删除')
    deleteDialog.visible = false
  } catch (error) {
    ElMessage.error('删除配置失败')
  }
}

/**
 * 格式化字节大小
 */
const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化日期时间
 */
const formatDate = (dateString) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '未知时间'
  
  const pad = (n) => String(n).padStart(2, '0')
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

onMounted(() => {
  configStore.fetchConfigs()
})
</script>

<style scoped>
.manager-container {
  max-width: 1200px;
  margin: 0 auto;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.header-titles {
  flex: 1;
  min-width: 240px;
}

.page-title {
  margin: 0 0 6px;
  font-size: 24px;
  color: var(--text-primary);
}

.page-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.header-btns {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* 分组过滤与搜索工具栏 */
.filter-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  gap: 14px;
  flex-wrap: wrap;
}

.group-pills-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex: 1;
}

.group-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  user-select: none;
}

.group-pill:hover {
  border-color: var(--color-primary);
  color: var(--text-primary);
}

.group-pill.active {
  background: rgba(56, 189, 248, 0.12);
  border-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.add-group-pill {
  border-style: dashed;
  color: var(--color-primary);
  background: rgba(56, 189, 248, 0.04);
}

.add-group-pill:hover {
  background: rgba(56, 189, 248, 0.12);
}

.pill-icon {
  font-size: 13px;
}

.pill-badge {
  display: inline-block;
  padding: 1px 6px;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: inherit;
}

.filter-search-box {
  min-width: 240px;
}

.search-input {
  width: 100%;
}

:deep(.search-input .el-input__wrapper) {
  background-color: var(--bg-card);
  border-radius: 20px;
}

/* 桌面端表格样式 */
.custom-table {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  overflow: hidden;
  width: 100%;
}

:deep(.el-table) {
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--bg-secondary);
  --el-table-header-text-color: var(--text-secondary);
  --el-table-row-hover-bg-color: var(--bg-hover);
  --el-table-border-color: var(--border-color);
}

:deep(.el-table th.el-table__cell) {
  background-color: var(--bg-secondary) !important;
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}

:deep(.el-table td.el-table__cell) {
  background-color: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
}

:deep(.el-table__fixed-right),
:deep(.el-table__fixed-right-patch),
:deep(.el-table__fixed-left) {
  background-color: var(--bg-card) !important;
}

:deep(.el-table__fixed-right th.el-table__cell),
:deep(.el-table__fixed-right-patch) {
  background-color: var(--bg-secondary) !important;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.config-title {
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-word;
}

.sub-link-tag {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  font-size: 11px;
  height: 20px;
  line-height: 18px;
  padding: 0 6px;
  border-radius: 4px;
}

.group-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}

.admin-group-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f0f9ff;
  color: var(--color-primary, #0284c7);
  border-color: #bae6fd;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.admin-group-tag:hover {
  background: #e0f2fe;
  border-color: var(--color-primary, #0284c7);
}

.group-quick-edit-btn {
  opacity: 0.6;
  transition: opacity var(--transition-fast);
  padding: 0 !important;
}

.group-cell:hover .group-quick-edit-btn {
  opacity: 1;
}

.table-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.schedule-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: help;
}

/* 移动端卡片列表样式 (Mobile Card View) */
.mobile-config-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.admin-config-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: var(--shadow-card);
}

.card-top-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.card-title-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  flex: 1;
}

.card-name {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  word-break: break-all;
}

.mobile-group-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  background: #f0f9ff;
  color: var(--color-primary, #0284c7);
  border-color: #bae6fd;
}

.card-size {
  font-size: 12px;
  color: var(--color-primary);
  font-family: monospace;
  flex-shrink: 0;
}

.card-desc {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
  white-space: pre-wrap;
}

.card-props-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.prop-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.prop-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.mobile-schedule-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
}

.no-schedule-tip {
  font-size: 11px;
  color: var(--text-muted);
}

.card-bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid var(--border-color);
  gap: 8px;
  flex-wrap: wrap;
}

.card-date {
  font-size: 11px;
  color: var(--text-muted);
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mobile-action-btn {
  padding: 4px 8px !important;
  font-size: 12px !important;
  height: 26px !important;
  margin: 0 !important;
}

/* 快捷分组标签选择框 */
.preset-groups-box {
  margin-top: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-sm);
}

.preset-title {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.preset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.clickable-preset-tag {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all var(--transition-fast);
}

.clickable-preset-tag:hover {
  transform: translateY(-1px);
  border-color: var(--color-primary);
}

.group-select-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

/* 分组管理中心面板 */
.group-manage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
}

.group-manage-tip {
  font-size: 13px;
  color: var(--text-secondary);
}

.group-name-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.group-manage-table {
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}

/* 弹窗与表单样式 */
.upload-area {
  width: 100%;
}

:deep(.upload-area .el-upload-dragger) {
  background-color: rgba(255, 255, 255, 0.02) !important;
  border: 1px dashed var(--border-color) !important;
}

.schedule-config-panel {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-warning);
}

.panel-body {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sub-label {
  font-size: 12px;
  color: var(--text-secondary);
  display: block;
  margin-bottom: 6px;
}

.schedule-tip {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.5;
}

.visibility-setting-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setting-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.edit-action-btn {
  background: var(--gradient-primary, linear-gradient(135deg, #0284c7 0%, #10b981 100%)) !important;
  border: none !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  border-radius: 6px !important;
  box-shadow: 0 2px 6px rgba(2, 132, 199, 0.25) !important;
}

.edit-action-btn:hover {
  background: var(--gradient-hover, linear-gradient(135deg, #0ea5e9 0%, #34d399 100%)) !important;
  color: #ffffff !important;
  box-shadow: 0 4px 10px rgba(2, 132, 199, 0.35) !important;
}

.edit-action-btn span,
.edit-action-btn .el-icon,
.edit-action-btn i {
  color: #ffffff !important;
  fill: #ffffff !important;
}

@media (max-width: 640px) {
  .page-title {
    font-size: 20px;
  }
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .upload-top-btn {
    width: 100%;
  }
  .filter-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-search-box {
    width: 100%;
  }
  .card-bottom-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .card-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>

