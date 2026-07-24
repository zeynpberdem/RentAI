<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../../../api/client'
import { useAuthStore } from '../../auth/store'

const router = useRouter()
const authStore = useAuthStore()

const vehicles = ref([])
const count = ref(0)
const nextUrl = ref(null)
const previousUrl = ref(null)
const isLoading = ref(false)
const errorMessage = ref('')
// Hangi aracın rezervasyonu yapılıyor / sonucu ne oldu — id'ye göre tutuluyor
// ki bir karttaki işlem diğer kartları etkilemesin.
const reservingVehicleId = ref(null)
const reservationMessages = ref({})
// Kullanıcı üstteki arama çubuğuyla en az bir kez arama yapana kadar
// sonuç listesini hiç göstermiyoruz — site ilk açıldığında sadece
// arama çubuğu görünsün istendi.
const hasSearched = ref(false)

// "YYYY-MM-DD" formatına çeviriyor — date.toISOString() KULLANMIYORUZ
// çünkü o, tarihi UTC'ye çevirir ve saat dilimine göre günü bir öne/
// arkaya kaydırabilir (örn. gece yarısına yakın saatlerde). getFullYear/
// getMonth/getDate ise hep KULLANICININ yerel gününü verir.
function formatDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const today = new Date()
const defaultReturnDate = new Date(today)
defaultReturnDate.setDate(today.getDate() + 3) // ortalama kiralama süresi: 3 gün

// Üstteki arama çubuğu: şube + tarih aralığı. Varsayılan olarak "bugün"
// ve "3 gün sonrası" ile açılıyor (siteyi ilk açtığında hazır bir tarih
// aralığı görsün diye, tıpkı örnek gösterdiğin sitelerdeki gibi).
const locations = ref([])
const selectedLocation = ref('')
const dateRange = ref({
  start_date: formatDate(today),
  end_date: formatDate(defaultReturnDate),
})

// Yan paneldeki filtreler. transmission/fuel birer DİZİ — checkbox'larla
// birden fazla seçilebiliyor (backend'de MultipleChoiceFilter'a karşılık gelir).
const filters = ref({
  segment: '',
  transmission: [],
  fuel: [],
  seats_min: '',
  daily_price_min: '',
  daily_price_max: '',
  has_ac: false,
  is_4wd: false,
})

function buildParams() {
  const params = {}

  if (selectedLocation.value) params.location = selectedLocation.value
  if (dateRange.value.start_date) params.start_date = dateRange.value.start_date
  if (dateRange.value.end_date) params.end_date = dateRange.value.end_date

  if (filters.value.segment) params.segment = filters.value.segment
  if (filters.value.transmission.length) params.transmission = filters.value.transmission
  if (filters.value.fuel.length) params.fuel = filters.value.fuel
  if (filters.value.seats_min) params.seats_min = filters.value.seats_min
  if (filters.value.daily_price_min) params.daily_price_min = filters.value.daily_price_min
  if (filters.value.daily_price_max) params.daily_price_max = filters.value.daily_price_max
  if (filters.value.has_ac) params.has_ac = true
  if (filters.value.is_4wd) params.is_4wd = true

  return params
}

async function fetchVehicles(url = null) {
  hasSearched.value = true
  isLoading.value = true
  errorMessage.value = ''
  try {
    // next/previous, backend'den TAM adres olarak geliyor
    // (http://localhost:8000/api/vehicles?page=2...) — axios'a olduğu
    // gibi verince, baseURL'i görmezden gelip onu kullanıyor.
    const response = url
      ? await apiClient.get(url)
      : await apiClient.get('/vehicles', { params: buildParams() })

    vehicles.value = response.data.results
    count.value = response.data.count
    nextUrl.value = response.data.next
    previousUrl.value = response.data.previous
  } catch (error) {
    errorMessage.value = 'Araçlar yüklenemedi, lütfen tekrar deneyin.'
  } finally {
    isLoading.value = false
  }
}

async function fetchLocations() {
  const response = await apiClient.get('/locations')
  locations.value = response.data
}

// Backend fiyatı "1200.00" gibi bir METİN olarak gönderiyor (Decimal
// alanı). Türkçe gösterim: binlik ayracı NOKTA (1.200), ondalık ayracı
// VİRGÜL — İngilizce'nin tam tersi. Intl.NumberFormat('tr-TR') bunu
// bizim için doğru yapıyor, elle string işlemeye gerek yok.
const priceFormatter = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 })

