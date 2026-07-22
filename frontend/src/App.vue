<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SiteHeader from './components/SiteHeader.vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => auth.load().catch(() => { auth.ready = true }))

async function logout() {
  await auth.logout()
  router.push('/')
}
</script>

<template>
  <SiteHeader :user="auth.user" @logout="logout" />
  <main><RouterView /></main>
  <footer class="site-footer">
    <div><strong>EventSpace</strong><span>Verified events. Real experiences.</span></div>
    <p>Built with care in Ireland · © 2026</p>
  </footer>
</template>

