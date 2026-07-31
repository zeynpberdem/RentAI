<template>
  <div class="fleet-page">
    <NavigationLoadingOverlay v-if="navLoading" :title="navLoading.title" subtitle="Bir saniye, hazırlanıyor…" />

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="isLoading">Yükleniyor...</p>

    <template v-else>
      <section class="hero">
        <div class="hero-content">
          <div class="hero-brand">RA</div>
          <div>
            <p class="hero-label">{{ welcomeLabel }}</p>
            <h1 class="hero-title">RentAI Filo Yönetimi</h1>
          </div>
        </div>
        <div class="hero-badge">
          <span class="live-dot"></span>
          <div>
            <p class="hero-badge-label">Aktif Filo</p>
            <p class="hero-badge-value">{{ vehicles.length }}</p>
          </div>
        </div>
      </section>

      <div class="stat-grid">
        <div class="stat-card">
          <p class="stat-label">Toplam Araç</p>
          <p class="stat-value">{{ vehicles.length }}</p>
          <div class="chip-row">
            <span class="chip available">{{ vehicleCounts.available }} müsait</span>
            <span class="chip rented">{{ vehicleCounts.rented }} kirada</span>
            <span class="chip maintenance">{{ vehicleCounts.maintenance }} bakımda</span>
          </div>
        </div>

        <div class="stat-card">
          <p class="stat-label">Toplam Sürücü</p>
          <p class="stat-value">{{ drivers.length }}</p>
          <div class="chip-row">
            <span class="chip complete">{{ driverCounts.complete }} profili tam</span>
            <span class="chip incomplete">{{ driverCounts.incomplete }} eksik</span>
          </div>
        </div>

        <div class="stat-card">
          <p class="stat-label">Aktif Rezervasyon</p>
          <p class="stat-value">{{ reservationCounts.active }}</p>
          <p class="stat-hint">Onay Bekliyor: {{ reservationCounts.pending }}</p>
        </div>

        <div class="stat-card">
          <p class="stat-label">Toplam Gelir</p>
          <p class="stat-value">{{ formatPrice(totalRevenue) }} TL</p>
          <p class="stat-hint">İptal edilenler hariç, {{ reservationCounts.billable }} rezervasyon</p>
        </div>
      </div>

      <section>
        <h2 class="section-title">Hızlı Erişim</h2>
        <div class="shortcut-grid">
          <button
            v-for="item in shortcuts"
            :key="item.id"
            type="button"
            class="shortcut-card"
            :style="{ background: item.gradient }"
            @click="handleShortcut(item)"
          >
            <svg viewBox="0 0 24 24" class="shortcut-icon" v-html="ICONS[item.icon]"></svg>
            <p class="shortcut-title">{{ item.title }}</p>
            <p class="shortcut-desc">{{ item.desc }}</p>
          </button>
        </div>
      </section>

      <div class="donut-grid">
        <section class="panel-card">
          <h2>Araç Durumu Dağılımı</h2>
          <div class="donut-row">
            <DonutChart :segments="vehicleDistribution" :center-value="vehicles.length" center-sub="Araç" />
            <div class="legend-col">
              <span v-for="segment in vehicleDistribution" :key="segment.id" class="legend-item">
                <i class="legend-dot" :style="{ background: segment.color }"></i>{{ segment.label }} ({{ segment.count }})
              </span>
            </div>
          </div>
        </section>

        <section class="panel-card">
          <h2>Rezervasyon Durumu Dağılımı</h2>
          <div class="donut-row">
            <DonutChart :segments="reservationDistribution" :center-value="reservations.length" center-sub="Rezervasyon" />
            <div class="legend-col">
              <span v-for="segment in reservationDistribution" :key="segment.id" class="legend-item">
                <i class="legend-dot" :style="{ background: segment.color }"></i>{{ segment.label }} ({{ segment.count }})
              </span>
            </div>
          </div>
        </section>
      </div>

      <section class="panel-card">
        <div class="section-header">
          <div>
            <h2>İşletme İstatistikleri</h2>
            <p class="section-sub">{{ selectedYear }} yılı özeti</p>
          </div>
          <div class="year-row">
            <button
              v-for="year in availableYears"
              :key="year"
              type="button"
              class="year-pill"
              :class="{ active: year === selectedYear }"
              @click="selectedYear = year"
            >
              {{ year }}
            </button>
          </div>
        </div>

        <div class="year-stat-grid">
          <div class="year-stat-card">
            <p class="stat-label">Yıllık Gelir</p>
            <p class="stat-value">{{ formatPrice(yearRevenue) }} TL</p>
          </div>
          <div class="year-stat-card">
            <p class="stat-label">Toplam Kiralama</p>
            <p class="stat-value">{{ yearBillable.length }}</p>
          </div>
          <div class="year-stat-card">
            <p class="stat-label">Kiralanan Gün</p>
            <p class="stat-value">{{ yearRentedDays }}</p>
          </div>
        </div>

        <div class="chart-block">
          <h3 class="chart-title">Aylık Gelir Trendi</h3>
          <RevenueLineChart :data="monthlyRevenue" :height="180" />
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DonutChart from '../../../components/DonutChart.vue'
import NavigationLoadingOverlay from '../../../components/NavigationLoadingOverlay.vue'
import RevenueLineChart from '../../../components/RevenueLineChart.vue'
import { ICONS } from '../../../icons'
import { fetchMe, fetchAllDrivers } from '../../auth/services'
import { fetchAllReservationsForCalendar } from '../../reservations/services'
import { fetchAllVehicles } from '../../vehicles/services'

