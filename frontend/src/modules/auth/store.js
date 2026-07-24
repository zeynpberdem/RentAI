// Giriş yapan kullanıcının token'larını burada tutuyoruz. Pinia, Vue'nun
// "birden fazla component'in aynı veriyi paylaşması" ihtiyacına cevap veren
// state yönetim aracı — örn. hem giriş ekranı hem menü çubuğu, aynı anda
// "kullanıcı giriş yapmış mı" bilgisine ihtiyaç duyar.
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '../../api/client'

// JWT'nin ortadaki bölümü (payload), base64url ile kodlanmış bir JSON'dur.
// Backend, login sırasında bu payload'ın içine "role" ve "user_id" koyuyor
// (bkz. RoleTokenObtainPairSerializer) — burada onu çözüp okuyoruz, ekstra
// bir "/me" isteği atmaya gerek kalmadan.
function decodeToken(token) {
  if (!token) return null
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(atob(base64))
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  // localStorage'dan okuyarak başlıyoruz: sayfa yenilense (F5) bile
  // kullanıcı çıkış yapmış gibi görünmesin diye.
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => Boolean(accessToken.value))
  const userId = computed(() => decodeToken(accessToken.value)?.user_id ?? null)
  const role = computed(() => decodeToken(accessToken.value)?.role ?? null)
  const isOperator = computed(() => role.value === 'operator')

  async function login(email, password) {
    const response = await apiClient.post('/auth/login', { email, password })

    accessToken.value = response.data.access
    refreshToken.value = response.data.refresh

    localStorage.setItem('access_token', accessToken.value)
    localStorage.setItem('refresh_token', refreshToken.value)
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return { accessToken, refreshToken, isAuthenticated, userId, role, isOperator, login, logout }
})
