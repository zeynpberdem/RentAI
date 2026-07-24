import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../modules/auth/pages/LoginView.vue'
import RegisterView from '../modules/auth/pages/RegisterView.vue'
import { useAuthStore } from '../modules/auth/store'
import MyReservationsView from '../modules/reservations/pages/MyReservationsView.vue'
import VehicleSearchView from '../modules/vehicles/pages/VehicleSearchView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/register', name: 'register', component: RegisterView },
    // "/" artık araç arama ekranı — giriş yapmadan da erişilebilir,
    // tıpkı backend'deki /api/vehicles'ın herkese açık olması gibi.
    { path: '/', name: 'vehicle-search', component: VehicleSearchView },
    {
      path: '/rezervasyonlarim',
      name: 'my-reservations',
      component: MyReservationsView,
      meta: { requiresAuth: true },
    },
  ],
})

// Giriş yapmamış biri korumalı (requiresAuth) bir sayfaya gitmeye
// çalışırsa, otomatik olarak giriş sayfasına yönlendirilir.
router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }
})

export default router