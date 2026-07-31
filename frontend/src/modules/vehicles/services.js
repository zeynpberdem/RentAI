// Araçlar/şubeler ile ilgili tüm backend istekleri burada toplanıyor.
import apiClient from '../../api/client'

// Dropdown/toplulaştırma kullanımları (rezervasyon formu, takvim, analiz vb.)
// TÜM araçlara ihtiyaç duyar — varsayılan 20'lik sayfalamayı page_size ile aşıyoruz.
export function fetchAllVehicles() {
  return apiClient.get('/vehicles', { params: { page_size: 500 } })
}

// Araçlar listesi sayfası: gerçek sayfalama + sütun filtreleri + arama.
// params örn. { page, search, segment, transmission, fuel, location, status }
export function fetchVehiclesPage(params) {
  return apiClient.get('/vehicles', { params })
}

export function fetchLocations() {
  return apiClient.get('/locations')
}

// Rezervasyon Takvimi ekranı: her araç, verilen tarih aralığıyla kesişen
// rezervasyonlarıyla birlikte TEK istekte gelir (backend'de prefetch ile
// join edilmiş) — ayrıca /reservations çekip client'ta eşleştirmeye gerek yok.
export function fetchVehiclesCalendar(params) {
  return apiClient.get('/vehicles/calendar', { params: { page_size: 500, ...params } })
}

// Bir yanlışlık olursa düzeltmek için — operatör de artık araç
// düzenleyip (soft-)silebiliyor, bkz. backend VehicleViewSet.get_permissions.
export function updateVehicle(id, payload) {
  return apiClient.patch(`/vehicles/${id}`, payload)
}

export function deleteVehicle(id) {
  return apiClient.delete(`/vehicles/${id}`)
}
