<!--
  ClientsView - 代理客户端下载页面（管理员和用户共用）
  
  功能说明：
    - 按客户端分类展示下载选项
    - 支持的客户端：
      - V2Ray (v2fly/v2ray-core) - Windows / Linux / macOS
      - Clash Verge (clash-verge-rev/clash-verge-rev) - Windows / Linux / macOS
      - V2RayNG (2dust/v2rayNG) - Android
      - Clash Meta (MetaCubeX/ClashMetaForAndroid) - Android
    - 下载流程：
      1. 用户点击下载
      2. 前端调用 POST /api/clients/{name}/fetch 触发服务器下载
      3. 轮询 GET /api/clients/{name}/status 显示下载进度
      4. 下载完成后调用 GET /api/clients/{name}/download 传输给用户
    - 缓存的文件 1 小时后过期
-->
<template>
  <div>ClientsView</div>
</template>

<script setup>
</script>

<style scoped>
</style>
