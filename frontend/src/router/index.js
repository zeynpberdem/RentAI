import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import VehicleSearchView from '../views/VehicleSearchView.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/register', name: 'register', component: RegisterView },
    // "/" artık araç arama ekranı — giriş yapmadan da erişilebilir,
    // tıpkı backend'deki /api/vehicles'ın herkese açık olması gibi.
    { path: '/', name: 'vehicle-search', component: VehicleSearchView },
  ],
})

// Giriş yapmamış biri korumalı (requiresAuth) bir sayfaya gitmeye
// çalışırsa, otomatik olarak giriş sayfasına yönlendirilir. Şu an
// hiçbir sayfa bunu kullanmıyor ama rezervasyon ekranı gibi ileride
// eklenecek korumalı sayfalar için altyapı hazır duruyor.
router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }
})

export default router