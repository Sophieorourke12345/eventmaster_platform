<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, euro, eventDate } from '../lib'

const events = ref([])
const counts = ref({})
const error = ref('')
const selected = ref(null)
const reason = ref('')
const busy = ref(false)
const statusFilter = ref('pending')

const visibleEvents = computed(() => statusFilter.value === 'all' ? events.value : events.value.filter(event => event.status === statusFilter.value))

async function load() {
  try {
    const data = await api('/events/admin/overview')
    events.value = data.events
    counts.value = data.counts
  } catch (err) { error.value = err.message }
}

async function decide(decision) {
  if (decision === 'rejected' && !reason.value.trim()) {
    error.value = 'Add a reason so the organiser knows what to change.'
    return
  }
  busy.value = true; error.value = ''
  try {
    await api(`/events/${selected.value.id}/decision`, { method: 'POST', body: JSON.stringify({ decision, reason: reason.value }) })
    selected.value = null; reason.value = ''; await load()
  } catch (err) { error.value = err.message }
  finally { busy.value = false }
}

async function removeSelected() {
  if (!window.confirm(`Permanently delete “${selected.value.title}”?`)) return
  busy.value = true; error.value = ''
  try { await api(`/events/${selected.value.id}`, { method: 'DELETE' }); selected.value = null; await load() }
  catch (err) { error.value = err.message }
  finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <section class="page-hero shell"><p class="eyebrow">EventSpace control room</p><h1>Verification</h1><p>Review organisers and event details before anything becomes public.</p></section>
  <section class="admin-layout shell">
    <div class="stat-grid">
      <button v-for="status in ['pending','approved','rejected','all']" :key="status" :class="{ active: statusFilter === status }" @click="statusFilter = status"><strong>{{ status === 'all' ? events.length : (counts[status] || 0) }}</strong><span>{{ status }}</span></button>
    </div>
    <p v-if="error" class="form-error">{{ error }}</p>
    <div class="admin-list">
      <article v-for="event in visibleEvents" :key="event.id">
        <div><span :class="`status status--${event.status}`">{{ event.status }}</span><h2>{{ event.title }}</h2><p>{{ eventDate(event.startsAt) }} · {{ event.venue }}, {{ event.county }}</p><small>{{ event.organiser.name }} · {{ euro(event.ticketPriceCents) }} · {{ event.ticketCapacity }} tickets</small></div>
        <button class="button button--small" @click="selected = event; reason = event.rejectionReason || ''">Review</button>
      </article>
      <div v-if="!visibleEvents.length" class="empty-state"><span>✓</span><h2>Nothing waiting here</h2><p>The {{ statusFilter }} queue is clear.</p></div>
    </div>
  </section>

  <div v-if="selected" class="modal-backdrop" @click.self="selected = null">
    <section class="review-modal" role="dialog" aria-modal="true" aria-labelledby="review-title">
      <button class="modal-close" aria-label="Close" @click="selected = null">×</button>
      <p class="eyebrow">Complete event review</p><h2 id="review-title">{{ selected.title }}</h2>
      <div class="review-facts"><p><strong>Organiser</strong>{{ selected.organiser.name }}</p><p><strong>Date</strong>{{ eventDate(selected.startsAt) }}</p><p><strong>Venue</strong>{{ selected.venue }}, {{ selected.county }}</p><p><strong>Tickets</strong>{{ selected.ticketCapacity }} × {{ euro(selected.ticketPriceCents) }}</p></div>
      <div v-if="selected.images.length" class="review-gallery"><img v-for="image in selected.images" :key="image.id" :src="image.url" :alt="image.alt" /></div><p v-else class="no-images">No event images were submitted.</p>
      <div class="review-description"><strong>Description</strong><p>{{ selected.description }}</p></div>
      <label>Feedback for organiser<textarea v-model="reason" rows="4" placeholder="Required when rejecting an event"></textarea></label>
      <div v-if="selected.status === 'pending'" class="button-row"><button class="button approve-button" :disabled="busy" @click="decide('approved')">Approve and publish</button><button class="button reject-button" :disabled="busy" @click="decide('rejected')">Reject with reason</button></div><button v-if="selected.ticketsSold === 0" class="danger-link modal-delete" type="button" :disabled="busy" @click="removeSelected">Delete event permanently</button>
    </section>
  </div>
</template>
