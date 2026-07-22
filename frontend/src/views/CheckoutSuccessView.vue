<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../lib'

const route = useRoute()
const confirming = ref(true)
const confirmed = ref(false)
const error = ref('')

async function confirmPayment() {
  confirming.value = true
  error.value = ''
  try {
    await api('/payments/checkout/confirm', {
      method: 'POST',
      body: JSON.stringify({ sessionId: route.query.session_id }),
    })
    confirmed.value = true
  } catch (err) {
    error.value = err.message
  } finally {
    confirming.value = false
  }
}

onMounted(confirmPayment)
</script>

<template>
  <section class="success-page shell">
    <div class="success-mark">{{ error ? '!' : '✓' }}</div>
    <p class="eyebrow">Payment received</p>
    <h1>{{ confirmed ? 'Your ticket is ready!' : 'Confirming your ticket…' }}</h1>
    <p v-if="confirming">We’re securely confirming your payment with Stripe and creating your unique entry code.</p>
    <p v-else-if="error" class="state-message state-message--error">{{ error }}</p>
    <p v-else>Your QR ticket has been issued. Keep it private and show it to the organiser at the door.</p>
    <div class="button-row">
      <RouterLink v-if="confirmed" class="button" to="/tickets">View my QR ticket</RouterLink>
      <button v-if="error" class="button" type="button" @click="confirmPayment">Try again</button>
      <RouterLink class="button button--outline" to="/events">Explore events</RouterLink>
    </div>
  </section>
</template>
