<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-card" :style="{ maxWidth: maxWidth }">
        <div class="modal-header">
          <h2>{{ title }}</h2>
          <button type="button" class="modal-close" title="Kapat" @click="$emit('close')">
            <svg viewBox="0 0 24 24" class="modal-close-icon" v-html="ICONS.close"></svg>
          </button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ICONS } from '../icons'

defineProps({
  title: { type: String, default: '' },
  // Form alanları büyüdükçe (Ziraat Filo'daki gibi) sayfanın ortasına
  // taşınan bu kart, sayfanın içeriğini aşağı itmeden büyüyebilsin diye
  // genişliği ayarlanabilir — varsayılan çoğu form için yeterli.
  maxWidth: { type: String, default: '640px' },
})
defineEmits(['close'])
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(2px);
  padding: 1.5rem;
  animation: modal-fade-in 150ms ease-out;
}

.modal-card {
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  animation: modal-scale-in 200ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  background: var(--color-surface);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.modal-header h2 {
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  padding: 0;
  border: none;
  background: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-muted);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.modal-close:hover {
  background: var(--color-bg);
  color: var(--color-foreground);
}

.modal-close-icon {
  width: 18px;
  height: 18px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
}

.modal-body {
  padding: 1.5rem;
}

@keyframes modal-fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes modal-scale-in {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(8px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>
