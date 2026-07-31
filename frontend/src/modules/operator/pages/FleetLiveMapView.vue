<template>
  <div class="fleet-page">
    <div class="page-header">
      <h1>Canlı Takip</h1>
    </div>
    <p class="intro">
      Not: Bu, gerçek GPS/canlı konum değil — her araç, bağlı olduğu şubenin konumunda gösterilir.
    </p>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <div ref="mapContainer" class="map-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'
import { fetchLocations, fetchAllVehicles } from '../../vehicles/services'

// Leaflet'in varsayılan marker ikonu, bundler'lar (Vite) altında yol
// çözümlemesi bozulduğu için elle tanımlanması gerekiyor — bilinen bir
// Leaflet+Webpack/Vite uyum sorunu.
const defaultIcon = L.icon({
  iconUrl,
  iconRetinaUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

const mapContainer = ref(null)
const errorMessage = ref('')
let map = null

const statusLabels = { available: 'Müsait', rented: 'Kirada', maintenance: 'Bakımda' }

async function loadMap() {
  try {
    const [locationsResponse, vehiclesResponse] = await Promise.all([
      fetchLocations(),
      fetchAllVehicles(),
    ])
    const locations = locationsResponse.data
    const vehicles = vehiclesResponse.data.results

    map = L.map(mapContainer.value).setView([39.9, 32.85], 6)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap',
    }).addTo(map)

    const bounds = []
    for (const location of locations) {
      if (location.latitude == null || location.longitude == null) continue
      const vehiclesHere = vehicles.filter((vehicle) => vehicle.location.id === location.id)
      const listHtml = vehiclesHere
        .map((vehicle) => `${vehicle.plate} — ${vehicle.brand} ${vehicle.model} (${statusLabels[vehicle.status]})`)
        .join('<br />')

      const marker = L.marker([location.latitude, location.longitude], { icon: defaultIcon }).addTo(map)
      marker.bindPopup(`<strong>${location.name}</strong><br />${listHtml || 'Bu şubede araç yok.'}`)
      bounds.push([location.latitude, location.longitude])
    }

    if (bounds.length) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 })
    }
  } catch (error) {
    errorMessage.value = 'Harita verisi yüklenemedi.'
  }
}

onMounted(loadMap)
onBeforeUnmount(() => {
  if (map) map.remove()
})
</script>

<style scoped>
.intro {
  color: var(--color-muted);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.map-container {
  height: 500px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
</style>