const router = useRouter()

const me = ref(null)
const vehicles = ref([])
const drivers = ref([])
const reservations = ref([])
const isLoading = ref(false)
const errorMessage = ref('')
const navLoading = ref(null)

const priceFormatter = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 })

function formatPrice(price) {
  return priceFormatter.format(Number(price))
}

const welcomeLabel = computed(() => {
  if (!me.value) return 'Hoş Geldiniz'
  const name = `${me.value.first_name} ${me.value.last_name}`.trim()
  return `Hoş Geldiniz, ${name || me.value.email}`
})

const shortcuts = [
  {
    id: 'araclar',
    icon: 'car',
    title: 'Araçlar',
    desc: 'Filo listesi ve durumları',
    to: '/operator/vehicles',
    gradient: 'linear-gradient(135deg, var(--color-primary), var(--color-primary-hover))',
  },
  {
    id: 'surucular',
    icon: 'user',
    title: 'Sürücüler',
    desc: 'Müşteri profilleri',
    to: '/operator/drivers',
    gradient: 'linear-gradient(135deg, #f59e0b, #ea580c)',
  },
  {
    id: 'rezervasyon-takvimi',
    icon: 'calendar',
    title: 'Rezervasyon Takvimi',
    desc: 'Araç bazlı müsaitlik',
    to: '/operator/reservation-calendar',
    gradient: 'linear-gradient(135deg, #6366f1, #4338ca)',
  },
  {
    id: 'canli-takip',
    icon: 'map-pin',
    title: 'Canlı Takip',
    desc: 'Haritada şube/araç konumu',
    to: '/operator/live-tracking',
    gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)',
  },
]

function handleShortcut(item) {
  if (navLoading.value) return
  navLoading.value = { title: item.title }
  window.setTimeout(() => {
    router.push(item.to)
  }, 650)
}

const vehicleCounts = computed(() => {
  const counts = { available: 0, rented: 0, maintenance: 0 }
  for (const vehicle of vehicles.value) {
    if (counts[vehicle.status] !== undefined) counts[vehicle.status] += 1
  }
  return counts
})

const driverCounts = computed(() => {
  const complete = drivers.value.filter((driver) => driver.is_profile_complete).length
  return { complete, incomplete: drivers.value.length - complete }
})

// Hacer Hanım'ın sayısal durum kodları: 1=Onay Bekliyor, 2=Teslim Bekliyor,
// 3=Kirada, 4=Tamamlandı, 99=İptal Edildi — bkz. backend reservations/helpers.py.
// Okunabilirlik için burada hâlâ isimli anahtarlar (pending/confirmed/...)
// kullanıyoruz, sadece API'den gelen ham sayıyla eşleştirme değişti.
const reservationCounts = computed(() => {
  const counts = { pending: 0, confirmed: 0, active: 0, completed: 0, cancelled: 0 }
  for (const reservation of reservations.value) {
    if (reservation.status === 1) counts.pending += 1
    else if (reservation.status === 2) counts.confirmed += 1
    else if (reservation.status === 3) counts.active += 1
    else if (reservation.status === 4) counts.completed += 1
    else if (reservation.status === 99) counts.cancelled += 1
  }
  return { ...counts, billable: reservations.value.length - counts.cancelled }
})

const totalRevenue = computed(() =>
  reservations.value
    .filter((reservation) => reservation.status !== 99)
    .reduce((sum, reservation) => sum + Number(reservation.total_price), 0)
)

function toDistribution(counts, labels, colors, total) {
  return Object.entries(counts)
    .filter(([, count]) => count > 0)
    .map(([id, count]) => ({
      id,
      label: labels[id],
      color: colors[id],
      count,
      percent: total > 0 ? (count / total) * 100 : 0,
    }))
}

const vehicleDistribution = computed(() =>
  toDistribution(
    vehicleCounts.value,
    { available: 'Müsait', rented: 'Kirada', maintenance: 'Bakımda' },
    {
      available: 'var(--color-success)',
      rented: 'var(--color-info)',
      maintenance: 'var(--color-warning)',
    },
    vehicles.value.length
  )
)

