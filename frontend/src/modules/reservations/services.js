// Rezervasyonlarla ilgili tüm backend istekleri burada toplanıyor.
import apiClient from '../../api/client'

// params örn. { page, search, status, start_date_from, start_date_to, ordering }
export function fetchReservations(params = {}) {
  return apiClient.get('/reservations', { params })
}

// Rezervasyon Takvimi (araç bazlı zaman çizelgesi) görünen tüm rezervasyonlara
// tek seferde ihtiyaç duyar — varsayılan 20'lik sayfalamayı page_size ile aşıyoruz.
export function fetchAllReservationsForCalendar() {
  return apiClient.get('/reservations', { params: { page_size: 500 } })
}

// Operatörün, Sürücüler ekranından seçtiği bir müşteri adına rezervasyon
// açması — backend'de ReservationStaffCreateSerializer bunu karşılıyor.
// pickup_location/return_location boş bırakılırsa backend aracın kendi
// şubesini varsayar (bkz. ReservationCreateSerializer.create).
// Rezervasyon Listesi'ndeki "Süre Uzat" satır aksiyonu.
export function extendReservation(id, endDate) {
  return apiClient.post(`/reservations/${id}/extend`, { end_date: endDate })
}

export function createReservationForDriver({
  customer,
  vehicle,
  start_date,
  end_date,
  type,
  source,
  pickup_location,
  return_location,
}) {
  return apiClient.post('/reservations', {
    customer,
    vehicle,
    start_date,
    end_date,
    type,
    source,
    pickup_location: pickup_location || undefined,
    return_location: return_location || undefined,
  })
}
