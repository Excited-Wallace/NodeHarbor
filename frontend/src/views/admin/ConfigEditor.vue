<!--
  ConfigEditor.vue - 配置文件在线编辑页面（管理员）
  
  文件功能说明：
    - 管理员编辑 Clash/Node 配置文件内容的页面
    - 使用 CodeMirror 6 (YamlEditor 组件) 实现高效 YAML 编辑
    - 支持保存、返回列表、实时状态反馈与错误捕获
  
  接口调用说明：
    - GET /api/configs/{id} (getConfigDetail): 获取配置的基础元数据（如名称、大小等）
    - GET /api/configs/{id}/content (getContent): 获取配置文件的完整文本内容
    - PUT /api/configs/{id}/content (updateContent): 将修改后的 YAML 文本写回服务器
-->
<template>
  <div class="editor-page-container">
    <!-- 头部操作栏：返回按钮、配置标题与保存按钮 -->
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="Back" plain>返回</el-button>
        <h2 class="page-title">编辑配置: {{ configName || '加载中...' }}</h2>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleSave" :loading="saving" :icon="Check">
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
 * 
 * 步骤：
 * 1. 调用 getConfigDetail(configId) 获取配置名称
 * 2. 调用 getContent(configId) 获取文本内容
 * 3. 赋值给 yamlContent 供编辑器展示
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
 * 
 * 步骤：
 * 1. 触发保存 loading 状态
 * 2. 调用 updateContent(configId, content) 发送 PUT 请求
 * 3. 提示成功或捕获异常并反馈
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
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.editor-content {
  flex: 1;
  min-height: 0;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  overflow: hidden;
  position: relative;
}

.error-container {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>

