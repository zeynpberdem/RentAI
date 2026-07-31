<template>
  <div class="line-chart">
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" class="chart-svg" :style="{ height: `${height}px` }">
      <defs>
        <linearGradient id="revenue-area" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--color-primary)" stop-opacity="0.3" />
          <stop offset="100%" stop-color="var(--color-primary)" stop-opacity="0" />
        </linearGradient>
      </defs>

      <line x1="0" y1="99" x2="100" y2="99" stroke="var(--color-border)" stroke-width="0.4" />

      <path :d="areaPath" fill="url(#revenue-area)" class="chart-area" />
      <path
        :d="linePath"
        fill="none"
        stroke="var(--color-primary)"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
        vector-effect="non-scaling-stroke"
        class="chart-line"
      />

      <circle
        v-for="(point, index) in points"
        :key="index"
        :cx="point.x"
        :cy="point.y"
        r="1.3"
        fill="var(--color-surface)"
        stroke="var(--color-primary)"
        stroke-width="0.9"
        vector-effect="non-scaling-stroke"
      >
        <title>{{ point.label }}: {{ formatPrice(point.value) }} TL</title>
      </circle>
    </svg>

    <div class="chart-labels">
      <span v-for="(item, index) in data" :key="index">{{ item.ay }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] }, // [{ ay: 'Oca', gelir: 1234 }, ...]
  height: { type: Number, default: 180 },
})

const priceFormatter = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 })
function formatPrice(value) {
  return priceFormatter.format(value)
}

const PAD_TOP = 12
const PAD_BOTTOM = 8

const maxValue = computed(() => Math.max(...props.data.map((d) => d.gelir ?? 0), 1))

const points = computed(() => {
  const n = props.data.length
  const step = n > 1 ? 100 / (n - 1) : 0
  return props.data.map((d, i) => {
    const value = d.gelir ?? 0
    const ratio = maxValue.value ? value / maxValue.value : 0
    return {
      x: n > 1 ? i * step : 50,
      y: 100 - PAD_BOTTOM - ratio * (100 - PAD_TOP - PAD_BOTTOM),
      value,
      label: d.ay,
    }
  })
})

// Catmull-Rom -> kübik Bezier: noktalar arasında düz kırık çizgi yerine
// yumuşak/eğrisel bir hat üretir.
const linePath = computed(() => {
  const pts = points.value
  if (!pts.length) return ''
  if (pts.length === 1) return `M ${pts[0].x} ${pts[0].y}`

  let d = `M ${pts[0].x} ${pts[0].y}`
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i]
    const p1 = pts[i]
    const p2 = pts[i + 1]
    const p3 = pts[i + 2] || p2
    const cp1x = p1.x + (p2.x - p0.x) / 6
    const cp1y = p1.y + (p2.y - p0.y) / 6
    const cp2x = p2.x - (p3.x - p1.x) / 6
    const cp2y = p2.y - (p3.y - p1.y) / 6
    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`
  }
  return d
})

const areaPath = computed(() => {
  const pts = points.value
  if (!pts.length) return ''
  const last = pts[pts.length - 1]
  const first = pts[0]
  return `${linePath.value} L ${last.x} 100 L ${first.x} 100 Z`
})
</script>

<style scoped>
.line-chart {
  width: 100%;
}

.chart-svg {
  width: 100%;
  display: block;
}

.chart-area {
  animation: chart-fade 0.6s ease both;
}

.chart-line {
  stroke-dasharray: 400;
  stroke-dashoffset: 400;
  animation: chart-draw 0.9s cubic-bezier(0.34, 1, 0.64, 1) both;
}

.chart-labels {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 0.15rem;
  margin-top: 0.5rem;
  text-align: center;
}

.chart-labels span {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-muted);
}

@keyframes chart-draw {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes chart-fade {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
