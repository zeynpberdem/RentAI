<template>
  <div class="fleet-page calendar-page">
    <div class="page-header">
      <h1>Rezervasyon Takvimi</h1>
      <div class="header-actions">
        <select v-model="locationFilter" title="Şube">
          <option value="">Tüm Şubeler</option>
          <option v-for="loc in locations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
        </select>
        <button class="nav-button" @click="goToday">Bugün</button>
        <button class="nav-button" @click="goPrevWeek">‹</button>
        <span class="range-label">{{ rangeLabel }}</span>
        <button class="nav-button" @click="goNextWeek">›</button>
      </div>
    </div>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="isLoading">Yükleniyor...</p>

    <section v-else class="panel-card calendar-card">
      <p v-if="!vehicles.length" class="empty-state">Araç bulunamadı.</p>

      <div v-else class="calendar-grid">
        <div class="calendar-row calendar-header-row">
          <div class="vehicle-col vehicle-col-header">Araç</div>
          <div class="days-track days-header">
            <div v-for="day in visibleDays" :key="`h-${day.toISOString()}`" class="day-cell day-header" :class="{ today: isToday(day) }">
              <span class="day-name">{{ formatDayName(day) }}</span>
              <span class="day-date">{{ formatDayDate(day) }}</span>
            </div>
          </div>
        </div>

        <div v-for="vehicle in vehicles" :key="vehicle.id" class="calendar-row">
          <div class="vehicle-col">
            <span class="plate">{{ vehicle.plate }}</span>
            <span class="vehicle-name">{{ vehicle.brand }} {{ vehicle.model }}</span>
          </div>
          <div class="days-track">
            <div v-for="day in visibleDays" :key="`c-${day.toISOString()}`" class="day-cell" :class="{ today: isToday(day) }"></div>
            <div
              v-for="reservation in vehicle.reservations"
              :key="reservation.id"
              class="reservation-bar"
              :class="'status-' + reservation.status"
              :style="barStyle(reservation)"
              :title="barTitle(reservation)"
            >
              {{ reservation.customer_name }}
            </div>
          </div>
        </div>
      </div>

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
import { fetchLocations, fetchVehiclesCalendar } from '../../vehicles/services'

const DAYS_TO_SHOW = 7
const DAY_MS = 24 * 60 * 60 * 1000
// Ziraat Filo referansındaki gibi filtre öncelikli yaklaşım: filo büyüdükçe
// tüm araçları tek sayfada listelemek yerine (uzun/kaydırılan bir liste),
// hem şube filtresi hem gerçek sayfalama var — backend zaten VehicleFilter'ı
// (bkz. /vehicles/calendar action) miras aldığı için burada sadece UI eklemek yeterli.
const PAGE_SIZE = 10

const vehicles = ref([])
const locations = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const locationFilter = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const viewStart = ref(startOfWeek(new Date()))

const totalPages = computed(() => Math.max(Math.ceil(totalCount.value / PAGE_SIZE), 1))

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadData()
}

watch(locationFilter, () => {
  currentPage.value = 1
  loadData()
})

function startOfWeek(date) {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  const mondayOffset = (d.getDay() + 6) % 7 // Pazartesi=0 olacak şekilde kaydır
  d.setDate(d.getDate() - mondayOffset)
  return d
}

function addDays(date, amount) {
  const d = new Date(date)
  d.setDate(d.getDate() + amount)
  return d
}

const visibleDays = computed(() => Array.from({ length: DAYS_TO_SHOW }, (_, i) => addDays(viewStart.value, i)))

const rangeLabel = computed(() => {
  const start = visibleDays.value[0]
  const end = visibleDays.value[DAYS_TO_SHOW - 1]
  const startLabel = start.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })
  const endLabel = end.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })
  return `${startLabel} – ${endLabel}`
})

function formatDayName(day) {
  return day.toLocaleDateString('tr-TR', { weekday: 'short' })
}

function formatDayDate(day) {
  return day.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })
}

function isToday(day) {
  const today = new Date()
  return day.toDateString() === today.toDateString()
}

function goToday() {
  viewStart.value = startOfWeek(new Date())
  currentPage.value = 1
  loadData()
}

