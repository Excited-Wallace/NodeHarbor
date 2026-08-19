<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    :title="title"
    width="400px"
    class="custom-dialog"
    :show-close="false"
  >
    <div class="dialog-content">
      <el-icon :class="['icon', type]">
        <Warning v-if="type === 'warning'" />
        <CircleClose v-else-if="type === 'danger'" />
        <InfoFilled v-else />
      </el-icon>
      <div class="message">{{ message }}</div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="$emit('cancel')" plain>{{ cancelText }}</el-button>
        <el-button :type="type === 'danger' ? 'danger' : 'primary'" @click="$emit('confirm')">
          {{ confirmText }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
defineProps({
  visible: Boolean,
  title: { type: String, default: '确认操作' },
  message: String,
  confirmText: { type: String, default: '确认' },
  cancelText: { type: String, default: '取消' },
  type: { type: String, default: 'warning' }
})
defineEmits(['update:visible', 'confirm', 'cancel'])
</script>

<style scoped>
.dialog-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-top: 10px;
}
.icon {
  font-size: 24px;
}
.icon.warning { color: var(--color-warning); }
.icon.danger { color: var(--color-danger); }
.icon.info { color: var(--color-primary); }
.message {
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.5;
}
</style>
<style>
.custom-dialog {
  background: var(--bg-card) !important;
  backdrop-filter: blur(12px) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: var(--radius-md) !important;
}
.custom-dialog .el-dialog__title {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.custom-dialog .el-dialog__header {
  border-bottom: 1px solid var(--border-color);
  margin-right: 0;
  padding-bottom: 16px;
}
.custom-dialog .el-dialog__footer {
  border-top: 1px solid var(--border-color);
  padding-top: 16px;
}
</style>
