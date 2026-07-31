// Auth ile ilgili tüm backend istekleri burada toplanıyor — component'ler
// (LoginView) ve store, apiClient'ı doğrudan çağırmak yerine bu
// fonksiyonları import edip kullanıyor.
import apiClient from '../../api/client'

export function login(email, password) {
  return apiClient.post('/auth/login', { email, password })
}

// Operatörün, rezervasyon açarken seçtiği müşteri (sürücü) listesi —
// backend'de sayfalı (bkz. core.pagination.DefaultPagination); Sürücüler
// ekranı page/search/profile_status parametreleriyle çağırır.
export function fetchDrivers(params = {}) {
  return apiClient.get('/auth/drivers', { params })
}

// Analiz ekranı gibi TÜM sürücülere ihtiyaç duyan yerler için — Araçlar'daki
// fetchAllVehicles ile aynı desen (page_size:500 ile pratikte "hepsi").
export function fetchAllDrivers() {
  return apiClient.get('/auth/drivers', { params: { page_size: 500 } })
}

// Sürücü şifresiz açılır — kendi hesabıyla hiç giriş yapmayacak, kaydını
// operatör oluşturur/düzenler (bkz. backend DriverCreateSerializer notu).
export function createDriver(payload) {
  return apiClient.post('/auth/drivers', payload)
}

export function updateDriver(driverId, payload) {
  return apiClient.patch(`/auth/drivers/${driverId}`, payload)
}

export function deleteDriver(driverId) {
  return apiClient.delete(`/auth/drivers/${driverId}`)
}

// Ayarlar > Hesabım: giriş yapmış kullanıcının kendi bilgileri.
export function fetchMe() {
  return apiClient.get('/auth/me')
}

// Ayarlar > Personel: diğer operatör hesapları.
export function fetchStaff() {
  return apiClient.get('/auth/staff')
}

export function createStaff(payload) {
  return apiClient.post('/auth/staff', payload)
}
