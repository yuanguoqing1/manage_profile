import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './auth'

const MAX_RETRY = 10

export const useWebSocketStore = defineStore('websocket', () => {
  const wsRef = ref(null)
  const wsConnected = ref(false)
  const wsConnecting = ref(false)
  const wsRetry = ref(0)
  
  let wsReconnectTimer = null
  let wsHeartbeatTimer = null

  const connectionStatus = computed(() => {
    if (wsConnected.value) return 'connected'
    if (wsConnecting.value) return 'connecting'
    return 'disconnected'
  })

  function clearWsTimers() {
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer)
      wsReconnectTimer = null
    }
    if (wsHeartbeatTimer) {
      clearInterval(wsHeartbeatTimer)
      wsHeartbeatTimer = null
    }
  }

  function disconnect() {
    clearWsTimers()
    wsConnected.value = false
    wsConnecting.value = false
    wsRetry.value = 0
    try {
      wsRef.value?.close?.()
    } catch {}
    wsRef.value = null
  }

  function scheduleReconnect() {
    clearWsTimers()
    const authStore = useAuthStore()
    if (!authStore.token) return

    if (wsRetry.value >= MAX_RETRY) {
      console.error('WebSocket 重连次数超过限制')
      return
    }

    const base = Math.min(800 * Math.pow(2, wsRetry.value), 12000)
    const jitter = Math.floor(Math.random() * 400)
    const delay = base + jitter

    wsReconnectTimer = setTimeout(() => {
      wsRetry.value += 1
      connect()
    }, delay)
  }

  function buildWsUrl(apiBase, token) {
    const base = new URL(apiBase)
    base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
    base.pathname = '/ws'
    base.search = `?token=${encodeURIComponent(token || '')}`
    return base.toString()
  }

  function connect(apiBase, onMessage) {
    const authStore = useAuthStore()
    if (!authStore.token) return

    if (wsRef.value && (wsRef.value.readyState === WebSocket.OPEN || wsRef.value.readyState === WebSocket.CONNECTING)) {
      return
    }

    wsConnecting.value = true
    wsConnected.value = false

    let wsUrl = ''
    try {
      wsUrl = buildWsUrl(apiBase, authStore.token)
    } catch (e) {
      wsConnecting.value = false
      console.error('WebSocket 地址解析失败', e)
      return
    }

    const ws = new WebSocket(wsUrl)
    wsRef.value = ws

    ws.onopen = () => {
      wsConnected.value = true
      wsConnecting.value = false
      wsRetry.value = 0

      clearWsTimers()
      wsHeartbeatTimer = setInterval(() => {
        try {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping')
        } catch {}
      }, 20000)
    }

    ws.onmessage = (evt) => {
      if (onMessage) onMessage(evt)
    }

    ws.onclose = () => {
      wsConnected.value = false
      wsConnecting.value = false
      scheduleReconnect()
    }

    ws.onerror = () => {
      wsConnected.value = false
      wsConnecting.value = false
      try { ws.close() } catch {}
    }
  }

  return {
    wsConnected,
    wsConnecting,
    connectionStatus,
    connect,
    disconnect,
  }
})
