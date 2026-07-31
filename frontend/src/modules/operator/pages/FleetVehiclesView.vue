<template>
  <div class="fleet-page">
    <div class="page-header">
      <h1>Araçlar</h1>
      <div class="header-actions">
        <input
          v-model="searchInput"
          type="search"
          placeholder="Plaka, marka veya model ara..."
          class="search-input"
          @keyup.enter="runSearch"
        />
        <button type="button" class="secondary btn-icon" @click="runSearch">
          <svg viewBox="0 0 24 24" v-html="ICONS.search"></svg>
          Ara
        </button>
      </div>
    </div>

    <Modal v-if="vehicleForm" :title="`Aracı Düzenle — ${vehicleForm.plate}`" @close="vehicleForm = null">
      <form class="vehicle-form" @submit.prevent="submitVehicleForm">
        <label>
          Marka
          <input v-model="vehicleForm.brand" type="text" required />
        </label>
        <label>
          Model
          <input v-model="vehicleForm.model" type="text" required />
        </label>
        <label>
          Plaka
          <input v-model="vehicleForm.plate" type="text" required />
        </label>
        <label>
          SIPP Kodu
          <input v-model="vehicleForm.sipp_code" type="text" maxlength="4" />
        </label>
        <label>
          Segment
          <select v-model="vehicleForm.segment">
            <option v-for="option in segments" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <label>
          Vites
          <select v-model="vehicleForm.transmission">
            <option v-for="option in transmissions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <label>
          Yakıt
          <select v-model="vehicleForm.fuel">
            <option v-for="option in fuels" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
        <label>
          Koltuk
          <input v-model.number="vehicleForm.seats" type="number" min="1" required />
        </label>
        <label>
          Günlük Fiyat
          <input v-model.number="vehicleForm.daily_price" type="number" min="0" step="0.01" required />
        </label>
        <label>
          Şube
          <select v-model="vehicleForm.location">
            <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
          </select>
        </label>
        <label>
          Durum
          <select v-model="vehicleForm.status">
            <option v-for="option in vehicleStatuses" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>

        <div class="form-actions">
          <button type="submit" :disabled="isSavingVehicle">{{ isSavingVehicle ? 'Kaydediliyor...' : 'Kaydet' }}</button>
          <button type="button" class="cancel-link" @click="vehicleForm = null">Vazgeç</button>
        </div>
      </form>
      <p v-if="vehicleFormError" class="error">{{ vehicleFormError }}</p>
    </Modal>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="isLoading">Yükleniyor...</p>

    <section v-else class="panel-card">
      <p v-if="!vehicles.length" class="empty-state">Aramanla eşleşen araç bulunamadı.</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Plaka</th>
            <th>Marka / Model</th>
            <ColumnFilterHeader label="Segment" :options="segments" v-model="segmentFilter" />
            <ColumnFilterHeader label="Vites" :options="transmissions" v-model="transmissionFilter" />
            <ColumnFilterHeader label="Yakıt" :options="fuels" v-model="fuelFilter" />
            <ColumnFilterHeader label="Şube" :options="locationOptions" v-model="locationFilter" />
            <th class="sortable-th" @click="toggleSort('daily_price')">
              Günlük Fiyat
              <span v-if="sortField === 'daily_price'" class="sort-arrow">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <ColumnFilterHeader label="Durum" :options="vehicleStatuses" v-model="statusFilter" />
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="vehicle in vehicles" :key="vehicle.id">
            <td class="plate">{{ vehicle.plate }}</td>
            <td>{{ vehicle.brand }} {{ vehicle.model }}</td>
            <td>{{ vehicle.segment }}</td>
            <td>{{ vehicle.transmission === 'automatic' ? 'Otomatik' : 'Manuel' }}</td>
            <td>{{ fuelLabels[vehicle.fuel] || vehicle.fuel }}</td>
            <td>
              <span class="location-pill" :style="locationStyle(vehicle.location)">{{ vehicle.location.name }}</span>
            </td>
            <td>{{ formatPrice(vehicle.daily_price) }} TL</td>
            <td><span class="status-badge" :class="vehicle.status">{{ statusLabels[vehicle.status] }}</span></td>
            <td class="row-actions">
              <button type="button" class="icon-action-button" title="Düzenle" @click="openEditVehicleForm(vehicle)">
                <svg viewBox="0 0 24 24" class="row-icon" v-html="ICONS.edit"></svg>
              </button>
              <button type="button" class="icon-action-button danger" title="Sil" @click="removeVehicle(vehicle)">
                <svg viewBox="0 0 24 24" class="row-icon" v-html="ICONS.trash"></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-row">
        <span class="count-badge">{{ totalCount }} araç</span>
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
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ColumnFilterHeader from '../../../components/ColumnFilterHeader.vue'
import Modal from '../../../components/Modal.vue'
import { ICONS } from '../../../icons'
import { deleteVehicle, fetchLocations, fetchVehiclesPage, updateVehicle } from '../../vehicles/services'

