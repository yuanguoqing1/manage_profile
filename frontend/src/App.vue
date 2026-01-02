<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { routes } from './router'
import { startChristmasEffects, stopChristmasEffects } from './utils/christmasEffects'

const apiBase = import.meta.env.DEV
  ? (import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8001')
  : ''

const loading = ref(false)
const chatLoading = ref(false)
const status = ref({ type: '', message: '' })
const activeMenu = ref('home')
const expandedMenus = ref({ chat: false, admin: false, favorites: false })
const themeMode = ref(localStorage.getItem('themeMode') || 'dark')
const christmasActive = ref(false)

const token = ref(localStorage.getItem('token') || '')
const currentUser = ref(JSON.parse(localStorage.getItem('user') || 'null'))

const dashboard = ref({
  redis: { register_count: 0, online_count: 0 },
  date: '',
  ip: '',
  weather: '',
})

const users = ref([])
const models = ref([])
const selectedModel = ref(null)
const categories = ref([])
const pages = ref([])
const selectedCategory = ref(null)
const logs = ref([])
const roleStats = ref({ admin: 0, user: 0 })
const rolePrompts = ref([])
const selectedRoleId = ref(null)
const editingRolePrompt = ref(null)
const chatMessages = ref([])
const chatInput = ref('')
const chatModelId = ref(null)
const contacts = ref([])
const peerMessages = ref([])
const selectedPeerId = ref(null)
const peerInput = ref('')
const peerSending = ref(false)
const peerMessagesLoading = ref(false)
const contactSearch = ref('')

// 用户管理搜索和分页
const userSearch = ref({ name: '', role: '', phone: '' })
const userPage = ref(1)
const userPageSize = 10

// 日记相关状态
const diaries = ref([])
const selectedDiary = ref(null)
const diaryForm = ref({ title: '', content: '', mood: '😊' })
const diaryEditing = ref(false)

// 相册相关状态
const albums = ref([])
const selectedAlbum = ref(null)
const albumPhotos = ref([])
const albumForm = ref({ name: '', description: '' })
const photoCaption = ref('')
const photoUploading = ref(false)
const previewPhoto = ref(null)
const isDragging = ref(false)
const showAllPhotos = ref(false)
const photosPerPage = 12

// 签到相关状态
const checkInLoading = ref(false)
const todayCheckedIn = ref(false)

// 消息通知状态
const notifications = ref([])
let notificationId = 0

// 地图相关状态
const mapLoaded = ref(false)
const mapInstance = ref(null)
const userLocation = ref(null)
const locationError = ref('')
const mapMarker = ref(null)
const isRequestingLocation = ref(false)
const showManualLocationInput = ref(false)
const manualAddress = ref('')
const manualLng = ref('')
const manualLat = ref('')

// 地图AI聊天状态
const mapChatMessages = ref([])
const mapChatInput = ref('')
const mapChatLoading = ref(false)

// 聊天消息容器ref
const chatBodyRef = ref(null)

const defaultRolePrompt =
  '你是一位可靠的智能助手，请保持简洁、专业并主动提供有用的下一步建议。'

// 未读数：key=peerId, value=count
const unreadMap = ref({})
// 联系人最近一条消息预览（可选展示）
const lastPreviewMap = ref({})

const modals = ref({
  login: false,
  register: false,
  user: false,
  model: false,
  category: false,
  page: false,
  pageEdit: false,
  role: false,
  rolePrompt: false,
  rolePromptEdit: false,
  userEdit: false,
  modelEdit: false,
  profileEdit: false,
})

const forms = ref({
  login: { name: '', password: '' },
  register: { name: '', password: '', role: 'user' },
  user: { name: '', password: '', role: 'user' },
  editUser: { id: null, name: '', password: '', role: 'user' },
  model: {
    name: '',
    base_url: '',
    api_key: '',
    model_name: '',
    max_tokens: 4096,
    temperature: 1,
    owner_id: '',
  },
  editModel: {
    id: null,
    name: '',
    base_url: '',
    api_key: '',
    model_name: '',
    max_tokens: 4096,
    temperature: 1,
    owner_id: '',
  },
  category: { name: '', description: '' },
  page: { category_id: '', url: '', account: '', password: '', cookie: '', note: '' },
  editPage: { id: null, category_id: '', url: '', account: '', password: '', cookie: '', note: '' },
  balance: { userId: '', amount: 0 },
  role: { user_id: '', role: 'user' },
  rolePrompt: { name: '', prompt: '' },
  editRolePrompt: { id: null, name: '', prompt: '' },
  profileEdit: { name: '', password: '', email: '', phone: '' },
})

const reportTrend = ref([52, 66, 48, 72, 95, 88, 76, 110, 90, 130])
const registerTrend = ref([8, 16, 20, 12, 18, 26, 24])

const isAuthed = computed(() => Boolean(token.value))
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const currentChatModel = computed(() => models.value.find((m) => m.id === chatModelId.value))

const currentRolePrompt = computed(() => {
  const target = rolePrompts.value.find((item) => item.id === selectedRoleId.value)
  if (target) return target.prompt
  return defaultRolePrompt
})

const isDarkMode = computed(() => themeMode.value === 'dark')

const availableContacts = computed(() => {
  const keyword = contactSearch.value.trim().toLowerCase()
  return contacts.value
    .filter((item) => item.id !== currentUser.value?.id)
    .filter((item) => !keyword || item.name.toLowerCase().includes(keyword))
    .sort((a, b) => {
      // 未读优先，其次在线优先，其次名字
      const au = Number(unreadMap.value?.[a.id] || 0)
      const bu = Number(unreadMap.value?.[b.id] || 0)
      if (au !== bu) return bu - au
      if (a.is_online !== b.is_online) return a.is_online ? -1 : 1
      return a.name.localeCompare(b.name)
    })
})

const selectedPeer = computed(() => contacts.value.find((item) => item.id === selectedPeerId.value) || null)

// 照片分页显示
const displayedPhotos = computed(() => {
  if (showAllPhotos.value) return albumPhotos.value
  return albumPhotos.value.slice(0, photosPerPage)
})

// 用户筛选和分页
const filteredUsers = computed(() => {
  return users.value.filter(u => {
    if (userSearch.value.name && !u.name.toLowerCase().includes(userSearch.value.name.toLowerCase())) return false
    if (userSearch.value.role && u.role !== userSearch.value.role) return false
    if (userSearch.value.phone && u.phone && !u.phone.includes(userSearch.value.phone)) return false
    return true
  })
})

const paginatedUsers = computed(() => {
  const start = (userPage.value - 1) * userPageSize
  return filteredUsers.value.slice(start, start + userPageSize)
})

const userTotalPages = computed(() => Math.ceil(filteredUsers.value.length / userPageSize) || 1)

let statusTimer = null
function setStatus(type, message) {
  // 清除之前的定时器，避免重复
  if (statusTimer) {
    clearTimeout(statusTimer)
    statusTimer = null
  }
  status.value = { type, message }
  if (message) {
    statusTimer = setTimeout(() => {
      status.value = { type: '', message: '' }
      statusTimer = null
    }, 2500) // 缩短显示时间
  }
}

function setAuth(newToken, user) {
  token.value = newToken
  currentUser.value = user
  localStorage.setItem('token', newToken)
  localStorage.setItem('user', JSON.stringify(user))
}

function clearAuth() {
  disconnectWs()

  token.value = ''
  currentUser.value = null
  rolePrompts.value = []
  selectedRoleId.value = null
  contacts.value = []
  peerMessages.value = []
  selectedPeerId.value = null
  peerInput.value = ''
  unreadMap.value = {}
  lastPreviewMap.value = {}
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

function truncateUrl(url, maxLen = 40) {
  if (!url || url.length <= maxLen) return url
  return url.slice(0, maxLen) + '...'
}

function escapeHtml(input) {
  return (input || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderMarkdown(content) {
  const escaped = escapeHtml(content)
  const withBlocks = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
  const withInline = withBlocks
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
  const paragraphs = withInline
    .split(/\n{2,}/)
    .map((part) => part.replace(/\n/g, '<br />'))
    .join('</p><p>')
  return `<p>${paragraphs}</p>`
}

function applyThemeClasses() {
  const root = document.documentElement
  if (!root) return
  root.classList.toggle('dark-mode', themeMode.value === 'dark')
  root.classList.toggle('light-mode', themeMode.value === 'light')
}

function switchTheme(mode) {
  themeMode.value = mode
  localStorage.setItem('themeMode', mode)
}

function toggleChristmas() {
  christmasActive.value = !christmasActive.value
  if (christmasActive.value) startChristmasEffects()
  else stopChristmasEffects()
}

function getRouteFromHash() {
  if (typeof window === 'undefined') return '/'
  const hash = window.location.hash || ''
  const path = hash.replace(/^#/, '').trim()
  return path || '/'
}

function resolveRoute(path) {
  return routes.find((route) => route.path === path) || null
}

function navigateTo(menu, options = {}) {
  const target = routes.find((route) => route.menu === menu)
  if (!target) return
  if (target.requiresAdmin && !isAdmin.value) return
  if (target.requiresAuth && !isAuthed.value) return
  activeMenu.value = target.menu
  
  // 如果切换到地图页面，需要调整地图大小
  if (menu === 'map' && mapLoaded.value && mapInstance.value) {
    // 使用nextTick确保DOM已更新
    setTimeout(() => {
      mapInstance.value.resize()
    }, 100)
  }
  
  if (typeof window === 'undefined') return
  const url = `#${target.path}`
  if (options.replace) window.history.replaceState(null, '', url)
  else window.location.hash = target.path
}

function syncRouteFromLocation() {
  const path = getRouteFromHash()
  const route = resolveRoute(path)
  if (!route) {
    navigateTo('home', { replace: true })
    return
  }
  if (route.requiresAdmin && !isAdmin.value) {
    navigateTo('home', { replace: true })
    return
  }
  if (route.requiresAuth && !isAuthed.value) {
    navigateTo('home', { replace: true })
    return
  }
  activeMenu.value = route.menu
}

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (token.value) {
    headers.Authorization = `Bearer ${token.value}`
  }
  const response = await fetch(`${apiBase}${path}`, { ...options, headers })
  const rawText = response.status === 204 ? '' : await response.text()
  let data = null
  if (rawText) {
    try {
      data = JSON.parse(rawText)
    } catch (error) {
      data = { detail: rawText }
    }
  }

  if (response.status === 401) {
    clearAuth()
    models.value = []
    users.value = []
    categories.value = []
    pages.value = []
    logs.value = []
    rolePrompts.value = []
    selectedRoleId.value = null
    chatMessages.value = []
    chatInput.value = ''
    dashboard.value = { redis: { register_count: 0, online_count: 0 }, date: '', ip: '', weather: '' }
    throw new Error('登录已失效，请重新登录')
  }

  if (!response.ok) {
    throw new Error(data?.detail || data?.error || '请求失败')
  }
  return data
}

async function fetchDashboard() {
  // 使用地图位置的城市，默认威县
  const city = userLocation.value?.city || '威县'
  const data = await request(`/dashboard?city=${encodeURIComponent(city)}`)
  dashboard.value = data
}

async function fetchUsers() {
  if (!isAdmin.value) {
    users.value = []
    return
  }
  users.value = await request('/users')
}

async function fetchModels() {
  models.value = await request('/models')
  if (selectedModel.value) {
    const refreshed = models.value.find((m) => m.id === selectedModel.value.id)
    selectedModel.value = refreshed || null
  }
  if (!chatModelId.value && models.value.length) {
    chatModelId.value = models.value[0].id
  }
}

async function fetchCategories() {
  categories.value = await request('/web/categories')
  if (selectedCategory.value) {
    const refreshed = categories.value.find((c) => c.id === selectedCategory.value.id)
    selectedCategory.value = refreshed || null
  }
}

async function fetchPages(categoryId = null) {
  const query = categoryId ? `?category_id=${categoryId}` : ''
  pages.value = await request(`/web/pages${query}`)
}

// 日记相关函数
async function fetchDiaries() {
  try {
    diaries.value = await request('/diaries')
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function createDiary() {
  try {
    await request('/diaries', {
      method: 'POST',
      body: JSON.stringify(diaryForm.value),
    })
    setStatus('success', '日记已保存')
    diaryForm.value = { title: '', content: '', mood: '😊' }
    await fetchDiaries()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function updateDiary() {
  if (!selectedDiary.value) return
  try {
    await request(`/diaries/${selectedDiary.value.id}`, {
      method: 'PUT',
      body: JSON.stringify(diaryForm.value),
    })
    setStatus('success', '日记已更新')
    diaryEditing.value = false
    selectedDiary.value = null
    diaryForm.value = { title: '', content: '', mood: '😊' }
    await fetchDiaries()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function deleteDiary(id) {
  if (!confirm('确认删除这篇日记吗？')) return
  try {
    await request(`/diaries/${id}`, { method: 'DELETE' })
    setStatus('success', '日记已删除')
    if (selectedDiary.value?.id === id) {
      selectedDiary.value = null
      diaryEditing.value = false
    }
    await fetchDiaries()
  } catch (error) {
    setStatus('error', error.message)
  }
}

function openDiaryEdit(diary) {
  selectedDiary.value = diary
  diaryForm.value = { title: diary.title, content: diary.content, mood: diary.mood || '😊' }
  diaryEditing.value = true
}

function cancelDiaryEdit() {
  selectedDiary.value = null
  diaryEditing.value = false
  diaryForm.value = { title: '', content: '', mood: '😊' }
}

// 签到相关函数
async function handleCheckIn() {
  if (checkInLoading.value || todayCheckedIn.value) return
  checkInLoading.value = true
  try {
    const res = await request('/user/check_in', { method: 'POST' })
    setStatus('success', `签到成功！连续${res.LDC}天，奖励${res.reward}积分`)
    todayCheckedIn.value = true
    // 更新本地用户信息
    if (currentUser.value) {
      currentUser.value.LDC = res.LDC
      currentUser.value.balance = res.balance
      localStorage.setItem('user', JSON.stringify(currentUser.value))
    }
  } catch (error) {
    setStatus('error', error.message)
  } finally {
    checkInLoading.value = false
  }
}

function checkTodayCheckIn() {
  // 检查今天是否已签到（通过比较 last_check_in）
  if (currentUser.value?.last_check_in) {
    const today = new Date().toISOString().split('T')[0]
    todayCheckedIn.value = currentUser.value.last_check_in === today
  } else {
    todayCheckedIn.value = false
  }
}

// 相册相关函数
async function fetchAlbums() {
  try {
    albums.value = await request('/albums')
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function createAlbum() {
  if (!albumForm.value.name.trim()) {
    setStatus('error', '请输入相册名称')
    return
  }
  try {
    await request('/albums', {
      method: 'POST',
      body: JSON.stringify(albumForm.value),
    })
    setStatus('success', '相册已创建')
    albumForm.value = { name: '', description: '' }
    await fetchAlbums()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function deleteAlbum(id) {
  if (!confirm('确认删除该相册及所有照片吗？')) return
  try {
    await request(`/albums/${id}`, { method: 'DELETE' })
    setStatus('success', '相册已删除')
    if (selectedAlbum.value?.id === id) {
      selectedAlbum.value = null
      albumPhotos.value = []
    }
    await fetchAlbums()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function openAlbum(album) {
  selectedAlbum.value = album
  showAllPhotos.value = false
  try {
    albumPhotos.value = await request(`/albums/${album.id}/photos`)
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function uploadPhoto(event) {
  const file = event.target.files?.[0]
  if (!file || !selectedAlbum.value) return
  
  photoUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('album_id', selectedAlbum.value.id)
    formData.append('caption', photoCaption.value)
    
    const headers = {}
    if (token.value) {
      headers.Authorization = `Bearer ${token.value}`
    }
    
    const response = await fetch(`${apiBase}/photos/upload`, {
      method: 'POST',
      headers,
      body: formData,
    })
    
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || '上传失败')
    }
    
    setStatus('success', '照片已上传')
    photoCaption.value = ''
    event.target.value = ''
    await openAlbum(selectedAlbum.value)
    await fetchAlbums() // 刷新封面
  } catch (error) {
    setStatus('error', error.message)
  } finally {
    photoUploading.value = false
  }
}

async function deletePhoto(id) {
  if (!confirm('确认删除这张照片吗？')) return
  try {
    await request(`/photos/${id}`, { method: 'DELETE' })
    setStatus('success', '照片已删除')
    await openAlbum(selectedAlbum.value)
  } catch (error) {
    setStatus('error', error.message)
  }
}

function openPreview(photo) {
  previewPhoto.value = photo
}

function closePreview() {
  previewPhoto.value = null
}

function handleDragOver(e) {
  e.preventDefault()
  isDragging.value = true
}

function handleDragLeave(e) {
  e.preventDefault()
  isDragging.value = false
}

async function handleDrop(e) {
  e.preventDefault()
  isDragging.value = false
  
  if (!selectedAlbum.value) {
    setStatus('error', '请先选择一个相册')
    return
  }
  
  const files = e.dataTransfer?.files
  if (!files || files.length === 0) return
  
  for (const file of files) {
    if (!file.type.startsWith('image/')) continue
    await uploadFileToAlbum(file)
  }
}

async function uploadFileToAlbum(file) {
  photoUploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('album_id', selectedAlbum.value.id)
    formData.append('caption', photoCaption.value)
    
    const headers = {}
    if (token.value) {
      headers.Authorization = `Bearer ${token.value}`
    }
    
    const response = await fetch(`${apiBase}/photos/upload`, {
      method: 'POST',
      headers,
      body: formData,
    })
    
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || '上传失败')
    }
    
    setStatus('success', '照片已上传')
    photoCaption.value = ''
    await openAlbum(selectedAlbum.value)
    await fetchAlbums()
  } catch (error) {
    setStatus('error', error.message)
  } finally {
    photoUploading.value = false
  }
}

async function fetchRoles() {
  if (!isAdmin.value) {
    roleStats.value = { admin: 0, user: 0 }
    return
  }
  const res = await request('/roles')
  roleStats.value = res.roles
}

async function fetchRolePrompts() {
  const res = await request('/role-prompts')
  rolePrompts.value = res
  if (!selectedRoleId.value && rolePrompts.value.length) {
    selectedRoleId.value = rolePrompts.value[0].id
  }
}

async function fetchLogs() {
  if (!isAdmin.value) {
    logs.value = []
    return
  }
  const res = await request('/logs')
  logs.value = res.lines || []
}

function clearUnread(peerId) {
  if (!peerId) return
  unreadMap.value = { ...unreadMap.value, [peerId]: 0 }
}

function incUnread(peerId) {
  if (!peerId) return
  const current = Number(unreadMap.value?.[peerId] || 0)
  unreadMap.value = { ...unreadMap.value, [peerId]: current + 1 }
}

function setLastPreview(peerId, content) {
  if (!peerId) return
  const trimmed = (content || '').trim()
  if (!trimmed) return
  const preview = trimmed.length > 30 ? `${trimmed.slice(0, 30)}…` : trimmed
  lastPreviewMap.value = { ...lastPreviewMap.value, [peerId]: preview }
}

async function fetchContacts({ keepSelected = true } = {}) {
  if (!isAuthed.value) {
    contacts.value = []
    return
  }
  try {
    contacts.value = await request('/contacts')
    if (!keepSelected) {
      selectedPeerId.value = contacts.value[0]?.id || null
      if (selectedPeerId.value) await fetchPeerMessages(selectedPeerId.value)
      return
    }
    // 保持已选会话
    const hasSelected = contacts.value.some((item) => item.id === selectedPeerId.value)
    if (!hasSelected) {
      selectedPeerId.value = contacts.value[0]?.id || null
    }
    if (selectedPeerId.value) {
      await fetchPeerMessages(selectedPeerId.value)
    }
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function fetchPeerMessages(peerId) {
  if (!peerId) return
  peerMessagesLoading.value = true
  try {
    const res = await request(`/contacts/messages/${peerId}`)
    peerMessages.value = res || []
    // 更新预览
    const last = peerMessages.value[peerMessages.value.length - 1]
    if (last?.content) setLastPreview(peerId, last.content)
    // 打开会话即清未读
    clearUnread(peerId)
  } catch (error) {
    setStatus('error', error.message)
  } finally {
    peerMessagesLoading.value = false
  }
}

async function openPeerChat(contact) {
  selectedPeerId.value = contact.id
  await fetchPeerMessages(contact.id)
}

async function syncAll() {
  loading.value = true
  try {
    await Promise.all([
      fetchDashboard(),
      fetchModels(),
      fetchCategories(),
      fetchPages(selectedCategory.value?.id || null),
      fetchUsers(),
      fetchRoles(),
      fetchRolePrompts(),
      fetchLogs(),
      fetchContacts(),
      fetchDiaries(),
      fetchAlbums(),
    ])
    setStatus('success', '数据已同步')
  } catch (error) {
    setStatus('error', error.message)
  } finally {
    loading.value = false
  }
}

async function handleLogin() {
  try {
    const res = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(forms.value.login),
    })
    setAuth(res.token, res.user)
    modals.value.login = false
    setStatus('success', '登录成功')
    await syncAll()
    checkTodayCheckIn()
    connectWs()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function handleRegister() {
  try {
    const payload = { ...forms.value.register }
    if (!payload.role) payload.role = 'user'
    const res = await request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    setStatus('success', `注册成功：${res.name}`)
    modals.value.register = false
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function handleLogout() {
  try {
    await request('/auth/logout', { method: 'POST' })
  } catch (error) {
    console.warn('登出提示：', error.message)
  }
  clearAuth()
  models.value = []
  users.value = []
  categories.value = []
  pages.value = []
  logs.value = []
  rolePrompts.value = []
  selectedRoleId.value = null
  chatMessages.value = []
  chatInput.value = ''
  contacts.value = []
  peerMessages.value = []
  selectedPeerId.value = null
  peerInput.value = ''
  contactSearch.value = ''
  dashboard.value = { redis: { register_count: 0, online_count: 0 }, date: '', ip: '', weather: '' }
}

async function createUser() {
  try {
    await request('/users', {
      method: 'POST',
      body: JSON.stringify(forms.value.user),
    })
    setStatus('success', '用户创建成功')
    modals.value.user = false
    forms.value.user = { name: '', password: '', role: 'user' }
    await fetchUsers()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function updateBalance(userId) {
  try {
    await request(`/users/${userId}/balance`, {
      method: 'PUT',
      body: JSON.stringify({ amount: Number(forms.value.balance.amount) }),
    })
    setStatus('success', '余额已更新')
    forms.value.balance = { userId: '', amount: 0 }
    await fetchUsers()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function createModel() {
  try {
    const payload = { ...forms.value.model, owner_id: forms.value.model.owner_id || null }
    await request('/models', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    setStatus('success', '大模型配置已创建')
    modals.value.model = false
    forms.value.model = {
      name: '',
      base_url: '',
      api_key: '',
      model_name: '',
      max_tokens: 4096,
      temperature: 1,
      owner_id: '',
    }
    await fetchModels()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function deleteModel(id) {
  if (!confirm('确认删除该配置吗？')) return
  try {
    await request(`/models/${id}`, { method: 'DELETE' })
    setStatus('success', '配置已删除')
    selectedModel.value = null
    await fetchModels()
  } catch (error) {
    setStatus('error', error.message)
  }
}

function openModelDetail(item) {
  selectedModel.value = item
  forms.value.editModel = {
    id: item.id,
    name: item.name,
    base_url: item.base_url,
    api_key: item.api_key,
    model_name: item.model_name,
    max_tokens: item.max_tokens,
    temperature: item.temperature,
    owner_id: item.owner_id ?? '',
  }
}

async function updateModel() {
  if (!forms.value.editModel.id) return
  const payload = {
    name: forms.value.editModel.name,
    base_url: forms.value.editModel.base_url,
    api_key: forms.value.editModel.api_key,
    model_name: forms.value.editModel.model_name,
    max_tokens: Number(forms.value.editModel.max_tokens),
    temperature: Number(forms.value.editModel.temperature),
    owner_id: forms.value.editModel.owner_id || null,
  }
  try {
    await request(`/models/${forms.value.editModel.id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
    setStatus('success', '模型已更新')
    modals.value.modelEdit = false
    await fetchModels()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function createCategory() {
  try {
    await request('/web/categories', {
      method: 'POST',
      body: JSON.stringify(forms.value.category),
    })
    setStatus('success', '分类已创建')
    modals.value.category = false
    forms.value.category = { name: '', description: '' }
    await fetchCategories()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function deleteCategory(id) {
  if (!confirm('确认删除该分类及其网页吗？')) return
  try {
    await request(`/web/categories/${id}`, { method: 'DELETE' })
    setStatus('success', '分类已删除')
    selectedCategory.value = null
    pages.value = []
    await fetchCategories()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function createPage() {
  try {
    const payload = { ...forms.value.page, category_id: Number(forms.value.page.category_id) }
    await request('/web/pages', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    setStatus('success', '网页已保存')
    modals.value.page = false
    forms.value.page = { category_id: '', url: '', account: '', password: '', cookie: '', note: '' }
    await fetchPages(selectedCategory.value?.id || null)
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function deletePage(id) {
  if (!confirm('确认删除该网页记录吗？')) return
  try {
    await request(`/web/pages/${id}`, { method: 'DELETE' })
    setStatus('success', '网页已删除')
    await fetchPages(selectedCategory.value?.id || null)
  } catch (error) {
    setStatus('error', error.message)
  }
}

function openEditPage(page) {
  forms.value.editPage = {
    id: page.id,
    category_id: page.category_id,
    url: page.url,
    account: page.account || '',
    password: page.password || '',
    cookie: page.cookie || '',
    note: page.note || '',
  }
  modals.value.pageEdit = true
}

async function updatePage() {
  if (!forms.value.editPage.id) return
  try {
    const payload = {
      category_id: Number(forms.value.editPage.category_id),
      url: forms.value.editPage.url,
      account: forms.value.editPage.account,
      password: forms.value.editPage.password,
      cookie: forms.value.editPage.cookie,
      note: forms.value.editPage.note,
    }
    await request(`/web/pages/${forms.value.editPage.id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
    setStatus('success', '网页信息已更新')
    modals.value.pageEdit = false
    forms.value.editPage = { id: null, category_id: '', url: '', account: '', password: '', cookie: '', note: '' }
    await fetchPages(selectedCategory.value?.id || null)
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function assignRole() {
  try {
    await request('/roles/assign', {
      method: 'POST',
      body: JSON.stringify({
        user_id: Number(forms.value.role.user_id),
        role: forms.value.role.role,
      }),
    })
    setStatus('success', '角色已更新')
    modals.value.role = false
    forms.value.role = { user_id: '', role: 'user' }
    await Promise.all([fetchUsers(), fetchRoles()])
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function createRolePrompt() {
  try {
    await request('/role-prompts', {
      method: 'POST',
      body: JSON.stringify(forms.value.rolePrompt),
    })
    setStatus('success', '提示词已创建')
    forms.value.rolePrompt = { name: '', prompt: '' }
    modals.value.rolePrompt = false
    await fetchRolePrompts()
  } catch (error) {
    setStatus('error', error.message)
  }
}

function openEditRolePrompt(item) {
  editingRolePrompt.value = item
  forms.value.editRolePrompt = { ...item }
  modals.value.rolePromptEdit = true
}

async function updateRolePrompt() {
  if (!forms.value.editRolePrompt.id) return
  try {
    await request(`/role-prompts/${forms.value.editRolePrompt.id}`, {
      method: 'PUT',
      body: JSON.stringify({
        name: forms.value.editRolePrompt.name,
        prompt: forms.value.editRolePrompt.prompt,
      }),
    })
    setStatus('success', '提示词已更新')
    modals.value.rolePromptEdit = false
    editingRolePrompt.value = null
    forms.value.editRolePrompt = { id: null, name: '', prompt: '' }
    await fetchRolePrompts()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function deleteRolePrompt(id) {
  if (!confirm('确认删除该提示词吗？')) return
  try {
    await request(`/role-prompts/${id}`, { method: 'DELETE' })
    setStatus('success', '提示词已删除')
    if (selectedRoleId.value === id) {
      selectedRoleId.value = rolePrompts.value.find((item) => item.id !== id)?.id || null
    }
    await fetchRolePrompts()
  } catch (error) {
    setStatus('error', error.message)
  }
}

function openEditUser(user) {
  forms.value.editUser = { id: user.id, name: user.name, password: '', role: user.role }
  modals.value.userEdit = true
}

async function updateUser() {
  if (!forms.value.editUser.id) return
  try {
    const payload = { name: forms.value.editUser.name, role: forms.value.editUser.role }
    if (forms.value.editUser.password) {
      payload.password = forms.value.editUser.password
    }
    await request(`/users/${forms.value.editUser.id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
    setStatus('success', '用户信息已更新')
    modals.value.userEdit = false
    forms.value.editUser = { id: null, name: '', password: '', role: 'user' }
    await fetchUsers()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function deleteUser(userId) {
  if (!confirm('确认删除该用户吗？')) return
  try {
    await request(`/users/${userId}`, { method: 'DELETE' })
    setStatus('success', '用户已删除')
    await Promise.all([fetchUsers(), fetchRoles()])
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function resetUserPassword(userId, userName) {
  const newPassword = prompt(`重置 ${userName} 的密码为：`, '123456')
  if (!newPassword) return
  try {
    await request(`/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify({ password: newPassword }),
    })
    setStatus('success', `${userName} 密码已重置`)
  } catch (error) {
    setStatus('error', error.message)
  }
}

function resetUserSearch() {
  userSearch.value = { name: '', role: '', phone: '' }
  userPage.value = 1
}

async function updateProfile() {
  try {
    const payload = { name: forms.value.profileEdit.name }
    if (forms.value.profileEdit.password) {
      payload.password = forms.value.profileEdit.password
    }
    if (forms.value.profileEdit.email) {
      payload.email = forms.value.profileEdit.email
    }
    if (forms.value.profileEdit.phone) {
      payload.phone = forms.value.profileEdit.phone
    }
    const res = await request(`/users/${currentUser.value.id}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
    currentUser.value = { ...currentUser.value, name: res.name, email: res.email, phone: res.phone }
    localStorage.setItem('user', JSON.stringify(currentUser.value))
    setStatus('success', '个人信息已更新')
    modals.value.profileEdit = false
    forms.value.profileEdit = { name: '', password: '', email: '', phone: '' }
  } catch (error) {
    setStatus('error', error.message)
  }
}

function openProfileEdit() {
  forms.value.profileEdit = {
    name: currentUser.value?.name || '',
    password: '',
    email: currentUser.value?.email || '',
    phone: currentUser.value?.phone || '',
  }
  modals.value.profileEdit = true
}

// ---------------------------
// 地图功能
// ---------------------------
function loadAmapScript() {
  return new Promise((resolve, reject) => {
    if (window.AMap) {
      resolve(window.AMap)
      return
    }
    
    // 从环境变量读取高德地图 API Key
    const amapKey = import.meta.env.VITE_AMAP_KEY || 'YOUR_AMAP_KEY'
    const amapSecret = import.meta.env.VITE_AMAP_SECRET || ''
    
    // 检查 API Key 是否配置
    if (!amapKey || amapKey === 'YOUR_AMAP_KEY' || amapKey === 'your_amap_web_key_here') {
      reject(new Error('请先在 .env 文件中配置 VITE_AMAP_KEY'))
      return
    }
    
    // 输出配置信息到控制台
    console.log('=== 高德地图配置 ===')
    console.log('API Key:', amapKey)
    console.log('安全密钥已配置:', amapSecret ? '是' : '否')
    console.log('==================')
    console.log('如果地图加载失败，请检查：')
    console.log('1. 访问 https://console.amap.com/')
    console.log('2. 确保Key类型是 "Web端(JS API)" 不是 "Web服务"')
    console.log('3. 在Key设置中生成"安全密钥(seccode)"并配置到VITE_AMAP_SECRET')
    console.log('4. 重启前端服务: npm run dev')
    console.log('==================')
    
    // 配置安全密钥
    if (amapSecret && amapSecret !== 'your_amap_secret_here') {
      window._AMapSecurityConfig = {
        securityJsCode: amapSecret,
      }
    }
    
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${amapKey}`
    script.async = true
    script.onload = () => {
      if (window.AMap) {
        resolve(window.AMap)
      } else {
        reject(new Error('高德地图脚本加载成功但 AMap 对象未定义'))
      }
    }
    script.onerror = () => reject(new Error('高德地图脚本加载失败，请检查网络连接和API Key'))
    document.head.appendChild(script)
  })
}

async function initMap() {
  // 每次都重新初始化，不检查mapLoaded
  
  try {
    const AMap = await loadAmapScript()
    
    // 如果已有地图实例，先销毁
    if (mapInstance.value) {
      try {
        mapInstance.value.destroy()
      } catch (e) {
        console.log('销毁旧地图实例:', e)
      }
    }
    
    // 创建地图实例 - 优化性能配置
    mapInstance.value = new AMap.Map('amap-container', {
      zoom: 13,
      center: [116.397428, 39.90923], // 默认北京
      viewMode: '2D', // 改为2D模式，性能更好
      pitch: 0,
      // 性能优化配置
      resizeEnable: true,
      rotateEnable: false, // 禁用旋转
      pitchEnable: false, // 禁用倾斜
      dragEnable: true,
      zoomEnable: true,
      doubleClickZoom: true,
      keyboardEnable: false, // 禁用键盘控制
      jogEnable: false, // 禁用惯性拖拽
      scrollWheel: true,
      touchZoom: true,
      // 地图样式 - 使用轻量级样式
      mapStyle: 'amap://styles/normal',
      features: ['bg', 'road', 'building', 'point'], // 添加point显示地名标注
      // 缩放动画
      animateEnable: false, // 禁用动画，提升性能
    })
    
    // 监听地图错误
    mapInstance.value.on('error', (e) => {
      console.error('地图错误:', e)
      if (e.info && e.info.includes('ENGINE_RESPONSE_DATA_ERROR')) {
        locationError.value = 'API Key配置错误：请确保使用Web端(JS API)类型的Key，并正确配置安全密钥'
        setStatus('error', '地图API配置错误，请检查控制台的配置说明')
      }
    })
    
    mapLoaded.value = true
    console.log('地图初始化完成')
    
    // 获取用户位置
    getUserLocation()
  } catch (error) {
    locationError.value = error.message
    setStatus('error', '地图加载失败：' + error.message)
  }
}

function getUserLocation() {
  if (!mapInstance.value) return
  
  const AMap = window.AMap
  if (!AMap) return
  
  // 使用高德地图定位插件
  AMap.plugin('AMap.Geolocation', () => {
    const geolocation = new AMap.Geolocation({
      enableHighAccuracy: false, // 改为false，提升速度
      timeout: 5000, // 减少超时时间
      zoomToAccuracy: false, // 禁用自动缩放
      convert: true,
      showButton: false,
      showMarker: false,
      showCircle: false,
      noIpLocate: 0,
      GeoLocationFirst: false // 优先使用IP定位，更快
    })
    
    geolocation.getCurrentPosition((status, result) => {
      if (status === 'complete') {
        const { lng, lat } = result.position
        userLocation.value = {
          lng,
          lat,
          address: result.formattedAddress || '未知地址',
          city: result.addressComponent?.city || result.addressComponent?.district || '威县',
        }
        
        // 定位成功后刷新天气
        fetchDashboard()
        
        // 设置地图中心（不使用动画）
        mapInstance.value.setCenter([lng, lat])
        
        // 添加标记（使用简单标记，不加载图片）
        if (mapMarker.value) {
          mapMarker.value.setMap(null)
        }
        
        mapMarker.value = new AMap.Marker({
          position: [lng, lat],
          title: '我的位置',
          // 不使用自定义图标，使用默认标记（性能更好）
        })
        
        mapInstance.value.add(mapMarker.value)
        
        // 不自动打开信息窗体，减少渲染
        // 用户可以点击标记查看详情
        mapMarker.value.on('click', () => {
          const infoWindow = new AMap.InfoWindow({
            content: `<div style="padding: 10px;">
              <h4 style="margin: 0 0 8px 0;">我的位置</h4>
              <p style="margin: 4px 0;">经度：${lng.toFixed(6)}</p>
              <p style="margin: 4px 0;">纬度：${lat.toFixed(6)}</p>
              <p style="margin: 4px 0;">地址：${userLocation.value.address}</p>
            </div>`,
          offset: new AMap.Pixel(0, -30),
        })
        
        setStatus('success', '定位成功')
        
          infoWindow.open(mapInstance.value, [lng, lat])
        })
      } else {
        // 定位失败，使用默认位置（北京）
        const defaultLng = 116.397428
        const defaultLat = 39.90923
        
        userLocation.value = {
          lng: defaultLng,
          lat: defaultLat,
          address: '自动定位失败，显示默认位置（北京天安门）',
          city: '北京市',
        }
        
        // 设置地图中心到默认位置
        mapInstance.value.setCenter([defaultLng, defaultLat])
        
        // 添加默认位置标记
        if (mapMarker.value) {
          mapMarker.value.setMap(null)
        }
        
        mapMarker.value = new AMap.Marker({
          position: [defaultLng, defaultLat],
          title: '默认位置',
        })
        
        mapInstance.value.add(mapMarker.value)
        
        // 清空错误信息，不显示为错误
        locationError.value = ''
        setStatus('info', '💡 自动定位失败，已显示默认位置。点击"请求定位权限"按钮手动授权定位')
      }
    })
  })
}

// 主动请求浏览器定位权限
async function requestBrowserLocation() {
  if (isRequestingLocation.value) return
  
  isRequestingLocation.value = true
  locationError.value = ''
  
  try {
    // 检查浏览器是否支持地理定位
    if (!navigator.geolocation) {
      throw new Error('您的浏览器不支持地理定位功能')
    }
    
    // 检查当前协议
    const isSecure = window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    
    if (!isSecure) {
      setStatus('warning', '⚠️ 定位功能需要 HTTPS 或 localhost 环境。当前使用：' + window.location.protocol)
      locationError.value = '定位功能需要安全上下文（HTTPS 或 localhost）'
      isRequestingLocation.value = false
      return
    }
    
    // 先检查权限状态
    if (navigator.permissions) {
      try {
        const permissionStatus = await navigator.permissions.query({ name: 'geolocation' })
        console.log('当前定位权限状态：', permissionStatus.state)
        
        if (permissionStatus.state === 'denied') {
          setStatus('error', '❌ 定位权限已被拒绝，请在浏览器设置中手动开启')
          locationError.value = '定位权限已被拒绝。请点击地址栏左侧的图标 → 网站设置 → 位置 → 允许'
          isRequestingLocation.value = false
          return
        }
      } catch (e) {
        console.log('无法查询权限状态：', e)
      }
    }
    
    setStatus('info', '正在请求定位权限...')
    console.log('开始请求定位权限...')
    
    // 使用浏览器原生定位API请求权限
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { longitude: lng, latitude: lat } = position.coords
        
        setStatus('success', '定位权限已授予，正在获取详细地址...')
        
        // 如果地图已加载，使用高德API进行逆地理编码获取地址
        if (window.AMap && mapLoaded.value) {
          try {
            const geocoder = new window.AMap.Geocoder()
            geocoder.getAddress([lng, lat], (status, result) => {
              if (status === 'complete' && result.info === 'OK') {
                const addressComponent = result.regeocode.addressComponent
                userLocation.value = {
                  lng,
                  lat,
                  address: result.regeocode.formattedAddress,
                  city: addressComponent.city || addressComponent.province,
                }
                
                // 更新地图中心和标记
                mapInstance.value.setCenter([lng, lat])
                
                if (mapMarker.value) {
                  mapMarker.value.setMap(null)
                }
                
                mapMarker.value = new window.AMap.Marker({
                  position: [lng, lat],
                  title: '我的位置',
                })
                
                mapInstance.value.add(mapMarker.value)
                
                setStatus('success', '✓ 定位成功！')
              } else {
                // 逆地理编码失败，仍然显示坐标
                userLocation.value = {
                  lng,
                  lat,
                  address: '地址解析中...',
                  city: '未知',
                }
                setStatus('success', '定位成功，但地址解析失败')
              }
            })
          } catch (err) {
            userLocation.value = {
              lng,
              lat,
              address: '地址解析失败',
              city: '未知',
            }
            setStatus('warning', '定位成功，但地址解析失败')
          }
        } else {
          // 地图未加载，只显示坐标
          userLocation.value = {
            lng,
            lat,
            address: '请先初始化地图以获取详细地址',
            city: '未知',
          }
          setStatus('success', '✓ 定位成功！')
        }
      },
      (error) => {
        let errorMsg = ''
        switch (error.code) {
          case error.PERMISSION_DENIED:
            errorMsg = '用户拒绝了定位请求。请在浏览器设置中允许定位权限'
            break
          case error.POSITION_UNAVAILABLE:
            errorMsg = '位置信息不可用'
            break
          case error.TIMEOUT:
            errorMsg = '定位请求超时'
            break
          default:
            errorMsg = '未知错误：' + error.message
        }
        locationError.value = errorMsg
        setStatus('error', '定位失败：' + errorMsg)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    )
  } catch (error) {
    locationError.value = error.message
    setStatus('error', '定位失败：' + error.message)
  } finally {
    isRequestingLocation.value = false
  }
}

function refreshLocation() {
  if (!mapInstance.value) {
    initMap()
    return
  }
  getUserLocation()
}

// 搜索地址并定位
async function searchAddress() {
  if (!manualAddress.value.trim()) return
  
  // 如果地图未加载，先初始化
  if (!mapLoaded.value) {
    setStatus('info', '正在初始化地图...')
    await initMap()
    // 等待地图加载完成
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  
  const AMap = window.AMap
  if (!AMap) {
    setStatus('error', '地图加载失败，请刷新页面重试')
    return
  }
  
  setStatus('info', '正在搜索地址...')
  
  AMap.plugin('AMap.Geocoder', () => {
    const geocoder = new AMap.Geocoder()
    
    geocoder.getLocation(manualAddress.value, (status, result) => {
      if (status === 'complete' && result.info === 'OK') {
        const location = result.geocodes[0].location
        const lng = location.lng
        const lat = location.lat
        
        userLocation.value = {
          lng,
          lat,
          address: result.geocodes[0].formattedAddress,
          city: result.geocodes[0].addressComponent.city || result.geocodes[0].addressComponent.province,
        }
        
        // 更新地图
        mapInstance.value.setCenter([lng, lat])
        
        if (mapMarker.value) {
          mapMarker.value.setMap(null)
        }
        
        mapMarker.value = new AMap.Marker({
          position: [lng, lat],
          title: '搜索位置',
        })
        
        mapInstance.value.add(mapMarker.value)
        
        locationError.value = ''
        setStatus('success', '✓ 地址搜索成功！')
        showManualLocationInput.value = false
      } else {
        setStatus('error', '地址搜索失败，请检查地址是否正确')
      }
    })
  })
}

// 设置手动输入的坐标
async function setManualLocation() {
  const lng = parseFloat(manualLng.value)
  const lat = parseFloat(manualLat.value)
  
  if (isNaN(lng) || isNaN(lat)) {
    setStatus('error', '请输入有效的经纬度')
    return
  }
  
  if (lng < -180 || lng > 180 || lat < -90 || lat > 90) {
    setStatus('error', '经纬度范围错误（经度：-180~180，纬度：-90~90）')
    return
  }
  
  // 如果地图未加载，先初始化
  if (!mapLoaded.value) {
    setStatus('info', '正在初始化地图...')
    await initMap()
    // 等待地图加载完成
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  
  const AMap = window.AMap
  if (!AMap) {
    setStatus('error', '地图加载失败，请刷新页面重试')
    return
  }
  
  setStatus('info', '正在解析地址...')
  
  // 逆地理编码获取地址
  AMap.plugin('AMap.Geocoder', () => {
    const geocoder = new AMap.Geocoder()
    
    geocoder.getAddress([lng, lat], (status, result) => {
      if (status === 'complete' && result.info === 'OK') {
        const addressComponent = result.regeocode.addressComponent
        userLocation.value = {
          lng,
          lat,
          address: result.regeocode.formattedAddress,
          city: addressComponent.city || addressComponent.province,
        }
      } else {
        userLocation.value = {
          lng,
          lat,
          address: '地址解析失败',
          city: '未知',
        }
      }
      
      // 更新地图
      mapInstance.value.setCenter([lng, lat])
      
      if (mapMarker.value) {
        mapMarker.value.setMap(null)
      }
      
      mapMarker.value = new AMap.Marker({
        position: [lng, lat],
        title: '手动位置',
      })
      
      mapInstance.value.add(mapMarker.value)
      
      locationError.value = ''
      setStatus('success', '✓ 位置设置成功！')
      showManualLocationInput.value = false
    })
  })
}

// ---------------------------
// 地图AI聊天功能
// ---------------------------
function formatMapChat(content) {
  if (!content) return ''
  // 简单的换行处理
  return content.replace(/\n/g, '<br>')
}

async function askMapAI(question) {
  if (!question.trim()) return
  
  // 获取当前位置信息
  const locationInfo = userLocation.value 
    ? `当前位置：${userLocation.value.address}，城市：${userLocation.value.city}` 
    : '位置未知'
  
  const fullQuestion = `${locationInfo}。请推荐${question}，给出具体的名称、地址和简短介绍。`
  
  mapChatInput.value = ''
  mapChatMessages.value.push({ role: 'user', content: question })
  mapChatLoading.value = true
  
  try {
    // 使用现有的AI聊天接口
    const modelId = chatModelId.value || (models.value.length > 0 ? models.value[0].id : null)
    
    if (!modelId) {
      mapChatMessages.value.push({ 
        role: 'assistant', 
        content: '❌ 请先在"大模型"页面配置AI模型' 
      })
      mapChatLoading.value = false
      return
    }
    
    const response = await fetch(`${apiBase}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token.value}`,
      },
      body: JSON.stringify({
        model_id: modelId,
        stream: true,
        messages: [
          { role: 'system', content: '你是一个本地生活助手，根据用户的位置信息推荐附近的美食、景点、酒店等。回答要简洁实用，包含具体名称和简短介绍。' },
          { role: 'user', content: fullQuestion }
        ],
      }),
    })
    
    if (!response.ok) {
      const text = await response.text()
      // 检测Cloudflare验证页面
      if (text.includes('Just a moment') || text.includes('challenge-platform')) {
        throw new Error('API被Cloudflare拦截，请检查模型配置或更换API')
      }
      // 解析错误详情
      let errorMsg = `请求失败 (${response.status})`
      try {
        const errorData = JSON.parse(text)
        if (errorData.detail) {
          errorMsg = errorData.detail
          // 如果是404错误，提供更详细的提示
          if (response.status === 404 && errorMsg.includes('上游错误')) {
            errorMsg += '\n\n💡 提示：请检查大模型配置中的 base_url 是否正确。\n常见格式：\n• OpenAI: https://api.openai.com\n• 本地Ollama: http://localhost:11434\n\n注意：base_url 不需要包含 /v1/chat/completions'
          }
        }
      } catch (e) {
        errorMsg = text || errorMsg
      }
      throw new Error(errorMsg)
    }
    
    // 处理流式响应
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('浏览器不支持流式读取')
    }
    
    const decoder = new TextDecoder()
    let buffer = ''
    let assistantContent = ''
    
    mapChatMessages.value.push({ role: 'assistant', content: '' })
    const assistantIndex = mapChatMessages.value.length - 1
    
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
      
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      for (const line of lines) {
        if (!line.startsWith('data:')) continue
        const jsonStr = line.slice(5).trim()
        if (jsonStr === '[DONE]') continue
        
        try {
          const data = JSON.parse(jsonStr)
          const delta = data.choices?.[0]?.delta?.content || ''
          assistantContent += delta
          mapChatMessages.value[assistantIndex].content = assistantContent
        } catch (e) {
          // 忽略解析错误
        }
      }
      
      if (done) break
    }
    
  } catch (error) {
    mapChatMessages.value.push({ 
      role: 'assistant', 
      content: `❌ 请求失败：${error.message}` 
    })
  } finally {
    mapChatLoading.value = false
  }
}

function sendMapChat() {
  if (!mapChatInput.value.trim()) return
  askMapAI(mapChatInput.value)
}

// ---------------------------
// Chat stream (原逻辑保留)
// ---------------------------
async function handleStreamResponse(response, assistantIndex) {
  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('浏览器暂不支持流式读取')
  }
  const decoder = new TextDecoder()
  let buffer = ''
  let scrollCounter = 0
  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const segments = buffer.split('\n\n')
    buffer = segments.pop() || ''
    for (const segment of segments) {
      const line = segment.trim()
      if (!line.startsWith('data:')) continue
      const dataStr = line.replace(/^data:\s*/, '')
      if (dataStr === '[DONE]') {
        scrollChatToBottom()
        return
      }
      try {
        const parsed = JSON.parse(dataStr)
        const delta =
          parsed?.choices?.[0]?.delta?.content || parsed?.choices?.[0]?.message?.content || ''
        if (delta) {
          chatMessages.value[assistantIndex].content += delta
          // 每10次更新滚动一次，避免频繁滚动
          scrollCounter++
          if (scrollCounter % 10 === 0) {
            scrollChatToBottom()
          }
        }
      } catch (err) {
        console.warn('流式解析失败：', err)
      }
    }
    if (done) break
  }
  scrollChatToBottom()
}

// 滚动聊天消息到底部
function scrollChatToBottom() {
  setTimeout(() => {
    if (chatBodyRef.value) {
      chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
    }
  }, 50)
}

async function sendChat() {
  if (!chatInput.value.trim()) {
    setStatus('error', '请输入提问内容')
    return
  }
  if (!models.value.length) {
    setStatus('error', '请先配置可用模型')
    return
  }
  const question = chatInput.value.trim()
  const payloadMessages = [...chatMessages.value, { role: 'user', content: question }]
  chatLoading.value = true
  chatInput.value = ''
  const userMessage = { role: 'user', content: question }
  chatMessages.value.push(userMessage)
  scrollChatToBottom() // 发送后滚动到底部
  const assistantIndex = chatMessages.value.push({ role: 'assistant', content: 'AI 正在生成中…' }) - 1
  scrollChatToBottom() // AI回复开始时滚动
  try {
    const headers = { 'Content-Type': 'application/json' }
    if (token.value) headers.Authorization = `Bearer ${token.value}`
    const response = await fetch(`${apiBase}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model_id: chatModelId.value,
        messages: payloadMessages,
        stream: true,
        role_prompt: currentRolePrompt.value || defaultRolePrompt,
        role_id: selectedRoleId.value,
      }),
    })
    if (!response.ok) {
      const errorText = response.status === 204 ? '请求失败' : await response.text()
      throw new Error(errorText || '请求失败')
    }
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('text/event-stream')) {
      chatMessages.value[assistantIndex].content = ''
      await handleStreamResponse(response, assistantIndex)
      if (!chatMessages.value[assistantIndex].content) {
        chatMessages.value[assistantIndex].content = '未获取到回复内容'
      }
    } else {
      const res = await response.json()
      const content = res?.choices?.[0]?.message?.content || '未获取到回复内容'
      chatMessages.value[assistantIndex].content = content
    }
  } catch (error) {
    chatMessages.value[assistantIndex].content = `生成失败：${error.message}`
    chatInput.value = question
    setStatus('error', error.message)
  } finally {
    chatLoading.value = false
  }
}

function deleteChatMessage(index) {
  chatMessages.value.splice(index, 1)
}

function resetChat() {
  chatMessages.value = []
  chatInput.value = ''
}

// ---------------------------
// 站内互聊：发送（去重 + 预览）
// ---------------------------
function stableMsgKey(msg) {
  // 后端有 id 最好，没有则做一个稳定 key
  if (msg?.id != null) return `id:${msg.id}`
  const s = `${msg?.sender_id || ''}|${msg?.receiver_id || ''}|${msg?.created_at || ''}|${msg?.content || ''}`
  return `h:${hashString(s)}`
}

function hashString(s) {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = (h << 5) - h + s.charCodeAt(i)
    h |= 0
  }
  return String(h)
}

function upsertPeerMessage(msg) {
  if (!msg) return
  const key = stableMsgKey(msg)
  const exists = peerMessages.value.some((m) => stableMsgKey(m) === key)
  if (exists) return
  peerMessages.value.push(msg)
  peerMessages.value.sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
}

async function sendPeerMessage() {
  if (!selectedPeerId.value) {
    setStatus('error', '请先选择联系人')
    return
  }
  if (!peerInput.value.trim()) {
    setStatus('error', '请输入要发送的内容')
    return
  }
  const content = peerInput.value.trim()
  peerSending.value = true
  try {
    const res = await request('/contacts/messages', {
      method: 'POST',
      body: JSON.stringify({ receiver_id: selectedPeerId.value, content }),
    })
    upsertPeerMessage(res)
    setLastPreview(selectedPeerId.value, content)
    peerInput.value = ''
  } catch (error) {
    setStatus('error', error.message)
  } finally {
    peerSending.value = false
  }
}

// ---------------------------
// WebSocket：实时收消息 + 未读
// ---------------------------
const wsRef = ref(null)
const wsConnected = ref(false)
const wsConnecting = ref(false)
const wsRetry = ref(0)
let wsReconnectTimer = null
let wsHeartbeatTimer = null

function safeJsonParse(s) {
  try {
    return JSON.parse(s)
  } catch {
    return null
  }
}

function buildWsUrl() {
  // 支持 apiBase 有无 path
  // http://x:8001 -> ws://x:8001/ws?token=...
  // https://... -> wss://...
  // 空字符串时使用当前页面地址
  const baseUrl = apiBase || window.location.origin
  const base = new URL(baseUrl)
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
  base.pathname = '/ws'
  base.search = `?token=${encodeURIComponent(token.value || '')}`
  return base.toString()
}

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

function disconnectWs() {
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
  if (!token.value) return
  // 指数退避（上限 12s）+ 抖动
  const base = Math.min(800 * Math.pow(2, wsRetry.value), 12000)
  const jitter = Math.floor(Math.random() * 400)
  const delay = base + jitter
  wsReconnectTimer = setTimeout(() => {
    wsRetry.value += 1
    connectWs()
  }, delay)
}

function resolveOtherPeerId(msg) {
  // other = (sender == me ? receiver : sender)
  const me = currentUser.value?.id
  if (!me) return null
  if (Number(msg.sender_id) === Number(me)) return Number(msg.receiver_id)
  return Number(msg.sender_id)
}

function showNotification(title, content) {
  const id = ++notificationId
  notifications.value.push({ id, title, content })
  setTimeout(() => {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }, 4000)
}

function handleIncomingPeerMessage(msg) {
  const otherId = resolveOtherPeerId(msg)
  if (!otherId) return

  setLastPreview(otherId, msg.content)

  // 是否是别人发给我的消息
  const isFromOther = Number(msg.sender_id) !== Number(currentUser.value?.id)

  // 当前会话
  if (Number(selectedPeerId.value) === Number(otherId)) {
    upsertPeerMessage(msg)
    clearUnread(otherId)
    // 当前会话也显示通知（如果是别人发的）
    if (isFromOther) {
      showNotification(msg.sender_name || '新消息', msg.content)
    }
    return
  }

  // 非当前会话 -> 未读 + 通知
  incUnread(otherId)
  if (isFromOther) {
    showNotification(msg.sender_name || '新消息', msg.content)
  }
}

function handleWsMessage(evt) {
  const raw = evt?.data
  if (!raw) return

  // 支持后端回 'pong' / 'ping'
  if (raw === 'pong' || raw === 'ping') return

  console.log('[WS] 收到消息:', raw)

  const payload = typeof raw === 'string' ? safeJsonParse(raw) : raw

  if (!payload) {
    console.log('[WS] 解析失败')
    return
  }

  console.log('[WS] 解析后:', payload)

  // 兼容两种格式：
  // 1) { type: 'peer_message', data: {...} }
  // 2) 直接就是消息体 {...sender_id, receiver_id, content...}
  if (payload.type === 'peer_message' && payload.data) {
    console.log('[WS] 处理 peer_message')
    handleIncomingPeerMessage(payload.data)
    return
  }
  if (payload.sender_id && payload.receiver_id && payload.content) {
    console.log('[WS] 处理直接消息')
    handleIncomingPeerMessage(payload)
    return
  }
}

function connectWs() {
  if (!token.value) return
  if (wsRef.value && (wsRef.value.readyState === WebSocket.OPEN || wsRef.value.readyState === WebSocket.CONNECTING)) {
    return
  }

  wsConnecting.value = true
  wsConnected.value = false

  let wsUrl = ''
  try {
    wsUrl = buildWsUrl()
  } catch (e) {
    wsConnecting.value = false
    setStatus('error', 'WebSocket 地址解析失败，请检查 VITE_API_BASE')
    return
  }

  const ws = new WebSocket(wsUrl)
  wsRef.value = ws

  ws.onopen = async () => {
    wsConnected.value = true
    wsConnecting.value = false
    wsRetry.value = 0

    clearWsTimers()
    // 心跳
    wsHeartbeatTimer = setInterval(() => {
      try {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping')
      } catch {}
    }, 20000)

    // 连接成功后刷新一次在线状态（不强制拉消息）
    fetchContacts({ keepSelected: true })
  }

  ws.onmessage = handleWsMessage

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

// ---------------------------
// 生命周期 & watch
// ---------------------------
watch(
  () => themeMode.value,
  () => {
    applyThemeClasses()
  },
  { immediate: true }
)

watch(
  () => selectedPeerId.value,
  (peerId) => {
    if (peerId) {
      fetchPeerMessages(peerId)
      clearUnread(peerId)
    } else {
      peerMessages.value = []
    }
  }
)

watch(
  () => token.value,
  (val) => {
    if (val) connectWs()
    else disconnectWs()
  }
)

onMounted(() => {
  applyThemeClasses()
  syncRouteFromLocation()
  window.addEventListener('hashchange', syncRouteFromLocation)
  if (token.value) {
    syncAll()
    checkTodayCheckIn()
    connectWs()
  }
})

onBeforeUnmount(() => {
  stopChristmasEffects()
  window.removeEventListener('hashchange', syncRouteFromLocation)
})

watch([isAuthed, isAdmin], () => {
  syncRouteFromLocation()
})

// 监听activeMenu变化，当切换到地图页面时自动初始化
watch(activeMenu, (newMenu, oldMenu) => {
  if (newMenu === 'map') {
    console.log('进入地图页面，自动初始化地图')
    // 延迟一下确保DOM已渲染
    setTimeout(() => {
      initMap()
    }, 100)
  }
})
</script>

<template>
  <div class="app-shell" :class="[themeMode, { 'christmas-on': christmasActive }]"><!--
    圣诞按钮触发飘雪效果，主题类用于切换深浅色。-->
    
    <!-- 右上角消息通知 -->
    <div class="notification-container">
      <transition-group name="notification">
        <div v-for="n in notifications" :key="n.id" class="notification-item">
          <div class="notification-title">{{ n.title }}</div>
          <div class="notification-content">{{ n.content.length > 50 ? n.content.slice(0, 50) + '...' : n.content }}</div>
        </div>
      </transition-group>
    </div>
    
    <aside class="sidebar">
      <div class="brand">
        <div class="logo">PM</div>
        <div>
          <div class="brand-name">个人管理系统</div>
          <div class="brand-sub">分工明确 · 一键直达</div>
        </div>
      </div>
      <nav class="menu">
        <button :class="{ active: activeMenu === 'home' }" @click="navigateTo('home')">首页</button>
        
        <!-- 聊天菜单组 -->
        <div class="menu-group">
          <button class="menu-parent" :class="{ expanded: expandedMenus.chat }" @click="expandedMenus.chat = !expandedMenus.chat">
            聊天
            <span class="arrow">{{ expandedMenus.chat ? '▼' : '▶' }}</span>
          </button>
          <div class="submenu" v-show="expandedMenus.chat">
            <button :class="{ active: activeMenu === 'chat' }" @click="navigateTo('chat')" :disabled="!isAuthed">
              星际聊天
            </button>
            <button :class="{ active: activeMenu === 'contacts' }" @click="navigateTo('contacts')" :disabled="!isAuthed">
              站内聊天
            </button>
          </div>
        </div>
        
        <!-- 后台设置菜单组 -->
        <div class="menu-group" v-if="isAdmin">
          <button class="menu-parent" :class="{ expanded: expandedMenus.admin }" @click="expandedMenus.admin = !expandedMenus.admin">
            后台设置
            <span class="arrow">{{ expandedMenus.admin ? '▼' : '▶' }}</span>
          </button>
          <div class="submenu" v-show="expandedMenus.admin">
            <button :class="{ active: activeMenu === 'models' }" @click="navigateTo('models')" :disabled="!isAuthed">
              大模型管理
            </button>
            <button :class="{ active: activeMenu === 'users' }" @click="navigateTo('users')" :disabled="!isAdmin">
              用户与角色
            </button>
            <button :class="{ active: activeMenu === 'album' }" @click="navigateTo('album')" :disabled="!isAdmin">
              相册管理
            </button>
            <button :class="{ active: activeMenu === 'logs' }" @click="navigateTo('logs')" :disabled="!isAdmin">
              日志记录
            </button>
          </div>
        </div>
        
        <!-- 收藏菜单组 -->
        <div class="menu-group">
          <button class="menu-parent" :class="{ expanded: expandedMenus.favorites }" @click="expandedMenus.favorites = !expandedMenus.favorites">
            收藏
            <span class="arrow">{{ expandedMenus.favorites ? '▼' : '▶' }}</span>
          </button>
          <div class="submenu" v-show="expandedMenus.favorites">
            <button :class="{ active: activeMenu === 'web' }" @click="navigateTo('web')" :disabled="!isAuthed">
              网页收藏
            </button>
          </div>
        </div>
        
        <button :class="{ active: activeMenu === 'diary' }" @click="navigateTo('diary')" :disabled="!isAuthed">
          日记
        </button>
        
        <button :class="{ active: activeMenu === 'map' }" @click="navigateTo('map')" :disabled="!isAuthed">
          地图
        </button>
      </nav>
      <div class="sidebar-footer">
        <p class="muted">注册数：{{ dashboard.redis.register_count }}</p>
        <p class="muted">在线人数：{{ dashboard.redis.online_count }}</p>
      </div>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <p class="eyebrow">管理控制台</p>
          <h1>数据面板</h1>
        </div>
        <div class="top-actions">
          <button class="ghost" @click="toggleChristmas">
            {{ christmasActive ? '取消圣诞特效' : '圣诞特效' }}
          </button>
          <button class="ghost" @click="switchTheme('light')" :disabled="themeMode === 'light'">白天模式</button>
          <button class="ghost" @click="switchTheme('dark')" :disabled="themeMode === 'dark'">黑暗模式</button>
          <button class="ghost" @click="syncAll" :disabled="!isAuthed || loading">刷新</button>
          <template v-if="!isAuthed">
            <button @click="modals.login = true">登录</button>
            <button class="outline" @click="modals.register = true">注册</button>
          </template>
          <template v-else>
            <div class="avatar" @click="modals.profileEdit = true" style="cursor: pointer;" title="点击修改个人信息">
              {{ currentUser?.name }} / {{ currentUser?.role }}
              <span class="ws-pill" :class="{ ok: wsConnected, bad: !wsConnected }" title="站内互聊实时连接状态">
                {{ wsConnected ? '实时' : (wsConnecting ? '连接中' : '离线') }}
              </span>
            </div>
            <button class="outline" @click="handleLogout">退出</button>
          </template>
        </div>
      </header>

      <div v-if="status.message" class="alert" :class="status.type">
        <strong>{{ status.type === 'error' ? '提示' : '完成' }}：</strong>
        <span>{{ status.message }}</span>
      </div>

      <div v-if="!isAuthed" class="empty">
        <p class="muted">请先登录或注册后查看仪表盘</p>
      </div>

      <template v-else>
        <section v-if="loading" class="loading-banner">正在加载...</section>

        <!-- 站内互聊 -->
        <section class="panel neon-panel wechat-panel" v-if="activeMenu === 'contacts'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">站内互聊</p>
              <h3>在线联系人</h3>
            </div>
            <div class="header-actions">
              <div class="meta-chip">
                实时：
                <span :style="{ fontWeight: 600 }">
                  {{ wsConnected ? '已连接' : (wsConnecting ? '连接中' : '未连接') }}
                </span>
              </div>
              <div class="meta-chip">在线 {{ contacts.filter((item) => item.is_online).length }} 人</div>
              <button class="outline" @click="fetchContacts({ keepSelected: true })">刷新联系人</button>
              <button class="outline" @click="connectWs" :disabled="wsConnected || wsConnecting">重连</button>
            </div>
          </div>

          <div class="peer-chat">
            <div class="peer-list">
              <div class="peer-list-header">
                <input
                  v-model="contactSearch"
                  class="inline-input"
                  placeholder="搜索联系人或昵称"
                  aria-label="搜索联系人"
                />
                <p class="muted small">点击左侧联系人即可发起聊天</p>
              </div>

              <div class="peer-items">
                <button
                  v-for="contact in availableContacts"
                  :key="contact.id"
                  :class="['peer-item', { active: contact.id === selectedPeerId } ]"
                  @click="openPeerChat(contact)"
                >
                  <div class="peer-avatar" :data-online="contact.is_online">
                    {{ contact.name.slice(0, 1) }}
                    <!-- 红点/未读数 -->
                    <span
                      v-if="Number(unreadMap?.[contact.id] || 0) > 0"
                      class="unread-badge"
                      :title="`未读 ${unreadMap[contact.id]} 条`"
                    >
                      {{ unreadMap[contact.id] > 99 ? '99+' : unreadMap[contact.id] }}
                    </span>
                  </div>

                  <div class="peer-meta">
                    <div class="peer-title">
                      <span class="contact-name">{{ contact.name }}</span>
                      <span class="tag" :class="{ success: contact.is_online }">
                        {{ contact.is_online ? '在线' : '离线' }}
                      </span>
                    </div>
                    <p class="muted small">
                      角色：{{ contact.role }}
                      <span v-if="lastPreviewMap?.[contact.id]" class="preview"> · {{ lastPreviewMap[contact.id] }}</span>
                    </p>
                  </div>
                </button>

                <div v-if="!availableContacts.length" class="empty muted">
                  暂无匹配的联系人，可刷新或清空搜索。
                </div>
              </div>
            </div>

            <div class="peer-conversation">
              <div class="wechat-topbar">
                <div class="wechat-contact" v-if="selectedPeer">
                  <div class="wechat-avatar assistant">{{ selectedPeer.name.slice(0, 1) }}</div>
                  <div>
                    <p class="contact-name">{{ selectedPeer.name }}</p>
                    <p class="contact-desc">
                      {{ selectedPeer.is_online ? '在线，可立即沟通' : '对方离线，可留言' }}
                    </p>
                  </div>
                </div>
                <div class="wechat-contact" v-else>
                  <div class="wechat-avatar assistant">?</div>
                  <div>
                    <p class="contact-name">选择联系人</p>
                    <p class="contact-desc">点击左侧列表开始聊天</p>
                  </div>
                </div>
                <div class="wechat-meta">
                  <span class="meta-chip">消息 {{ peerMessages.length }} 条</span>
                  <span class="meta-chip" v-if="peerMessagesLoading">加载中...</span>
                </div>
              </div>

              <div class="wechat-body peer-body">
                <div
                  v-for="msg in peerMessages"
                  :key="msg.id ?? (msg.sender_id + '-' + msg.created_at)"
                  class="wechat-row"
                  :class="msg.sender_id === currentUser?.id ? 'right' : 'left'"
                >
                  <div class="wechat-avatar" :class="msg.sender_id === currentUser?.id ? 'user' : 'assistant'">
                    {{
                      msg.sender_id === currentUser?.id
                        ? currentUser?.name?.slice(0, 1) || '我'
                        : msg.sender_name?.slice(0, 1) || 'Ta'
                    }}
                  </div>
                  <div class="wechat-bubble" :class="msg.sender_id === currentUser?.id ? 'user' : 'assistant'">
                    <div class="bubble-meta">
                      <span class="role-tag">{{ msg.sender_id === currentUser?.id ? '我' : msg.sender_name }}</span>
                      <span class="bubble-time">{{ new Date(msg.created_at).toLocaleString() }}</span>
                    </div>
                    <div class="bubble-body">{{ msg.content }}</div>
                  </div>
                </div>

                <div v-if="!peerMessages.length && selectedPeer" class="empty muted">还没有历史记录，开始打个招呼吧。</div>
                <div v-if="!selectedPeer" class="empty muted">选择联系人后即可开始对话。</div>
              </div>

              <div class="wechat-composer peer-composer">
                <textarea
                  v-model="peerInput"
                  rows="4"
                  class="wechat-input"
                  placeholder="请输入聊天内容，Enter 发送，Shift+Enter 换行"
                  :disabled="!selectedPeer"
                  @keyup.enter.exact.prevent="sendPeerMessage"
                ></textarea>
                <div class="composer-actions">
                  <div>
                    <p class="muted small">聊天对象：{{ selectedPeer?.name || '未选择' }}</p>
                    <p class="muted small">
                      在线状态：{{ selectedPeer?.is_online ? '在线' : '离线' }} ·
                      实时：{{ wsConnected ? '已连接' : '未连接' }}
                    </p>
                  </div>
                  <div class="composer-buttons">
                    <button class="ghost" @click="peerInput = ''" :disabled="!selectedPeer">清空</button>
                    <button @click="sendPeerMessage" :disabled="peerSending || !selectedPeer">
                      {{ peerSending ? '发送中...' : '发送' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Chat（原样保留） -->
        <section class="panel neon-panel wechat-panel" v-if="activeMenu === 'chat'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">对话</p>
              <h3>对话面板 · 沉浸式气泡</h3>
            </div>
            <div class="header-actions wechat-toolbar">
              <div class="toolbar-field">
                <label>角色预设</label>
                <select v-model="selectedRoleId" class="inline-input">
                  <option v-for="prompt in rolePrompts" :key="prompt.id" :value="prompt.id">
                    {{ prompt.name }}
                  </option>
                  <option v-if="!rolePrompts.length" :value="null">默认提示词</option>
                </select>
              </div>
              <div class="toolbar-field">
                <label>使用模型</label>
                <select v-model="chatModelId" class="inline-input" :disabled="!models.length">
                  <option v-for="model in models" :key="model.id" :value="model.id">{{ model.name }}</option>
                </select>
              </div>
              <div class="toolbar-buttons">
                <button class="outline" @click="resetChat">清空历史</button>
                <button class="outline" v-if="isAdmin" @click="modals.rolePrompt = true">新增提示词</button>
              </div>
            </div>
          </div>

          <div class="wechat-chat">
            <div class="wechat-window">
              <div class="wechat-topbar">
                <div class="wechat-contact">
                  <div class="wechat-avatar">{{ currentChatModel?.name?.slice(0, 1) || '星' }}</div>
                  <div>
                    <p class="contact-name">{{ currentChatModel?.name || '星链助手' }}</p>
                    <p class="contact-desc">
                      {{ rolePrompts.find((item) => item.id === selectedRoleId)?.name || '默认提示词' }} · 双击 Enter 换行
                    </p>
                  </div>
                </div>
                <div class="wechat-meta">
                  <span class="meta-chip">上下文 {{ chatMessages.length }} 条</span>
                  <span class="meta-chip" v-if="chatLoading">正在生成...</span>
                </div>
              </div>

              <div class="wechat-body" ref="chatBodyRef">
                <div
                  v-for="(msg, index) in chatMessages"
                  :key="index"
                  class="wechat-row"
                  :class="msg.role === 'assistant' ? 'left' : 'right'"
                >
                  <div class="wechat-avatar" :class="msg.role === 'assistant' ? 'assistant' : 'user'">
                    {{ msg.role === 'assistant' ? 'AI' : (currentUser?.name?.slice(0, 1) || '我') }}
                  </div>
                  <div class="wechat-bubble" :class="msg.role === 'assistant' ? 'assistant' : 'user'">
                    <div class="bubble-meta">
                      <span class="role-tag">{{ msg.role === 'assistant' ? '星链助手' : '我' }}</span>
                      <button class="icon ghost" @click="deleteChatMessage(index)" title="删除这条记录">×</button>
                    </div>
                    <div class="bubble-body" v-html="renderMarkdown(msg.content)"></div>
                  </div>
                </div>

                <div v-if="!chatMessages.length" class="empty muted">还没有对话记录，发送后会自动携带上下文。</div>
                <div v-if="chatLoading" class="chat-loading-hint">
                  <span class="spinner"></span>
                  <span>AI 正在生成回答，请稍候...</span>
                </div>
              </div>

              <div class="wechat-composer">
                <textarea
                  v-model="chatInput"
                  rows="5"
                  class="wechat-input"
                  placeholder="输入问题或需求，Enter 发送，Shift+Enter 换行"
                  @keyup.enter.exact.prevent="sendChat"
                ></textarea>
                <div class="composer-actions">
                  <div>
                    <p class="muted small">Markdown 渲染友好，历史自动拼接。</p>
                    <p class="muted small">
                      当前角色：{{ rolePrompts.find((item) => item.id === selectedRoleId)?.name || '默认提示词' }}
                    </p>
                  </div>
                  <div class="composer-buttons">
                    <button class="ghost" @click="resetChat">重置</button>
                    <button @click="sendChat" :disabled="chatLoading">{{ chatLoading ? '正在生成' : '发送' }}</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="table-wrapper role-prompts-wrapper" v-if="rolePrompts.length">
            <div class="table-title">角色提示词库</div>
            <table class="table compact">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>提示词</th>
                  <th v-if="isAdmin">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in rolePrompts" :key="item.id">
                  <td>{{ item.name }}</td>
                  <td class="prompt-cell">{{ item.prompt }}</td>
                  <td v-if="isAdmin" class="row-actions">
                    <button class="ghost" @click="openEditRolePrompt(item)">编辑</button>
                    <button class="ghost danger" @click="deleteRolePrompt(item.id)">删除</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- 首页 -->
        <section class="report-section" v-if="activeMenu === 'home'">
          <!-- 数据面板（所有用户可见） -->
          <div class="section-title">
            <h3>📊 数据面板</h3>
          </div>
          <div class="report-row stats-row">
            <div class="report-card stat-card">
              <div class="card-title">时间 / 天气</div>
              <div class="card-value">{{ dashboard.date || '-' }}</div>
              <p class="muted">{{ dashboard.weather || '晴朗' }}</p>
              <div class="pill-row">
                <span class="pill">本地时间</span>
                <span class="pill">实时气象</span>
              </div>
            </div>
            <div class="report-card stat-card">
              <div class="card-title">来源 IP</div>
              <div class="card-value">{{ dashboard.ip || '-' }}</div>
              <p class="muted">请求入口定位</p>
              <div class="pill-row">
                <span class="pill outline">安全审计</span>
              </div>
            </div>
            <div class="report-card stat-card check-in-card">
              <div class="card-title">每日签到</div>
              <div class="card-value">{{ currentUser?.LDC || 0 }} 天</div>
              <p class="muted">连续签到天数</p>
              <div class="pill-row">
                <button 
                  class="check-in-btn" 
                  @click="handleCheckIn" 
                  :disabled="checkInLoading || todayCheckedIn"
                >
                  {{ checkInLoading ? '签到中...' : (todayCheckedIn ? '已签到 ✓' : '立即签到') }}
                </button>
              </div>
            </div>
            <div class="report-card stat-card">
              <div class="card-title">我的余额</div>
              <div class="card-value">{{ currentUser?.balance?.toFixed(1) || 0 }}</div>
              <p class="muted">积分账户</p>
              <div class="pill-row">
                <span class="pill success">签到可得</span>
              </div>
            </div>
          </div>

          <!-- 系统运维（仅管理员可见） -->
          <template v-if="isAdmin">
            <div class="section-title" style="margin-top: 24px;">
              <h3>🛠️ 系统运维</h3>
            </div>
            <div class="report-row stats-row">
              <div class="report-card stat-card">
                <div class="card-title">新增注册人数</div>
                <div class="card-value">{{ dashboard.redis.register_count }}</div>
                <p class="muted">实时同步 Redis 注册计数</p>
                <div class="mini-bars">
                  <span
                    v-for="(value, idx) in registerTrend"
                    :key="`reg-${idx}`"
                    class="bar"
                    :style="{ height: `${Math.max(30, value * 3)}%` }"
                  ></span>
                </div>
              </div>
              <div class="report-card stat-card">
                <div class="card-title">在线人数</div>
                <div class="card-value">{{ dashboard.redis.online_count }}</div>
                <p class="muted">活跃会话实时态势</p>
                <div class="pill-row">
                  <span class="pill success">高并发守护</span>
                  <span class="pill outline">低延迟</span>
                </div>
              </div>
            </div>

            <div class="report-row main-row">
              <div class="report-card radar-card">
                <div class="card-head">
                  <div>
                    <p class="eyebrow">运行态势</p>
                    <h3>实时容量镜像</h3>
                  </div>
                  <span class="meta-chip">圣诞黑白一键触发</span>
                </div>
                <div class="radar-wrap">
                  <div class="radar-core">
                    <div class="radar-ring"></div>
                    <div class="radar-ring small"></div>
                    <div class="radar-dot"></div>
                    <div class="radar-value">{{ dashboard.redis.online_count }}</div>
                    <p class="radar-desc">在线用户</p>
                  </div>
                  <div class="radar-meta">
                    <p>注册：{{ dashboard.redis.register_count }}</p>
                    <p>天气：{{ dashboard.weather || '晴朗' }}</p>
                    <p>IP：{{ dashboard.ip || '-' }}</p>
                  </div>
                </div>
              </div>

              <div class="report-card trend-card">
                <div class="card-head">
                  <div>
                    <p class="eyebrow">业务增长</p>
                    <h3>请求与在线走势</h3>
                  </div>
                  <span class="meta-chip">近 10 组</span>
                </div>
                <div class="line-chart">
                  <div
                    v-for="(value, idx) in reportTrend"
                    :key="`trend-${idx}`"
                    class="line-bar"
                    :style="{ height: `${Math.min(140, value)}px` }"
                  >
                    <span class="dot"></span>
                    <span class="bar-label">{{ value }}</span>
                  </div>
                </div>
              </div>

              <div class="report-card circle-card">
                <div class="card-head">
                  <div>
                    <p class="eyebrow">资源占比</p>
                    <h3>模型与角色</h3>
                  </div>
                  <span class="meta-chip">健康</span>
                </div>
                <div class="circle-wrap">
                  <div class="progress-circle">{{ models.length }}</div>
                  <p class="muted">已配置模型</p>
                  <div class="progress-circle alt">{{ rolePrompts.length || 0 }}</div>
                  <p class="muted">预设提示词</p>
                </div>
              </div>
            </div>

            <div class="report-row map-row">
              <div class="report-card board-card" style="flex: 1;">
                <div class="card-head">
                  <div>
                    <p class="eyebrow">运维快照</p>
                    <h3>实时提示面板</h3>
                  </div>
                  <span class="meta-chip">安全态</span>
                </div>
                <div class="board-grid">
                  <div class="board-item">
                    <p class="muted">圣诞黑白</p>
                    <strong>{{ christmasActive ? '已启用' : '未启用' }}</strong>
                    <small>点击顶部按钮即可触发飘雪与黑白</small>
                  </div>
                  <div class="board-item">
                    <p class="muted">主题</p>
                    <strong>{{ isDarkMode ? '黑暗模式' : '白天模式' }}</strong>
                    <small>双模式随时切换</small>
                  </div>
                  <div class="board-item">
                    <p class="muted">在线模型</p>
                    <strong>{{ models.length }}</strong>
                    <small>模型配置总数</small>
                  </div>
                  <div class="board-item">
                    <p class="muted">在线人数</p>
                    <strong>{{ dashboard.redis.online_count }}</strong>
                    <small>实时在线用户</small>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </section>

        <!-- 模型管理（原样保留） -->
        <section class="panel" v-if="activeMenu === 'models'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">大模型</p>
              <h3>模型访问配置</h3>
            </div>
            <div class="header-actions">
              <button class="outline" @click="syncAll" :disabled="loading">同步</button>
              <button @click="modals.model = true" :disabled="!isAdmin">新建配置</button>
            </div>
          </div>
          <div class="table-wrapper two-column">
            <div class="table-panel">
              <table class="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>名称</th>
                    <th>模型</th>
                    <th>最大 Token</th>
                    <th v-if="isAdmin">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in models" :key="item.id" @click="openModelDetail(item)" class="clickable">
                    <td>{{ item.id }}</td>
                    <td>{{ item.name }}</td>
                    <td>{{ item.model_name }}</td>
                    <td>{{ item.max_tokens }}</td>
                    <td v-if="isAdmin">
                      <button class="ghost danger" @click.stop="deleteModel(item.id)">删除</button>
                    </td>
                  </tr>
                  <tr v-if="!models.length">
                    <td colspan="5" class="muted">暂无配置</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="detail-panel" v-if="selectedModel">
              <h4>模型详情</h4>
              <p class="muted">点击列表即可查看详情</p>
              <ul class="detail-list">
                <li><span>名称</span><strong>{{ selectedModel.name }}</strong></li>
                <li><span>接口地址</span><strong>{{ selectedModel.base_url }}</strong></li>
                <li><span>模型</span><strong>{{ selectedModel.model_name }}</strong></li>
                <li><span>密钥</span><strong>{{ selectedModel.api_key }}</strong></li>
                <li><span>最大 Token</span><strong>{{ selectedModel.max_tokens }}</strong></li>
                <li><span>温度</span><strong>{{ selectedModel.temperature }}</strong></li>
                <li><span>绑定用户</span><strong>{{ selectedModel.owner_id || '无' }}</strong></li>
              </ul>
              <div class="row-actions" v-if="isAdmin">
                <button class="ghost" @click="modals.modelEdit = true">编辑配置</button>
                <button class="ghost danger" @click="deleteModel(selectedModel.id)">删除</button>
              </div>
            </div>
          </div>
        </section>

        <!-- 网页收藏（原样保留） -->
        <section class="panel" v-if="activeMenu === 'web'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">网页收藏</p>
              <h3>分类与账号信息</h3>
            </div>
            <div class="header-actions">
              <button class="outline" @click="fetchPages(selectedCategory?.id || null)" :disabled="!categories.length">
                刷新网页
              </button>
              <button class="outline" @click="modals.category = true" :disabled="!isAdmin">新建分类</button>
              <button @click="modals.page = true" :disabled="!isAdmin || !categories.length">新增网页</button>
            </div>
          </div>
          <div class="table-wrapper web-bookmarks-layout">
            <div class="table-panel">
              <table class="table">
                <thead>
                  <tr>
                    <th>分类</th>
                    <th>描述</th>
                    <th v-if="isAdmin">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="item in categories"
                    :key="item.id"
                    @click="selectedCategory = item; fetchPages(item.id)"
                    class="clickable"
                  >
                    <td>{{ item.name }}</td>
                    <td>{{ item.description || '无' }}</td>
                    <td v-if="isAdmin"><button class="ghost danger" @click.stop="deleteCategory(item.id)">删除</button></td>
                  </tr>
                  <tr v-if="!categories.length">
                    <td colspan="3" class="muted">暂无分类</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="table-panel">
              <table class="table">
                <thead>
                  <tr>
                    <th>网址</th>
                    <th>账号</th>
                    <th>密码</th>
                    <th>备注</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="page in pages" :key="page.id">
                    <td :title="page.url" class="url-cell">{{ truncateUrl(page.url) }}</td>
                    <td>{{ page.account || '无' }}</td>
                    <td>{{ page.password || '无' }}</td>
                    <td>{{ page.note || '无' }}</td>
                    <td class="row-actions">
                      <a :href="page.url" target="_blank" class="ghost-link" title="跳转到网站">🔗</a>
                      <template v-if="isAdmin">
                        <button class="ghost small" @click="openEditPage(page)">编辑</button>
                        <button class="ghost danger small" @click="deletePage(page.id)">删除</button>
                      </template>
                    </td>
                  </tr>
                  <tr v-if="!pages.length">
                    <td colspan="5" class="muted">请选择分类查看或暂无记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <!-- 相册管理 -->
        <section class="panel neon-panel" v-if="activeMenu === 'album'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">相册管理</p>
              <h3>照片存储与管理</h3>
            </div>
            <div class="header-actions">
              <button @click="fetchAlbums">刷新</button>
            </div>
          </div>
          
          <div class="album-container">
            <!-- 相册列表 -->
            <div class="album-sidebar">
              <div class="album-create">
                <input v-model="albumForm.name" placeholder="相册名称" />
                <input v-model="albumForm.description" placeholder="描述（可选）" />
                <button @click="createAlbum">创建相册</button>
              </div>
              <div class="album-list">
                <div class="album-item" v-for="album in albums" :key="album.id"
                     :class="{ active: selectedAlbum?.id === album.id }"
                     @click="openAlbum(album)">
                  <div class="album-cover" :style="album.cover_url ? { backgroundImage: `url(${apiBase}${album.cover_url})` } : {}">
                    <span v-if="!album.cover_url">📷</span>
                  </div>
                  <div class="album-info">
                    <div class="album-name">{{ album.name }}</div>
                    <div class="album-desc muted">{{ album.description || '无描述' }}</div>
                  </div>
                  <button class="ghost danger small" @click.stop="deleteAlbum(album.id)">删除</button>
                </div>
                <div v-if="!albums.length" class="empty muted">暂无相册</div>
              </div>
            </div>
            
            <!-- 照片区域 -->
            <div class="photo-area" 
                 @dragover="handleDragOver" 
                 @dragleave="handleDragLeave" 
                 @drop="handleDrop"
                 :class="{ 'drag-over': isDragging }">
              <div v-if="selectedAlbum" class="photo-header">
                <h4>{{ selectedAlbum.name }}</h4>
                <div class="photo-upload">
                  <input v-model="photoCaption" placeholder="照片描述（可选）" />
                  <label class="upload-btn">
                    {{ photoUploading ? '上传中...' : '上传照片' }}
                    <input type="file" accept="image/*" @change="uploadPhoto" :disabled="photoUploading" hidden />
                  </label>
                </div>
              </div>
              <div class="drag-hint" v-if="isDragging && selectedAlbum">
                <span>📷 松开鼠标上传照片</span>
              </div>
              <div class="photo-grid" v-if="selectedAlbum && !isDragging">
                <div class="photo-item" v-for="photo in displayedPhotos" :key="photo.id" @click="openPreview(photo)">
                  <img :src="`${apiBase}${photo.url}`" :alt="photo.caption" />
                  <div class="photo-overlay">
                    <span class="photo-caption">{{ photo.caption || '' }}</span>
                    <button class="ghost danger small" @click.stop="deletePhoto(photo.id)">删除</button>
                  </div>
                </div>
                <div v-if="!albumPhotos.length" class="empty muted drag-tip">相册为空，拖动图片到此处或点击上传</div>
              </div>
              <div v-if="selectedAlbum && albumPhotos.length > photosPerPage" class="photo-pagination">
                <button class="ghost" @click="showAllPhotos = !showAllPhotos">
                  {{ showAllPhotos ? '收起' : `显示全部 (${albumPhotos.length})` }}
                </button>
              </div>
              <div v-if="!selectedAlbum" class="empty muted" style="padding: 40px;">请选择一个相册</div>
            </div>
          </div>
        </section>
        
        <!-- 照片预览弹窗 -->
        <div class="modal-mask" v-if="previewPhoto" @click="closePreview">
          <div class="photo-preview" @click.stop>
            <img :src="`${apiBase}${previewPhoto.url}`" :alt="previewPhoto.caption" />
            <div class="preview-info" v-if="previewPhoto.caption">{{ previewPhoto.caption }}</div>
            <button class="preview-close" @click="closePreview">✕</button>
          </div>
        </div>

        <!-- 日记 -->
        <section class="panel neon-panel" v-if="activeMenu === 'diary'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">我的日记</p>
              <h3>记录生活点滴</h3>
            </div>
            <div class="header-actions">
              <button @click="fetchDiaries">刷新</button>
            </div>
          </div>
          
          <div class="diary-container">
            <!-- 日记列表 -->
            <div class="diary-list">
              <div class="diary-item" v-for="diary in diaries" :key="diary.id" 
                   :class="{ active: selectedDiary?.id === diary.id }"
                   @click="openDiaryEdit(diary)">
                <div class="diary-item-header">
                  <span class="diary-mood">{{ diary.mood || '😊' }}</span>
                  <span class="diary-title">{{ diary.title || '无标题' }}</span>
                </div>
                <div class="diary-item-meta">
                  <span class="diary-date">{{ new Date(diary.created_at).toLocaleDateString() }}</span>
                  <button class="ghost danger small" @click.stop="deleteDiary(diary.id)">删除</button>
                </div>
              </div>
              <div v-if="!diaries.length" class="empty muted">暂无日记，开始写第一篇吧</div>
            </div>
            
            <!-- 日记编辑区 -->
            <div class="diary-editor">
              <div class="diary-form">
                <div class="diary-form-header">
                  <input v-model="diaryForm.title" placeholder="日记标题..." class="diary-title-input" />
                  <select v-model="diaryForm.mood" class="diary-mood-select">
                    <option value="😊">😊 开心</option>
                    <option value="😢">😢 难过</option>
                    <option value="😡">😡 生气</option>
                    <option value="😴">😴 疲惫</option>
                    <option value="🤔">🤔 思考</option>
                    <option value="😍">😍 幸福</option>
                    <option value="😎">😎 自信</option>
                    <option value="🥳">🥳 庆祝</option>
                  </select>
                </div>
                <textarea v-model="diaryForm.content" placeholder="今天发生了什么..." class="diary-content-input"></textarea>
                <div class="diary-form-actions">
                  <button v-if="diaryEditing" class="ghost" @click="cancelDiaryEdit">取消</button>
                  <button v-if="diaryEditing" @click="updateDiary">更新日记</button>
                  <button v-else @click="createDiary" :disabled="!diaryForm.content.trim()">保存日记</button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 地图定位 -->
        <section class="panel neon-panel" v-if="activeMenu === 'map'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">地图定位</p>
              <h3>高德地图 · 实时位置</h3>
            </div>
            <div class="header-actions">
              <button class="outline" @click="requestBrowserLocation">
                <span v-if="!isRequestingLocation">📍 请求定位权限</span>
                <span v-else>⏳ 请求中...</span>
              </button>
              <button class="outline" @click="showManualLocationInput = !showManualLocationInput">
                📝 手动输入位置
              </button>
              <button class="outline" @click="refreshLocation">刷新定位</button>
            </div>
          </div>

          <div class="map-wrapper">
            <div v-if="locationError" class="alert error">
              <strong>定位错误：</strong>
              <span>{{ locationError }}</span>
              <p class="muted small" style="margin-top: 8px;">
                💡 提示：如果设备不支持定位，可以点击"手动输入位置"按钮输入地址或坐标
              </p>
            </div>

            <!-- 手动输入位置表单 -->
            <div v-if="showManualLocationInput" class="manual-location-form">
              <h4>手动输入位置</h4>
              <div class="form-row">
                <input 
                  v-model="manualAddress" 
                  type="text" 
                  placeholder="输入地址，例如：北京市朝阳区"
                  @keyup.enter="searchAddress"
                />
                <button @click="searchAddress" :disabled="!manualAddress.trim()">搜索地址</button>
              </div>
              <div class="form-row">
                <input 
                  v-model="manualLng" 
                  type="number" 
                  step="0.000001"
                  placeholder="经度，例如：116.397428"
                />
                <input 
                  v-model="manualLat" 
                  type="number" 
                  step="0.000001"
                  placeholder="纬度，例如：39.90923"
                />
                <button @click="setManualLocation" :disabled="!manualLng || !manualLat">设置坐标</button>
              </div>
            </div>

            <div v-if="userLocation" class="location-info">
              <div class="info-card">
                <span class="label">经度</span>
                <strong>{{ userLocation.lng.toFixed(6) }}</strong>
              </div>
              <div class="info-card">
                <span class="label">纬度</span>
                <strong>{{ userLocation.lat.toFixed(6) }}</strong>
              </div>
              <div class="info-card">
                <span class="label">城市</span>
                <strong>{{ userLocation.city }}</strong>
              </div>
              <div class="info-card full-width">
                <span class="label">详细地址</span>
                <strong>{{ userLocation.address }}</strong>
              </div>
            </div>

            <!-- 地图和AI聊天并排布局 -->
            <div class="map-chat-layout">
              <div class="map-section">
                <div id="amap-container" class="map-container"></div>
                <div v-if="!mapLoaded" class="map-placeholder">
                  <p class="muted">地图加载中...</p>
                  <p class="muted small">首次使用需要授权浏览器定位权限</p>
                </div>
              </div>

              <!-- AI聊天框 -->
              <div class="map-chat-section">
                <div class="map-chat-header">
                  <h4>🤖 AI助手</h4>
                  <span class="muted small">基于当前位置为您推荐</span>
                </div>

                <!-- 快捷按钮 -->
                <div class="map-chat-shortcuts">
                  <button class="shortcut-btn" @click="askMapAI('附近美食')">
                    🍜 附近美食
                  </button>
                  <button class="shortcut-btn" @click="askMapAI('附近旅游攻略')">
                    🏞️ 旅游攻略
                  </button>
                  <button class="shortcut-btn" @click="askMapAI('附近酒店')">
                    🏨 附近酒店
                  </button>
                  <button class="shortcut-btn" @click="askMapAI('附近景点')">
                    📍 附近景点
                  </button>
                </div>

                <!-- 聊天消息区域 -->
                <div class="map-chat-messages">
                  <div v-if="mapChatMessages.length === 0" class="chat-empty">
                    <p class="muted">👋 你好！我是地图AI助手</p>
                    <p class="muted small">点击上方按钮或输入问题，我会根据您的位置为您推荐</p>
                  </div>
                  <div v-for="(msg, idx) in mapChatMessages" :key="idx" 
                       :class="['chat-bubble', msg.role]">
                    <div class="bubble-content" v-html="formatMapChat(msg.content)"></div>
                  </div>
                  <div v-if="mapChatLoading" class="chat-bubble assistant">
                    <div class="bubble-content typing">
                      <span></span><span></span><span></span>
                    </div>
                  </div>
                </div>

                <!-- 输入框 -->
                <div class="map-chat-input">
                  <input 
                    v-model="mapChatInput" 
                    type="text" 
                    placeholder="问问AI，例如：附近有什么好吃的？"
                    @keyup.enter="sendMapChat"
                    :disabled="mapChatLoading"
                  />
                  <button @click="sendMapChat" :disabled="mapChatLoading || !mapChatInput.trim()">
                    发送
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 用户与角色（原样保留） -->
        <section class="panel" v-if="activeMenu === 'users' && isAdmin">
          <div class="panel-header">
            <div>
              <p class="eyebrow">用户管理</p>
              <h3>用户列表</h3>
            </div>
            <div class="header-actions">
              <button @click="modals.user = true">+ 新建</button>
            </div>
          </div>
          
          <!-- 搜索筛选区 -->
          <div class="user-search-bar">
            <div class="search-field">
              <label>用户名</label>
              <input v-model="userSearch.name" placeholder="请输入" />
            </div>
            <div class="search-field">
              <label>手机号</label>
              <input v-model="userSearch.phone" placeholder="请输入" />
            </div>
            <div class="search-field">
              <label>角色</label>
              <select v-model="userSearch.role">
                <option value="">全部</option>
                <option value="admin">管理员</option>
                <option value="user">普通用户</option>
              </select>
            </div>
            <div class="search-actions">
              <button @click="userPage = 1">查询</button>
              <button class="ghost" @click="resetUserSearch">重置</button>
            </div>
          </div>
          
          <!-- 用户表格 -->
          <div class="table-wrapper">
            <table class="table user-table">
              <thead>
                <tr>
                  <th style="width: 60px;">ID</th>
                  <th>用户名</th>
                  <th>邮箱</th>
                  <th>手机号</th>
                  <th style="width: 100px;">角色</th>
                  <th style="width: 100px;">余额</th>
                  <th style="width: 80px;">连签</th>
                  <th style="width: 200px;">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in paginatedUsers" :key="user.id">
                  <td>{{ user.id }}</td>
                  <td>{{ user.name }}</td>
                  <td>{{ user.email || '-' }}</td>
                  <td>{{ user.phone || '-' }}</td>
                  <td>
                    <span :class="['role-badge', user.role]">
                      {{ user.role === 'admin' ? '管理员' : '普通用户' }}
                    </span>
                  </td>
                  <td>¥ {{ user.balance.toFixed(2) }}</td>
                  <td>{{ user.LDC || 0 }}天</td>
                  <td class="row-actions">
                    <button class="ghost small" @click="openEditUser(user)">编辑</button>
                    <button class="ghost small" @click="resetUserPassword(user.id, user.name)">重置密码</button>
                    <button class="ghost danger small" @click="deleteUser(user.id)" :disabled="user.id === currentUser?.id">删除</button>
                  </td>
                </tr>
                <tr v-if="!paginatedUsers.length">
                  <td colspan="8" class="muted">暂无用户</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 分页 -->
          <div class="user-pagination" v-if="filteredUsers.length > userPageSize">
            <span class="page-info">共 {{ filteredUsers.length }} 条</span>
            <div class="page-btns">
              <button class="ghost small" @click="userPage = Math.max(1, userPage - 1)" :disabled="userPage <= 1">上一页</button>
              <span class="page-num">{{ userPage }} / {{ userTotalPages }}</span>
              <button class="ghost small" @click="userPage = Math.min(userTotalPages, userPage + 1)" :disabled="userPage >= userTotalPages">下一页</button>
            </div>
          </div>
        </section>

        <!-- 日志（原样保留） -->
        <section class="panel" v-if="activeMenu === 'logs' && isAdmin">
          <div class="panel-header">
            <div>
              <p class="eyebrow">日志</p>
              <h3>后端运行记录</h3>
            </div>
            <div class="header-actions">
              <button class="outline" @click="fetchLogs">刷新日志</button>
            </div>
          </div>
          <div class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>最近日志</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(line, idx) in logs" :key="idx">
                  <td>{{ line }}</td>
                </tr>
                <tr v-if="!logs.length">
                  <td class="muted">暂无日志记录</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>

      <!-- 下面这些 modal 你原本就有，我保持原样 -->
      <div v-if="modals.login" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>登录</h3>
            <button class="icon" @click="modals.login = false">×</button>
          </div>
          <label>用户名</label>
          <input v-model="forms.login.name" placeholder="请输入用户名" />
          <label>密码</label>
          <input v-model="forms.login.password" type="password" placeholder="请输入密码" />
          <button @click="handleLogin">确认登录</button>
        </div>
      </div>

      <div v-if="modals.register" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>注册</h3>
            <button class="icon" @click="modals.register = false">×</button>
          </div>
          <label>用户名</label>
          <input v-model="forms.register.name" placeholder="请输入用户名" />
          <label>密码</label>
          <input v-model="forms.register.password" type="password" placeholder="请输入密码" />
          <label>角色（仅首个管理员允许）</label>
          <select v-model="forms.register.role">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
          <button @click="handleRegister">完成注册</button>
        </div>
      </div>

      <div v-if="modals.user" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>新建用户</h3>
            <button class="icon" @click="modals.user = false">×</button>
          </div>
          <label>用户名</label>
          <input v-model="forms.user.name" placeholder="请输入用户名" />
          <label>密码</label>
          <input v-model="forms.user.password" type="password" placeholder="初始密码" />
          <label>角色</label>
          <select v-model="forms.user.role">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
          <button @click="createUser">创建</button>
        </div>
      </div>

      <div v-if="modals.userEdit" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>编辑用户</h3>
            <button class="icon" @click="modals.userEdit = false">×</button>
          </div>
          <label>用户名</label>
          <input v-model="forms.editUser.name" placeholder="请输入用户名" />
          <label>新密码（可选）</label>
          <input v-model="forms.editUser.password" type="password" placeholder="不修改可留空" />
          <label>角色</label>
          <select v-model="forms.editUser.role">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
          <button @click="updateUser">保存</button>
        </div>
      </div>

      <div v-if="modals.model" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>新建模型配置</h3>
            <button class="icon" @click="modals.model = false">×</button>
          </div>
          <label>名称</label>
          <input v-model="forms.model.name" placeholder="如：内部 GPT" />
          <label>接口地址</label>
          <input v-model="forms.model.base_url" placeholder="https://api.example.com" />
          <label>模型名称</label>
          <input v-model="forms.model.model_name" placeholder="gpt-4o" />
          <label>密钥</label>
          <input v-model="forms.model.api_key" placeholder="sk-xxxx" />
          <label>最大 Token</label>
          <input v-model.number="forms.model.max_tokens" type="number" placeholder="4096" />
          <label>温度</label>
          <input v-model.number="forms.model.temperature" type="number" step="0.1" placeholder="1" />
          <label>绑定用户 ID（可选）</label>
          <input v-model="forms.model.owner_id" placeholder="用户 ID" />
          <button @click="createModel">保存</button>
        </div>
      </div>

      <div v-if="modals.modelEdit" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>编辑模型配置</h3>
            <button class="icon" @click="modals.modelEdit = false">×</button>
          </div>
          <label>名称</label>
          <input v-model="forms.editModel.name" placeholder="如：内部 GPT" />
          <label>接口地址</label>
          <input v-model="forms.editModel.base_url" placeholder="https://api.example.com" />
          <label>模型名称</label>
          <input v-model="forms.editModel.model_name" placeholder="gpt-4o" />
          <label>密钥</label>
          <input v-model="forms.editModel.api_key" placeholder="sk-xxxx" />
          <label>最大 Token</label>
          <input v-model.number="forms.editModel.max_tokens" type="number" placeholder="4096" />
          <label>温度</label>
          <input v-model.number="forms.editModel.temperature" type="number" step="0.1" placeholder="1" />
          <label>绑定用户 ID（可选）</label>
          <input v-model="forms.editModel.owner_id" placeholder="用户 ID" />
          <button @click="updateModel">保存</button>
        </div>
      </div>

      <div v-if="modals.category" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>新建分类</h3>
            <button class="icon" @click="modals.category = false">×</button>
          </div>
          <label>分类名称</label>
          <input v-model="forms.category.name" placeholder="如：工作" />
          <label>描述</label>
          <input v-model="forms.category.description" placeholder="可选描述" />
          <button @click="createCategory">保存</button>
        </div>
      </div>

      <div v-if="modals.page" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>新增网页</h3>
            <button class="icon" @click="modals.page = false">×</button>
          </div>
          <label>所属分类</label>
          <select v-model="forms.page.category_id">
            <option value="" disabled>请选择</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
          <label>网址</label>
          <input v-model="forms.page.url" placeholder="https://..." />
          <label>账号</label>
          <input v-model="forms.page.account" placeholder="账号（可选）" />
          <label>密码</label>
          <input v-model="forms.page.password" placeholder="密码（可选）" />
          <label>Cookie</label>
          <input v-model="forms.page.cookie" placeholder="Cookie（可选）" />
          <label>备注</label>
          <input v-model="forms.page.note" placeholder="备注信息" />
          <button @click="createPage">保存</button>
        </div>
      </div>

      <div v-if="modals.pageEdit" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>编辑网页</h3>
            <button class="icon" @click="modals.pageEdit = false">×</button>
          </div>
          <label>所属分类</label>
          <select v-model="forms.editPage.category_id">
            <option value="" disabled>请选择</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
          <label>网址</label>
          <input v-model="forms.editPage.url" placeholder="https://..." />
          <label>账号</label>
          <input v-model="forms.editPage.account" placeholder="账号（可选）" />
          <label>密码</label>
          <input v-model="forms.editPage.password" placeholder="密码（可选）" />
          <label>Cookie</label>
          <input v-model="forms.editPage.cookie" placeholder="Cookie（可选）" />
          <label>备注</label>
          <input v-model="forms.editPage.note" placeholder="备注信息" />
          <button @click="updatePage">更新</button>
        </div>
      </div>

      <div v-if="modals.role" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>角色分配</h3>
            <button class="icon" @click="modals.role = false">×</button>
          </div>
          <label>用户 ID</label>
          <input v-model="forms.role.user_id" placeholder="输入用户 ID" />
          <label>角色</label>
          <select v-model="forms.role.role">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
          <button @click="assignRole">更新角色</button>
          <p class="muted small">当前统计：管理员 {{ roleStats.admin || 0 }} / 普通 {{ roleStats.user || 0 }}</p>
        </div>
      </div>

      <div v-if="modals.rolePrompt" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>新增提示词</h3>
            <button class="icon" @click="modals.rolePrompt = false">×</button>
          </div>
          <label>名称</label>
          <input v-model="forms.rolePrompt.name" placeholder="如：产品语气" />
          <label>提示词</label>
          <textarea v-model="forms.rolePrompt.prompt" rows="4" placeholder="输入系统提示词"></textarea>
          <button @click="createRolePrompt">保存</button>
        </div>
      </div>

      <div v-if="modals.rolePromptEdit" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>编辑提示词</h3>
            <button class="icon" @click="modals.rolePromptEdit = false">×</button>
          </div>
          <label>名称</label>
          <input v-model="forms.editRolePrompt.name" />
          <label>提示词</label>
          <textarea v-model="forms.editRolePrompt.prompt" rows="4"></textarea>
          <button @click="updateRolePrompt">更新</button>
        </div>
      </div>

      <div v-if="modals.profileEdit" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>修改个人信息</h3>
            <button class="icon" @click="modals.profileEdit = false">×</button>
          </div>
          <label>用户名</label>
          <input v-model="forms.profileEdit.name" placeholder="请输入用户名" />
          <label>新密码（可选）</label>
          <input v-model="forms.profileEdit.password" type="password" placeholder="不修改可留空" />
          <label>邮箱（可选）</label>
          <input v-model="forms.profileEdit.email" type="email" placeholder="请输入邮箱" />
          <label>手机号（可选）</label>
          <input v-model="forms.profileEdit.phone" placeholder="请输入手机号" />
          <button @click="updateProfile">保存</button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* 只加和“未读/实时状态”相关的最小样式，不碰你原有大样式体系 */
.unread-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: #ff3b30;
  color: #fff;
  font-size: 12px;
  line-height: 18px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 14px rgba(255, 59, 48, 0.25);
}

.peer-avatar {
  position: relative;
}

.preview {
  opacity: 0.9;
}

.ws-pill {
  margin-left: 8px;
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 12px;
  line-height: 18px;
  background: rgba(0, 0, 0, 0.08);
}

.ws-pill.ok {
  background: rgba(0, 200, 83, 0.18);
}

.ws-pill.bad {
  background: rgba(255, 59, 48, 0.18);
}

/* 地图相关样式 */
.map-wrapper {
  position: relative;
  min-height: 450px;
}

.map-chat-layout {
  display: flex;
  gap: 16px;
}

.map-section {
  flex: 0 0 70%;
  position: relative;
}

.map-container {
  width: 100%;
  height: 450px !important;
  min-height: 450px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateZ(0);
  will-change: transform;
  visibility: visible !important;
  opacity: 1 !important;
}

/* AI聊天框样式 */
.map-chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  height: 450px;
}

.map-chat-header {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
}

.map-chat-header h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
}

.map-chat-shortcuts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.shortcut-btn {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: inherit;
  cursor: pointer;
  transition: all 0.2s;
}

.shortcut-btn:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.4), rgba(139, 92, 246, 0.4));
  transform: translateY(-1px);
}

.map-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-empty {
  text-align: center;
  padding: 20px;
}

.chat-bubble {
  max-width: 90%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
}

.chat-bubble.user {
  align-self: flex-end;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #fff;
}

.chat-bubble.assistant {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.1);
}

.bubble-content.typing {
  display: flex;
  gap: 4px;
}

.bubble-content.typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: typing 1s infinite;
}

.bubble-content.typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.bubble-content.typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.map-chat-input {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
}

.map-chat-input input {
  flex: 1;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: inherit;
  font-size: 13px;
}

.map-chat-input button {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
}

/* 白天模式适配 */
.light-mode .map-chat-section {
  background: #ffffff;
  border-color: #e5e7eb;
}

.light-mode .map-chat-header {
  background: #f8fafc;
  border-color: #e5e7eb;
}

.light-mode .map-chat-shortcuts {
  border-color: #e5e7eb;
}

.light-mode .shortcut-btn {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
  border-color: #d1d5db;
  color: #1e293b;
}

.light-mode .chat-bubble.assistant {
  background: #f1f5f9;
  color: #1e293b;
}

.light-mode .map-chat-input {
  background: #f8fafc;
  border-color: #e5e7eb;
}

.light-mode .map-chat-input input {
  background: #ffffff;
  border-color: #d1d5db;
  color: #1e293b;
}

.map-placeholder {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  padding: 40px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dark-mode .map-placeholder {
  background: rgba(30, 30, 30, 0.95);
}

.manual-location-form {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.dark-mode .manual-location-form {
  background: rgba(40, 40, 40, 0.9);
}

.manual-location-form h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.manual-location-form .form-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.manual-location-form .form-row:last-child {
  margin-bottom: 0;
}

.manual-location-form input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  font-size: 14px;
  background: white;
}

.dark-mode .manual-location-form input {
  background: rgba(30, 30, 30, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.manual-location-form button {
  padding: 10px 20px;
  white-space: nowrap;
}

.location-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.info-card {
  padding: 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dark-mode .info-card {
  background: rgba(40, 40, 40, 0.8);
}

.info-card.full-width {
  grid-column: 1 / -1;
}

.info-card .label {
  font-size: 12px;
  opacity: 0.7;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-card strong {
  font-size: 16px;
  font-weight: 600;
}
</style>
