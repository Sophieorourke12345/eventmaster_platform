<script setup>
const categories = [
  { label: 'Live music', value: 'Music' },
  { label: 'Comedy', value: 'Comedy' },
  { label: 'Food & drink', value: 'Food & Drink' },
  { label: 'Sport', value: 'Sports' },
  { label: 'Workshops', value: 'Education' },
  { label: 'Festivals', value: 'Festival' },
]
</script>

<template>
  <section class="hero shell">
    <div class="hero__content">
      <p class="eyebrow">Same events. Better value.</p>
      <h1>Find something worth <em>showing up for.</em></h1>
      <p class="hero__copy">Verified events across Ireland, fairer fees for organisers, and memorable experiences for everyone. Discover your next plan or bring your own idea to life.</p>
      <div class="button-row">
        <RouterLink class="button" to="/events">Explore events</RouterLink>
        <RouterLink class="button button--outline" to="/organiser/events/new">Host an event</RouterLink>
      </div>
      <p class="trust-note"><span>✓</span> Every event reviewed before it goes live</p>
    </div>
    <div class="hero__visual" aria-hidden="true">
      <div class="poster poster--back"><small>THIS WEEKEND</small><strong>GOOD<br />TIMES</strong></div>
      <div class="poster poster--front"><span>LIVE</span><strong>CORK<br />NIGHTS</strong><small>Music · Food · People</small></div>
      <div class="spark spark--one">✦</div><div class="spark spark--two">✦</div>
    </div>
  </section>

  <section class="category-section shell">
    <div class="section-heading"><div><p class="eyebrow">Pick your mood</p><h2>What are you into?</h2></div><RouterLink to="/events">View everything →</RouterLink></div>
    <div class="category-grid">
      <RouterLink v-for="(category, index) in categories" :key="category.value" :to="`/events?category=${encodeURIComponent(category.value)}`" :class="`category category--${index + 1}`">
        <span>0{{ index + 1 }}</span><strong>{{ category.label }}</strong><i>↗</i>
      </RouterLink>
    </div>
  </section>

  <section class="host-banner shell">
    <div><p class="eyebrow">For organisers</p><h2>Your event.<br />Your audience.</h2></div>
    <div><p>Create your listing, pass our quick verification, and sell securely. EventSpace takes 4% only when you make a sale.</p><RouterLink class="button button--light" to="/organiser/events/new">Start hosting</RouterLink></div>
  </section>
</template>
