<script setup>
import { onMounted, ref } from 'vue'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const loading = ref(false)

const summary = ref({ user_count: 0, total_balance: 0, api_key_count: 0 })
const users = ref([])
const keys = ref([])

const newUser = ref({ name: '', balance: 0 })
const balanceUpdate = ref({ userId: '', amount: 0 })
const newKey = ref({ label: '', key: '', owner_id: '' })

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
  } finally {
    loading.value = false
  }
}

async function createUser() {
  if (!newUser.value.name.trim()) return
  await request('/users', {
    method: 'POST',
    body: JSON.stringify({ ...newUser.value, balance: Number(newUser.value.balance) }),
  })
  newUser.value = { name: '', balance: 0 }
  await loadData()
}

async function updateBalance() {
  if (!balanceUpdate.value.userId) return
  await request(`/users/${balanceUpdate.value.userId}/balance?amount=${balanceUpdate.value.amount}`, {
    method: 'PUT',
  })
  balanceUpdate.value = { userId: '', amount: 0 }
  await loadData()
}

async function createApiKey() {
  if (!newKey.value.label.trim() || !newKey.value.key.trim()) return
  await request('/apikeys', {
    method: 'POST',
    body: JSON.stringify({
      label: newKey.value.label,
      key: newKey.value.key,
      owner_id: newKey.value.owner_id ? Number(newKey.value.owner_id) : null,
    }),
  })
  newKey.value = { label: '', key: '', owner_id: '' }
  await loadData()
}

async function deleteKey(id) {
  await request(`/apikeys/${id}`, { method: 'DELETE' })
  await loadData()
}

onMounted(loadData)
</script>

<template>
  <div class="container">
    <h1>余额 &amp; AI Key 管理</h1>
    <p class="helper">后端 FastAPI + 前端 Vue 3 / Vite</p>

    <div class="grid">
      <div class="card">
        <h2>概览</h2>
        <p>用户数：<strong>{{ summary.user_count }}</strong></p>
        <p>API Keys：<strong>{{ summary.api_key_count }}</strong></p>
        <p>余额合计：<strong>{{ summary.total_balance.toFixed(2) }}</strong></p>
        <p class="helper" v-if="loading">正在加载数据…</p>
      </div>

      <div class="card">
        <h2>新建用户</h2>
        <label>昵称</label>
        <input v-model="newUser.name" placeholder="如：运营账号" />
        <label>初始余额</label>
        <input type="number" v-model.number="newUser.balance" min="0" step="0.01" />
        <button :disabled="!newUser.name" @click="createUser">创建</button>
      </div>

      <div class="card">
        <h2>调整余额</h2>
        <label>用户 ID</label>
        <input v-model="balanceUpdate.userId" placeholder="输入用户 ID" />
        <label>调整金额（可正可负）</label>
        <input type="number" v-model.number="balanceUpdate.amount" step="0.01" />
        <button :disabled="!balanceUpdate.userId" @click="updateBalance">更新</button>
      </div>

      <div class="card">
        <h2>新建 API Key</h2>
        <label>Key 描述</label>
        <input v-model="newKey.label" placeholder="如：生产环境 Key" />
        <label>Key 值</label>
        <input v-model="newKey.key" placeholder="sk-xxxx" />
        <label>绑定用户 ID（可选）</label>
        <input v-model="newKey.owner_id" placeholder="用户 ID" />
        <button :disabled="!newKey.label || !newKey.key" @click="createApiKey">保存</button>
      </div>
    </div>

    <div class="card">
      <div class="actions">
        <h2>用户列表</h2>
        <button style="width:auto" @click="loadData">刷新</button>
      </div>
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
            <td colspan="3" class="helper">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card">
      <h2>API Keys</h2>
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
            <td><button @click="deleteKey(item.id)">删除</button></td>
          </tr>
          <tr v-if="!keys.length">
            <td colspan="5" class="helper">暂无数据</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
