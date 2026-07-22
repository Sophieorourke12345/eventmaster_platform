import { defineStore } from 'pinia'
import { api } from '../lib'

export const useAuthStore = defineStore('auth', {
  state: () => ({ user: null, ready: false }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
    isAdmin: (state) => state.user?.role === 'admin',
    isOrganiser: (state) => ['organiser', 'admin'].includes(state.user?.role),
  },
  actions: {
    async load() {
      const data = await api('/auth/me')
      this.user = data.user
      this.ready = true
    },
    async login(credentials) {
      const data = await api('/auth/login', { method: 'POST', body: JSON.stringify(credentials) })
      this.user = data.user
    },
    async register(details) {
      const data = await api('/auth/register', { method: 'POST', body: JSON.stringify(details) })
      this.user = data.user
    },
    async logout() {
      await api('/auth/logout', { method: 'POST' })
      this.user = null
    },
  },
})

