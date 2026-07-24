<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '../../../api/client'
import { useAuthStore } from '../../auth/store'

const authStore = useAuthStore()

// --- Ortak: araç listesi (her iki formda da "hangi araç" seçimi için) ---
const vehicles = ref([])

async function fetchVehicles() {
  const response = await apiClient.get('/vehicles')
  vehicles.value = response.data.results
}

function vehicleLabel(vehicle) {
  return `${vehicle.brand} ${vehicle.model} — ${vehicle.location.name}`
}

// --- Bölüm 1: Bakım/Servis/Yıkama Talepleri (SRV-1/SRV-2) ---
const serviceRequests = ref([])
const newRequest = ref({ vehicle: '', request_type: 'maintenance', priority: 'normal' })
const requestErrorMessage = ref('')

const requestTypeLabels = { maintenance: 'Bakım', service: 'Servis', wash: 'Yıkama' }
const priorityLabels = { low: 'Düşük', normal: 'Normal', high: 'Yüksek' }
const requestStatusLabels = { open: 'Açık', in_progress: 'İşlemde', done: 'Tamamlandı', cancelled: 'İptal' }

// SRV-2 kabul kriteri: sadece open→in_progress→done geçişlerine izin var.
// Backend zaten bunu doğruluyor, burada kullanıcıya sadece izinli seçenekleri
// göstererek gereksiz bir hata denemesinin önüne geçiyoruz.
const nextStatusOptions = {
  open: ['open', 'in_progress', 'cancelled'],
  in_progress: ['in_progress', 'done', 'cancelled'],
  done: ['done'],
  cancelled: ['cancelled'],
}

async function fetchServiceRequests() {
  const response = await apiClient.get('/service-requests')
  serviceRequests.value = response.data.results
}

async function createServiceRequest() {
  requestErrorMessage.value = ''
  try {
    await apiClient.post('/service-requests', newRequest.value)
    newRequest.value = { vehicle: '', request_type: 'maintenance', priority: 'normal' }
    await fetchServiceRequests()
  } catch (error) {
    requestErrorMessage.value = 'Talep oluşturulamadı, alanları kontrol et.'
  }
}

async function updateServiceRequestStatus(request, status) {
  await apiClient.patch(`/service-requests/${request.id}`, { status })
  await fetchServiceRequests()
}

async function assignToMe(request) {
  await apiClient.patch(`/service-requests/${request.id}`, { assigned_to: authStore.userId })
  await fetchServiceRequests()
}

// --- Bölüm 2: Teslim / İade (HND-1/HND-2) ---
const reservations = ref([])
const handoverForm = ref({
  reservation: '',
  type: 'delivery',
  odometer_km: '',
  fuel_level: '',
  damage_notes: '',
})
const handoverMessage = ref(null)

async function fetchReservations() {
  const response = await apiClient.get('/reservations')
  reservations.value = response.data.results
}

function reservationLabel(reservation) {
  return `${reservation.vehicle.brand} ${reservation.vehicle.model} · ${reservation.start_date} → ${reservation.end_date} (${reservation.status})`
}

async function submitHandover() {
  handoverMessage.value = null
  try {
    const response = await apiClient.post('/handovers', handoverForm.value)
    const extraCharge = Number(response.data.extra_charge)
    handoverMessage.value = {
      type: 'success',
      text:
        handoverForm.value.type === 'return' && extraCharge > 0
          ? `İade kaydedildi. Ek ücret: ${extraCharge} TL (eksik yakıt).`
          : 'Kayıt oluşturuldu.',
    }
    handoverForm.value = { reservation: '', type: 'delivery', odometer_km: '', fuel_level: '', damage_notes: '' }
    await fetchReservations()
  } catch (error) {
    const detail = error.response?.data?.non_field_errors?.[0]
    handoverMessage.value = { type: 'error', text: detail || 'Kayıt oluşturulamadı.' }
  }
}

onMounted(() => {
  fetchVehicles()
  fetchServiceRequests()
  fetchReservations()
})
</script>

<template>
  <div class="operator-page">
    <h1>Operatör Paneli</h1>

    <section>
      <h2>Bakım / Servis / Yıkama Talepleri</h2>

      <form class="inline-form" @submit.prevent="createServiceRequest">
        <select v-model="newRequest.vehicle" required>
          <option value="" disabled>Araç seç</option>
          <option v-for="vehicle in vehicles" :key="vehicle.id" :value="vehicle.id">
            {{ vehicleLabel(vehicle) }}
          </option>
        </select>
        <select v-model="newRequest.request_type">
          <option value="maintenance">Bakım</option>
          <option value="service">Servis</option>
          <option value="wash">Yıkama</option>
        </select>
        <select v-model="newRequest.priority">
          <option value="low">Düşük</option>
          <option value="normal">Normal</option>
          <option value="high">Yüksek</option>
        </select>
        <button type="submit">Talep Aç</button>
      </form>
      <p v-if="requestErrorMessage" class="error">{{ requestErrorMessage }}</p>

      <table class="data-table">
        <thead>
          <tr>
            <th>Araç</th>
            <th>Tür</th>
            <th>Öncelik</th>
            <th>Durum</th>
            <th>Maliyet</th>
            <th>Atanan</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="request in serviceRequests" :key="request.id">
            <td>{{ request.vehicle.brand }} {{ request.vehicle.model }}</td>
            <td>{{ requestTypeLabels[request.request_type] }}</td>
            <td>{{ priorityLabels[request.priority] }}</td>
            <td>
              <select
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
              <span v-else>Atandı</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section>
      <h2>Teslim / İade</h2>

      <form class="handover-form" @submit.prevent="submitHandover">
        <select v-model="handoverForm.reservation" required>
          <option value="" disabled>Rezervasyon seç</option>
          <option v-for="reservation in reservations" :key="reservation.id" :value="reservation.id">
            {{ reservationLabel(reservation) }}
          </option>
        </select>

        <label>
          <input type="radio" value="delivery" v-model="handoverForm.type" /> Teslim
        </label>
        <label>
          <input type="radio" value="return" v-model="handoverForm.type" /> İade
        </label>

        <input v-model="handoverForm.odometer_km" type="number" min="0" placeholder="Kilometre" required />
        <input v-model="handoverForm.fuel_level" type="number" min="0" max="100" placeholder="Yakıt (%)" required />
        <input v-model="handoverForm.damage_notes" type="text" placeholder="Hasar notu (opsiyonel)" />

        <button type="submit">Kaydet</button>
      </form>
      <p v-if="handoverMessage" :class="handoverMessage.type === 'error' ? 'error' : 'success'">
        {{ handoverMessage.text }}
      </p>
    </section>
  </div>
</template>

<style scoped>
.operator-page {
  max-width: 1000px;
  margin: 2rem auto;
  padding: 0 1rem;
}

section {
  margin-bottom: 2.5rem;
}

.inline-form,
.handover-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.inline-form select,
.handover-form select,
.handover-form input {
  padding: 0.5rem;
}

button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  background: #1a73e8;
  color: white;
  cursor: pointer;
}

.link-button {
  background: none;
  border: none;
  color: #1a73e8;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
}

.error {
  color: #d33;
}

.success {
  color: #1a8c3f;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  text-align: left;
  padding: 0.5rem;
  border-bottom: 1px solid #ddd;
}
</style>
