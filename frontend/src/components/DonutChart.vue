<template>
  <svg :viewBox="`0 0 ${size} ${size}`" :width="size" :height="size" class="donut-chart">
    <g class="donut-rotate" :style="{ transformOrigin: `${size / 2}px ${size / 2}px` }">
      <circle :cx="size / 2" :cy="size / 2" :r="radius" fill="none" stroke="var(--color-border)" :stroke-width="strokeWidth" />
      <circle
        v-for="segment in segmentsWithOffset"
        :key="segment.id"
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="segment.color"
        :stroke-width="strokeWidth"
        stroke-linecap="butt"
        :stroke-dasharray="`${segment.dash} ${circumference - segment.dash}`"
        :stroke-dashoffset="segment.offset"
        class="donut-segment"
      >
        <title>{{ segment.label }}: {{ segment.count }}</title>
      </circle>
    </g>
    <text :x="size / 2" :y="size / 2 - 6" text-anchor="middle" class="donut-value">{{ centerValue }}</text>
    <text v-if="centerSub" :x="size / 2" :y="size / 2 + 16" text-anchor="middle" class="donut-sub">{{ centerSub }}</text>
  </svg>
</template>

<script setup>
import { computed } from 'vue'

// segments: [{ id, label, count, percent (0-100), color }]
const props = defineProps({
  segments: { type: Array, required: true },
  size: { type: Number, default: 168 },
  strokeWidth: { type: Number, default: 24 },
  centerValue: { type: [String, Number], default: '' },
  centerSub: { type: String, default: '' },
})

const radius = computed(() => props.size / 2 - props.strokeWidth / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)

const segmentsWithOffset = computed(() => {
  let cumulativePercent = 0
  return props.segments.map((segment) => {
    const dash = (segment.percent / 100) * circumference.value
    const offset = circumference.value * (1 - cumulativePercent / 100)
    cumulativePercent += segment.percent
    return { ...segment, dash, offset }
  })
})
</script>

<style scoped>
.donut-rotate {
  /* SVG çemberler 3 yönünden (saat 3) başlar; -90deg ile üstten (saat 12)
     başlatıyoruz, grafiklerde alışılan görünüm bu. */
  transform: rotate(-90deg);
}

.donut-segment {
  transition: stroke-dasharray 300ms ease, stroke-dashoffset 300ms ease;
}

.donut-value {
  font-size: 1.6rem;
  font-weight: 800;
  fill: var(--color-foreground);
  font-family: var(--font-sans);
}

.donut-sub {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  fill: var(--color-muted);
  font-family: var(--font-sans);
}
</style>
