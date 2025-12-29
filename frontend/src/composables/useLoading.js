import { ref } from 'vue'

/**
 * 加载状态管理 Composable
 * @param {boolean} initialState - 初始加载状态
 * @returns {Object} 加载状态和控制方法
 */
export function useLoading(initialState = false) {
  const loading = ref(initialState)
  const loadingText = ref('')

  /**
   * 开始加载
   * @param {string} text - 加载提示文本
   */
  function startLoading(text = '加载中...') {
    loading.value = true
    loadingText.value = text
  }

  /**
   * 停止加载
   */
  function stopLoading() {
    loading.value = false
    loadingText.value = ''
  }

  /**
   * 包装异步函数，自动管理加载状态
   * @param {Function} fn - 异步函数
   * @param {string} text - 加载提示文本
   * @returns {Function} 包装后的函数
   */
  function withLoading(fn, text = '加载中...') {
    return async (...args) => {
      startLoading(text)
      try {
        return await fn(...args)
      } finally {
        stopLoading()
      }
    }
  }

  return {
    loading,
    loadingText,
    startLoading,
    stopLoading,
    withLoading,
  }
}

/**
 * 防止重复提交的 Composable
 * @returns {Object} 提交状态和控制方法
 */
export function useSubmit() {
  const submitting = ref(false)

  /**
   * 包装提交函数，防止重复提交
   * @param {Function} fn - 提交函数
   * @returns {Function} 包装后的函数
   */
  function withSubmit(fn) {
    return async (...args) => {
      if (submitting.value) {
        console.warn('请勿重复提交')
        return
      }

      submitting.value = true
      try {
        return await fn(...args)
      } finally {
        submitting.value = false
      }
    }
  }

  return {
    submitting,
    withSubmit,
  }
}
