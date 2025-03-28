import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import IPSubnetView from '../views/IPSubnetView.vue'
import IPView from '../views/IPView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/ip/:eid',
      name: 'ip',
      component: IPView,
    },
    {
      path: '/ip_subnet/:ip/:prefix',
      name: 'ip_subnet',
      component: IPSubnetView,
    },
  ],
})

export default router
