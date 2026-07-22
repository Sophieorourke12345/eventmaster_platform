<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EventCard from '../components/EventCard.vue'
import { api } from '../lib'

const route = useRoute()
const router = useRouter()
const events = ref([])
const loading = ref(true)
const error = ref('')
const query = ref(route.query.q || '')
const category = ref(route.query.category || '')

async function loadEvents() {
  loading.value = true
  error.value = ''
  const params = new URLSearchParams()
  if (query.value) params.set('q', query.value)
  if (category.value) params.set('category', category.value)
  try {
    const data = await api(`/events?${params}`)
    events.value = data.events
  } catch (err) { error.value = err.message }
  finally { loading.value = false }
}

function search() {
  router.replace({ query: { q: query.value || undefined, category: category.value || undefined } })
  loadEvents()
}

watch(() => route.query.category, (value) => { category.value = value || ''; loadEvents() })
onMounted(loadEvents)
</script>

<template>
  <section class="page-hero shell"><p class="eyebrow">Go somewhere</p><h1>Explore events</h1><p>Hand-reviewed experiences from organisers across Ireland.</p></section>
  <section class="shell">
    <form class="filter-bar" @submit.prevent="search">
      <label><span>Search</span><input v-model="query" placeholder="Artist, event or venue" /></label>
      <label><span>Category</span><select v-model="category"><option value="">All events</option><option>Music</option><option>Comedy</option><option>Sports</option><option>Festival</option><option>Food & Drink</option><option>Education</option></select></label>
      <button class="button" type="submit">Find events</button>
    </form>
    <p v-if="loading" class="state-message">Finding great events…</p>
    <p v-else-if="error" class="state-message state-message--error">{{ error }}</p>
    <div v-else-if="events.length" class="event-grid"><EventCard v-for="event in events" :key="event.id" :event="event" /></div>
    <div v-else class="empty-state"><span>✦</span><h2>No events found yet</h2><p>Try another search, or become the first organiser to list one.</p><RouterLink class="button" to="/organiser/events/new">Host an event</RouterLink></div>
  </section>
</template>

