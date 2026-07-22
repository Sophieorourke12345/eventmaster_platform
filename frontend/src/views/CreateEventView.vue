<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import EventForm from '../components/EventForm.vue'
import { api } from '../lib'
const router = useRouter(); const error = ref(''); const busy = ref(false)
async function submit(form) { error.value = ''; busy.value = true; try { const { images, ...details } = form; const created = await api('/events', { method: 'POST', body: JSON.stringify(details) }); if (images.length) { const body = new FormData(); images.forEach(image => body.append('images', image)); await api(`/events/${created.event.id}/images`, { method: 'POST', body }) } await api(`/events/${created.event.id}/submit`, { method: 'POST', body: JSON.stringify({}) }); router.push('/organiser') } catch (err) { error.value = err.message } finally { busy.value = false } }
</script>
<template><section class="form-page shell"><div class="form-intro"><p class="eyebrow">Bring people together</p><h1>Host an event</h1><p>Tell us the essentials. Your listing stays private until EventSpace reviews and verifies it.</p><div class="review-note"><strong>No upfront listing fee</strong><span>We take 4% only when a ticket sells.</span></div></div><EventForm :busy="busy" @submit="submit"><template #message><p v-if="error" class="form-error">{{ error }}</p></template></EventForm></section></template>
