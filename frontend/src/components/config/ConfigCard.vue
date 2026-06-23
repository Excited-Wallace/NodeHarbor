<!--
  ConfigCard - 配置文件卡片组件
  
  Props:
    - config: 配置文件对象 { id, name, description, file_size, created_at, updated_at }
    - showActions: 是否显示管理操作（编辑/删除），管理员模式为 true
  
  Events:
    - @download: 下载配置文件
    - @edit: 编辑配置文件（仅管理员）
    - @delete: 删除配置文件（仅管理员）
    - @copy-link: 复制订阅链接
-->
<template>
  <div>ConfigCard</div>
</template>

<script setup>
</script>

<style scoped>
</style>
