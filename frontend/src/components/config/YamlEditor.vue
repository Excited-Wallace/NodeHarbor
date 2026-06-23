<!--
  YamlEditor - YAML 在线编辑器组件（封装 CodeMirror 6）
  
  Props:
    - modelValue: YAML 文本内容（v-model）
    - readonly: 是否只读模式
  
  Events:
    - @update:modelValue: 内容变化时触发
  
  功能说明：
    - 使用 @codemirror/lang-yaml 提供 YAML 语法高亮
    - 使用 @codemirror/theme-one-dark 暗色主题
    - 支持撤销/重做
    - 行号显示
-->
<template>
  <div>YamlEditor</div>
</template>

<script setup>
</script>

<style scoped>
</style>
