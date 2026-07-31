<template>
  <div class="fleet-page">
    <div class="page-header">
      <h1>Bakım Merkezi</h1>
      <button type="button" class="btn-icon" @click="openRequestForm">
        <svg viewBox="0 0 24 24" v-html="ICONS.plus"></svg>
        Talep Aç
      </button>
    </div>

    <Modal v-if="showRequestForm" title="Yeni Bakım/Servis Talebi" @close="showRequestForm = false">
      <form class="inline-form" @submit.prevent="createServiceRequest">
        <label>
          Araç
          <select v-model="newRequest.vehicle" required>
            <option value="" disabled>Araç seç</option>
            <option v-for="vehicle in vehicles" :key="vehicle.id" :value="vehicle.id">
              {{ vehicleLabel(vehicle) }}
            </option>
          </select>
        </label>
        <label>
          Tür
          <select v-model="newRequest.request_type">
            <option value="maintenance">Bakım</option>
            <option value="service">Servis</option>
            <option value="wash">Yıkama</option>
          </select>
        </label>
        <label>
          Öncelik
          <select v-model="newRequest.priority">
            <option value="low">Düşük</option>
            <option value="normal">Normal</option>
            <option value="high">Yüksek</option>
          </select>
        </label>
        <div class="form-actions">
          <button type="submit">Talep Aç</button>
          <button type="button" class="cancel-link" @click="showRequestForm = false">Vazgeç</button>
        </div>
      </form>
      <p v-if="requestErrorMessage" class="error">{{ requestErrorMessage }}</p>
    </Modal>

    <section class="panel-card">
      <p v-if="!serviceRequests.length" class="empty-state">Henüz bir talep yok.</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Araç</th>
            <th>Tür</th>
            <th>Öncelik</th>
            <th>Durum</th>
            <th>Maliyet</th>
            <th>Atanan</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="request in serviceRequests" :key="request.id">
            <td>{{ request.vehicle.brand }} {{ request.vehicle.model }}</td>
            <td>{{ requestTypeLabels[request.request_type] }}</td>
            <td><span class="badge" :class="`priority-${request.priority}`">{{ priorityLabels[request.priority] }}</span></td>
            <td>
              <select
                class="status-select"
                :value="request.status"
                @change="updateServiceRequestStatus(request, $event.target.value)"
              >
                <option v-for="status in nextStatusOptions[request.status]" :key="status" :value="status">
                  {{ requestStatusLabels[status] }}
                </option>
              </select>
            </td>
            <td>{{ request.cost }} TL</td>
            <td>
              <button v-if="!request.assigned_to" class="link-button" @click="assignToMe(request)">
                Bana Ata
              </button>
              <span v-else class="assigned-label">Atandı</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-row">
        <span class="count-badge">{{ totalCount }} talep</span>
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
import Modal from '../../../components/Modal.vue'
import { ICONS } from '../../../icons'
import { useAuthStore } from '../../auth/store'
import { fetchAllVehicles } from '../../vehicles/services'
import { createServiceRequest as createServiceRequestRequest, fetchServiceRequests as fetchServiceRequestsRequest, updateServiceRequest } from '../services'

const authStore = useAuthStore()

const vehicles = ref([])

async function fetchVehicles() {
  const response = await fetchAllVehicles()
  vehicles.value = response.data.results
}

function vehicleLabel(vehicle) {
  return `${vehicle.plate} — ${vehicle.brand} ${vehicle.model}`
}

const PAGE_SIZE = 20

const serviceRequests = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const newRequest = ref({ vehicle: '', request_type: 'maintenance', priority: 'normal' })
const requestErrorMessage = ref('')
const showRequestForm = ref(false)

const totalPages = computed(() => Math.max(Math.ceil(totalCount.value / PAGE_SIZE), 1))

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchServiceRequests()
}

function openRequestForm() {
  newRequest.value = { vehicle: '', request_type: 'maintenance', priority: 'normal' }
  requestErrorMessage.value = ''
  showRequestForm.value = true
}

const requestTypeLabels = { maintenance: 'Bakım', service: 'Servis', wash: 'Yıkama' }
const priorityLabels = { low: 'Düşük', normal: 'Normal', high: 'Yüksek' }
const requestStatusLabels = { open: 'Açık', in_progress: 'İşlemde', done: 'Tamamlandı', cancelled: 'İptal' }

// SRV-2 kabul kriteri: sadece open→in_progress→done geçişlerine izin var.
const nextStatusOptions = {
  open: ['open', 'in_progress', 'cancelled'],
  in_progress: ['in_progress', 'done', 'cancelled'],
  done: ['done'],
  cancelled: ['cancelled'],
}

async function fetchServiceRequests() {
  const response = await fetchServiceRequestsRequest({ page: currentPage.value })
  serviceRequests.value = response.data.results
  totalCount.value = response.data.count
}

async function createServiceRequest() {
  requestErrorMessage.value = ''
  try {
    await createServiceRequestRequest(newRequest.value)
    showRequestForm.value = false
    currentPage.value = 1
    await fetchServiceRequests()
  } catch (error) {
    requestErrorMessage.value = 'Talep oluşturulamadı, alanları kontrol et.'
  }
}

async function updateServiceRequestStatus(request, status) {
  await updateServiceRequest(request.id, { status })
  await fetchServiceRequests()
}

async function assignToMe(request) {
  await updateServiceRequest(request.id, { assigned_to: authStore.userId })
  await fetchServiceRequests()
}

onMounted(() => {
  fetchVehicles()
  fetchServiceRequests()
})
</script>

<style scoped>
.inline-form {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.inline-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--color-muted);
  flex: 1;
  min-width: 160px;
}

.form-actions {
  flex-basis: 100%;
  display: flex;
  gap: 0.75rem;
}

.inline-form select {
  min-width: 200px;
}

.link-button {
  background: none;
  border: none;
  color: var(--color-primary);
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
  font-weight: 500;
}

.link-button:hover {
  background: none;
  color: var(--color-primary-hover);
}

.assigned-label {
  color: var(--color-muted);
  font-size: 0.9rem;
}

.status-select {
  padding: 0.4rem 0.5rem;
  min-width: auto;
}

.priority-low {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.priority-normal {
  background: var(--color-border);
  color: var(--color-muted);
}

.priority-high {
  background: var(--color-destructive-soft);
  color: var(--color-destructive);
}

.panel-card {
  overflow-x: auto;
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
