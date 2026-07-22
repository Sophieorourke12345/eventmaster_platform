<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import QrScanner from 'qr-scanner'
import { api, eventDate } from '../lib'

const video = ref(null)
const scanner = ref(null)
const events = ref([])
const selectedEvent = ref('')
const manualCode = ref('')
const guestSearch = ref('')
const guestList = ref([])
const cameraActive = ref(false)
const busy = ref(false)
const result = ref(null)
const error = ref('')

const selected = computed(() => events.value.find((event) => String(event.id) === String(selectedEvent.value)))
const visibleGuests = computed(() => {
  const query = guestSearch.value.toLowerCase().trim()
  return guestList.value.filter((ticket) => !query || `${ticket.attendee} ${ticket.email} ${ticket.id}`.toLowerCase().includes(query))
})

async function loadEvents() {
  events.value = (await api('/payments/check-in/events')).events
  if (!selectedEvent.value && events.value.length) selectedEvent.value = String(events.value[0].id)
}

async function loadGuests() {
  if (!selectedEvent.value) { guestList.value = []; return }
  guestList.value = (await api(`/payments/check-in/events/${selectedEvent.value}/tickets`)).tickets
}

async function checkCode(code) {
  if (busy.value || !code) return
  busy.value = true
  error.value = ''
  try {
    const response = await api('/payments/check-in', {
      method: 'POST',
      body: JSON.stringify({ verificationCode: code, eventId: selectedEvent.value }),
    })
    result.value = response
    manualCode.value = ''
    await loadEvents()
    await loadGuests()
  } catch (err) {
    result.value = null
    error.value = err.message
  } finally {
    busy.value = false
  }
}

async function startCamera() {
  error.value = ''
  await nextTick()
  try {
    scanner.value = new QrScanner(video.value, ({ data }) => checkCode(data), {
      returnDetailedScanResult: true,
      highlightScanRegion: true,
      highlightCodeOutline: true,
      maxScansPerSecond: 4,
    })
    await scanner.value.start()
    cameraActive.value = true
  } catch {
    error.value = 'Camera access was unavailable. Allow camera permission or enter the ticket code manually.'
  }
}

function stopCamera() {
  scanner.value?.stop()
  scanner.value?.destroy()
  scanner.value = null
  cameraActive.value = false
}

onMounted(async () => { await loadEvents(); await loadGuests() })
watch(selectedEvent, loadGuests)
onBeforeUnmount(stopCamera)
</script>

<template>
  <section class="page-hero shell checkin-hero">
    <p class="eyebrow">Event-day tools</p>
    <h1>Ticket check-in</h1>
    <p>Scan each guest’s QR code. EventSpace validates it instantly and blocks duplicate entry.</p>
  </section>
  <section class="shell checkin-layout">
    <aside class="checkin-panel">
      <label>Checking in for
        <select v-model="selectedEvent">
          <option v-for="event in events" :key="event.id" :value="String(event.id)">{{ event.title }}</option>
        </select>
      </label>
      <div v-if="selected" class="checkin-stats">
        <strong>{{ selected.checkedIn }} / {{ selected.ticketsIssued }}</strong>
        <span>guests checked in</span>
        <small>{{ eventDate(selected.startsAt) }}</small>
      </div>
      <p v-else>No events with issued tickets yet.</p>
    </aside>

    <div class="scanner-card">
      <div class="scanner-frame" :class="{ active: cameraActive }">
        <video ref="video" muted playsinline></video>
        <div v-if="!cameraActive" class="camera-placeholder"><span>⌗</span><p>Use your phone or laptop camera to scan a guest’s ticket.</p></div>
      </div>
      <div class="scanner-actions">
        <button v-if="!cameraActive" class="button" type="button" @click="startCamera">Start camera</button>
        <button v-else class="button button--outline" type="button" @click="stopCamera">Stop camera</button>
      </div>
      <form class="manual-checkin" @submit.prevent="checkCode(manualCode)">
        <label>Or enter the ticket code manually
          <input v-model.trim="manualCode" placeholder="Paste entry code" autocomplete="off" />
        </label>
        <button class="button button--outline" :disabled="busy || !manualCode" type="submit">Check ticket</button>
      </form>
      <div v-if="result" class="scan-result" :class="`scan-result--${result.status}`">
        <strong>{{ result.status === 'checked_in' ? '✓' : '!' }} {{ result.message }}</strong>
        <span>{{ result.ticket.attendee }} · {{ result.ticket.eventTitle }}</span>
      </div>
      <p v-if="error" class="state-message state-message--error">{{ error }}</p>
    </div>
    <div class="guest-list-card">
      <div class="guest-list-head"><div><p class="eyebrow">Door list</p><h2>Guest names</h2></div><input v-model="guestSearch" aria-label="Search guests" placeholder="Search name or email" /></div>
      <div v-if="visibleGuests.length" class="guest-list">
        <article v-for="ticket in visibleGuests" :key="ticket.id" :class="{ checked: ticket.checkedInAt }">
          <span class="guest-tick">{{ ticket.checkedInAt ? '✓' : '' }}</span>
          <div><strong>{{ ticket.attendee }}</strong><small>{{ ticket.email }} · Ticket #{{ ticket.id }}</small></div>
          <button v-if="!ticket.checkedInAt" class="manual-tick" type="button" :disabled="busy" @click="checkCode(ticket.verificationCode)">Check in</button>
          <span v-else class="checked-label">Checked in</span>
        </article>
      </div>
      <p v-else class="state-message">{{ guestSearch ? 'No guests match that search.' : 'No paid ticket holders yet.' }}</p>
    </div>
  </section>
</template>