const reservationDistribution = computed(() =>
  toDistribution(
    {
      pending: reservationCounts.value.pending,
      confirmed: reservationCounts.value.confirmed,
      active: reservationCounts.value.active,
      completed: reservationCounts.value.completed,
      cancelled: reservationCounts.value.cancelled,
    },
    {
      pending: 'Onay Bekliyor',
      confirmed: 'Onaylandı',
      active: 'Devam Ediyor',
      completed: 'Tamamlandı',
      cancelled: 'İptal Edildi',
    },
    {
      pending: 'var(--color-info)',
      confirmed: 'var(--color-success)',
      active: 'var(--color-success)',
      completed: 'var(--color-muted)',
      cancelled: 'var(--color-destructive)',
    },
    reservations.value.length
  )
)

// --- Yıl bazlı işletme istatistikleri ---

const selectedYear = ref(new Date().getFullYear())

const availableYears = computed(() => {
  const years = new Set([new Date().getFullYear()])
  for (const reservation of reservations.value) {
    years.add(new Date(reservation.start_date).getFullYear())
  }
  return [...years].sort((a, b) => b - a)
})

const yearReservations = computed(() =>
  reservations.value.filter((reservation) => new Date(reservation.start_date).getFullYear() === selectedYear.value)
)

// İptal edilen rezervasyonlar gelire/istatistiğe dahil edilmiyor.
const yearBillable = computed(() => yearReservations.value.filter((reservation) => reservation.status !== 99))

const yearRevenue = computed(() =>
  yearBillable.value.reduce((sum, reservation) => sum + Number(reservation.total_price), 0)
)

const yearRentedDays = computed(() =>
  yearBillable.value.reduce((sum, reservation) => {
    const days = Math.round((new Date(reservation.end_date) - new Date(reservation.start_date)) / 86400000)
    return sum + Math.max(days, 0)
  }, 0)
)

const MONTH_NAMES = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']

const monthlyRevenue = computed(() => {
  const months = Array(12).fill(0)
  for (const reservation of yearBillable.value) {
    const monthIndex = new Date(reservation.start_date).getMonth()
    months[monthIndex] += Number(reservation.total_price)
  }
  return MONTH_NAMES.map((name, index) => ({ ay: name, gelir: months[index] }))
})

async function loadData() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [meResponse, vehiclesResponse, driversResponse, reservationsResponse] = await Promise.all([
      fetchMe(),
      fetchAllVehicles(),
      fetchAllDrivers(),
      fetchAllReservationsForCalendar(),
    ])
    me.value = meResponse.data
    vehicles.value = vehiclesResponse.data.results
    drivers.value = driversResponse.data.results
    reservations.value = reservationsResponse.data.results
  } catch (error) {
    errorMessage.value = 'Analiz verileri yüklenemedi, lütfen tekrar deneyin.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.5rem;
  background: linear-gradient(135deg, #0f172a 0%, var(--color-primary-hover) 100%);
  border-radius: var(--radius-lg);
  padding: 2rem;
  margin-bottom: 1.5rem;
  color: white;
}

.hero-content {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.hero-brand {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.1rem;
  flex-shrink: 0;
}

.hero-label {
  margin: 0 0 0.2rem;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  font-weight: 600;
}

.hero-title {
  margin: 0;
  color: white;
  font-size: 1.5rem;
}

.hero-badge {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-md);
  padding: 0.75rem 1.25rem;
}

.live-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.25);
  flex-shrink: 0;
}

.hero-badge-label {
  margin: 0;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.65);
}

.hero-badge-value {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
  color: white;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 1.35rem;
}

.stat-label {
  margin: 0 0 0.4rem;
  color: var(--color-muted);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-value {
  margin: 0 0 0.6rem;
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--color-foreground);
}

.stat-hint {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.82rem;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.chip {
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  background: var(--color-border);
  color: var(--color-muted);
}

.chip.available,
.chip.complete {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.chip.rented {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.chip.maintenance,
.chip.incomplete {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.section-title {
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-muted);
  margin: 0 0 0.9rem;
}

.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.shortcut-card {
  border: none;
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  text-align: left;
  color: white;
  cursor: pointer;
  transition: transform 200ms ease, box-shadow 200ms ease;
  background-color: var(--color-primary);
}

.shortcut-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.shortcut-icon {
  width: 26px;
  height: 26px;
  fill: none;
  stroke: white;
  stroke-width: 1.8;
  margin-bottom: 0.9rem;
}

.shortcut-title {
  margin: 0 0 0.2rem;
  font-weight: 700;
}

.shortcut-desc {
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.85;
}

.donut-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.donut-row {
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.legend-col {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  font-size: 0.88rem;
  color: var(--color-foreground);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.section-sub {
  margin: 0.2rem 0 0;
  color: var(--color-muted);
  font-size: 0.85rem;
}

.year-row {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.year-pill {
  padding: 0.4rem 0.9rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-muted);
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 150ms ease;
}

.year-pill:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.year-pill.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.year-stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.year-stat-card {
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: 1rem 1.1rem;
}

.chart-block {
  border-top: 1px solid var(--color-border);
  padding-top: 1.25rem;
}

.chart-title {
  margin: 0 0 1rem;
  font-size: 0.95rem;
}
</style>
