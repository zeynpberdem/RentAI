<template>
  <div class="fleet-layout">
    <FleetSidebar />
    <main class="fleet-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import FleetSidebar from '../components/FleetSidebar.vue'
</script>

<style scoped>
.fleet-layout {
  display: flex;
  min-height: 100vh;
}

.fleet-content {
  flex: 1;
  padding: 2rem 2.5rem 2.5rem 1.5rem;
  background: var(--color-bg);
  min-width: 0;
}
</style>
