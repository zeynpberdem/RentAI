<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
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
    router.push('/')
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

<template>
  <div class="login-page">
    <form class="login-form" @submit.prevent="handleSubmit">
      <h1>Giriş Yap</h1>

      <label for="email">Email</label>
      <input id="email" v-model="email" type="email" required autocomplete="username" />

      <label for="password">Şifre</label>
      <input id="password" v-model="password" type="password" required autocomplete="current-password" />

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

      <button type="submit" :disabled="isLoading">
        {{ isLoading ? 'Giriş yapılıyor...' : 'Giriş Yap' }}
      </button>

      <router-link to="/register" class="link">Hesabın yok mu? Kayıt ol</router-link>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.login-form {
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
