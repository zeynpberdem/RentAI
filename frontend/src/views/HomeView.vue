<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="home-page">
    <h1>Giriş başarılı</h1>
    <p>Token'ların tarayıcının kalıcı hafızasında (localStorage) saklandı.</p>
    <button @click="handleLogout">Çıkış Yap</button>
  </div>
</template>

<style scoped>
.home-page {
  max-width: 480px;
  margin: 4rem auto;
  text-align: center;
}

button {
  padding: 0.6rem 1rem;
  cursor: pointer;
}
</style>
