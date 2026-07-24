import { createRouter, createWebHistory } from 'vue-router'
import { backendOrigin } from '../api/client'
import LoginView from '../modules/auth/pages/LoginView.vue'
import RegisterView from '../modules/auth/pages/RegisterView.vue'
import { useAuthStore } from '../modules/auth/store'
import OperatorPanelView from '../modules/operator/pages/OperatorPanelView.vue'
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
    {
      path: '/operator',
      name: 'operator-panel',
      component: OperatorPanelView,
      meta: { requiresAuth: true, requiresOperator: true },
    },
  ],
})

// Giriş yapmamış biri korumalı (requiresAuth) bir sayfaya gitmeye
// çalışırsa, otomatik olarak giriş sayfasına yönlendirilir. requiresOperator
// ise operatör rolünde olmayanları araç arama sayfasına geri yollar
// (backend zaten IsOperator ile korunuyor, bu sadece arayüz tarafında
// erişilemeyecek bir sayfaya gidilmesini önlüyor).
router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }
  if (to.meta.requiresOperator && !authStore.isOperator) {
    return { name: 'vehicle-search' }
  }

  // Araç arama ekranı müşteri storefront'u — operatör/admin buraya
  // (ör. "RentAI" logosuna basarak) gelirse kendi ekranına geri yönlendirilir.
  if (to.name === 'vehicle-search') {
    if (authStore.role === 'operator') {
      return { name: 'operator-panel' }
    }
    if (authStore.role === 'admin') {
      window.location.href = `${backendOrigin}/admin/`
      return false
    }
  }
})

export default router