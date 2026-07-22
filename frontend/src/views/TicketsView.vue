<script setup>
import { onMounted, ref } from 'vue'
import { api, eventDate } from '../lib'
const tickets = ref([]); const error = ref(''); const loading = ref(true)
onMounted(async () => { try { tickets.value = (await api('/payments/tickets')).tickets } catch (err) { error.value = err.message } finally { loading.value = false } })
</script>
<template>
  <section class="page-hero shell"><p class="eyebrow">Your plans</p><h1>My tickets</h1><p>Everything you need for event day, in one place.</p></section>
  <section class="shell tickets-section"><p v-if="loading" class="state-message">Loading tickets…</p><p v-else-if="error" class="state-message state-message--error">{{ error }}</p><div v-else-if="tickets.length" class="ticket-list"><article v-for="ticket in tickets" :key="ticket.id"><div class="ticket-stub"><span>EventSpace</span><strong>{{ ticket.event.category }}</strong></div><div class="ticket-main"><p class="eyebrow">Admit one</p><h2>{{ ticket.event.title }}</h2><p>{{ eventDate(ticket.event.startsAt) }}</p><p>{{ ticket.event.venue }}, {{ ticket.event.county }}</p></div><div class="ticket-code"><small>Entry code</small><strong>{{ ticket.verificationCode }}</strong><span>{{ ticket.checkedInAt ? 'Checked in' : 'Ready to scan' }}</span></div></article></div><div v-else class="empty-state"><span>✦</span><h2>No tickets yet</h2><p>Find something brilliant to look forward to.</p><RouterLink class="button" to="/events">Explore events</RouterLink></div></section>
</template>

