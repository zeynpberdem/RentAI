<script setup>
import { useAuthStore } from '../modules/auth/store'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="app-header">
    <router-link to="/" class="brand">RentAI</router-link>
    <nav>
      <template v-if="authStore.isAuthenticated">
        <router-link v-if="authStore.isOperator" to="/operator">Operatör Paneli</router-link>
        <router-link v-else to="/rezervasyonlarim">Rezervasyonlarım</router-link>
        <button @click="handleLogout">Çıkış Yap</button>
      </template>
      <template v-else>
        <router-link to="/login">Giriş Yap</router-link>
        <router-link to="/register">Kayıt Ol</router-link>
      </template>
    </nav>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #ddd;
}

.brand {
  font-weight: bold;
  text-decoration: none;
  color: inherit;
}

nav {
  display: flex;
  gap: 1rem;
  align-items: center;
}

button {
  cursor: pointer;
  padding: 0.4rem 0.8rem;
}
</style>