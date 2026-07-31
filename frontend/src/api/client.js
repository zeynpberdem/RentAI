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

// Access token 60 dakikada bir doluyor (bkz. SimpleJWT ayarları, config/settings.py).
// Süresi dolunca backend 401 döner; bunu yakalayıp refresh_token ile sessizce
// yeni bir access token alıp isteği bir kere daha deniyoruz. Bu olmadan
// kullanıcı "giriş yapmış" görünen ama her isteği 401 alan kırık bir ekranda
// kalıyordu (örn. Analiz sayfasındaki "veriler yüklenemedi" hatası).
let refreshPromise = null

async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) throw new Error('Refresh token yok.')

  const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/refresh`, {
    refresh: refreshToken,
  })
  localStorage.setItem('access_token', response.data.access)
  // ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION açık (bkz. SIMPLE_JWT
  // ayarları): her refresh'te backend eski refresh_token'ı geçersiz kılıp
  // yenisini döner. Bunu da kaydetmezsek bir sonraki 60 dakikada elimizde
  // artık kullanılamayan (kara listeye alınmış) bir refresh_token kalır.
  if (response.data.refresh) {
    localStorage.setItem('refresh_token', response.data.refresh)
  }
  return response.data.access
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const isAuthEndpoint = originalRequest?.url?.includes('/auth/login') || originalRequest?.url?.includes('/auth/refresh')

    if (error.response?.status !== 401 || originalRequest._retried || isAuthEndpoint) {
      return Promise.reject(error)
    }

    originalRequest._retried = true
    try {
      // Aynı anda birden fazla istek 401 alırsa (ör. Promise.all ile paralel
      // çağrılar), refresh uç noktasına tek seferde gidilsin diye promise'i paylaşıyoruz.
      refreshPromise = refreshPromise || refreshAccessToken()
      const newAccessToken = await refreshPromise
      refreshPromise = null
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
      return apiClient(originalRequest)
    } catch {
      refreshPromise = null
      // refresh_token da geçersizse oturum gerçekten bitmiştir — girişe yolla.
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      return Promise.reject(error)
    }
  }
)

export default apiClient
