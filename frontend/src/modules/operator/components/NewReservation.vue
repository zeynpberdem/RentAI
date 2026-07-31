<template>
  <Modal title="Yeni Rezervasyon" @close="$emit('close')">
    <!-- Adım 1: sürücü ara / seç. Bulunamazsa "+ Yeni Sürücü" ile NewDriver
         component'i aynı diyalog içinde açılır — ayrı bir sayfaya gidilmez. -->
    <div v-if="!driver" class="search-step">
      <div v-if="!showNewDriverForm">
        <label class="search-label">
          Sürücü Ara
          <input
            v-model="query"
            type="search"
            placeholder="Ad, email veya telefon ara..."
            @keyup.enter="search"
          />
        </label>
        <button type="button" class="secondary" @click="search">Ara</button>

        <p v-if="hasSearched && !results.length" class="empty-state">
          Eşleşen sürücü bulunamadı.
        </p>

        <ul v-if="results.length" class="driver-results">
          <li v-for="candidate in results" :key="candidate.id">
            <button type="button" class="driver-result" @click="selectDriver(candidate)">
              <span class="driver-result-name">{{ candidate.first_name }} {{ candidate.last_name }}</span>
              <span class="driver-result-email">{{ candidate.email }}</span>
            </button>
          </li>
        </ul>

        <button type="button" class="new-driver-button" @click="showNewDriverForm = true">
          <svg viewBox="0 0 24 24" class="row-icon" v-html="ICONS.plus"></svg>
          Yeni Sürücü
        </button>
      </div>

      <div v-else>
        <p class="new-driver-heading">Yeni Sürücü</p>
        <NewDriver @created="selectDriver" @cancel="showNewDriverForm = false" />
      </div>
    </div>

    <!-- Adım 2: sürücü seçildi/oluşturuldu — rezervasyon bilgileri. -->
    <div v-else>
      <div class="selected-driver">
        <span>Sürücü: <strong>{{ driver.first_name }} {{ driver.last_name }}</strong></span>
        <button type="button" class="link-button" @click="driver = null">Değiştir</button>
      </div>

      <p v-if="!driver.is_profile_complete" class="warning">
        Bu sürücünün profili henüz tamamlanmamış — önce Sürücüler ekranından "Düzenle" ile TC/ehliyet bilgilerini gir.
      </p>

      <form v-else class="reserve-form" @submit.prevent="submitReservation">
        <label>
          Araç
          <select v-model="reservationForm.vehicle" required>
            <option value="" disabled>Araç seç</option>
            <option v-for="vehicle in vehicles" :key="vehicle.id" :value="vehicle.id">
              {{ vehicle.plate }} — {{ vehicle.brand }} {{ vehicle.model }}
            </option>
          </select>
        </label>
        <label>
          Teslim Tarihi ve Saati
          <input v-model="reservationForm.start_date" type="datetime-local" required />
        </label>
        <label>
          İade Tarihi ve Saati
          <input v-model="reservationForm.end_date" type="datetime-local" required />
        </label>
        <label>
          Rezervasyon Tipi
          <select v-model="reservationForm.type">
            <option v-for="option in reservationTypes" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label>
          Rezervasyon Kaynağı
          <select v-model="reservationForm.source">
            <option v-for="option in reservationSources" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
        <label>
          Teslim Alma Ofisi
          <select v-model="reservationForm.pickup_location">
            <option value="">Aracın kendi şubesi</option>
            <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
          </select>
        </label>
        <label>
          Teslim Etme Ofisi
          <select v-model="reservationForm.return_location">
            <option value="">Aracın kendi şubesi</option>
            <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
          </select>
        </label>
        <div class="form-actions">
          <button type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Oluşturuluyor...' : 'Rezervasyon Oluştur' }}
          </button>
        </div>
      </form>
      <p v-if="reservationMessage" :class="reservationMessage.type === 'error' ? 'error' : 'success'">
        {{ reservationMessage.text }}
      </p>
    </div>
  </Modal>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Modal from '../../../components/Modal.vue'
