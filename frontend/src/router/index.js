import { createRouter, createWebHistory } from 'vue-router'

import CreateEventView from '../views/CreateEventView.vue'
import EventDetailView from '../views/EventDetailView.vue'
import EventsView from '../views/EventsView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import OrganiserView from '../views/OrganiserView.vue'
import RegisterView from '../views/RegisterView.vue'

export default createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', component: HomeView },
    { path: '/events', component: EventsView },
    { path: '/events/:slug', component: EventDetailView },
    { path: '/login', component: LoginView },
    { path: '/register', component: RegisterView },
    { path: '/organiser', component: OrganiserView },
    { path: '/organiser/events/new', component: CreateEventView },
  ],
})

