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
const date = ref(route.query.date || '')
const county = ref(route.query.county || '')
const minPrice = ref(route.query.minPrice || '')
const maxPrice = ref(route.query.maxPrice || '')
const sort = ref(route.query.sort || 'date')
const showFilters = ref(false)
const dateOptions = [
  { value: '', label: 'Any date' },
  { value: 'today', label: 'Today' },
  { value: 'tomorrow', label: 'Tomorrow' },
  { value: 'this-weekend', label: 'This weekend' },
  { value: 'next-week', label: 'Next week' },
]

async function loadEvents() {
  loading.value = true
  error.value = ''
  const params = new URLSearchParams()
  if (query.value) params.set('q', query.value)
  if (category.value) params.set('category', category.value)
  if (date.value) params.set('date', date.value)
  if (county.value) params.set('county', county.value)
  if (minPrice.value) params.set('minPrice', minPrice.value)
  if (maxPrice.value) params.set('maxPrice', maxPrice.value)
  if (sort.value) params.set('sort', sort.value)
  try {
    const data = await api(`/events?${params}`)
    events.value = data.events
  } catch (err) { error.value = err.message }
  finally { loading.value = false }
}

function search() {
  router.replace({ query: { q: query.value || undefined, category: category.value || undefined, date: date.value || undefined, county: county.value || undefined, minPrice: minPrice.value || undefined, maxPrice: maxPrice.value || undefined, sort: sort.value !== 'date' ? sort.value : undefined } })
  loadEvents()
}

function chooseDate(value) { date.value = value; search() }
function clearFilters() { query.value = ''; category.value = ''; date.value = ''; county.value = ''; minPrice.value = ''; maxPrice.value = ''; sort.value = 'date'; search() }

watch(() => route.query.category, (value) => { category.value = value || ''; loadEvents() })
onMounted(loadEvents)
</script>

<template>
  <section class="page-hero shell"><p class="eyebrow">Go somewhere</p><h1>Explore events</h1><p>Hand-reviewed experiences from organisers across Ireland.</p></section>
  <section class="shell">
    <div class="date-pills" aria-label="Filter events by date"><button v-for="option in dateOptions" :key="option.value" :class="{ active: date === option.value }" @click="chooseDate(option.value)">{{ option.label }}</button></div>
    <form class="filter-bar" @submit.prevent="search">
      <label><span>Search</span><input v-model="query" placeholder="Artist, event or venue" /></label>
      <label><span>Category</span><select v-model="category"><option value="">All events</option><option>Music</option><option>Comedy</option><option>Sports</option><option>Festival</option><option>Food & Drink</option><option>Education</option></select></label>
      <button class="filter-toggle" type="button" :aria-expanded="showFilters" @click="showFilters = !showFilters">Filters <span>⌄</span></button>
      <button class="button" type="submit">Find events</button>
      <div v-if="showFilters" class="advanced-filters">
        <label><span>County</span><input v-model="county" placeholder="e.g. Cork" /></label>
        <label><span>Minimum price</span><input v-model="minPrice" type="number" min="0" placeholder="€0" /></label>
        <label><span>Maximum price</span><input v-model="maxPrice" type="number" min="0" placeholder="Any" /></label>
        <label><span>Sort by</span><select v-model="sort"><option value="date">Soonest</option><option value="price-low">Lowest price</option><option value="price-high">Highest price</option></select></label>
        <button class="text-button clear-filters" type="button" @click="clearFilters">Clear all filters</button>
      </div>
    </form>
    <p v-if="loading" class="state-message">Finding great events…</p>
    <p v-else-if="error" class="state-message state-message--error">{{ error }}</p>
    <div v-else-if="events.length" class="event-grid"><EventCard v-for="event in events" :key="event.id" :event="event" /></div>
    <div v-else class="empty-state"><span>✦</span><h2>No events found yet</h2><p>Try another search, or become the first organiser to list one.</p><RouterLink class="button" to="/organiser/events/new">Host an event</RouterLink></div>
  </section>
</template>
