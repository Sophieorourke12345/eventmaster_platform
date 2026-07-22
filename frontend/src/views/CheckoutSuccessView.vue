<template>
  <section class="success-page shell">
    <div class="success-mark">✓</div>
    <p class="eyebrow">Payment received</p>
    <h1>You’re going!</h1>
    <p>Stripe has confirmed your checkout. Your tickets will appear as soon as the secure payment webhook finishes processing.</p>
    <div class="button-row"><RouterLink class="button" to="/tickets">View my tickets</RouterLink><RouterLink class="button button--outline" to="/events">Find another event</RouterLink></div>
  </section>
</template>

