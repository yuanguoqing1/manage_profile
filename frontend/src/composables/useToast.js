import { ref } from 'vue'

/**
 * Toast通知状态管理
 */
const toasts = ref([])
let toastId = 0

/**
 * Toast通知组合式函数
 * 提供显示和管理Toast通知的功能
 */
export function useToast() {
  /**
   * 显示Toast通知
   * @param {string} message - 通知消息
   * @param {string} type - 通知类型: 'error' | 'warning' | 'success' | 'info'
   * @param {number} duration - 显示时长（毫秒），0表示不自动关闭
   * @returns {number} Toast ID
   */
  const showToast = (message, type = 'info', duration = 3000) => {
    const id = toastId++
    const toast = {
      id,
      message,
      type,
      duration,
      visible: true
    }
    
    toasts.value.push(toast)
    
    // 自动移除
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration + 300) // 加上动画时间
    }
    
    return id
  }

  /**
   * 显示错误通知
   * @param {string} message - 错误消息
   * @param {number} duration - 显示时长
   */
  const showError = (message, duration = 4000) => {
    return showToast(message, 'error', duration)
  }

  /**
   * 显示警告通知
   * @param {string} message - 警告消息
   * @param {number} duration - 显示时长
   */
  const showWarning = (message, duration = 3000) => {
    return showToast(message, 'warning', duration)
  }

  /**
   * 显示成功通知
   * @param {string} message - 成功消息
   * @param {number} duration - 显示时长
   */
  const showSuccess = (message, duration = 3000) => {
    return showToast(message, 'success', duration)
  }

  /**
   * 显示信息通知
   * @param {string} message - 信息消息
   * @param {number} duration - 显示时长
   */
  const showInfo = (message, duration = 3000) => {
    return showToast(message, 'info', duration)
  }

  /**
   * 移除指定Toast
   * @param {number} id - Toast ID
   */
  const removeToast = (id) => {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value[index].visible = false
      // 等待动画完成后移除
      setTimeout(() => {
        toasts.value.splice(index, 1)
      }, 300)
    }
  }

  /**
   * 清除所有Toast
   */
  const clearToasts = () => {
    toasts.value.forEach(toast => {
      toast.visible = false
    })
    setTimeout(() => {
      toasts.value = []
    }, 300)
  }

  return {
    toasts,
    showToast,
    showError,
    showWarning,
    showSuccess,
    showInfo,
    removeToast,
    clearToasts
  }
}
