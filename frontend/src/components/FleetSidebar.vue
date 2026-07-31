<template>
  <div class="fleet-nav">
    <aside class="icon-rail">
      <button
        type="button"
        class="brand-mark"
        :class="{ active: route.path.startsWith('/operator/settings') }"
        title="Ayarlar"
        @click="goToSettings"
      >
        RA
      </button>

      <nav class="icon-list">
        <template v-for="module in modules" :key="module.id">
          <button
            v-if="module.children"
            type="button"
            class="icon-button"
            :class="{ active: activeSection === module.id }"
            :title="module.label"
            @click="openSection(module)"
          >
            <svg viewBox="0 0 24 24" class="icon" v-html="ICONS[module.icon]"></svg>
          </button>

          <router-link
            v-else
            :to="module.to"
            class="icon-button"
            :class="{ active: isPlainActive(module) }"
            :title="module.label"
            @click="activeSection = null"
          >
            <svg viewBox="0 0 24 24" class="icon" v-html="ICONS[module.icon]"></svg>
          </router-link>
        </template>
      </nav>

      <button type="button" class="icon-button logout" title="Çıkış Yap" @click="handleLogout">
        <svg viewBox="0 0 24 24" class="icon" v-html="ICONS.logout"></svg>
      </button>
    </aside>

    <!-- Rezervasyon Listesi ikonuna tıklayınca AÇILAN, kalıcı (baloncuk gibi
         kaybolmayan) ikinci bir panel — ana içeriğin yanına gerçekten
         yerleşiyor (position:absolute floating DEĞİL), tıklanan alt sayfaya
         gidiliyor ve panel açık kalıyor; sadece düz bir rail ikonuna
         (Araçlar, Sürücüler vb.) tıklanınca kapanıyor. -->
    <aside v-if="activeSectionModule" class="section-panel">
      <h2 class="section-title">{{ activeSectionModule.label }}</h2>
      <nav class="section-list">
        <router-link
          v-for="child in activeSectionModule.children"
          :key="child.id"
          :to="child.to"
          class="section-item"
          :class="{ active: isChildActive(child) }"
        >
          {{ child.label }}
        </router-link>
      </nav>
    </aside>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ICONS } from '../icons'
import { useAuthStore } from '../modules/auth/store'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

// Rezervasyon Takvimi kendi başına, DİREKT gidilen bağımsız bir ikon.
// Rezervasyon Listesi ise gruplu: tıklanınca yanda, altında zaten var olan
// verilerle (durum/tip filtresi) veya yeni eklenen Teslimat Listesi gibi
// alt ekranlarla dolu küçük bir menü açılıyor.
const modules = [
  { id: 'analiz', icon: 'chart', label: 'Analiz', to: '/operator/analytics' },
  { id: 'araclar', icon: 'car', label: 'Araçlar', to: '/operator/vehicles' },
  { id: 'surucular', icon: 'user', label: 'Sürücüler', to: '/operator/drivers' },
  {
    id: 'rezervasyon-listesi-grup',
    icon: 'list',
    label: 'Rezervasyon Listesi',
    children: [
      { id: 'tum-rezervasyonlar', label: 'Tüm Rezervasyonlar', to: '/operator/reservations' },
      { id: 'kurumsal-kisa-donem', label: 'Kurumsal Kısa Dönem', to: '/operator/reservations?type=corporate' },
      { id: 'teslim-bekleyenler', label: 'Teslim Bekleyen Rezervasyonlar', to: '/operator/reservations?status=2' },
      { id: 'kiradaki-araclar', label: 'Kiradaki Araç Listesi', to: '/operator/vehicles?status=rented' },
      { id: 'musait-araclar', label: 'Müsait Araç Listesi', to: '/operator/vehicles?status=available' },
      { id: 'iptal-edilenler', label: 'İptal Edilen Rezervasyonlar', to: '/operator/reservations?status=99' },
      { id: 'teslimat-listesi', label: 'Teslimat Listesi', to: '/operator/handovers' },
      { id: 'iade-alinacak', label: 'İade Alınacak Listesi', to: '/operator/reservations?status=3&ordering=end_date' },
    ],
  },
  { id: 'rezervasyon-takvimi', icon: 'calendar', label: 'Rezervasyon Takvimi', to: '/operator/reservation-calendar' },
  { id: 'bakim', icon: 'wrench', label: 'Bakım Merkezi', to: '/operator/maintenance' },
  { id: 'canli-takip', icon: 'map-pin', label: 'Canlı Takip', to: '/operator/live-tracking' },
]

