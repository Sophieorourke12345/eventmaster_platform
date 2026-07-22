<script setup>
import { onMounted, ref } from 'vue'
import QRCode from 'qrcode'
import { api, eventDate } from '../lib'

const tickets = ref([])
const error = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await api('/payments/tickets')
    tickets.value = await Promise.all(data.tickets.map(async (ticket) => ({
      ...ticket,
      qrCode: ticket.orderStatus === 'paid' ? await QRCode.toDataURL(`eventspace://ticket/${ticket.verificationCode}`, {
        width: 280,
        margin: 2,
        color: { dark: '#151515', light: '#ffffff' },
        errorCorrectionLevel: 'H',
      }) : null,
    })))
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <section class="page-hero shell">
    <p class="eyebrow">Your plans</p>
    <h1>My tickets</h1>
    <p>Show the QR code at the door. Each code is unique and can only be checked in once.</p>
  </section>
  <section class="shell tickets-section">
    <p v-if="loading" class="state-message">Loading tickets…</p>
    <p v-else-if="error" class="state-message state-message--error">{{ error }}</p>
    <div v-else-if="tickets.length" class="ticket-list">
      <article v-for="ticket in tickets" :key="ticket.id">
        <div class="ticket-stub"><span>EventSpace</span><strong>{{ ticket.event.category }}</strong></div>
        <div class="ticket-main" :class="{ 'ticket-main--cancelled': ticket.orderStatus === 'refunded' }">
          <p class="eyebrow">Admit one</p>
          <h2>{{ ticket.event.title }}</h2>
          <p>{{ eventDate(ticket.event.startsAt) }}</p>
          <p>{{ ticket.event.venue }}, {{ ticket.event.county }}</p>
          <span v-if="ticket.orderStatus === 'refunded'" class="ticket-status cancelled">Cancelled · Refunded</span>
          <span v-else class="ticket-status" :class="{ used: ticket.checkedInAt }">{{ ticket.checkedInAt ? '✓ Checked in' : 'Ready for entry' }}</span>
        </div>
        <div v-if="ticket.qrCode" class="ticket-qr">
          <img :src="ticket.qrCode" :alt="`Entry QR code for ${ticket.event.title}`" />
          <small>Ticket #{{ ticket.id }} · Keep this code private</small>
        </div>
        <div v-else class="ticket-qr ticket-qr--cancelled"><strong>Ticket invalid</strong><small>Your refund was returned to the original payment method.</small></div>
      </article>
    </div>
    <div v-else class="empty-state"><span>✦</span><h2>No tickets yet</h2><p>Find something brilliant to look forward to.</p><RouterLink class="button" to="/events">Explore events</RouterLink></div>
  </section>
</template>
