<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  initialEvent: { type: Object, default: null },
  submitLabel: { type: String, default: 'Submit for verification' },
  busy: Boolean,
})
const emit = defineEmits(['submit'])

const form = reactive({
  title: '', description: '', venue: '', county: '', startsAt: '',
  category: 'Music', ticketPrice: '', ticketCapacity: '',
})
const images = ref([])
const previews = ref([])

watch(() => props.initialEvent, (event) => {
  if (!event) return
  Object.assign(form, {
    title: event.title,
    description: event.description,
    venue: event.venue,
    county: event.county,
    startsAt: event.startsAt?.slice(0, 16),
    category: event.category,
    ticketPrice: event.ticketPriceCents / 100,
    ticketCapacity: event.ticketCapacity,
  })
}, { immediate: true })

function submit() {
  emit('submit', {
    ...form,
    ticketPriceCents: Math.round(Number(form.ticketPrice) * 100),
    ticketCapacity: Number(form.ticketCapacity),
    images: images.value,
  })
}

function chooseImages(event) {
  images.value = Array.from(event.target.files).slice(0, 6)
  previews.value.forEach(item => URL.revokeObjectURL(item.url))
  previews.value = images.value.map(file => ({ name: file.name, url: URL.createObjectURL(file) }))
}
</script>

<template>
  <form class="form-card form-card--wide" @submit.prevent="submit">
    <slot name="message" />
    <label>Event title<input v-model="form.title" maxlength="200" required /></label>
    <label>Description<textarea v-model="form.description" rows="6" required></textarea></label>
    <div class="field-row"><label>Venue<input v-model="form.venue" required /></label><label>County<input v-model="form.county" required /></label></div>
    <div class="field-row"><label>Date and time<input v-model="form.startsAt" type="datetime-local" required /></label><label>Category<select v-model="form.category"><option>Music</option><option>Comedy</option><option>Sports</option><option>Festival</option><option>Food & Drink</option><option>Education</option><option>Family</option><option>Nightlife</option><option>Business</option><option>Community</option></select></label></div>
    <div class="field-row"><label>Ticket price (€)<input v-model="form.ticketPrice" type="number" min="0" step="0.01" required /></label><label>Number of tickets<input v-model="form.ticketCapacity" type="number" min="1" required /></label></div>
    <label class="image-upload">Event images <span>Choose up to six clear images. The first becomes the event cover.</span><input type="file" accept="image/jpeg,image/png,image/webp" multiple @change="chooseImages" /></label>
    <div v-if="initialEvent?.images?.length || previews.length" class="image-preview-grid">
      <figure v-for="image in initialEvent?.images || []" :key="image.id"><img :src="image.url" :alt="image.alt" /><figcaption>Existing image</figcaption></figure>
      <figure v-for="image in previews" :key="image.url"><img :src="image.url" :alt="image.name" /><figcaption>{{ image.name }}</figcaption></figure>
    </div>
    <button class="button" type="submit" :disabled="busy">{{ busy ? 'Saving…' : submitLabel }}</button>
  </form>
</template>
