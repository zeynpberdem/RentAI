// Backend ile konuşan ortak axios nesnesi. Her yerde bunu import edip
// kullanacağız, tekrar tekrar "baseURL nedir" yazmamıza gerek kalmasın diye.
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
})

// İstek gönderilmeden hemen önce çalışır: localStorage'da bir access token
// varsa, isteğin Authorization header'ına otomatik ekler. Böylece her
// çağrıda elle token eklemek zorunda kalmayız.
apiClient.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem('access_token')
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

export default apiClient
