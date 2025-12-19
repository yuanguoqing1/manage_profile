// 简单状态容器，可替换为 Pinia/Vuex

export const store = {
  state: {
    user: null,
    token: '',
  },
  setUser(user) {
    this.state.user = user
  },
  setToken(token) {
    this.state.token = token
  },
}