function goPrevWeek() {
  viewStart.value = addDays(viewStart.value, -DAYS_TO_SHOW)
  currentPage.value = 1
  loadData()
}

function goNextWeek() {
  viewStart.value = addDays(viewStart.value, DAYS_TO_SHOW)
  currentPage.value = 1
  loadData()
}

function barStyle(reservation) {
  const rangeStart = viewStart.value
  const rangeEnd = addDays(viewStart.value, DAYS_TO_SHOW)
  const start = new Date(reservation.start_date)
  const end = new Date(reservation.end_date)

  const clampedStart = start < rangeStart ? rangeStart : start
  const clampedEnd = end > rangeEnd ? rangeEnd : end
  const offsetDays = (clampedStart - rangeStart) / DAY_MS
  const spanDays = Math.max((clampedEnd - clampedStart) / DAY_MS, 0.15)

  return {
    left: `${(offsetDays / DAYS_TO_SHOW) * 100}%`,
    width: `${(spanDays / DAYS_TO_SHOW) * 100}%`,
  }
}

function barTitle(reservation) {
  return `${reservation.customer_name} · ${reservation.start_date} → ${reservation.end_date}`
}

// Sunucuya "YYYY-MM-DD" formatında gönderiyoruz — toISOString() UTC'ye
// çevirirken saat dilimine göre günü kaydırabileceği için elle formatlıyoruz.
function toDateParam(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

async function loadData() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const params = {
      start_date: toDateParam(viewStart.value),
      end_date: toDateParam(addDays(viewStart.value, DAYS_TO_SHOW)),
      page: currentPage.value,
      page_size: PAGE_SIZE,
    }
    if (locationFilter.value) params.location = locationFilter.value

    const response = await fetchVehiclesCalendar(params)
    vehicles.value = response.data.results
    totalCount.value = response.data.count
  } catch (error) {
    errorMessage.value = 'Takvim yüklenemedi, lütfen tekrar deneyin.'
  } finally {
    isLoading.value = false
  }
}

async function loadLocations() {
  const response = await fetchLocations()
  locations.value = response.data
}

onMounted(() => {
  loadData()
  loadLocations()
})
</script>

<style scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.nav-button {
  padding: 0.45rem 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  cursor: pointer;
  font-weight: 700;
  color: var(--color-foreground);
  transition: border-color 150ms ease, color 150ms ease;
}

.nav-button:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.range-label {
  font-size: 0.9rem;
  color: var(--color-muted);
  min-width: 170px;
  text-align: center;
  font-weight: 600;
}

.panel-card {
  overflow-x: auto;
}

.calendar-grid {
  min-width: 760px;
}

.calendar-row {
  display: flex;
  border-bottom: 1px solid var(--color-border);
}

.calendar-row:last-child {
  border-bottom: none;
}

.calendar-header-row {
  border-bottom: 2px solid var(--color-border);
  padding-bottom: 0.5rem;
}

.vehicle-col {
  width: 200px;
  flex-shrink: 0;
  padding: 0.7rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.vehicle-col-header {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-muted);
  justify-content: center;
}

.plate {
  font-weight: 700;
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
}

.vehicle-name {
  font-size: 0.8rem;
  color: var(--color-muted);
}

.days-track {
  position: relative;
  flex: 1;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  min-height: 56px;
}

.days-header {
  min-height: auto;
}

.day-cell {
  border-left: 1px solid var(--color-border);
}

.day-cell.today {
  background: var(--color-primary-soft);
}

.day-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.4rem 0;
  gap: 0.1rem;
}

.day-name {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--color-muted);
}

.day-date {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--color-foreground);
}

.day-header.today .day-date {
  color: var(--color-primary-hover);
}

.reservation-bar {
  position: absolute;
  top: 8px;
  bottom: 8px;
  border-radius: var(--radius-sm);
  background: var(--color-info-soft);
  color: var(--color-info);
  border: 1px solid transparent;
  padding: 0 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  overflow: hidden;
  white-space: nowrap;
  cursor: default;
}

.reservation-bar.status-3,
.reservation-bar.status-2 {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.reservation-bar.status-4 {
  background: var(--color-border);
  color: var(--color-muted);
}

.reservation-bar.status-99 {
  background: var(--color-destructive-soft);
  color: var(--color-destructive);
  text-decoration: line-through;
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
