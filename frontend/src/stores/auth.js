import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const currentUser = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthed = computed(() => Boolean(token.value))
  const isAdmin = computed(() => currentUser.value?.role === 'admin')

  function setAuth(newToken, user) {
    token.value = newToken
    currentUser.value = user
    localStorage.setItem('token', newToken)
    localStorage.setItem('user', JSON.stringify(user))
  }

  function clearAuth() {
    token.value = ''
    currentUser.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    token,
    currentUser,
    isAuthed,
    isAdmin,
    setAuth,
    clearAuth,
  }
})
