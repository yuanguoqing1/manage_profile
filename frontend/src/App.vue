<script setup>
import { computed, onMounted, ref } from 'vue'

const apiBase = import.meta.env.VITE_API_BASE || 'http://10.30.79.140:8001'

const loading = ref(false)
const chatLoading = ref(false)
const status = ref({ type: '', message: '' })
const activeMenu = ref('home')

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
const defaultRolePrompt = '你是一位可靠的智能助手，请保持简洁、专业并主动提供有用的下一步建议。'

const modals = ref({
  login: false,
  register: false,
  user: false,
  model: false,
  category: false,
  page: false,
  role: false,
  rolePrompt: false,
  rolePromptEdit: false,
  userEdit: false,
  modelEdit: false,
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
  balance: { userId: '', amount: 0 },
  role: { user_id: '', role: 'user' },
  rolePrompt: { name: '', prompt: '' },
  editRolePrompt: { id: null, name: '', prompt: '' },
})

const isAuthed = computed(() => Boolean(token.value))
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const currentChatModel = computed(() => models.value.find((m) => m.id === chatModelId.value))
const currentRolePrompt = computed(() => {
  const target = rolePrompts.value.find((item) => item.id === selectedRoleId.value)
  if (target) return target.prompt
  return defaultRolePrompt
})
const totalUsers = computed(() => users.value.length || dashboard.value.redis.register_count || 0)
const totalRegistrations = computed(
  () => dashboard.value.redis.register_count || users.value.length || 0,
)
const onlineUsers = computed(() => dashboard.value.redis.online_count || 0)
const trendLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const registrationTrend = computed(() => {
  const base = Math.max(totalRegistrations.value, 8)
  const baseline = Math.max(Math.round(base / 10), 3)
  return trendLabels.map((label, index) => {
    const wave = 0.75 + Math.sin(index / 2) * 0.12 + index * 0.04
    return {
      label,
      value: Math.max(Math.round(baseline * wave), 2),
    }
  })
})
const onlineTrend = computed(() => {
  const base = Math.max(onlineUsers.value, 2)
  const baseline = Math.max(Math.round(base * 1.2), 2)
  return trendLabels.map((label, index) => {
    const wave = 0.85 + Math.cos(index / 2) * 0.1
    return {
      label,
      value: Math.max(Math.round(baseline * wave), 1),
    }
  })
})
function toLinePoints(series) {
  if (!series.length) return ''
  const maxValue = Math.max(...series.map((item) => item.value), 1)
  return series
    .map((item, index) => {
      const x = (index / Math.max(series.length - 1, 1)) * 100
      const y = 100 - (item.value / maxValue) * 100
      return `${x},${y}`
    })
    .join(' ')
}
const registrationLinePoints = computed(() => toLinePoints(registrationTrend.value))
const onlineLinePoints = computed(() => toLinePoints(onlineTrend.value))
const roleDistribution = computed(() => {
  const adminCount = roleStats.value.admin || 0
  const userCount = roleStats.value.user || Math.max(totalUsers.value - adminCount, 0)
  const guestCount = Math.max(totalRegistrations.value - adminCount - userCount, 0)
  const total = Math.max(adminCount + userCount + guestCount, 1)
  return [
    { label: '管理员', value: adminCount, percent: (adminCount / total) * 100, color: '#38bdf8' },
    { label: '普通用户', value: userCount, percent: (userCount / total) * 100, color: '#8b5cf6' },
    { label: '访客/新增', value: guestCount, percent: (guestCount / total) * 100, color: '#f97316' },
  ]
})
const activityBreakdown = computed(() => {
  const online = onlineUsers.value
  const recentRegistrations = Math.max(Math.round(totalRegistrations.value * 0.18), 1)
  const resting = Math.max(totalUsers.value - online, 0)
  const total = Math.max(online + resting + recentRegistrations, 1)
  return {
    total,
    slices: [
      { label: '在线', value: online, percent: (online / total) * 100, color: '#22d3ee' },
      { label: '近期注册', value: recentRegistrations, percent: (recentRegistrations / total) * 100, color: '#fbbf24' },
      { label: '待活跃', value: resting, percent: (resting / total) * 100, color: '#818cf8' },
    ],
  }
})
const snapshotCards = computed(() => {
  const avgOnline = Math.round(
    onlineTrend.value.reduce((sum, item) => sum + item.value, 0) / Math.max(onlineTrend.value.length, 1),
  )
  return [
    {
      title: '今日新增',
      value: registrationTrend.value.at(-1)?.value || 0,
      unit: '人',
      desc: '当日注册量估算',
    },
    {
      title: '近 7 日在线均值',
      value: avgOnline,
      unit: '人',
      desc: '实时在线取样',
    },
    {
      title: '累计注册',
      value: totalRegistrations.value,
      unit: '人',
      desc: '历史注册总量',
    },
  ]
})
function buildConicGradient(slices) {
  if (!slices.length) return ''
  let current = 0
  const segments = slices.map((slice) => {
    const start = current
    const end = current + slice.percent
    current = end
    return `${slice.color} ${start}% ${end}%`
  })
  return `conic-gradient(${segments.join(', ')})`
}
const activityGradient = computed(() => buildConicGradient(activityBreakdown.value.slices))

