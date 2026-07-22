<script setup>
defineProps({ user: Object })
defineEmits(['logout'])
</script>

<template>
  <header class="site-header">
    <RouterLink class="brand" to="/">Event<span>Space</span></RouterLink>
    <nav aria-label="Main navigation">
      <RouterLink to="/events">Explore events</RouterLink>
      <RouterLink v-if="user" to="/organiser">Organiser hub</RouterLink>
      <RouterLink v-if="user" class="button button--small button--outline" to="/organiser/events/new">Host an event</RouterLink>
      <RouterLink v-if="!user" to="/login">Log in</RouterLink>
      <RouterLink v-if="!user" class="button button--small" to="/register">Join EventSpace</RouterLink>
      <button v-else class="text-button" type="button" @click="$emit('logout')">Log out</button>
    </nav>
  </header>
</template>

