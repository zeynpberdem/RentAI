<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import apiClient from '../api/client'

const email = ref('')
const password = ref('')
const phone = ref('')
const errorMessage = ref('')
const isLoading = ref(false)

const authStore = useAuthStore()
const router = useRouter()

async function handleSubmit() {
  errorMessage.value = ''
  isLoading.value = true

  try {
    // 1) Hesabı oluştur
    await apiClient.post('/auth/register', {
      email: email.value,
      password: password.value,
      phone: phone.value,
    })
    // 2) Aynı bilgilerle otomatik giriş yap (kullanıcı ikinci kez
    // email/şifre girmek zorunda kalmasın diye).
    await authStore.login(email.value, password.value)
    router.push('/')
  } catch (error) {
    if (error.response && error.response.status === 400) {
      // Backend'in doğrulama hataları (örn. "bu email zaten kayıtlı",
      // "şifre çok zayıf") — ilk hatayı kullanıcıya gösteriyoruz.
      const data = error.response.data
      const firstError = Object.values(data)[0]
      errorMessage.value = Array.isArray(firstError) ? firstError[0] : String(firstError)
    } else {
      errorMessage.value = 'Kayıt oluşturulamadı, lütfen tekrar deneyin.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="register-page">
    <form class="register-form" @submit.prevent="handleSubmit">
      <h1>Kayıt Ol</h1>

      <label for="email">Email</label>
      <input id="email" v-model="email" type="email" required autocomplete="username" />

      <label for="password">Şifre</label>
      <input id="password" v-model="password" type="password" required autocomplete="new-password" />

      <label for="phone">Telefon (opsiyonel)</label>
      <input id="phone" v-model="phone" type="tel" autocomplete="tel" />

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

      <button type="submit" :disabled="isLoading">
        {{ isLoading ? 'Kayıt olunuyor...' : 'Kayıt Ol' }}
      </button>

      <router-link to="/login" class="link">Zaten hesabın var mı? Giriş yap</router-link>
    </form>
  </div>
</template>

<style scoped>
.register-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
  max-width: 320px;
  padding: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.error {
  color: #d33;
  font-size: 0.9rem;
}

button {
  margin-top: 1rem;
  padding: 0.6rem;
  cursor: pointer;
}

.link {
  margin-top: 0.75rem;
  font-size: 0.9rem;
  text-align: center;
}
</style>