const route = useRoute()

const PAGE_SIZE = 20

const vehicles = ref([])
const locations = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const isLoading = ref(false)
const errorMessage = ref('')

const vehicleForm = ref(null)
const vehicleFormError = ref('')
const isSavingVehicle = ref(false)

// Arama kutusu: yazarken backend'e istek atmıyor, sadece Enter'a basılınca
// ya da "Ara" butonuna tıklanınca — searchInput anlık yazılan değer,
// appliedSearch gerçekten istekte gönderilen (uygulanmış) değer.
const searchInput = ref('')
const appliedSearch = ref('')

// Boş string = filtre yok (segment/vites/yakıt/şube ile tutarlı olsun diye).
// route.query.status: Rezervasyon Listesi'ndeki alt menüden ("Kiradaki
// Araç Listesi" / "Müsait Araç Listesi") gelen ön-filtreyi uygular.
const statusFilter = ref(route.query.status || '')
const segmentFilter = ref('')
const transmissionFilter = ref('')
const fuelFilter = ref('')
const locationFilter = ref('')

// Sıralama: "Günlük Fiyat" başlığına tıklanınca artan/azalan geçiş yapar.
const sortField = ref(null)
const sortDirection = ref('asc')

function toggleSort(field) {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  currentPage.value = 1
  loadVehicles()
}

const statusLabels = {
  available: 'Müsait',
  rented: 'Kirada',
  maintenance: 'Bakımda',
}

const segments = [
  { value: 'economy', label: 'Economy' },
  { value: 'mid', label: 'Mid-size' },
  { value: 'suv', label: 'SUV' },
  { value: 'luxury', label: 'Luxury' },
]

const transmissions = [
  { value: 'manual', label: 'Manuel' },
  { value: 'automatic', label: 'Otomatik' },
]

const fuels = [
  { value: 'petrol', label: 'Benzin' },
  { value: 'diesel', label: 'Dizel' },
  { value: 'electric', label: 'Elektrik' },
  { value: 'hybrid', label: 'Hibrit' },
]

const fuelLabels = Object.fromEntries(fuels.map((f) => [f.value, f.label]))

const locationOptions = computed(() => locations.value.map((loc) => ({ value: loc.id, label: loc.name })))

const vehicleStatuses = [
  { value: 'available', label: 'Müsait' },
  { value: 'rented', label: 'Kirada' },
  { value: 'maintenance', label: 'Bakımda' },
]

const totalPages = computed(() => Math.max(Math.ceil(totalCount.value / PAGE_SIZE), 1))

// Şube sayısı zamanla artabileceği için tek tek isimle renk eşlemek yerine,
// şubenin id'sinden basit bir hash ile sabit bir palet üzerinden renk
// seçiyoruz — yeni bir şube eklense de elle güncellemeye gerek kalmaz,
// aynı şube her zaman aynı rengi alır. Bilerek Durum rozetleriyle (Müsait/
// Kirada/Bakımda) aynı canlı renkleri KULLANMIYORUZ — ikisi karışmasın diye
// tamamen ayrı, yumuşak/pastel tonlarda bir palet.
const LOCATION_PALETTE = [
  { bg: '#fce7f0', fg: '#b3466e' },
  { bg: '#ede9fe', fg: '#7c6bb0' },
  { bg: '#e0f2fe', fg: '#4a7ba6' },
  { bg: '#dcfce7', fg: '#4a9b6e' },
  { bg: '#ffedd5', fg: '#b8763f' },
  { bg: '#fef9c3', fg: '#a68b2c' },
  { bg: '#ccfbf1', fg: '#3f8f83' },
  { bg: '#e0e7ff', fg: '#6366a3' },
]

function locationStyle(location) {
  if (!location) return {}
  let hash = 0
  for (const char of String(location.id)) {
    hash = (hash * 31 + char.charCodeAt(0)) % 1000000007
  }
  const { bg, fg } = LOCATION_PALETTE[hash % LOCATION_PALETTE.length]
  return { background: bg, color: fg }
}

const priceFormatter = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 })

function formatPrice(price) {
  return priceFormatter.format(Number(price))
}

