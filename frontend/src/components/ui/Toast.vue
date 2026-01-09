<template>
  <Transition name="toast">
    <div v-if="visible" :class="['toast', `toast-${type}`]" @click="close">
      <div class="toast-icon">
        <span v-if="type === 'error'">❌</span>
        <span v-else-if="type === 'warning'">⚠️</span>
        <span v-else-if="type === 'success'">✅</span>
        <span v-else>ℹ️</span>
      </div>
      <div class="toast-content">
        <div class="toast-message">{{ message }}</div>
      </div>
      <button class="toast-close" @click.stop="close" aria-label="关闭">
        ×
      </button>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  message: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['error', 'warning', 'success', 'info'].includes(value)
  },
  duration: {
    type: Number,
    default: 3000
  },
  visible: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close'])

const visible = ref(props.visible)
let timer = null

const close = () => {
  visible.value = false
  emit('close')
}

const startTimer = () => {
  if (timer) {
    clearTimeout(timer)
  }
  if (props.duration > 0) {
    timer = setTimeout(() => {
      close()
    }, props.duration)
  }
}

watch(() => props.visible, (newVal) => {
  visible.value = newVal
  if (newVal) {
    startTimer()
  }
})

onMounted(() => {
  if (visible.value) {
    startTimer()
  }
})
</script>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  right: 20px;
  min-width: 300px;
  max-width: 500px;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 9999;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toast:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

.toast-error {
  background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
  color: white;
}

.toast-warning {
  background: linear-gradient(135deg, #ffaa00 0%, #ff8800 100%);
  color: white;
}

.toast-success {
  background: linear-gradient(135deg, #00cc66 0%, #009944 100%);
  color: white;
}

.toast-info {
  background: linear-gradient(135deg, #4488ff 0%, #2266dd 100%);
  color: white;
}

.toast-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-message {
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.toast-close {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toast-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 动画效果 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .toast {
    top: 10px;
    right: 10px;
    left: 10px;
    min-width: auto;
    max-width: none;
  }
}
</style>
