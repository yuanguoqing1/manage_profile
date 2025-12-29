import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const status = ref({ type: '', message: '' })
  const themeMode = ref(localStorage.getItem('themeMode') || 'dark')

  function setStatus(type, message) {
    status.value = { type, message }
    if (message) {
      setTimeout(() => {
        status.value = { type: '', message: '' }
      }, 3200)
    }
  }

  function switchTheme(mode) {
    themeMode.value = mode
    localStorage.setItem('themeMode', mode)
  }

  function setLoading(value) {
    loading.value = value
  }

  return {
    loading,
    status,
    themeMode,
    setStatus,
    switchTheme,
    setLoading,
  }
})
