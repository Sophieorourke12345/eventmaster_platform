<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const auth = useAuthStore(); const router = useRouter(); const error = ref(''); const form = reactive({ firstName: '', lastName: '', email: '', password: '' })
async function submit() { error.value = ''; try { await auth.register(form); router.push('/events') } catch (err) { error.value = err.message } }
</script>
<template><section class="auth-page"><form class="form-card" @submit.prevent="submit"><p class="eyebrow">Join the crowd</p><h1>Create an account</h1><p v-if="error" class="form-error">{{ error }}</p><div class="field-row"><label>First name<input v-model="form.firstName" required /></label><label>Last name<input v-model="form.lastName" required /></label></div><label>Email<input v-model="form.email" type="email" required /></label><label>Password<input v-model="form.password" type="password" minlength="10" required /><small>At least 10 characters, including a letter and number.</small></label><button class="button" type="submit">Create account</button><p>Already a member? <RouterLink to="/login">Log in</RouterLink></p></form></section></template>

