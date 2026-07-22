<script setup>
import { onMounted, ref } from 'vue'
import { api, eventDate } from '../lib'

const events = ref([])
const stripeStatus = ref(null)
const error = ref('')
const connecting = ref(false)
const cancellingId = ref(null)

async function load() {
  try {
    events.value = (await api('/events/mine/list')).events
    stripeStatus.value = await api('/payments/connect/status')
  } catch (err) {
    if (!err.message.includes('not configured')) error.value = err.message
  }
}

async function connectStripe() {
  connecting.value = true; error.value = ''
  try {
    const data = await api('/payments/connect/onboard', { method: 'POST' })
    window.location.href = data.url
  } catch (err) { error.value = err.message; connecting.value = false }
}

async function removeEvent(event) {
  if (!window.confirm(`Delete “${event.title}”? This cannot be undone.`)) return
  error.value = ''
  try { await api(`/events/${event.id}`, { method: 'DELETE' }); await load() }
  catch (err) { error.value = err.message }
}

async function cancelEvent(event) {
  const sold = event.ticketsSold
  const warning = sold
    ? `Cancel “${event.title}” and refund all ${sold} issued ticket${sold === 1 ? '' : 's'}? This removes the event from sale and cannot be undone.`
    : `Cancel “${event.title}”? It will immediately be removed from sale and cannot be republished.`
  if (!window.confirm(warning)) return
  cancellingId.value = event.id
  error.value = ''
  try {
    const result = await api(`/payments/events/${event.id}/cancel`, { method: 'POST', body: '{}' })
    window.alert(result.message)
    await load()
  } catch (err) {
    error.value = err.message
    await load()
  } finally {
    cancellingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <section class="page-hero shell"><p class="eyebrow">Organiser hub</p><h1>Your events</h1><p>Manage submissions, verification, ticket sales and payouts in one place.</p><RouterLink class="button" to="/organiser/events/new">Create event</RouterLink></section>
  <section class="shell">
    <div class="payout-banner" :class="{ complete: stripeStatus?.onboarded }">
      <div><p class="eyebrow">Payouts</p><h2>{{ stripeStatus?.onboarded ? 'Stripe is ready' : 'Connect your payout account' }}</h2><p>{{ stripeStatus?.onboarded ? 'Your verified events can accept ticket payments and transfer your share automatically.' : 'Stripe securely verifies your identity and bank details. EventSpace never stores them.' }}</p></div>
      <div><span class="fee-badge">You receive 96%*</span><button v-if="!stripeStatus?.onboarded" class="button" :disabled="connecting" @click="connectStripe">{{ connecting ? 'Opening Stripe…' : stripeStatus?.accountCreated ? 'Continue verification' : 'Connect with Stripe' }}</button><span v-else class="payout-ready">✓ Payments enabled</span><small>*Stripe processing fees are separate.</small></div>
    </div>
    <p v-if="error" class="state-message state-message--error">{{ error }}</p>
    <div v-if="events.length" class="dashboard-list"><article v-for="event in events" :key="event.id"><div><span :class="`status status--${event.expired ? 'expired' : event.status}`">{{ event.expired ? 'past event' : event.status }}</span><h2>{{ event.title }}</h2><p>{{ eventDate(event.startsAt) }} · {{ event.ticketsRemaining }} tickets remaining · {{ event.ticketsSold }} sold</p><small v-if="event.rejectionReason" class="rejection-text">Reviewer: {{ event.rejectionReason }}</small><small v-if="event.refundsOutstanding" class="rejection-text">{{ event.refundsOutstanding }} refund(s) still require attention</small></div><div class="dashboard-actions"><RouterLink v-if="event.status === 'approved' && !event.expired" :to="`/events/${event.slug}`">View live</RouterLink><RouterLink v-if="event.ticketsSold === 0 && event.status !== 'cancelled'" :to="`/organiser/events/${event.id}/edit`">{{ event.status === 'rejected' ? 'Revise' : 'Edit' }}</RouterLink><button v-if="event.ticketsSold === 0 && event.status !== 'approved' && event.status !== 'cancelled'" class="danger-link" type="button" @click="removeEvent(event)">Delete</button><button v-if="event.status === 'approved'" class="danger-link" type="button" :disabled="cancellingId === event.id" @click="cancelEvent(event)">{{ cancellingId === event.id ? 'Refunding…' : 'Cancel & refund' }}</button><button v-if="event.status === 'cancelled' && event.refundsOutstanding" class="danger-link" type="button" :disabled="cancellingId === event.id" @click="cancelEvent(event)">Retry outstanding refunds</button></div></article></div>
    <div v-else class="empty-state"><span>✦</span><h2>Your first event starts here</h2><p>Create a listing and submit it for verification.</p><RouterLink class="button" to="/organiser/events/new">Host an event</RouterLink></div>
  </section>
</template>
