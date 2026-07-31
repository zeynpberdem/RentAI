import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

// Geniş tablolar (.panel-card, overflow-x:auto) için: yatay kaydırma çubuğu
// hep en altta, uzun sayfalarda ekranın en altına inmeden erişilemiyordu.
// Bunun yerine, tablonun üzerindeyken normal fare tekerleği (dikey scroll)
// tabloyu YATAY kaydırır — sayfanın herhangi bir yerinde, aşağı inmeden.
document.addEventListener(
  'wheel',
  (event) => {
    const panelCard = event.target.closest('.panel-card')
    if (!panelCard) return
    if (panelCard.scrollWidth <= panelCard.clientWidth) return
    if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return

    event.preventDefault()
    panelCard.scrollLeft += event.deltaY
  },
  { passive: false }
)
