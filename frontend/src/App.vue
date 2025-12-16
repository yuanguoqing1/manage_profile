<script setup>
import { onMounted, ref } from 'vue'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const loading = ref(false)
const status = ref({ type: '', message: '' })

const summary = ref({ user_count: 0, total_balance: 0, api_key_count: 0 })
const users = ref([])
const keys = ref([])

const newUser = ref({ name: '', balance: 0 })
const balanceUpdate = ref({ userId: '', amount: 0 })
const newKey = ref({ label: '', key: '', owner_id: '' })
const activeMenu = ref('dashboard')

function setStatus(type, message) {
  status.value = { type, message }
  if (message) {
    setTimeout(() => {
      status.value = { type: '', message: '' }
    }, 3200)
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(detail.detail || '请求失败')
  }
  return response.status === 204 ? null : response.json()
}

async function loadData() {
  loading.value = true
  try {
    ;[summary.value, users.value, keys.value] = await Promise.all([
      request('/summary'),
      request('/users'),
      request('/apikeys'),
    ])
    setStatus('success', '数据已同步')
  } catch (error) {
    console.error(error)
    setStatus('error', error.message)
  } finally {
    loading.value = false
  }
}

async function createUser() {
  if (!newUser.value.name.trim()) return
  try {
    await request('/users', {
      method: 'POST',
      body: JSON.stringify({ ...newUser.value, balance: Number(newUser.value.balance) }),
    })
    newUser.value = { name: '', balance: 0 }
    setStatus('success', '用户创建成功')
    await loadData()
  } catch (error) {
    console.error(error)
    setStatus('error', error.message)
  }
}

async function updateBalance() {
  if (!balanceUpdate.value.userId) return
  try {
    await request(
      `/users/${balanceUpdate.value.userId}/balance?amount=${balanceUpdate.value.amount}`,
      {
        method: 'PUT',
      },
    )
    balanceUpdate.value = { userId: '', amount: 0 }
    setStatus('success', '余额已更新')
    await loadData()
  } catch (error) {
    console.error(error)
    setStatus('error', error.message)
  }
}

async function createApiKey() {
  if (!newKey.value.label.trim() || !newKey.value.key.trim()) return
  try {
    await request('/apikeys', {
      method: 'POST',
      body: JSON.stringify({
        label: newKey.value.label,
        key: newKey.value.key,
        owner_id: newKey.value.owner_id ? Number(newKey.value.owner_id) : null,
      }),
    })
    newKey.value = { label: '', key: '', owner_id: '' }
    setStatus('success', 'API Key 创建成功')
    await loadData()
  } catch (error) {
    console.error(error)
    setStatus('error', error.message)
  }
}

async function deleteKey(id) {
  try {
    await request(`/apikeys/${id}`, { method: 'DELETE' })
    setStatus('success', 'API Key 已删除')
    await loadData()
  } catch (error) {
    console.error(error)
    setStatus('error', error.message)
  }
}

onMounted(loadData)
</script>

<template>

  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="dot"></span>
        <div>
          <div class="brand-name">Balance Admin</div>
          <div class="brand-sub">Vue + FastAPI</div>
        </div>
      </div>
      <nav class="menu">
        <button :class="{ active: activeMenu === 'dashboard' }" @click="activeMenu = 'dashboard'">
          总览
        </button>
        <button :class="{ active: activeMenu === 'users' }" @click="activeMenu = 'users'">用户</button>
        <button :class="{ active: activeMenu === 'keys' }" @click="activeMenu = 'keys'">API Keys</button>
        <button :class="{ active: activeMenu === 'settings' }" @click="activeMenu = 'settings'" disabled>
          设置
        </button>
      </nav>
      <div class="sidebar-footer">
        <p>数据实时同步</p>
        <small v-if="loading">正在加载…</small>
      </div>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <p class="eyebrow">管理控制台</p>
          <h1>余额 &amp; Key 管理</h1>
        </div>
        <div class="top-actions">
          <button class="ghost" @click="loadData">刷新数据</button>
          <div class="avatar">管理员</div>
        </div>
      </header>

      <div v-if="status.message" class="alert" :class="status.type">
        <strong>{{ status.type === 'error' ? '提示' : '完成' }}：</strong>
        <span>{{ status.message }}</span>
      </div>

      <div v-if="loading" class="loading-banner">正在同步数据…</div>

      <section v-if="activeMenu === 'dashboard'" class="panel-grid">
        <div class="panel stat">
          <p class="label">用户数</p>
          <h2>{{ summary.user_count }}</h2>
          <p class="muted">所有活跃用户</p>
        </div>
        <div class="panel stat">
          <p class="label">API Keys</p>
          <h2>{{ summary.api_key_count }}</h2>
          <p class="muted">已登记的密钥</p>
        </div>
        <div class="panel stat">
          <p class="label">余额合计</p>
          <h2>¥ {{ summary.total_balance.toFixed(2) }}</h2>
          <p class="muted">可用资金</p>
        </div>
      </section>

      <section v-if="activeMenu === 'dashboard'" class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">快速操作</p>
            <h3>用户与余额</h3>
          </div>
        </div>
        <div class="form-grid">
          <div class="form-card">
            <div class="form-title">新建用户</div>
            <label>昵称</label>
            <input v-model="newUser.name" placeholder="如：运营账号" />
            <label>初始余额</label>
            <input type="number" v-model.number="newUser.balance" min="0" step="0.01" />
            <button :disabled="!newUser.name" @click="createUser">创建</button>
          </div>
          <div class="form-card">
            <div class="form-title">调整余额</div>
            <label>用户 ID</label>
            <input v-model="balanceUpdate.userId" placeholder="输入用户 ID" />
            <label>调整金额（可正可负）</label>
            <input type="number" v-model.number="balanceUpdate.amount" step="0.01" />
            <button :disabled="!balanceUpdate.userId" @click="updateBalance">更新</button>
          </div>
          <div class="form-card">
            <div class="form-title">新建 API Key</div>
            <label>Key 描述</label>
            <input v-model="newKey.label" placeholder="如：生产环境 Key" />
            <label>Key 值</label>
            <input v-model="newKey.key" placeholder="sk-xxxx" />
            <label>绑定用户 ID（可选）</label>
            <input v-model="newKey.owner_id" placeholder="用户 ID" />
            <button :disabled="!newKey.label || !newKey.key" @click="createApiKey">保存</button>
          </div>
        </div>
      </section>

      <section v-if="activeMenu === 'users' || activeMenu === 'dashboard'" class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">列表</p>
            <h3>用户管理</h3>
          </div>
          <button class="ghost" @click="loadData">刷新</button>
        </div>
        <div class="table-wrapper">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>昵称</th>
                <th>余额</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.id }}</td>
                <td>{{ user.name }}</td>
                <td>{{ user.balance.toFixed(2) }}</td>
              </tr>
              <tr v-if="!users.length">
                <td colspan="3" class="muted">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section v-if="activeMenu === 'keys' || activeMenu === 'dashboard'" class="panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">列表</p>
            <h3>API Key 管理</h3>
          </div>
        </div>
        <div class="table-wrapper">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>描述</th>
                <th>Key</th>
                <th>绑定用户</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in keys" :key="item.id">
                <td>{{ item.id }}</td>
                <td>{{ item.label }}</td>
                <td><span class="tag">{{ item.key }}</span></td>
                <td>{{ item.owner_id || '未绑定' }}</td>
                <td><button class="ghost danger" @click="deleteKey(item.id)">删除</button></td>
              </tr>
              <tr v-if="!keys.length">
                <td colspan="5" class="muted">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</template>
