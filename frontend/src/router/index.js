import { createRouter, createWebHistory } from 'vue-router'

import CreateEventView from '../views/CreateEventView.vue'
import CheckoutSuccessView from '../views/CheckoutSuccessView.vue'
import CheckInView from '../views/CheckInView.vue'
import AdminView from '../views/AdminView.vue'
import EditEventView from '../views/EditEventView.vue'
import EventDetailView from '../views/EventDetailView.vue'
import EventsView from '../views/EventsView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import OrganiserView from '../views/OrganiserView.vue'
import RegisterView from '../views/RegisterView.vue'
import TicketsView from '../views/TicketsView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', component: HomeView },
    { path: '/events', component: EventsView },
    { path: '/events/:slug', component: EventDetailView },
    { path: '/login', component: LoginView, meta: { guestOnly: true } },
    { path: '/register', component: RegisterView, meta: { guestOnly: true } },
    { path: '/organiser', component: OrganiserView, meta: { requiresAuth: true } },
    { path: '/organiser/events/new', component: CreateEventView, meta: { requiresAuth: true } },
    { path: '/organiser/events/:id/edit', component: EditEventView, meta: { requiresAuth: true } },
    { path: '/admin', component: AdminView, meta: { requiresAdmin: true } },
    { path: '/tickets', component: TicketsView, meta: { requiresAuth: true } },
    { path: '/checkout/success', component: CheckoutSuccessView, meta: { requiresAuth: true } },
    { path: '/organiser/check-in', component: CheckInView, meta: { requiresAuth: true } },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.ready) await auth.load().catch(() => { auth.ready = true })
  if ((to.meta.requiresAuth || to.meta.requiresAdmin) && !auth.isAuthenticated) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.meta.requiresAdmin && !auth.isAdmin) return { path: '/' }
  if (to.meta.guestOnly && auth.isAuthenticated) return { path: '/events' }
})

export default router
