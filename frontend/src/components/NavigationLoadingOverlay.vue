<template>
  <Teleport to="body">
    <div class="nav-overlay">
      <div class="nav-overlay-backdrop"></div>
      <div class="nav-overlay-card">
        <div class="nav-spinner"></div>
        <p class="nav-title">{{ title }}</p>
        <p class="nav-subtitle">{{ subtitle }}</p>
        <div class="nav-progress">
          <div class="nav-progress-bar"></div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'Yükleniyor' },
  subtitle: { type: String, default: 'Sayfa hazırlanıyor…' },
})
</script>

<style scoped>
.nav-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: overlay-in 200ms ease-out;
}

.nav-overlay-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
}

.nav-overlay-card {
  position: relative;
  width: 100%;
  max-width: 320px;
  margin: 0 1rem;
  padding: 2rem;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  animation: card-in 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.nav-spinner {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  margin-bottom: 1.25rem;
  animation: spin 0.8s linear infinite;
}

.nav-title {
  font-weight: 700;
  color: var(--color-foreground);
  margin: 0;
}

.nav-subtitle {
  color: var(--color-muted);
  font-size: 0.85rem;
  margin: 0.25rem 0 0;
}

.nav-progress {
  width: 100%;
  height: 4px;
  border-radius: 999px;
  background: var(--color-border);
  overflow: hidden;
  margin-top: 1.25rem;
}

.nav-progress-bar {
  height: 100%;
  background: var(--color-primary);
  transform-origin: left;
  transform: scaleX(0);
  animation: progress 900ms ease-in-out forwards;
}

@keyframes overlay-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes progress {
  to {
    transform: scaleX(1);
  }
}
</style>