// Hangi grubun paneli açık — sadece bir tanesi bir anda açık olabilir,
// düz bir rail ikonuna (Araçlar, Sürücüler vb.) tıklanınca kapanır.
const activeSection = ref(null)

const activeSectionModule = computed(() => modules.find((m) => m.id === activeSection.value) || null)

function openSection(module) {
  activeSection.value = module.id
  router.push(module.children[0].to)
}

// Düz (gruplu olmayan) bir rail ikonu, SADECE hiçbir bölüm paneli açık
// değilken kendi path'indeyse aktif sayılır. Bu kontrol olmadan, ör.
// "Kiradaki Araç Listesi" (grup içinden /operator/vehicles'a giden bir
// bağlantı) tıklandığında Vue Router'ın active-class'ı path eşleşmesine
// bakıp query'yi görmezden geldiği için Araçlar ikonu da yanlışlıkla
// aktif görünürdü — iki ikon aynı anda aktif gibi dururdu.
function isPlainActive(module) {
  return !activeSection.value && route.path === module.to
}

// Bir alt öğe, kendi "to"sundaki path + query ile şu an açık olan route
// birebir eşleşiyorsa aktif sayılır (sadece path yetmez — "Tüm
// Rezervasyonlar" ile "İptal Edilen Rezervasyonlar" aynı path'i
// paylaşıyor, ayıran şey query).
function isChildActive(child) {
  const [childPath, childQueryString] = child.to.split('?')
  if (route.path !== childPath) return false

  const childParams = new URLSearchParams(childQueryString || '')
  for (const [key, value] of childParams) {
    if (route.query[key] !== value) return false
  }
  // Query'siz bir bağlantı (ör. Tüm Rezervasyonlar), mevcut route'ta da
  // hiç query yoksa aktif sayılır — aksi halde filtreli bir alt öğedeyken
  // "Tüm Rezervasyonlar" da yanlışlıkla aktif görünürdü.
  if (![...childParams.keys()].length && Object.keys(route.query).length) return false
  return true
}

function goToSettings() {
  activeSection.value = null
  router.push('/operator/settings')
}

function handleLogout() {
  activeSection.value = null
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.fleet-nav {
  flex-shrink: 0;
  /* Bu sarmalayıcı, dış flex layout'ta (FleetLayout) uzun sayfalarda tüm
     içerik boyunca uzuyor — ama kendisi bir flex container OLMADIĞI için
     içindeki .icon-rail bunu miras almıyordu, sadece min-height:100vh ile
     ekran yüksekliğinde kalıp uzun sayfalarda yarıda kesiliyordu. display:flex
     ile .icon-rail'i bu sarmalayıcının tam (uzamış) yüksekliğine geriyoruz. */
  display: flex;
}

.icon-rail {
  width: 64px;
  min-height: 100vh;
  background: #0f172a;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0;
  gap: 0.35rem;
}

.brand-mark {
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: var(--color-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.8rem;
  letter-spacing: 0.02em;
  margin-bottom: 1rem;
  flex-shrink: 0;
  cursor: pointer;
  transition: box-shadow 150ms ease;
}

.brand-mark.active {
  box-shadow: 0 0 0 2px #0f172a, 0 0 0 4px var(--color-primary);
}

.icon-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.icon-button {
  width: 42px;
  height: 42px;
  padding: 0;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: rgba(255, 255, 255, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 150ms ease, color 150ms ease;
}

.icon-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.icon-button.active {
  background: var(--color-primary);
  color: white;
}

.icon {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
}

.icon-button.logout {
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

/* Kalıcı ikinci panel — icon-rail'in hemen yanına, normal flex akışının
   İÇİNDE oturuyor (position:absolute floating değil), bu yüzden ana
   içeriği gerçekten kenara iter; bir "tooltip/baloncuk" gibi belirip
   kaybolmuyor, ilgili bölümdeyken (ya da bir alt öğesine tıklanana kadar)
   açık kalıyor. */
.section-panel {
  width: 180px;
  min-height: 100vh;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: 1.1rem 0.65rem;
}

.section-title {
  margin: 0 0 0.75rem;
  padding: 0 0.35rem;
  font-size: 0.82rem;
  font-weight: 800;
  color: var(--color-foreground);
}

.section-list {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.section-item {
  padding: 0.45rem 0.6rem;
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  font-size: 0.78rem;
  font-weight: 600;
  text-decoration: none;
  transition: background-color 150ms ease, color 150ms ease;
}

.section-item:hover {
  background: var(--color-bg);
  color: var(--color-foreground);
}

.section-item.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
</style>
