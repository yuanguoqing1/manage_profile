// 简易路由表（Hash 路由用于菜单定位）
export const routes = [
  { path: '/', name: 'home', menu: 'home' },
  { path: '/chat', name: 'chat', menu: 'chat', requiresAuth: true },
  { path: '/contacts', name: 'contacts', menu: 'contacts', requiresAuth: true },
  { path: '/models', name: 'models', menu: 'models', requiresAuth: true },
  { path: '/web', name: 'web', menu: 'web', requiresAuth: true },
  { path: '/users', name: 'users', menu: 'users', requiresAdmin: true },
  { path: '/logs', name: 'logs', menu: 'logs', requiresAdmin: true },
]
