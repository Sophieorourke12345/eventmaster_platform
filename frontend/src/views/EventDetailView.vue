<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, euro, eventDate } from '../lib'

const route = useRoute()
const event = ref(null)
const error = ref('')
onMounted(async () => {
  try { event.value = (await api(`/events/${route.params.slug}`)).event }
  catch (err) { error.value = err.message }
})
</script>

<template>
  <p v-if="error" class="state-message state-message--error">{{ error }}</p>
  <section v-else-if="event" class="detail shell">
    <div class="detail__image"><img v-if="event.images?.[0]" :src="event.images[0].url" :alt="event.images[0].alt" /><span v-else>{{ event.category }}</span></div>
    <div class="detail__content"><p class="eyebrow">Verified event · {{ event.category }}</p><h1>{{ event.title }}</h1><dl><div><dt>When</dt><dd>{{ eventDate(event.startsAt) }}</dd></div><div><dt>Where</dt><dd>{{ event.venue }}, {{ event.county }}</dd></div><div><dt>Hosted by</dt><dd>{{ event.organiser.name }}</dd></div></dl><p class="detail__description">{{ event.description }}</p></div>
    <aside class="ticket-box"><p>Tickets from</p><strong>{{ euro(event.ticketPriceCents) }}</strong><span>{{ event.ticketsRemaining }} tickets remaining</span><button class="button" :disabled="event.soldOut">{{ event.soldOut ? 'Sold out' : 'Get tickets' }}</button><small>Secure checkout powered by Stripe</small></aside>
  </section>
  <p v-else class="state-message">Loading event…</p>
</template>

