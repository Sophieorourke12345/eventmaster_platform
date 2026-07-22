<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import EventForm from '../components/EventForm.vue'
import { api } from '../lib'

const route = useRoute(); const router = useRouter(); const event = ref(null); const error = ref(''); const busy = ref(false)
onMounted(async () => { try { const events = (await api('/events/mine/list')).events; event.value = events.find(item => item.id === Number(route.params.id)); if (!event.value) error.value = 'Event not found.' } catch (err) { error.value = err.message } })
async function submit(form) { busy.value = true; error.value = ''; try { await api(`/events/${route.params.id}`, { method: 'PUT', body: JSON.stringify(form) }); router.push('/organiser') } catch (err) { error.value = err.message } finally { busy.value = false } }
</script>
<template><section class="form-page shell"><div class="form-intro"><p class="eyebrow">Revise and resubmit</p><h1>Edit event</h1><p>Your changes will return the event to the verification queue.</p><div v-if="event?.rejectionReason" class="rejection-note"><strong>Reviewer feedback</strong><span>{{ event.rejectionReason }}</span></div></div><EventForm v-if="event" :initial-event="event" :busy="busy" submit-label="Save and resubmit" @submit="submit"><template #message><p v-if="error" class="form-error">{{ error }}</p></template></EventForm><p v-else class="state-message">{{ error || 'Loading event…' }}</p></section></template>

