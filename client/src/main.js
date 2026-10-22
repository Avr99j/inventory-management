import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

// Views are lazy-loaded so each page's code is fetched only when its route is first visited
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('./views/Dashboard.vue') },
    { path: '/inventory', component: () => import('./views/Inventory.vue') },
    { path: '/orders', component: () => import('./views/Orders.vue') },
    { path: '/demand', component: () => import('./views/Demand.vue') },
    { path: '/spending', component: () => import('./views/Spending.vue') },
    { path: '/reports', component: () => import('./views/Reports.vue') },
    { path: '/restocking', component: () => import('./views/Restocking.vue') }
  ]
})

const app = createApp(App)
app.use(router)
app.mount('#app')
