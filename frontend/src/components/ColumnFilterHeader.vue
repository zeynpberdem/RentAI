<template>
  <th class="filterable-th">
    <div class="th-inner">
      {{ label }}
      <button type="button" class="th-filter-btn" :class="{ active: modelValue }" @click.stop="open = !open">
        <svg viewBox="0 0 24 24" class="th-filter-icon" v-html="ICONS.filter"></svg>
      </button>
    </div>

    <div v-if="open" class="th-filter-backdrop" @click="open = false"></div>
    <div v-if="open" class="th-filter-dropdown">
      <button type="button" class="th-filter-option" :class="{ active: !modelValue }" @click="select('')">
        {{ allLabel }}
      </button>
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        class="th-filter-option"
        :class="{ active: modelValue === option.value }"
        @click="select(option.value)"
      >
        {{ option.label }}
      </button>
    </div>
  </th>
</template>

<script setup>
import { ref } from 'vue'
import { ICONS } from '../icons'

defineProps({
  label: { type: String, required: true },
  options: { type: Array, required: true }, // [{ value, label }]
  modelValue: { type: [String, Number], default: '' },
  allLabel: { type: String, default: 'Tümü' },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)

function select(value) {
  emit('update:modelValue', value)
  open.value = false
}
</script>

<style scoped>
.filterable-th {
  position: relative;
}

.th-inner {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.th-filter-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  background: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-muted);
  cursor: pointer;
  border-radius: 4px;
}

.th-filter-btn:hover {
  background: var(--color-bg);
  color: var(--color-primary);
}

.th-filter-btn.active {
  color: var(--color-primary);
}

.th-filter-icon {
  width: 13px;
  height: 13px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
}

.th-filter-backdrop {
  position: fixed;
  inset: 0;
  z-index: 25;
}

.th-filter-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 0.35rem;
  min-width: 160px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: 0.35rem;
  z-index: 30;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  text-transform: none;
  letter-spacing: normal;
  font-weight: 500;
}

.th-filter-option {
  text-align: left;
  padding: 0.45rem 0.6rem;
  border: none;
  background: none;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  color: var(--color-foreground);
  cursor: pointer;
}

.th-filter-option:hover {
  background: var(--color-bg);
}

.th-filter-option.active {
  background: var(--color-primary-soft);
  color: var(--color-primary-hover);
  font-weight: 700;
}
</style>
