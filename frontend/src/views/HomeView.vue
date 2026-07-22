<script setup>
const categories = ['Live music', 'Comedy', 'Food & drink', 'Sport', 'Workshops', 'Festivals']
</script>

<template>
  <section class="hero shell">
    <div class="hero__content">
      <p class="eyebrow">Verified events across Ireland</p>
      <h1>Find something worth <em>showing up for.</em></h1>
      <p class="hero__copy">From intimate workshops to unforgettable nights out—discover trusted events or bring your own idea to life.</p>
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
      <RouterLink v-for="(category, index) in categories" :key="category" :to="`/events?category=${encodeURIComponent(category)}`" :class="`category category--${index + 1}`">
        <span>0{{ index + 1 }}</span><strong>{{ category }}</strong><i>↗</i>
      </RouterLink>
    </div>
  </section>

  <section class="host-banner shell">
    <div><p class="eyebrow">For organisers</p><h2>Your event.<br />Your audience.</h2></div>
    <div><p>Create your listing, pass our quick verification, and sell securely. EventSpace takes 4% only when you make a sale.</p><RouterLink class="button button--light" to="/organiser/events/new">Start hosting</RouterLink></div>
  </section>
</template>

