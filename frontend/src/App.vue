<script setup>
import { computed, onMounted, ref } from 'vue'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

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
const chatMessages = ref([])
const chatInput = ref('')
const chatModelId = ref(null)
const chatRole = ref('general')

const rolePresets = [
  {
    key: 'general',
    name: '通用助手',
    prompt: '你是一个耐心且高效的通用助手，请用简洁中文回答。',
  },
  {
    key: 'engineer',
    name: '工程专家',
    prompt: '你是一名严谨的资深工程师，请给出可执行、分步骤的解决方案。',
  },
  {
    key: 'pm',
    name: '产品经理',
    prompt: '你是一名产品经理，请以业务价值和用户体验为核心给出建议。',
  },
]

const modals = ref({
  login: false,
  register: false,
  user: false,
  model: false,
  category: false,
  page: false,
  role: false,
})

const forms = ref({
  login: { name: '', password: '' },
  register: { name: '', password: '', role: 'user' },
  user: { name: '', password: '', role: 'user' },
  model: {
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
})

const isAuthed = computed(() => Boolean(token.value))
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const currentChatModel = computed(() => models.value.find((m) => m.id === chatModelId.value))
const currentRolePrompt = computed(() => rolePresets.find((item) => item.key === chatRole.value)?.prompt || '')

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
        role_prompt: currentRolePrompt.value || undefined,
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
                <select v-model="chatRole" class="inline-input">
                  <option v-for="preset in rolePresets" :key="preset.key" :value="preset.key">
                    {{ preset.name }}
                  </option>
                </select>
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
                    <p class="muted small">当前角色：{{ rolePresets.find((item) => item.key === chatRole)?.name }}</p>
                  </div>
                  <button @click="sendChat" :disabled="chatLoading">{{ chatLoading ? '正在生成' : '发送星链' }}</button>
                </div>
              </div>
            </div>
        </section>

        <section class="panel-grid" v-if="activeMenu === 'home'">
          <div class="panel stat">
            <p class="label">Redis 注册数</p>
            <h2>{{ dashboard.redis.register_count }}</h2>
            <p class="muted">历史注册总量</p>
          </div>
          <div class="panel stat">
            <p class="label">在线人数</p>
            <h2>{{ dashboard.redis.online_count }}</h2>
            <p class="muted">实时在线</p>
          </div>
          <div class="panel stat">
            <p class="label">当前时间</p>
            <h2>{{ dashboard.date || '-' }}</h2>
            <p class="muted">本地服务器时间</p>
          </div>
          <div class="panel stat">
            <p class="label">IP 信息</p>
            <h2>{{ dashboard.ip || '-' }}</h2>
            <p class="muted">请求来源</p>
          </div>
          <div class="panel stat">
            <p class="label">天气</p>
            <h2>{{ dashboard.weather || '晴朗' }}</h2>
            <p class="muted">简易天气展示</p>
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
    </main>
  </div>
</template>
