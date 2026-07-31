<template>
  <div class="login-page">
    <section class="brand-panel">
      <div class="brand-mark">RA</div>
      <h1>RentAI</h1>
      <p class="tagline">Filo Yönetimi</p>
      <p class="brand-desc">Araçlarınızı, sürücülerinizi ve rezervasyonlarınızı tek panelden yönetin.</p>
    </section>

    <section class="form-panel">
      <form class="login-form" @submit.prevent="handleSubmit">
        <h2>Giriş Yap</h2>
        <p class="form-hint">Devam etmek için hesap bilgilerinizi girin.</p>

        <label for="email">E-Posta</label>
        <input id="email" v-model="email" type="email" required autocomplete="username" />

        <label for="password">Şifre</label>
        <input id="password" v-model="password" type="password" required autocomplete="current-password" />

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <button type="submit" :disabled="isLoading">
          {{ isLoading ? 'Giriş yapılıyor...' : 'Giriş Yap' }}
        </button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { backendOrigin } from '../../../api/client'
import { useAuthStore } from '../store'

const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const authStore = useAuthStore()
const router = useRouter()

async function handleSubmit() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    await authStore.login(email.value, password.value)

    // Site artık sadece personel için — müşteri kendi hesabıyla giriş
    // yapmıyor (bkz. DriverCreateSerializer: sürücü hesapları şifresiz
    // açılıyor). Admin, Vue tarafında hiç ekranı olmadığı için doğrudan
    // Django admin paneline çıkar.
    if (authStore.role === 'admin') {
      window.location.href = `${backendOrigin}/admin/`
    } else if (authStore.role === 'operator') {
      router.push('/operator')
    } else {
      authStore.logout()
      errorMessage.value = 'Bu hesapla panele giriş yapılamaz.'
    }
  } catch (error) {
    // 401: backend "email/şifre yanlış" dediğinde döner (bkz. SimpleJWT).
    if (error.response && error.response.status === 401) {
      errorMessage.value = 'Email veya şifre hatalı.'
    } else {
      errorMessage.value = 'Giriş yapılamadı, lütfen tekrar deneyin.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  min-height: 100vh;
}

.brand-panel {
  flex: 1;
  display: none;
  flex-direction: column;
  justify-content: center;
  padding: 4rem;
  background: linear-gradient(155deg, #0f172a 0%, var(--color-primary-hover) 100%);
  color: white;
}

.brand-mark {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
}

.brand-panel h1 {
  color: white;
  font-size: 2.25rem;
  margin-bottom: 0.35rem;
}

.tagline {
  color: rgba(255, 255, 255, 0.75);
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.brand-desc {
  color: rgba(255, 255, 255, 0.6);
  max-width: 320px;
  line-height: 1.6;
}

.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--color-surface);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  width: 100%;
  max-width: 340px;
}

.login-form h2 {
  font-size: 1.4rem;
  margin-bottom: 0.25rem;
}

.form-hint {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

label {
  font-weight: 600;
  color: var(--color-foreground);
  margin-top: 0.5rem;
}

.error {
  margin-top: 0.5rem;
}

button {
  margin-top: 1.5rem;
  padding: 0.75rem;
  font-size: 0.95rem;
}

@media (min-width: 900px) {
  .brand-panel {
    display: flex;
  }
}
</style>
