<script setup>
import { ref } from 'vue'
defineProps({ user: Object })
defineEmits(['logout'])
const open = ref(false)
</script>

<template>
  <header class="site-header">
    <RouterLink class="brand" to="/">Event<span>Space</span></RouterLink>
    <button class="menu-button" type="button" :aria-expanded="open" aria-label="Open navigation" @click="open = !open"><span></span><span></span></button>
    <nav :class="{ open }" aria-label="Main navigation" @click="open = false">
      <RouterLink to="/events">Explore events</RouterLink>
      <RouterLink v-if="user" to="/tickets">My tickets</RouterLink>
      <RouterLink v-if="user" to="/organiser">Organiser hub</RouterLink>
      <RouterLink v-if="user?.role === 'admin'" to="/admin">Admin review</RouterLink>
      <RouterLink v-if="user" class="button button--small button--outline" to="/organiser/events/new">Host an event</RouterLink>
      <RouterLink v-if="!user" to="/login">Log in</RouterLink>
      <RouterLink v-if="!user" class="button button--small" to="/register">Join EventSpace</RouterLink>
      <button v-else class="text-button" type="button" @click="$emit('logout')">Log out</button>
    </nav>
  </header>
</template>
