<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore(); const route = useRoute(); const router = useRouter(); const error = ref(''); const form = reactive({ email: '', password: '', remember: true })
async function submit() { error.value = ''; try { await auth.login(form); router.push(route.query.redirect || '/events') } catch (err) { error.value = err.message } }
</script>
<template><section class="auth-page"><form class="form-card" @submit.prevent="submit"><p class="eyebrow">Welcome back</p><h1>Log in</h1><p v-if="error" class="form-error">{{ error }}</p><label>Email<input v-model="form.email" type="email" autocomplete="email" required /></label><label>Password<input v-model="form.password" type="password" autocomplete="current-password" required /></label><label class="checkbox"><input v-model="form.remember" type="checkbox" /> Keep me logged in</label><button class="button" type="submit">Log in</button><p>New here? <RouterLink to="/register">Create an account</RouterLink></p></form></section></template>
