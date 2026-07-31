import { createRouter, createWebHistory } from 'vue-router'
import { backendOrigin } from '../api/client'
import FleetLayout from '../layouts/FleetLayout.vue'
import LoginView from '../modules/auth/pages/LoginView.vue'
import { useAuthStore } from '../modules/auth/store'
import FleetAnalyticsView from '../modules/operator/pages/FleetAnalyticsView.vue'
import FleetCalendarView from '../modules/operator/pages/FleetCalendarView.vue'
import FleetDriversView from '../modules/operator/pages/FleetDriversView.vue'
import FleetHandoversView from '../modules/operator/pages/FleetHandoversView.vue'
import FleetLiveMapView from '../modules/operator/pages/FleetLiveMapView.vue'
import FleetMaintenanceView from '../modules/operator/pages/FleetMaintenanceView.vue'
import FleetReservationsView from '../modules/operator/pages/FleetReservationsView.vue'
import FleetSettingsView from '../modules/operator/pages/FleetSettingsView.vue'
import FleetVehiclesView from '../modules/operator/pages/FleetVehiclesView.vue'

// Site artık tamamen filo yönetimi aracı — müşteri kendi kendine giriş
// yapıp araç aramıyor/kiralamıyor, her şey operatör panelinden yönetiliyor.
// Bu yüzden sadece iki gerçek hedef var: giriş ekranı ve operatör paneli.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    {
      path: '/operator',
      component: FleetLayout,
      meta: { requiresAuth: true, requiresOperator: true },
      children: [
        { path: '', redirect: { name: 'fleet-analytics' } },
        { path: 'analytics', name: 'fleet-analytics', component: FleetAnalyticsView },
        { path: 'vehicles', name: 'fleet-vehicles', component: FleetVehiclesView },
        { path: 'drivers', name: 'fleet-drivers', component: FleetDriversView },
        { path: 'maintenance', name: 'fleet-maintenance', component: FleetMaintenanceView },
        { path: 'reservations', name: 'fleet-reservations', component: FleetReservationsView },
        { path: 'reservation-calendar', name: 'fleet-calendar', component: FleetCalendarView },
        { path: 'handovers', name: 'fleet-handovers', component: FleetHandoversView },
        { path: 'live-tracking', name: 'fleet-live', component: FleetLiveMapView },
        { path: 'settings', name: 'fleet-settings', component: FleetSettingsView },
      ],
    },
    { path: '/', redirect: '/login' },
    { path: '/:pathMatch(.*)*', redirect: '/login' },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'login' }
  }
  if (to.meta.requiresOperator && !authStore.isOperator) {
    return { name: 'login' }
  }

  // Zaten giriş yapmış biri /login'e giderse kendi paneline geri yollanır.
  if (to.name === 'login' && authStore.isAuthenticated) {
    if (authStore.role === 'operator') {
      return { name: 'fleet-analytics' }
    }
    if (authStore.role === 'admin') {
      window.location.href = `${backendOrigin}/admin/`
      return false
    }
  }
})

export default router
