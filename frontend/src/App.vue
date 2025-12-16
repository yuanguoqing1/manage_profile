<script setup>
import { computed, onMounted, ref } from 'vue'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const loading = ref(false)
const status = ref({ type: '', message: '' })
const activeMenu = ref('home')

const token = ref(localStorage.getItem('token') || '')
const currentUser = ref(JSON.parse(localStorage.getItem('user') || 'null'))

const dashboard = ref({
  summary: { user_count: 0, total_balance: 0, api_key_count: 0 },
  redis: { register_count: 0, online_count: 0 },
  date: '',
  ip: '',
  weather: '',
})

const users = ref([])
const keys = ref([])
const selectedKey = ref(null)
const roleStats = ref({ admin: 0, user: 0 })

const modals = ref({
  login: false,
  register: false,
  user: false,
  key: false,
  role: false,
})

const forms = ref({
  login: { name: '', password: '' },
  register: { name: '', password: '', role: 'user' },
  user: { name: '', password: '', role: 'user' },
  key: { label: '', key: '', owner_id: '' },
  balance: { userId: '', amount: 0 },
  role: { user_id: '', role: 'user' },
})

const isAuthed = computed(() => Boolean(token.value))
const isAdmin = computed(() => currentUser.value?.role === 'admin')

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

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) }
  if (token.value) {
    headers.Authorization = `Bearer ${token.value}`
  }
  const response = await fetch(`${apiBase}${path}`, { ...options, headers })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(detail.detail || '请求失败')
  }
  return response.status === 204 ? null : response.json()
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

