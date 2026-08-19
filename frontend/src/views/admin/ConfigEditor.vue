<!--
  ConfigEditor.vue - 配置文件在线编辑页面（管理员）
  
  文件功能说明：
    - 管理员编辑 Clash/Node 配置文件内容的页面
    - 使用 CodeMirror 6 (YamlEditor 组件) 实现高效 YAML 编辑
    - 支持保存、返回列表、实时状态反馈与错误捕获
    - 针对移动端屏幕优化头部操作栏排列与编辑器高度自适应
  
  接口调用说明：
    - GET /api/configs/{id} (getConfigDetail): 获取配置的基础元数据
    - GET /api/configs/{id}/content (getContent): 获取配置文件的完整文本内容
    - PUT /api/configs/{id}/content (updateContent): 将修改后的 YAML 文本写回服务器
-->
<template>
  <div class="editor-page-container">
    <!-- 头部操作栏：返回按钮、配置标题与保存按钮 -->
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="Back" plain size="small">返回</el-button>
        <h2 class="page-title" :title="configName">
          编辑: {{ configName || '加载中...' }}
        </h2>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleSave" :loading="saving" :icon="Check" size="small">
          保存修改
        </el-button>
      </div>
    </div>

    <!-- 主编辑区域：loading 转圈与编辑器挂载 -->
    <div class="editor-content" v-loading="loading" element-loading-text="正在加载配置文件内容...">
      <YamlEditor v-if="!loading && !loadFailed" v-model="yamlContent" />
      
      <!-- 加载失败时的重试提示 -->
      <div v-if="loadFailed && !loading" class="error-container">
        <el-empty description="配置文件加载失败">
          <el-button type="primary" @click="loadData">重试加载</el-button>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 引入依赖与 API
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getConfigDetail, getContent, updateContent } from '../../api/configs'
import YamlEditor from '../../components/config/YamlEditor.vue'
import { ElMessage } from 'element-plus'
import { Back, Check } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 当前配置 ID（从路由参数中解析）
const configId = route.params.id

// 页面响应式状态定义
const configName = ref('')
const yamlContent = ref('')
const loading = ref(true)
const saving = ref(false)
const loadFailed = ref(false)

/**
 * 加载配置元数据及文本内容
 */
const loadData = async () => {
  loading.value = true
  loadFailed.value = false
  try {
    const detailRes = await getConfigDetail(configId)
    configName.value = detailRes.data?.name || `Config #${configId}`
    
    const contentRes = await getContent(configId)
    yamlContent.value = contentRes.data?.content ?? ''
  } catch (error) {
    loadFailed.value = true
    ElMessage.error('加载配置文件失败，请检查网络或后端状态')
    console.error('Failed to load configuration:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 保存配置文件内容
 */
const handleSave = async () => {
  saving.value = true
  try {
    await updateContent(configId, yamlContent.value)
    ElMessage.success('配置文件保存成功')
  } catch (error) {
    ElMessage.error('保存失败，请稍后重试')
    console.error('Failed to save configuration:', error)
  } finally {
    saving.value = false
  }
}

/**
 * 返回上一页路由
 */
const goBack = () => {
  router.back()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.editor-page-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  gap: 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.editor-content {
  flex: 1;
  min-height: 0;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  overflow: hidden;
  position: relative;
  border: 1px solid var(--border-color);
}

.error-container {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

@media (max-width: 600px) {
  .page-title {
    font-size: 15px;
  }
}
</style>
