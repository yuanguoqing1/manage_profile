import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { createVueErrorHandler, setupGlobalErrorHandlers } from './utils/errorHandler'

import './assets/styles/main.css'

const app = createApp(App)
const pinia = createPinia()

// 设置全局错误处理
app.config.errorHandler = createVueErrorHandler()
setupGlobalErrorHandlers()

app.use(pinia)
app.mount('#app')