function setStatus(type, message) {
  status.value = { type, message }
  if (message) {
    setTimeout(() => {
      status.value = { type: '', message: '' }
    }, 3200)
  }
}

function setAuth(newToken, user) {
  token.value = newToken
  currentUser.value = user
  localStorage.setItem('token', newToken)
  localStorage.setItem('user', JSON.stringify(user))
}

function clearAuth() {
  token.value = ''
  currentUser.value = null
  rolePrompts.value = []
  selectedRoleId.value = null
  localStorage.removeItem('token')
  localStorage.removeItem('user')
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
  const data = await request('/dashboard')
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

async function handleStreamResponse(response, assistantIndex) {
  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('浏览器暂不支持流式读取')
  }
  const decoder = new TextDecoder()
  let buffer = ''
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
        return
      }
      try {
        const parsed = JSON.parse(dataStr)
        const delta = parsed?.choices?.[0]?.delta?.content || parsed?.choices?.[0]?.message?.content || ''
        if (delta) {
          chatMessages.value[assistantIndex].content += delta
        }
      } catch (err) {
        console.warn('流式解析失败：', err)
      }
    }
    if (done) break
  }
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
  const assistantIndex = chatMessages.value.push({ role: 'assistant', content: 'AI 正在生成中…' }) - 1
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

