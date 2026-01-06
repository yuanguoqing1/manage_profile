<template>
  <section class="view github-trending">
    <div class="header">
      <h2>GitHub 热点 Python 项目</h2>
      <button 
        class="refresh-btn" 
        :disabled="loading" 
        @click="fetchProjects"
      >
        <span v-if="loading" class="refresh-icon spinning">⟳</span>
        <span v-else class="refresh-icon">⟳</span>
        刷新
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && !projects.length" class="loading-container">
      <LoadingSpinner :show="true" size="large" text="正在加载热门项目..." />
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <p class="error-message">{{ error }}</p>
      <button class="retry-btn" @click="fetchProjects">重试</button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!projects.length" class="empty-container">
      <p>暂无热门项目</p>
    </div>

    <!-- 项目列表 -->
    <div v-else class="projects-grid">
      <a
        v-for="project in projects"
        :key="project.full_name"
        :href="project.url"
        target="_blank"
        rel="noopener noreferrer"
        class="project-card"
      >
        <div class="project-header">
          <h3 class="project-name">{{ project.name }}</h3>
          <span class="project-author">{{ project.author }}</span>
        </div>
        <p class="project-description">{{ project.description_cn || project.description || '暂无描述' }}</p>
        <div class="project-stats">
          <span class="stat">
            <span class="stat-icon">⭐</span>
            {{ formatNumber(project.stars) }}
          </span>
          <span class="stat">
            <span class="stat-icon">🍴</span>
            {{ formatNumber(project.forks) }}
          </span>
          <span class="stat language">
            {{ project.language }}
          </span>
        </div>
      </a>
    </div>


    <!-- 缓存信息 -->
    <div v-if="updatedAt" class="cache-info">
      <span v-if="cached">数据来自缓存</span>
      <span>更新时间: {{ formatDate(updatedAt) }}</span>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useApi } from '../composables/useApi'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'

const { request } = useApi()

// 数据状态
const projects = ref([])
const loading = ref(false)
const error = ref(null)
const cached = ref(false)
const updatedAt = ref(null)

// 获取热门项目
async function fetchProjects() {
  loading.value = true
  error.value = null
  
  try {
    const data = await request('/api/github/trending')
    projects.value = data.projects || []
    cached.value = data.cached || false
    updatedAt.value = data.updated_at || null
  } catch (err) {
    error.value = err.message || '获取数据失败，请点击重试'
  } finally {
    loading.value = false
  }
}

// 格式化数字
function formatNumber(num) {
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'k'
  }
  return num.toString()
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 页面加载时自动获取数据
onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.github-trending {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #ccc;
}

.refresh-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.refresh-icon {
  font-size: 16px;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-container,
.error-container,
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: #666;
}

.error-message {
  color: #e74c3c;
  margin-bottom: 16px;
}

.retry-btn {
  padding: 8px 24px;
  border: none;
  border-radius: 8px;
  background: #3498db;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #2980b9;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.project-card {
  display: block;
  padding: 20px;
  border: 1px solid #e1e4e8;
  border-radius: 12px;
  background: #fff;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
}

.project-card:hover {
  border-color: #3498db;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.project-name {
  margin: 0;
  font-size: 18px;
  color: #0366d6;
  word-break: break-word;
}

.project-author {
  font-size: 12px;
  color: #666;
  flex-shrink: 0;
  margin-left: 8px;
}

.project-description {
  margin: 0 0 16px;
  font-size: 14px;
  color: #586069;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.project-stats {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #666;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-icon {
  font-size: 14px;
}

.language {
  background: #f1f8ff;
  padding: 2px 8px;
  border-radius: 4px;
  color: #0366d6;
}

.cache-info {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
  font-size: 12px;
  color: #999;
  display: flex;
  gap: 16px;
}
</style>
