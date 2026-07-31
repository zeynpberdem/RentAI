<template>
  <div class="fleet-page">
    <div class="page-header">
      <h1>Teslimat Listesi</h1>
    </div>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <section class="panel-card">
      <p v-if="!handovers.length" class="empty-state">Henüz bir teslimat kaydı yok.</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Araç</th>
            <th>Müşteri</th>
            <th>Kilometre</th>
            <th>Yakıt</th>
            <th>Hasar Notu</th>
            <th>Tarih</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="handover in handovers" :key="handover.id">
            <td class="plate">{{ handover.vehicle_plate }} — {{ handover.vehicle_label }}</td>
            <td>{{ handover.customer_name }}</td>
            <td>{{ handover.odometer_km }} km</td>
            <td>%{{ handover.fuel_level }}</td>
            <td>{{ handover.damage_notes || '—' }}</td>
            <td>{{ formatDate(handover.created_at) }}</td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-row">
        <span class="count-badge">{{ totalCount }} teslimat</span>
        <div v-if="totalPages > 1" class="pagination-controls">
          <button type="button" class="secondary" :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">‹ Önceki</button>
          <span class="page-label">Sayfa {{ currentPage }} / {{ totalPages }}</span>
          <button type="button" class="secondary" :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">Sonraki ›</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchHandovers } from '../services'

const PAGE_SIZE = 20

const handovers = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const errorMessage = ref('')

const totalPages = computed(() => Math.max(Math.ceil(totalCount.value / PAGE_SIZE), 1))

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('tr-TR')
}

async function loadHandovers() {
  errorMessage.value = ''
  try {
    const response = await fetchHandovers({ page: currentPage.value, type: 'delivery' })
    handovers.value = response.data.results
    totalCount.value = response.data.count
  } catch (error) {
    errorMessage.value = 'Teslimat listesi yüklenemedi, lütfen tekrar deneyin.'
  }
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadHandovers()
}

onMounted(loadHandovers)
</script>

<style scoped>
.panel-card {
  overflow-x: auto;
}

.plate {
  font-weight: 700;
}

.pagination-row {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 1rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.pagination-row .count-badge {
  grid-column: 1;
  margin-left: 0;
}

.pagination-controls {
  grid-column: 2;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.page-label {
  font-size: 0.85rem;
  color: var(--color-muted);
  font-weight: 600;
}
</style>