function formatPrice(price) {
  return priceFormatter.format(Number(price))
}

async function reserveVehicle(vehicle) {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  reservingVehicleId.value = vehicle.id
  reservationMessages.value = { ...reservationMessages.value, [vehicle.id]: '' }
  try {
    // Kartta gösterilen araçlar zaten arama çubuğundaki tarih aralığında
    // müsait olacak şekilde filtrelenmişti (bkz. filter_availability),
    // bu yüzden rezervasyonu da aynı tarih aralığıyla açıyoruz.
    await apiClient.post('/reservations', {
      vehicle: vehicle.id,
      start_date: dateRange.value.start_date,
      end_date: dateRange.value.end_date,
    })
    reservationMessages.value = {
      ...reservationMessages.value,
      [vehicle.id]: { type: 'success', text: 'Rezervasyon oluşturuldu.' },
    }
  } catch (error) {
    const detail = error.response?.data?.non_field_errors?.[0]
    reservationMessages.value = {
      ...reservationMessages.value,
      [vehicle.id]: { type: 'error', text: detail || 'Rezervasyon oluşturulamadı.' },
    }
  } finally {
    reservingVehicleId.value = null
  }
}

onMounted(() => {
  fetchLocations()
  // fetchVehicles() BİLEREK burada çağrılmıyor — sonuçlar sadece
  // kullanıcı "Araç Bul"a bastığında (veya bir filtre değiştirdiğinde) çıksın.
})
</script>

<template>
  <div class="search-page">
    <h1>Araç Ara</h1>

    <form class="date-bar" @submit.prevent="fetchVehicles()">
      <label>
        Teslim Alış Yeri
        <select v-model="selectedLocation">
          <option value="">Tüm şubeler</option>
          <option v-for="location in locations" :key="location.id" :value="location.id">
            {{ location.name }}, {{ location.city }}
          </option>
        </select>
      </label>
      <label>
        Teslim Alış Tarihi
        <input v-model="dateRange.start_date" type="date" />
      </label>
      <label>
        Teslim Ediş Tarihi
        <input v-model="dateRange.end_date" type="date" />
      </label>
      <button type="submit">Araç Bul</button>
    </form>

    <div class="content">
      <aside v-if="hasSearched" class="filter-panel">
        <h2>Filtreler</h2>

        <div class="filter-group">
          <label for="segment">Segment</label>
          <select id="segment" v-model="filters.segment" @change="fetchVehicles()">
            <option value="">Hepsi</option>
            <option value="economy">Ekonomi</option>
            <option value="mid">Orta</option>
            <option value="suv">SUV</option>
            <option value="luxury">Lüks</option>
          </select>
        </div>

        <div class="filter-group">
          <span class="filter-title">Vites Tipi</span>
          <label><input type="checkbox" value="automatic" v-model="filters.transmission" @change="fetchVehicles()" /> Otomatik</label>
          <label><input type="checkbox" value="manual" v-model="filters.transmission" @change="fetchVehicles()" /> Manuel</label>
        </div>

        <div class="filter-group">
          <span class="filter-title">Yakıt Tipi</span>
          <label><input type="checkbox" value="petrol" v-model="filters.fuel" @change="fetchVehicles()" /> Benzin</label>
          <label><input type="checkbox" value="diesel" v-model="filters.fuel" @change="fetchVehicles()" /> Dizel</label>
          <label><input type="checkbox" value="electric" v-model="filters.fuel" @change="fetchVehicles()" /> Elektrikli</label>
          <label><input type="checkbox" value="hybrid" v-model="filters.fuel" @change="fetchVehicles()" /> Hibrit</label>
        </div>

        <div class="filter-group">
          <label for="seats-min">En Az Koltuk</label>
          <input id="seats-min" v-model="filters.seats_min" type="number" min="1" @change="fetchVehicles()" />
        </div>

        <div class="filter-group">
          <span class="filter-title">Fiyat Aralığı (TL/gün)</span>
          <input v-model="filters.daily_price_min" type="number" placeholder="Min" @change="fetchVehicles()" />
          <input v-model="filters.daily_price_max" type="number" placeholder="Max" @change="fetchVehicles()" />
        </div>

        <div class="filter-group">
          <span class="filter-title">Özellikler</span>
          <label><input type="checkbox" v-model="filters.has_ac" @change="fetchVehicles()" /> Klima</label>
          <label><input type="checkbox" v-model="filters.is_4wd" @change="fetchVehicles()" /> Dörtçeker</label>
        </div>
      </aside>

      <main class="results">
        <template v-if="hasSearched">
          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
          <p v-if="isLoading">Yükleniyor...</p>
          <p v-else class="result-count">{{ count }} araç bulundu</p>

          <div class="vehicle-grid">
            <div v-for="vehicle in vehicles" :key="vehicle.id" class="vehicle-card">
              <div class="vehicle-image">
                <img v-if="vehicle.image" :src="vehicle.image" :alt="`${vehicle.brand} ${vehicle.model}`" />
                <div v-else class="vehicle-image-placeholder">🚗</div>
              </div>

              <div class="vehicle-info">
                <h3>{{ vehicle.brand }} {{ vehicle.model }}</h3>

                <p class="badges">
                  <span class="badge">👤 {{ vehicle.seats }}</span>
                  <span class="badge">⚙ {{ vehicle.transmission === 'automatic' ? 'Otomatik' : 'Manuel' }}</span>
                </p>

                <p class="details">
                  {{ vehicle.segment }} · {{ vehicle.fuel }}{{ vehicle.has_ac ? ' · Klima' : '' }}{{ vehicle.is_4wd ? ' · Dörtçeker' : '' }}
                </p>

                <p class="price">{{ formatPrice(vehicle.daily_price) }} TL/gün</p>
                <p class="location">{{ vehicle.location.name }}, {{ vehicle.location.city }}</p>

                <button
                  class="reserve-button"
                  :disabled="reservingVehicleId === vehicle.id"
                  @click="reserveVehicle(vehicle)"
                >
                  {{ reservingVehicleId === vehicle.id ? 'Gönderiliyor...' : 'Rezervasyon Yap' }}
                </button>
                <p
                  v-if="reservationMessages[vehicle.id]"
                  :class="reservationMessages[vehicle.id].type === 'error' ? 'error' : 'success'"
                >
                  {{ reservationMessages[vehicle.id].text }}
                </p>
              </div>
            </div>
          </div>

          <div class="pagination">
            <button :disabled="!previousUrl" @click="fetchVehicles(previousUrl)">Önceki</button>
            <button :disabled="!nextUrl" @click="fetchVehicles(nextUrl)">Sonraki</button>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<style scoped>
