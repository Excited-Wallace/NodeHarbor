<!--
  ConfigEditor - 配置文件在线编辑页面（管理员）
  
  功能说明：
    - 集成 CodeMirror 6 编辑器
    - YAML 语法高亮（使用 @codemirror/lang-yaml）
    - 暗色主题（使用 @codemirror/theme-one-dark）
    - 保存按钮：调用 PUT /api/configs/{id}/content 更新文件
    - 撤销功能
    - 通过路由参数 :id 获取配置文件内容
-->
<template>
  <div>ConfigEditor</div>
</template>

<script setup>
</script>

<style scoped>
</style>
