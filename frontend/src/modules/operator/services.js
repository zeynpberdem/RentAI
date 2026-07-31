// Bakım/servis/yıkama talepleri ve teslim/iade ile ilgili tüm backend
// istekleri burada toplanıyor.
import apiClient from '../../api/client'

export function fetchServiceRequests(params = {}) {
  return apiClient.get('/service-requests', { params })
}

export function createServiceRequest(payload) {
  return apiClient.post('/service-requests', payload)
}

export function updateServiceRequest(id, payload) {
  return apiClient.patch(`/service-requests/${id}`, payload)
}

export function createHandover(payload) {
  return apiClient.post('/handovers', payload)
}

// Teslimat Listesi: params örn. { page, type: 'delivery' }
export function fetchHandovers(params = {}) {
  return apiClient.get('/handovers', { params })
}