function buildParams() {
  const params = { page: currentPage.value }
  if (appliedSearch.value) params.search = appliedSearch.value
  if (statusFilter.value) params.status = statusFilter.value
  if (segmentFilter.value) params.segment = segmentFilter.value
  if (transmissionFilter.value) params.transmission = transmissionFilter.value
  if (fuelFilter.value) params.fuel = fuelFilter.value
  if (locationFilter.value) params.location = locationFilter.value
  if (sortField.value) params.ordering = sortDirection.value === 'desc' ? `-${sortField.value}` : sortField.value
  return params
}

async function loadVehicles() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await fetchVehiclesPage(buildParams())
    vehicles.value = response.data.results
    totalCount.value = response.data.count
  } catch (error) {
    errorMessage.value = 'Araçlar yüklenemedi, lütfen tekrar deneyin.'
  } finally {
    isLoading.value = false
  }
}

function runSearch() {
  appliedSearch.value = searchInput.value.trim()
  currentPage.value = 1
  loadVehicles()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadVehicles()
}

function openEditVehicleForm(vehicle) {
  vehicleFormError.value = ''
  vehicleForm.value = {
    id: vehicle.id,
    brand: vehicle.brand,
    model: vehicle.model,
    plate: vehicle.plate,
    sipp_code: vehicle.sipp_code || '',
    segment: vehicle.segment,
    transmission: vehicle.transmission,
    fuel: vehicle.fuel,
    seats: vehicle.seats,
    daily_price: vehicle.daily_price,
    location: vehicle.location.id,
    status: vehicle.status,
  }
}

async function submitVehicleForm() {
  isSavingVehicle.value = true
  vehicleFormError.value = ''
  try {
    const { id, ...payload } = vehicleForm.value
    await updateVehicle(id, payload)
    vehicleForm.value = null
    await loadVehicles()
  } catch (error) {
    const data = error.response?.data
    const firstError = data && Object.values(data)[0]
    vehicleFormError.value = Array.isArray(firstError) ? firstError[0] : firstError || 'Kaydedilemedi.'
  } finally {
    isSavingVehicle.value = false
  }
}

async function removeVehicle(vehicle) {
  const label = `${vehicle.plate} — ${vehicle.brand} ${vehicle.model}`
  if (!window.confirm(`${label} aracını silmek istediğine emin misin?`)) return

  try {
    await deleteVehicle(vehicle.id)
    await loadVehicles()
  } catch (error) {
    errorMessage.value = 'Araç silinemedi, lütfen tekrar deneyin.'
  }
}

// Sütun filtreleri (arama hariç) değişince sayfa 1'e dönüp yeniden yükle.
watch([statusFilter, segmentFilter, transmissionFilter, fuelFilter, locationFilter], () => {
  currentPage.value = 1
  loadVehicles()
})

// Sayfa zaten AÇIKKEN (ör. Rezervasyon Listesi sidebar alt menüsünden farklı
// bir ön-filtreli bağlantıya tıklanınca) Vue Router aynı component'i yeniden
// KURMAZ, sadece route.query'yi günceller — statusFilter yukarıda sadece İLK
// açılışta okunduğu için, bu durumda filtre hiç uygulanmazdı.
watch(
  () => route.query.status,
  (status) => {
    statusFilter.value = status || ''
  }
)

async function loadLocations() {
  const response = await fetchLocations()
  locations.value = response.data
}

onMounted(() => {
  loadVehicles()
  loadLocations()
})
</script>

<style scoped>
.panel-card {
  overflow-x: auto;
}

.sortable-th {
  cursor: pointer;
  user-select: none;
}

.sortable-th:hover {
  color: var(--color-primary);
}

.sort-arrow {
  margin-left: 0.25rem;
  font-size: 0.7rem;
  color: var(--color-primary);
}

.plate {
  font-weight: 700;
  font-family: ui-monospace, monospace;
}

/* 3 sütunlu grid: sayaç solda sabit, sayfalama kontrolleri ise (sayaç ne
   kadar yer kaplarsa kaplasın) satırın TAM ortasında kalır — sağdaki boş
   1fr, soldaki sayacın genişliğini dengeleyip ortalamayı bozmuyor. */
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

.vehicle-form {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.vehicle-form label {
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

.location-pill {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
}

.row-actions {
  display: flex;
  gap: 0.4rem;
  white-space: nowrap;
}

.icon-action-button {
  width: 32px;
  height: 32px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-muted);
}

.icon-action-button:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.icon-action-button.danger:hover {
  border-color: var(--color-destructive);
  color: var(--color-destructive);
  background: var(--color-destructive-soft);
}

.row-icon {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
}
</style>