.search-page {
  max-width: 1100px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.date-bar {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1.5rem;
  align-items: end;
  max-width: 900px;
  margin: 0 auto 2rem;
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.date-bar label {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.95rem;
}

.date-bar select,
.date-bar input[type='date'] {
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  min-width: 220px;
}

.date-bar button {
  padding: 0.85rem 2rem;
  font-size: 1.05rem;
  font-weight: bold;
  border: none;
  border-radius: 8px;
  background: #1a73e8;
  color: white;
  cursor: pointer;
}

.date-bar button:hover {
  background: #1558b0;
}

.content {
  display: flex;
  gap: 1.5rem;
  align-items: start;
}

.filter-panel {
  width: 220px;
  flex-shrink: 0;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1.25rem;
}

.filter-title {
  font-weight: bold;
  font-size: 0.9rem;
}

.filter-group select,
.filter-group input[type='number'] {
  padding: 0.4rem;
}

.results {
  flex: 1;
}

.error {
  color: #d33;
}

.vehicle-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.vehicle-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.vehicle-image {
  aspect-ratio: 16 / 9;
  background: #f2f2f2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vehicle-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.vehicle-image-placeholder {
  font-size: 2.5rem;
  opacity: 0.4;
}

.vehicle-info {
  padding: 1rem;
}

.badges {
  display: flex;
  gap: 0.5rem;
}

.badge {
  background: #f2f2f2;
  border-radius: 4px;
  padding: 0.15rem 0.5rem;
  font-size: 0.85rem;
}

.details {
  color: #666;
  font-size: 0.85rem;
}

.price {
  font-weight: bold;
}

.location {
  color: #666;
  font-size: 0.9rem;
}

.reserve-button {
  margin-top: 0.75rem;
  width: 100%;
  padding: 0.6rem;
  font-size: 0.95rem;
  font-weight: bold;
  border: none;
  border-radius: 6px;
  background: #1a73e8;
  color: white;
  cursor: pointer;
}

.reserve-button:hover {
  background: #1558b0;
}

.reserve-button:disabled {
  background: #9bb8e0;
  cursor: default;
}

.success {
  color: #1a8c3f;
  font-size: 0.85rem;
}

.pagination {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}
</style>