import { ICONS } from '../../../icons'
import { fetchDrivers } from '../../auth/services'
import { createReservationForDriver } from '../../reservations/services'
import { fetchAllVehicles, fetchLocations } from '../../vehicles/services'
import NewDriver from './NewDriver.vue'

const emit = defineEmits(['close', 'created'])

const reservationTypes = [
  { value: 'short_term', label: 'Kısa Dönem' },
  { value: 'long_term', label: 'Uzun Dönem' },
  { value: 'corporate', label: 'Kurumsal' },
]

const reservationSources = [
  { value: 'branch', label: 'Şube' },
  { value: 'call_center', label: 'Çağrı Merkezi' },
  { value: 'web', label: 'Web Sitesi' },
  { value: 'agency', label: 'Online Acenta' },
]

const query = ref('')
const results = ref([])
const hasSearched = ref(false)
const showNewDriverForm = ref(false)

const driver = ref(null)

const vehicles = ref([])
const locations = ref([])

function emptyReservationForm() {
  return {
    vehicle: '',
    start_date: '',
    end_date: '',
    type: 'short_term',
    source: 'branch',
    pickup_location: '',
    return_location: '',
  }
}

const reservationForm = ref(emptyReservationForm())
const reservationMessage = ref(null)
const isSubmitting = ref(false)

async function search() {
  hasSearched.value = true
  const trimmed = query.value.trim()
  if (!trimmed) {
    results.value = []
    return
  }
  const response = await fetchDrivers({ search: trimmed })
  results.value = response.data.results
}

function selectDriver(candidate) {
  driver.value = candidate
  showNewDriverForm.value = false
  reservationMessage.value = null
  reservationForm.value = emptyReservationForm()
}

async function submitReservation() {
  isSubmitting.value = true
  reservationMessage.value = null
  try {
    await createReservationForDriver({
      customer: driver.value.id,
      vehicle: reservationForm.value.vehicle,
      start_date: reservationForm.value.start_date,
      end_date: reservationForm.value.end_date,
      type: reservationForm.value.type,
      source: reservationForm.value.source,
      pickup_location: reservationForm.value.pickup_location,
      return_location: reservationForm.value.return_location,
    })
    reservationMessage.value = { type: 'success', text: 'Rezervasyon oluşturuldu.' }
    emit('created')
  } catch (error) {
    const detail = error.response?.data?.non_field_errors?.[0]
    reservationMessage.value = { type: 'error', text: detail || 'Rezervasyon oluşturulamadı.' }
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  const [vehiclesResponse, locationsResponse] = await Promise.all([fetchAllVehicles(), fetchLocations()])
  vehicles.value = vehiclesResponse.data.results
  locations.value = locationsResponse.data
})
</script>

<style scoped>
.search-label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--color-muted);
  margin-bottom: 0.75rem;
}

.search-label input {
  min-width: 260px;
}

.empty-state {
  margin: 1rem 0;
}

.driver-results {
  list-style: none;
  margin: 0.75rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 220px;
  overflow-y: auto;
}

.driver-result {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.1rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  text-align: left;
}

.driver-result:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.driver-result-name {
  font-weight: 700;
  color: var(--color-foreground);
}

.driver-result-email {
  font-size: 0.8rem;
  color: var(--color-muted);
}

.new-driver-button {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 1rem;
  background: none;
  border: none;
  color: var(--color-primary);
  font-weight: 600;
  padding: 0;
}

.new-driver-button:hover {
  color: var(--color-primary-hover);
  background: none;
}

.new-driver-button .row-icon {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
}

.new-driver-heading {
  font-weight: 700;
  margin: 0 0 0.75rem;
}

.selected-driver {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.link-button {
  background: none;
  border: none;
  color: var(--color-primary);
  text-decoration: underline;
  padding: 0;
  font-weight: 500;
}

.link-button:hover {
  background: none;
  color: var(--color-primary-hover);
}

.reserve-form {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 1rem;
}

.reserve-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--color-muted);
}

.reserve-form select,
.reserve-form input {
  min-width: 180px;
}

.form-actions {
  flex-basis: 100%;
}
</style>
