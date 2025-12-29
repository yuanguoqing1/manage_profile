/**
 * 全局错误处理器
 */

const ERROR_MESSAGES = {
  400: '请求参数错误',
  401: '登录已失效，请重新登录',
  403: '权限不足',
  404: '请求的资源不存在',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误',
  502: '网关错误',
  503: '服务暂时不可用',
  504: '网关超时',
}

/**
 * 格式化错误消息
 * @param {Error|Object} error - 错误对象
 * @returns {string} 用户友好的错误消息
 */
export function formatErrorMessage(error) {
  // 网络错误
  if (error.message === 'Failed to fetch' || error.message === 'Network request failed') {
    return '网络连接失败，请检查网络设置'
  }

  // HTTP 状态码错误
  if (error.status || error.statusCode) {
    const status = error.status || error.statusCode
    const defaultMessage = ERROR_MESSAGES[status] || `请求失败 (${status})`
    return error.message || error.detail || defaultMessage
  }

  // 自定义错误消息
  if (error.detail) {
    return error.detail
  }

  if (error.message) {
    return error.message
  }

  return '操作失败，请稍后重试'
}

/**
 * 全局错误处理函数
 * @param {Error} error - 错误对象
 * @param {Function} setStatus - 设置状态的函数
 */
export function handleError(error, setStatus) {
  console.error('Error:', error)
  
  const message = formatErrorMessage(error)
  
  if (setStatus) {
    setStatus('error', message)
  }
  
  return message
}

/**
 * 创建 Vue 错误处理器
 * @param {Function} setStatus - 设置状态的函数
 * @returns {Function} Vue 错误处理器
 */
export function createVueErrorHandler(setStatus) {
  return (err, instance, info) => {
    console.error('Vue Error:', err, info)
    handleError(err, setStatus)
  }
}

/**
 * 创建全局未捕获错误处理器
 * @param {Function} setStatus - 设置状态的函数
 */
export function setupGlobalErrorHandlers(setStatus) {
  // 捕获未处理的 Promise 错误
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise Rejection:', event.reason)
    handleError(event.reason, setStatus)
    event.preventDefault()
  })

  // 捕获全局错误
  window.addEventListener('error', (event) => {
    console.error('Global Error:', event.error)
    if (event.error) {
      handleError(event.error, setStatus)
    }
  })
}
