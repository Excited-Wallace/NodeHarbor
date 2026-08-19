<template>
  <div :class="['spinner-container', { fullscreen }]">
    <div class="spinner">
      <div class="cube1"></div>
      <div class="cube2"></div>
    </div>
    <div v-if="text" class="text">{{ text }}</div>
  </div>
</template>

<script setup>
defineProps({
  fullscreen: {
    type: Boolean,
    default: false
  },
  text: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.spinner-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  min-height: 100px;
}
.spinner-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(4px);
  z-index: 9999;
}
.spinner {
  margin: 20px auto;
  width: 40px;
  height: 40px;
  position: relative;
}
.cube1, .cube2 {
  background-color: var(--color-primary);
  width: 15px;
  height: 15px;
  position: absolute;
  top: 0;
  left: 0;
  animation: sk-cubemove 1.8s infinite ease-in-out;
}
.cube2 {
  animation-delay: -0.9s;
}
.text {
  margin-top: 10px;
  color: var(--text-secondary);
  font-size: 14px;
}
@keyframes sk-cubemove {
  25% { transform: translateX(42px) rotate(-90deg) scale(0.5); }
  50% { transform: translateX(42px) translateY(42px) rotate(-180deg); }
  75% { transform: translateX(0px) translateY(42px) rotate(-270deg) scale(0.5); }
  100% { transform: rotate(-360deg); }
}
</style>
