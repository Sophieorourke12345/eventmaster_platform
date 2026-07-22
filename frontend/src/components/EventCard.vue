<script setup>
import { eventDate, euro } from '../lib'
defineProps({ event: { type: Object, required: true } })
</script>

<template>
  <RouterLink class="event-card" :to="`/events/${event.slug}`">
    <div class="event-card__image">
      <img v-if="event.images?.[0]" :src="event.images[0].url" :alt="event.images[0].alt" />
      <div v-else class="event-card__placeholder">{{ event.category }}</div>
      <span class="event-card__tag">Verified</span>
    </div>
    <div class="event-card__body">
      <p class="eyebrow">{{ event.category }} · {{ event.county }}</p>
      <h3>{{ event.title }}</h3>
      <p>{{ eventDate(event.startsAt) }}</p>
      <div class="event-card__footer">
        <strong>{{ euro(event.ticketPriceCents) }}</strong>
        <span>{{ event.soldOut ? 'Sold out' : `${event.ticketsRemaining} left` }}</span>
      </div>
    </div>
  </RouterLink>
</template>

