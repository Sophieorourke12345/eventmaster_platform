<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, euro, eventDate } from '../lib'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const event = ref(null)
const error = ref('')
const quantity = ref(1)
const checkoutBusy = ref(false)
onMounted(async () => {
  try { event.value = (await api(`/events/${route.params.slug}`)).event }
  catch (err) { error.value = err.message }
})

async function checkout() {
  if (!auth.isAuthenticated) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  checkoutBusy.value = true; error.value = ''
  try {
    const data = await api('/payments/checkout', { method: 'POST', body: JSON.stringify({ eventId: event.value.id, quantity: quantity.value }) })
    window.location.href = data.url
  } catch (err) { error.value = err.message; checkoutBusy.value = false }
}
</script>

<template>
  <p v-if="error" class="state-message state-message--error">{{ error }}</p>
  <section v-else-if="event" class="detail shell">
    <div class="detail__image"><img v-if="event.images?.[0]" :src="event.images[0].url" :alt="event.images[0].alt" /><span v-else>{{ event.category }}</span></div>
    <div class="detail__content"><p class="eyebrow">Verified event · {{ event.category }}</p><h1>{{ event.title }}</h1><dl><div><dt>When</dt><dd>{{ eventDate(event.startsAt) }}</dd></div><div><dt>Where</dt><dd>{{ event.venue }}, {{ event.county }}</dd></div><div><dt>Hosted by</dt><dd>{{ event.organiser.name }}</dd></div></dl><p class="detail__description">{{ event.description }}</p></div>
    <aside class="ticket-box"><p>Tickets from</p><strong>{{ euro(event.ticketPriceCents) }}</strong><span>{{ event.ticketsRemaining }} tickets remaining</span><label v-if="!event.soldOut">Quantity<select v-model.number="quantity"><option v-for="number in Math.min(event.ticketsRemaining, 10)" :key="number" :value="number">{{ number }}</option></select></label><p v-if="error" class="form-error">{{ error }}</p><button class="button" :disabled="event.soldOut || checkoutBusy" @click="checkout">{{ event.soldOut ? 'Sold out' : checkoutBusy ? 'Opening checkout…' : 'Get tickets' }}</button><small>Secure checkout powered by Stripe</small></aside>
  </section>
  <p v-else class="state-message">Loading event…</p>
</template>
