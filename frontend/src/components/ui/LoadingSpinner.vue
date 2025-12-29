<template>
  <div v-if="show" :class="['loading-spinner', size, { overlay }]">
    <div class="spinner">
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
    </div>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  show: {
    type: Boolean,
    default: true,
  },
  size: {
    type: String,
    default: 'medium', // small, medium, large
    validator: (value) => ['small', 'medium', 'large'].includes(value),
  },
  text: {
    type: String,
    default: '',
  },
  overlay: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.loading-spinner.overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9999;
}

.spinner {
  position: relative;
  display: inline-block;
}

.small .spinner {
  width: 24px;
  height: 24px;
}

.medium .spinner {
  width: 40px;
  height: 40px;
}

.large .spinner {
  width: 60px;
  height: 60px;
}

.spinner-ring {
  position: absolute;
  border: 3px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}

.small .spinner-ring {
  width: 24px;
  height: 24px;
  border-width: 2px;
}

.medium .spinner-ring {
  width: 40px;
  height: 40px;
  border-width: 3px;
}

.large .spinner-ring {
  width: 60px;
  height: 60px;
  border-width: 4px;
}

.spinner-ring:nth-child(1) {
  animation-delay: -0.45s;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.3s;
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.15s;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin: 0;
  font-size: 14px;
  color: currentColor;
}

.overlay .loading-text {
  color: white;
}
</style>