async function fetchKeys() {
  keys.value = await request('/apikeys')
  if (selectedKey.value) {
    const refreshed = keys.value.find((k) => k.id === selectedKey.value.id)
    selectedKey.value = refreshed || null
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

async function syncAll() {
  loading.value = true
  try {
    await Promise.all([fetchDashboard(), fetchKeys(), fetchUsers(), fetchRoles()])
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
  keys.value = []
  users.value = []
  dashboard.value = {
    summary: { user_count: 0, total_balance: 0, api_key_count: 0 },
    redis: { register_count: 0, online_count: 0 },
    date: '',
    ip: '',
    weather: '',
  }
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
    await fetchDashboard()
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
    await fetchDashboard()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function createApiKey() {
  try {
    const payload = { ...forms.value.key, owner_id: forms.value.key.owner_id || null }
    await request('/apikeys', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
    setStatus('success', 'API Key 已创建')
    modals.value.key = false
    forms.value.key = { label: '', key: '', owner_id: '' }
    await fetchKeys()
  } catch (error) {
    setStatus('error', error.message)
  }
}

async function deleteKey(id) {
  if (!confirm('确认删除该 Key 吗？')) return
  try {
    await request(`/apikeys/${id}`, { method: 'DELETE' })
    setStatus('success', 'API Key 已删除')
    await fetchKeys()
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

function openKeyDetail(item) {
  selectedKey.value = item
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
          <div class="brand-name">Profile Manager</div>
          <div class="brand-sub">Vue + FastAPI</div>
        </div>
      </div>
      <nav class="menu">
        <button :class="{ active: activeMenu === 'home' }" @click="activeMenu = 'home'">首页</button>
        <button :class="{ active: activeMenu === 'users' }" @click="activeMenu = 'users'" :disabled="!isAdmin">
          用户与角色
        </button>
        <button :class="{ active: activeMenu === 'keys' }" @click="activeMenu = 'keys'" :disabled="!isAuthed">
          API Keys
        </button>
      </nav>
      <div class="sidebar-footer">
        <p class="muted">Redis 注册数：{{ dashboard.redis.register_count }}</p>
        <p class="muted">在线人数：{{ dashboard.redis.online_count }}</p>
      </div>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <p class="eyebrow">管理控制台</p>
          <h1>账户 · 权限 · API Keys</h1>
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

        <section class="panel-grid">
          <div class="panel stat">
            <p class="label">用户数</p>
            <h2>{{ dashboard.summary.user_count }}</h2>
            <p class="muted">全局用户</p>
          </div>
          <div class="panel stat">
            <p class="label">API Keys</p>
            <h2>{{ dashboard.summary.api_key_count }}</h2>
            <p class="muted">登记密钥</p>
          </div>
          <div class="panel stat">
            <p class="label">余额合计</p>
            <h2>¥ {{ dashboard.summary.total_balance.toFixed(2) }}</h2>
            <p class="muted">当前资金</p>
          </div>
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
          <div class="panel stat wide">
            <p class="label">今日信息</p>
            <div class="info-row">
              <span>时间</span>
              <strong>{{ dashboard.date || '-' }}</strong>
            </div>
            <div class="info-row">
              <span>IP</span>
              <strong>{{ dashboard.ip || '-' }}</strong>
            </div>
            <div class="info-row">
              <span>天气</span>
              <strong>{{ dashboard.weather || '晴朗' }}</strong>
            </div>
          </div>
        </section>

        <section class="panel" v-if="activeMenu === 'home'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">说明</p>
              <h3>功能入口</h3>
            </div>
            <div class="tag">每个按钮只做一件事</div>
          </div>
          <div class="action-grid">
            <div class="action-card" @click="activeMenu = 'keys'">
              <h4>API Key 查看</h4>
              <p class="muted">点击进入即可查看详情与创建</p>
            </div>
            <div class="action-card" :class="{ disabled: !isAdmin }" @click="isAdmin && (activeMenu = 'users')">
              <h4>用户/角色</h4>
              <p class="muted">管理员入口：管理账号与权限</p>
            </div>
            <div class="action-card" @click="syncAll">
              <h4>刷新数据</h4>
              <p class="muted">同步 Redis 与仪表盘数据</p>
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

        <section class="panel" v-if="activeMenu === 'keys'">
          <div class="panel-header">
            <div>
              <p class="eyebrow">API</p>
              <h3>API Key 管理</h3>
            </div>
            <div class="header-actions">
              <button class="outline" @click="syncAll" :disabled="loading">同步</button>
              <button @click="modals.key = true" :disabled="!isAdmin">新建 API Key</button>
            </div>
          </div>
          <div class="table-wrapper two-column">
            <div class="table-panel">
              <table class="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>描述</th>
                    <th>Key</th>
                    <th>绑定用户</th>
                    <th v-if="isAdmin">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in keys" :key="item.id" @click="openKeyDetail(item)" class="clickable">
                    <td>{{ item.id }}</td>
                    <td>{{ item.label }}</td>
                    <td><span class="tag">{{ item.key }}</span></td>
                    <td>{{ item.owner_id || '未绑定' }}</td>
                    <td v-if="isAdmin"><button class="ghost danger" @click.stop="deleteKey(item.id)">删除</button></td>
                  </tr>
                  <tr v-if="!keys.length">
                    <td colspan="5" class="muted">暂无数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="detail-panel" v-if="selectedKey">
              <h4>API 详情</h4>
              <p class="muted">点击列表即可在此查看详情</p>
              <ul class="detail-list">
                <li><span>描述</span><strong>{{ selectedKey.label }}</strong></li>
                <li><span>Key</span><strong>{{ selectedKey.key }}</strong></li>
                <li><span>绑定用户</span><strong>{{ selectedKey.owner_id || '未绑定' }}</strong></li>
              </ul>
            </div>
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

      <div v-if="modals.key" class="modal-mask">
        <div class="modal">
          <div class="modal-header">
            <h3>新建 API Key</h3>
            <button class="icon" @click="modals.key = false">×</button>
          </div>
          <label>描述</label>
          <input v-model="forms.key.label" placeholder="如：生产环境 Key" />
          <label>Key 值</label>
          <input v-model="forms.key.key" placeholder="sk-xxxx" />
          <label>绑定用户 ID（可选）</label>
          <input v-model="forms.key.owner_id" placeholder="用户 ID" />
          <button @click="createApiKey">保存</button>
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