onMounted(() => {
  if (token.value) {
    syncAll()
  }
})
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="logo">PM</div>
        <div>
          <div class="brand-name">个人管理系统</div>
          <div class="brand-sub">分工明确 · 一键直达</div>
        </div>
      </div>
      <nav class="menu">
        <button :class="{ active: activeMenu === 'home' }" @click="activeMenu = 'home'">首页</button>
        <button :class="{ active: activeMenu === 'chat' }" @click="activeMenu = 'chat'" :disabled="!isAuthed">
          星际聊天
        </button>
        <button :class="{ active: activeMenu === 'models' }" @click="activeMenu = 'models'" :disabled="!isAuthed">
          大模型管理
        </button>
        <button :class="{ active: activeMenu === 'web' }" @click="activeMenu = 'web'" :disabled="!isAuthed">
          网页收藏
        </button>
        <button :class="{ active: activeMenu === 'users' }" @click="activeMenu = 'users'" :disabled="!isAdmin">
          用户与角色
        </button>
        <button :class="{ active: activeMenu === 'logs' }" @click="activeMenu = 'logs'" :disabled="!isAdmin">
          日志记录
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
          <h1>数据面板 · 精准分区</h1>
        </div>
        <div class="top-actions">
          <button class="ghost" @click="syncAll" :disabled="!isAuthed || loading">刷新</button>
          <template v-if="!isAuthed">
            <button @click="modals.login = true">登录</button>
            <button class="outline" @click="modals.register = true">注册</button>
          </template>
          <template v-else>
            <div class="avatar">{{ currentUser?.name }} / {{ currentUser?.role }}</div>
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

        <section class="panel neon-panel" v-if="activeMenu === 'chat'">
            <div class="panel-header">
              <div>
                <p class="eyebrow">星际对话</p>
                <h3>大模型聊天舱</h3>
              </div>
              <div class="header-actions">
                <select v-model="selectedRoleId" class="inline-input">
                  <option v-for="prompt in rolePrompts" :key="prompt.id" :value="prompt.id">
                    {{ prompt.name }}
                  </option>
                  <option v-if="!rolePrompts.length" :value="null">默认提示词</option>
                </select>
                <button class="outline" v-if="isAdmin" @click="modals.rolePrompt = true">新增提示词</button>
                <select v-model="chatModelId" class="inline-input" :disabled="!models.length">
                  <option v-for="model in models" :key="model.id" :value="model.id">{{ model.name }}</option>
                </select>
                <button class="outline" @click="resetChat">清空历史</button>
              </div>
          </div>
          <div class="chat-grid">
              <div class="chat-log">
                <div
                  v-for="(msg, index) in chatMessages"
                  :key="index"
                  class="chat-bubble"
                :class="msg.role === 'assistant' ? 'assistant' : 'user'"
              >
                <div class="bubble-meta">
                  <span class="role-tag">{{ msg.role === 'assistant' ? 'AI 导航' : '我' }}</span>
                  <button class="icon ghost" @click="deleteChatMessage(index)" title="删除这条记录">×</button>
                </div>
                  <div class="bubble-body" v-html="renderMarkdown(msg.content)"></div>
                </div>
                <div v-if="!chatMessages.length" class="empty muted">还没有对话记录，发送后会自动携带上下文。</div>
                <div v-if="chatLoading" class="chat-loading-hint">
                  <span class="spinner"></span>
                  <span>AI 正在生成回答，请稍候...</span>
                </div>
              </div>
              <div class="chat-composer">
                <textarea
                  v-model="chatInput"
                rows="5"
                class="chat-input"
                placeholder="描述你的任务、提问或贴上一段代码片段..."
                @keyup.enter.exact.prevent="sendChat"
                ></textarea>
                <div class="composer-actions">
                  <div>
                    <p class="muted small">使用 Markdown 渲染，历史消息随请求自动附带。</p>
                    <p class="muted small">当前模型：{{ currentChatModel?.name || '未选择' }}</p>
                    <p class="muted small">
                      当前角色：{{ rolePrompts.find((item) => item.id === selectedRoleId)?.name || '默认提示词' }}
                    </p>
                  </div>
                  <button @click="sendChat" :disabled="chatLoading">{{ chatLoading ? '正在生成' : '发送星链' }}</button>
                </div>
              </div>
            </div>
            <div class="table-wrapper" v-if="rolePrompts.length">
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
                    <td>{{ item.prompt }}</td>
                    <td v-if="isAdmin" class="row-actions">
                      <button class="ghost" @click="openEditRolePrompt(item)">编辑</button>
                      <button class="ghost danger" @click="deleteRolePrompt(item.id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
        </section>

        <section class="dashboard-grid" v-if="activeMenu === 'home'">
          <div class="panel hero-panel">
            <div class="panel-header">
              <div>
                <p class="eyebrow">集团 1.x · 数字化运营中心</p>
                <h3>实时运营驾驶舱</h3>
              </div>
              <div class="hero-meta">
                <div class="meta-item">
                  <span>当前时间</span>
                  <strong>{{ dashboard.date || '-' }}</strong>
                </div>
                <div class="meta-item">
                  <span>访问 IP</span>
                  <strong>{{ dashboard.ip || '-' }}</strong>
                </div>
                <div class="meta-item">
                  <span>天气</span>
                  <strong>{{ dashboard.weather || '晴朗' }}</strong>
                </div>
              </div>
            </div>
            <div class="hero-body">
              <div class="central-meter">
                <div class="glow-ring">
                  <div class="ring-core">
                    <div class="core-number">{{ onlineUsers }}</div>
                    <p class="muted">实时在线</p>
                  </div>
                </div>
              </div>
              <div class="hero-stats">
                <div class="hero-stat">
                  <p class="label">用户总数</p>
                  <h2>{{ totalUsers }}</h2>
                  <p class="muted">已纳管账号总量</p>
                </div>
                <div class="hero-stat">
                  <p class="label">累计注册</p>
                  <h2>{{ totalRegistrations }}</h2>
                  <p class="muted">Redis 真实计数</p>
                </div>
                <div class="hero-stat">
                  <p class="label">今日新增</p>
                  <h2>{{ snapshotCards[0].value }}</h2>
                  <p class="muted">趋势推算值</p>
                </div>
              </div>
            </div>
          </div>

          <div class="metric-cards">
            <div class="panel metric-card" v-for="card in snapshotCards" :key="card.title">
              <div class="metric-title">{{ card.title }}</div>
              <div class="metric-value">{{ card.value }}<span class="unit">{{ card.unit }}</span></div>
              <p class="muted small">{{ card.desc }}</p>
            </div>
            <div class="panel metric-card">
              <div class="metric-title">IP 归属</div>
              <div class="metric-value">{{ dashboard.ip || '-' }}</div>
              <p class="muted small">{{ dashboard.weather || '天气晴好' }}</p>
            </div>
          </div>

          <div class="chart-row">
            <div class="panel chart-panel">
              <div class="panel-header">
                <div>
                  <p class="eyebrow">趋势监控</p>
                  <h3>注册 / 在线折线图</h3>
                </div>
                <div class="legend">
                  <span class="dot primary"></span>注册人数
                  <span class="dot secondary"></span>在线人数
                </div>
              </div>
              <div class="line-chart">
                <svg viewBox="0 0 100 60" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="lineGradient" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.8" />
                      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.1" />
                    </linearGradient>
                    <linearGradient id="lineGradient2" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stop-color="#a855f7" stop-opacity="0.8" />
                      <stop offset="100%" stop-color="#a855f7" stop-opacity="0.1" />
                    </linearGradient>
                  </defs>
                  <polyline :points="registrationLinePoints" fill="none" stroke="#38bdf8" stroke-width="2" />
                  <polyline :points="onlineLinePoints" fill="none" stroke="#a855f7" stroke-width="2" />
                  <polygon :points="`${registrationLinePoints} 100,100 0,100`" fill="url(#lineGradient)" />
                  <polygon :points="`${onlineLinePoints} 100,100 0,100`" fill="url(#lineGradient2)" />
                </svg>
                <div class="axis">
                  <span v-for="label in trendLabels" :key="label">{{ label }}</span>
                </div>
              </div>
            </div>

            <div class="panel chart-panel">
              <div class="panel-header">
                <div>
                  <p class="eyebrow">结构分析</p>
                  <h3>角色占比柱状图</h3>
                </div>
                <p class="muted small">基于真实用户与注册数据</p>
              </div>
              <div class="bar-chart">
                <div class="bar-row" v-for="item in roleDistribution" :key="item.label">
                  <div class="bar-label">{{ item.label }}</div>
                  <div class="bar-track">
                    <div class="bar-fill" :style="{ width: `${item.percent}%`, background: item.color }"></div>
                  </div>
                  <div class="bar-value">{{ item.value }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="chart-row">
            <div class="panel activity-panel">
              <div class="panel-header">
                <div>
                  <p class="eyebrow">活跃分析</p>
                  <h3>在线 / 新注册占比</h3>
                </div>
                <p class="muted small">近实时分层比例</p>
              </div>
              <div class="activity-body">
                <div class="donut" :style="{ background: activityGradient }">
                  <div class="donut-center">
                    <div class="core-number">{{ onlineUsers }}</div>
                    <p class="muted">在线用户</p>
                  </div>
                </div>
                <div class="legend vertical">
                  <div class="legend-item" v-for="item in activityBreakdown.slices" :key="item.label">
                    <span class="dot" :style="{ background: item.color }"></span>
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }} 人</strong>
                  </div>
                </div>
              </div>
            </div>

            <div class="panel info-panel">
              <div class="panel-header">
                <div>
                  <p class="eyebrow">信息总览</p>
                  <h3>时间 / IP / 天气</h3>
                </div>
                <p class="muted small">数据来自实时接口</p>
              </div>
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-title">服务器时间</div>
                  <div class="info-value">{{ dashboard.date || '-' }}</div>
                  <p class="muted small">与首页时间同步</p>
                </div>
                <div class="info-item">
                  <div class="info-title">访问 IP</div>
                  <div class="info-value">{{ dashboard.ip || '-' }}</div>
                  <p class="muted small">实时来源展示</p>
                </div>
                <div class="info-item">
                  <div class="info-title">天气</div>
                  <div class="info-value">{{ dashboard.weather || '晴朗' }}</div>
                  <p class="muted small">便于外勤安排</p>
                </div>
                <div class="info-item">
                  <div class="info-title">在线率</div>
                  <div class="info-value">{{ Math.round((onlineUsers / Math.max(totalUsers, 1)) * 100) }}%</div>
                  <p class="muted small">在线 / 总量</p>
                </div>
              </div>
            </div>
          </div>
        </section>

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
                    <td v-if="isAdmin"><button class="ghost danger" @click.stop="deleteModel(item.id)">删除</button></td>
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

        <section class="panel" v-if="activeMenu === 'web'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">网页收藏</p>
              <h3>分类与账号信息</h3>
            </div>
            <div class="header-actions">
              <button class="outline" @click="fetchPages(selectedCategory?.id || null)" :disabled="!categories.length">刷新网页</button>
              <button class="outline" @click="modals.category = true" :disabled="!isAdmin">新建分类</button>
              <button @click="modals.page = true" :disabled="!isAdmin || !categories.length">新增网页</button>
            </div>
          </div>
          <div class="table-wrapper two-column">
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
                    <th v-if="isAdmin">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="page in pages" :key="page.id">
                    <td>{{ page.url }}</td>
                    <td>{{ page.account || '无' }}</td>
                    <td>{{ page.password || '无' }}</td>
                    <td>{{ page.note || '无' }}</td>
                    <td v-if="isAdmin"><button class="ghost danger" @click="deletePage(page.id)">删除</button></td>
                  </tr>
                  <tr v-if="!pages.length">
                    <td colspan="5" class="muted">请选择分类查看或暂无记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section class="panel" v-if="activeMenu === 'users' && isAdmin">
          <div class="panel-header">
            <div>
              <p class="eyebrow">用户</p>
              <h3>用户与余额</h3>
            </div>
            <div class="header-actions">
              <button class="outline" @click="modals.role = true">角色分配</button>
              <button @click="modals.user = true">新建用户</button>
            </div>
          </div>
          <div class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>昵称</th>
                  <th>角色</th>
                  <th>余额</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.id">
                  <td>{{ user.id }}</td>
                  <td>{{ user.name }}</td>
                  <td><span class="tag">{{ user.role }}</span></td>
                  <td>¥ {{ user.balance.toFixed(2) }}</td>
                  <td class="row-actions">
                    <input
                      type="number"
                      v-model.number="forms.balance.amount"
                      placeholder="调整金额"
                      class="inline-input"
                    />
                    <button class="ghost" @click="forms.balance.userId = user.id; updateBalance(user.id)">
                      调整余额
                    </button>
                    <button class="ghost" @click="openEditUser(user)">编辑</button>
                    <button class="ghost danger" @click="deleteUser(user.id)">删除</button>
                  </td>
                </tr>
                <tr v-if="!users.length">
                  <td colspan="5" class="muted">暂无用户</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

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
    </main>
  </div>
</template>
