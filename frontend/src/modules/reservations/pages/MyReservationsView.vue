<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '../../../api/client'

const reservations = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
// Hangi rezervasyon iptal ediliyor — id'ye göre, tek bir kartı disable etmek için.
const cancellingId = ref(null)

const statusLabels = {
  pending: 'Onay Bekliyor',
  confirmed: 'Onaylandı',
  active: 'Devam Ediyor',
  completed: 'Tamamlandı',
  cancelled: 'İptal Edildi',
}

const priceFormatter = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 })

function formatPrice(price) {
  return priceFormatter.format(Number(price))
}

async function fetchReservations() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await apiClient.get('/reservations')
    reservations.value = response.data.results
  } catch (error) {
    errorMessage.value = 'Rezervasyonlar yüklenemedi, lütfen tekrar deneyin.'
  } finally {
    isLoading.value = false
  }
}

async function cancelReservation(reservation) {
  cancellingId.value = reservation.id
  try {
    const response = await apiClient.post(`/reservations/${reservation.id}/cancel`)
    reservation.status = response.data.status
  } catch (error) {
    errorMessage.value = 'Rezervasyon iptal edilemedi.'
  } finally {
    cancellingId.value = null
  }
}

onMounted(fetchReservations)
</script>

<template>
  <div class="reservations-page">
    <h1>Rezervasyonlarım</h1>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="isLoading">Yükleniyor...</p>
    <p v-else-if="!reservations.length">Henüz bir rezervasyonun yok.</p>

    <div class="reservation-list">
      <div v-for="reservation in reservations" :key="reservation.id" class="reservation-card">
        <div class="reservation-info">
          <h3>{{ reservation.vehicle.brand }} {{ reservation.vehicle.model }}</h3>
          <p class="dates">{{ reservation.start_date }} → {{ reservation.end_date }}</p>
          <p class="price">{{ formatPrice(reservation.total_price) }} TL</p>
          <span class="status" :class="reservation.status">{{ statusLabels[reservation.status] }}</span>
        </div>

        <button
          v-if="['pending', 'confirmed'].includes(reservation.status)"
          class="cancel-button"
          :disabled="cancellingId === reservation.id"
          @click="cancelReservation(reservation)"
        >
          {{ cancellingId === reservation.id ? 'İptal Ediliyor...' : 'İptal Et' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reservations-page {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.error {
  color: #d33;
}

.reservation-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reservation-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

.dates {
  color: #666;
  font-size: 0.9rem;
}

.price {
  font-weight: bold;
}

.status {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 4px;
  font-size: 0.85rem;
  background: #f2f2f2;
}

.status.confirmed,
.status.active {
  background: #e3f2e6;
  color: #1a8c3f;
}

.status.cancelled {
  background: #fbe4e4;
  color: #d33;
}

.cancel-button {
  padding: 0.5rem 1rem;
  border: 1px solid #d33;
  border-radius: 6px;
  background: white;
  color: #d33;
  cursor: pointer;
}

.cancel-button:disabled {
  opacity: 0.5;
  cursor: default;
}
</style>
