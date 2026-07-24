// Backend ile konuşan ortak axios nesnesi. Her yerde bunu import edip
// kullanacağız, tekrar tekrar "baseURL nedir" yazmamıza gerek kalmasın diye.
import axios from 'axios'

// VITE_API_BASE_URL "http://localhost:8000/api" gibi — sondaki "/api"'yi
// atınca backend'in kök adresi kalır. Admin girişinde Django admin paneline
// (backend/admin/) yönlendirirken kullanılıyor (bkz. router/index.js).
export const backendOrigin = import.meta.env.VITE_API_BASE_URL.replace(/\/api\/?$/, '')

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  // axios varsayılan olarak diziyi transmission[]=manual şeklinde gönderir;
  // backend'deki (django-filter) MultipleChoiceFilter ise köşeli parantezsiz,
  // tekrar eden anahtarlarla (transmission=manual&transmission=automatic)
  // bekliyor. indexes: null bu formatı üretiyor.
  paramsSerializer: { indexes: null },
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
