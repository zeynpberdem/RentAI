<template>
  <div class="fleet-page">
    <div class="page-header">
      <h1>Rezervasyonlar</h1>
      <div class="header-actions">
        <input
          v-model="searchInput"
          type="search"
          placeholder="Müşteri veya plaka ara..."
          class="search-input"
          @keyup.enter="runSearch"
        />
        <button type="button" class="secondary btn-icon" @click="runSearch">
          <svg viewBox="0 0 24 24" v-html="ICONS.search"></svg>
          Ara
        </button>

        <input v-model="dateFrom" type="date" title="Başlangıç tarihi (min)" @change="onDateChange" />
        <input v-model="dateTo" type="date" title="Başlangıç tarihi (maks)" @change="onDateChange" />

        <div class="presets-wrapper">
          <button type="button" class="secondary btn-icon" @click="showPresets = !showPresets">
            <svg viewBox="0 0 24 24" v-html="ICONS.filter"></svg>
            Filtre Şablonları
          </button>
          <div v-if="showPresets" class="presets-backdrop" @click="showPresets = false"></div>
          <div v-if="showPresets" class="presets-dropdown">
            <p v-if="!savedPresets.length" class="presets-empty">Henüz kayıtlı şablon yok.</p>
            <div v-for="preset in savedPresets" :key="preset.name" class="preset-row">
              <button type="button" class="preset-apply" @click="applyPreset(preset)">{{ preset.name }}</button>
              <button type="button" class="preset-remove" title="Sil" @click="removePreset(preset.name)">
                <svg viewBox="0 0 24 24" class="preset-remove-icon" v-html="ICONS.trash"></svg>
              </button>
            </div>
            <hr />
            <button type="button" class="preset-save" @click="saveCurrentPreset">+ Şu anki filtreyi kaydet</button>
          </div>
        </div>

        <button type="button" class="secondary btn-icon" :disabled="isExporting" @click="exportCsv">
          <svg viewBox="0 0 24 24" v-html="ICONS.download"></svg>
          {{ isExporting ? 'Hazırlanıyor...' : 'Dışa Aktar' }}
        </button>

        <button type="button" class="new-button btn-icon" @click="showNewReservation = true">
          <svg viewBox="0 0 24 24" v-html="ICONS.plus"></svg>
          Yeni
        </button>
      </div>
    </div>

    <NewReservation
      v-if="showNewReservation"
      @close="showNewReservation = false"
      @created="handleReservationCreated"
    />

    <Modal v-if="historyReservation" title="Rezervasyon Geçmişi" @close="historyReservation = null">
      <p class="history-subtitle">
        {{ historyReservation.vehicle.plate }} — {{ historyReservation.customer_name }}
      </p>
      <ul class="timeline">
        <li v-for="event in historyEvents" :key="event.label" class="timeline-item">
          <span class="timeline-label">{{ event.label }}</span>
          <span class="timeline-date">{{ formatDateTime(event.date) }}</span>
        </li>
      </ul>
    </Modal>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <section class="panel-card">
      <p v-if="!reservations.length" class="empty-state">Eşleşen rezervasyon yok.</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <ColumnFilterHeader label="Rezervasyon Tipi" :options="typeOptions" v-model="typeFilter" />
            <th>Araç</th>
            <th>Araç SIPP Kodu</th>
            <th>Müşteri</th>
            <ColumnFilterHeader label="Rezervasyon Kaynağı" :options="sourceOptions" v-model="sourceFilter" />
            <th>Teslim Alma Ofisi</th>
            <th>Teslim Etme Ofisi</th>
            <th class="sortable-th" @click="toggleSort('start_date')">
              Teslim Tarihi
              <span v-if="sortField === 'start_date'" class="sort-arrow">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <th class="sortable-th" @click="toggleSort('end_date')">
              İade Tarihi
              <span v-if="sortField === 'end_date'" class="sort-arrow">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <ColumnFilterHeader label="Durum" :options="statusOptions" v-model="statusFilter" />
            <th>Tutar</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="reservation in reservations" :key="reservation.id">
            <td>{{ typeLabels[reservation.type] }}</td>
            <td>{{ reservation.vehicle.plate }} — {{ reservation.vehicle.brand }} {{ reservation.vehicle.model }}</td>
            <td>{{ reservation.vehicle.sipp_code || '—' }}</td>
            <td>{{ reservation.customer_name }}</td>
            <td><span class="source-pill">{{ sourceLabels[reservation.source] }}</span></td>
            <td>{{ reservation.pickup_location?.name ?? reservation.vehicle.location.name }}</td>
            <td>{{ reservation.return_location?.name ?? reservation.vehicle.location.name }}</td>
            <td>{{ formatDateTime(reservation.start_date) }}</td>
            <td>{{ formatDateTime(reservation.end_date) }}</td>
            <td><span class="status-badge" :class="'status-' + reservation.status">{{ statusLabels[reservation.status] }}</span></td>
            <td class="price-cell" :class="priceClass(reservation.status)">
              <span v-if="reservation.is_extended" class="price-prefix extended" title="Süresi uzatıldı">+</span>
              <span v-else-if="reservation.is_early_return" class="price-prefix early" title="Erken teslim edildi">-</span>
              {{ formatPrice(reservation.total_price) }} TL
            </td>
            <td class="row-actions">
              <button type="button" class="icon-action-button" title="Detay" @click="openHistoryModal(reservation)">
                <svg viewBox="0 0 24 24" class="row-icon" v-html="ICONS.info"></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-row">
        <span class="count-badge">{{ totalCount }} rezervasyon</span>
        <div v-if="totalPages > 1" class="pagination-controls">
          <button type="button" class="secondary" :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">‹ Önceki</button>
          <span class="page-label">Sayfa {{ currentPage }} / {{ totalPages }}</span>
          <button type="button" class="secondary" :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">Sonraki ›</button>
        </div>
      </div>
    </section>

    <section class="panel-card">
      <h2>Teslim / İade</h2>

      <form class="handover-form" @submit.prevent="submitHandover">
        <label class="full-width">
          Rezervasyon
          <select v-model="handoverForm.reservation" required>
            <option value="" disabled>Rezervasyon seç</option>
            <option v-for="reservation in handoverReservations" :key="reservation.id" :value="reservation.id">
              {{ reservationLabel(reservation) }}
            </option>
          </select>
        </label>

        <div class="radio-group">
          <label class="radio-label">
            <input type="radio" value="delivery" v-model="handoverForm.type" /> Teslim
          </label>
          <label class="radio-label">
            <input type="radio" value="return" v-model="handoverForm.type" /> İade
          </label>
        </div>

        <label>
          Kilometre
          <input v-model="handoverForm.odometer_km" type="number" min="0" required />
        </label>
        <label>
          Yakıt (%)
          <input v-model="handoverForm.fuel_level" type="number" min="0" max="100" required />
        </label>
        <label class="full-width">
          Hasar Notu (opsiyonel)
          <input v-model="handoverForm.damage_notes" type="text" />
        </label>

        <button type="submit">Kaydet</button>
      </form>
      <p v-if="handoverMessage" :class="handoverMessage.type === 'error' ? 'error' : 'success'">
        {{ handoverMessage.text }}
      </p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import ColumnFilterHeader from '../../../components/ColumnFilterHeader.vue'
import Modal from '../../../components/Modal.vue'
import { ICONS } from '../../../icons'
import {
  fetchAllReservationsForCalendar,
  fetchReservations as fetchReservationsRequest,
} from '../../reservations/services'
import NewReservation from '../components/NewReservation.vue'
import { createHandover } from '../services'

const route = useRoute()
const PAGE_SIZE = 20
const PRESETS_KEY = 'rentai_reservation_filter_presets'

const reservations = ref([])
const handoverReservations = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const errorMessage = ref('')
const isExporting = ref(false)
const showNewReservation = ref(false)

function handleReservationCreated() {
  showNewReservation.value = false
  currentPage.value = 1
  loadReservations()
}

// Arama: yazarken backend'e istek atmıyor, sadece Enter'a basılınca ya da
// "Ara" butonuna tıklanınca (Araçlar ekranındaki ile aynı desen).
const searchInput = ref('')
const appliedSearch = ref('')

// Boş string = filtre yok (Araçlar/Sürücüler'deki desenle tutarlı).
// route.query: Rezervasyon Listesi alt menüsündeki ön-filtreli bağlantılar
// (ör. "İptal Edilen Rezervasyonlar", "Kurumsal Kısa Dönem") buradan gelir.
const statusFilter = ref(route.query.status || '')
const typeFilter = ref(route.query.type || '')
const sourceFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')

// Teslim/İade Tarihi başlıklarına tıklayınca sıralama — route.query.ordering
// varsa (ör. "İade Alınacak Listesi" alt menüsünden "end_date" ile gelinmişse)
// başlangıç durumu ondan türetiliyor.
function parseOrdering(raw) {
  if (!raw) return { field: null, direction: 'asc' }
  if (raw.startsWith('-')) return { field: raw.slice(1), direction: 'desc' }
  return { field: raw, direction: 'asc' }
}
const initialOrdering = parseOrdering(route.query.ordering)
const sortField = ref(initialOrdering.field)
const sortDirection = ref(initialOrdering.direction)

function toggleSort(field) {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  currentPage.value = 1
  loadReservations()
}

// Sayfa zaten AÇIKKEN (ör. Rezervasyon Listesi sidebar alt menüsünden farklı
// bir ön-filtreli bağlantıya tıklanınca) Vue Router aynı sayfa component'ini
// YENİDEN KURMAZ, sadece route.query'yi günceller — statusFilter/typeFilter
// yukarıda sadece İLK açılışta route.query'den okunduğu için, bu durumda
// filtre hiç uygulanmadan eski (filtresiz) veri görünmeye devam ederdi.
// Bu watch, route.query her değiştiğinde filtreleri yeniden senkronlar.
watch(
  () => route.query,
  (query) => {
    statusFilter.value = query.status || ''
    typeFilter.value = query.type || ''
    const ordering = parseOrdering(query.ordering)
    sortField.value = ordering.field
    sortDirection.value = ordering.direction
    currentPage.value = 1
    loadReservations()
  }
)

const showPresets = ref(false)
const savedPresets = ref(loadPresets())

const handoverForm = ref({
  reservation: '',
  type: 'delivery',
  odometer_km: '',
  fuel_level: '',
  damage_notes: '',
})
const handoverMessage = ref(null)

// Hacer Hanım'ın sayısal durum kodları: 1=Onay Bekliyor, 2=Teslim Bekliyor,
// 3=Kirada, 4=Tamamlandı, 99=İptal Edildi (bilerek sıralı akışın dışında —
// bkz. backend reservations/helpers.py Status).
const statusLabels = {
  1: 'Onay Bekliyor',
  2: 'Teslim Bekliyor',
  3: 'Kirada',
  4: 'Tamamlandı',
  99: 'İptal Edildi',
}

const typeLabels = {
  short_term: 'Kısa Dönem',
  long_term: 'Uzun Dönem',
  corporate: 'Kurumsal',
}

const sourceLabels = {
  branch: 'Şube',
  call_center: 'Çağrı Merkezi',
  web: 'Web Sitesi',
  agency: 'Online Acenta',
}

const statusOptions = Object.entries(statusLabels).map(([value, label]) => ({ value, label }))
const typeOptions = Object.entries(typeLabels).map(([value, label]) => ({ value, label }))
const sourceOptions = Object.entries(sourceLabels).map(([value, label]) => ({ value, label }))

const priceFormatter = new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 2 })

function formatPrice(price) {
  return priceFormatter.format(Number(price))
}

// Tutar sütununda hızlı görsel ayırt etme: onay bekleyen tutarlar yeşil,
// iptal edilenler kırmızı (fiyat hâlâ görünür ama "gerçekleşmedi" hissi verir).
function priceClass(status) {
  if (status === 1) return 'price-pending'
  if (status === 99) return 'price-cancelled'
  return ''
}

const dateTimeFormatter = new Intl.DateTimeFormat('tr-TR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

function formatDateTime(value) {
  if (!value) return '—'
  return dateTimeFormatter.format(new Date(value))
}

// Rezervasyon Geçmişi: tek bir rezervasyonun yaşam döngüsü — oluşturuldu,
// (varsa) teslim edildi, (varsa) süresi uzatıldı, (varsa) iade edildi/
// tamamlandı, (varsa) iptal edildi. Hepsi gerçek zaman damgalarından
// (created_at, handovers, extended_at, cancelled_at) türetiliyor, uydurma
// bir şey yok — bkz. ReservationSerializer.
const historyReservation = ref(null)

const historyEvents = computed(() => {
  const reservation = historyReservation.value
  if (!reservation) return []

  const events = [{ label: 'Oluşturuldu', date: reservation.created_at }]

  const delivery = reservation.handovers.find((h) => h.type === 'delivery')
  if (delivery) events.push({ label: 'Teslim Edildi', date: delivery.created_at })

  if (reservation.extended_at) events.push({ label: 'Süresi Uzatıldı', date: reservation.extended_at })

  const returnHandover = reservation.handovers.find((h) => h.type === 'return')
  if (returnHandover) events.push({ label: 'İade Edildi (Tamamlandı)', date: returnHandover.created_at })

  if (reservation.cancelled_at) events.push({ label: 'İptal Edildi', date: reservation.cancelled_at })

  return events.sort((a, b) => new Date(a.date) - new Date(b.date))
})

function openHistoryModal(reservation) {
  historyReservation.value = reservation
}

const totalPages = computed(() => Math.max(Math.ceil(totalCount.value / PAGE_SIZE), 1))

function buildParams(extra = {}) {
  const params = { page: currentPage.value, ...extra }
  if (appliedSearch.value) params.search = appliedSearch.value
  if (statusFilter.value) params.status = statusFilter.value
  if (typeFilter.value) params.type = typeFilter.value
  if (sourceFilter.value) params.source = sourceFilter.value
  if (dateFrom.value) params.start_date_from = dateFrom.value
  if (dateTo.value) params.start_date_to = dateTo.value
  if (sortField.value) params.ordering = sortDirection.value === 'desc' ? `-${sortField.value}` : sortField.value
  return params
}

async function loadReservations() {
  errorMessage.value = ''
  try {
    const response = await fetchReservationsRequest(buildParams())
    reservations.value = response.data.results
    totalCount.value = response.data.count
  } catch (error) {
    errorMessage.value = 'Rezervasyonlar yüklenemedi, lütfen tekrar deneyin.'
  }
}

function runSearch() {
  appliedSearch.value = searchInput.value.trim()
  currentPage.value = 1
  loadReservations()
}

watch([statusFilter, typeFilter, sourceFilter], () => {
  currentPage.value = 1
  loadReservations()
})

function onDateChange() {
  currentPage.value = 1
  loadReservations()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadReservations()
}

// --- Filtre Şablonları: kayıtlı filtre kombinasyonları — backend/model
// gerektirmesin diye tarayıcının localStorage'ında tutuluyor (junior/staj
// ölçeğinde bir "şablon yönetimi" ekranı kurmak yerine en sade çözüm).
function loadPresets() {
  try {
    return JSON.parse(localStorage.getItem(PRESETS_KEY)) || []
  } catch {
    return []
  }
}

function persistPresets() {
  localStorage.setItem(PRESETS_KEY, JSON.stringify(savedPresets.value))
}

function saveCurrentPreset() {
  const name = window.prompt('Bu filtreye bir isim ver:')
  if (!name) return
  savedPresets.value = [
    ...savedPresets.value.filter((preset) => preset.name !== name),
    {
      name,
      status: statusFilter.value,
      type: typeFilter.value,
      source: sourceFilter.value,
      dateFrom: dateFrom.value,
      dateTo: dateTo.value,
      search: appliedSearch.value,
    },
  ]
  persistPresets()
  showPresets.value = false
}

function applyPreset(preset) {
  statusFilter.value = preset.status
  typeFilter.value = preset.type || ''
  sourceFilter.value = preset.source || ''
  dateFrom.value = preset.dateFrom
  dateTo.value = preset.dateTo
  searchInput.value = preset.search
  appliedSearch.value = preset.search
  showPresets.value = false
  currentPage.value = 1
  loadReservations()
}

function removePreset(name) {
  savedPresets.value = savedPresets.value.filter((preset) => preset.name !== name)
  persistPresets()
}

// --- Dışa Aktar: mevcut filtrelerle eşleşen TÜM rezervasyonları (sadece
// görünen sayfayı değil) tek seferlik büyük bir istekle çekip CSV'ye çevirir.
function escapeCsvField(value) {
  const text = String(value ?? '')
  if (text.includes(',') || text.includes('"') || text.includes('\n')) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

async function exportCsv() {
  isExporting.value = true
  try {
    const response = await fetchReservationsRequest(buildParams({ page: undefined, page_size: 1000 }))
    const rows = response.data.results

    const header = [
      'Rezervasyon Tipi',
      'Araç',
      'SIPP Kodu',
      'Müşteri',
      'Kaynak',
      'Teslim Alma Ofisi',
      'Teslim Etme Ofisi',
      'Teslim Tarihi',
      'İade Tarihi',
      'Durum',
      'Tutar',
    ]
    const lines = [header, ...rows.map((r) => [
      typeLabels[r.type],
      `${r.vehicle.plate} ${r.vehicle.brand} ${r.vehicle.model}`,
      r.vehicle.sipp_code || '',
      r.customer_name,
      sourceLabels[r.source],
      r.pickup_location?.name ?? r.vehicle.location.name,
      r.return_location?.name ?? r.vehicle.location.name,
      formatDateTime(r.start_date),
      formatDateTime(r.end_date),
      statusLabels[r.status],
      r.total_price,
    ])]

    const csvContent = lines.map((row) => row.map(escapeCsvField).join(',')).join('\n')
    // Başına BOM: Excel'in Türkçe karakterleri (ş, ı, ğ vb.) doğru okuması için.
    const blob = new Blob(['﻿' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `rezervasyonlar-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
  } catch (error) {
    errorMessage.value = 'Dışa aktarma başarısız oldu, lütfen tekrar deneyin.'
  } finally {
    isExporting.value = false
  }
}

function reservationLabel(reservation) {
  return `${reservation.vehicle.plate} — ${reservation.customer_name} · ${formatDateTime(reservation.start_date)} → ${formatDateTime(reservation.end_date)} (${statusLabels[reservation.status]})`
}

async function loadHandoverReservations() {
  const response = await fetchAllReservationsForCalendar()
  handoverReservations.value = response.data.results
}

async function submitHandover() {
  handoverMessage.value = null
  try {
    const response = await createHandover(handoverForm.value)
    const extraCharge = Number(response.data.extra_charge)
    handoverMessage.value = {
      type: 'success',
      text:
        handoverForm.value.type === 'return' && extraCharge > 0
          ? `İade kaydedildi. Ek ücret: ${extraCharge} TL (eksik yakıt).`
          : 'Kayıt oluşturuldu.',
    }
    handoverForm.value = { reservation: '', type: 'delivery', odometer_km: '', fuel_level: '', damage_notes: '' }
    await loadReservations()
    await loadHandoverReservations()
  } catch (error) {
    const detail = error.response?.data?.non_field_errors?.[0]
    handoverMessage.value = { type: 'error', text: detail || 'Kayıt oluşturulamadı.' }
  }
}

onMounted(() => {
  loadReservations()
  loadHandoverReservations()
})
</script>

<style scoped>
.header-actions {
  flex-wrap: wrap;
}

.new-button {
  padding: 0.6rem 1.25rem;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  transition: background-color 150ms ease;
}

.new-button:hover {
  background: var(--color-primary-hover);
}

.presets-wrapper {
  position: relative;
}

.presets-backdrop {
  position: fixed;
  inset: 0;
  z-index: 25;
}

.presets-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.4rem;
  width: 260px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: 0.5rem;
  z-index: 30;
}

.presets-empty {
  color: var(--color-muted);
  font-size: 0.85rem;
  padding: 0.5rem;
  margin: 0;
}

.preset-row {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.preset-apply {
  flex: 1;
  text-align: left;
  background: none;
  border: none;
  color: var(--color-foreground);
  font-weight: 500;
  padding: 0.5rem 0.6rem;
  border-radius: var(--radius-sm);
}

.preset-apply:hover {
  background: var(--color-bg);
}

.preset-remove {
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  background: none;
  color: var(--color-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
}

.preset-remove:hover {
  color: var(--color-destructive);
  background: var(--color-destructive-soft);
}

.preset-remove-icon {
  width: 14px;
  height: 14px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
}

.presets-dropdown hr {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 0.4rem 0;
}

.preset-save {
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  color: var(--color-primary);
  font-weight: 600;
  padding: 0.5rem 0.6rem;
  border-radius: var(--radius-sm);
}

.preset-save:hover {
  background: var(--color-primary-soft);
}

.panel-card {
  overflow-x: auto;
}

.pagination-row {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 1rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.pagination-row .count-badge {
  grid-column: 1;
  margin-left: 0;
}

.pagination-controls {
  grid-column: 2;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.page-label {
  font-size: 0.85rem;
  color: var(--color-muted);
  font-weight: 600;
}

.handover-form {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 1rem;
}

.handover-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--color-muted);
}

.full-width {
  flex-basis: 100%;
}

.handover-form select,
.handover-form input[type='text'],
.handover-form input[type='number'] {
  min-width: 200px;
}

.radio-group {
  display: flex;
  gap: 1.25rem;
}

.radio-label {
  flex-direction: row !important;
  align-items: center;
  gap: 0.4rem !important;
  color: inherit !important;
}

.radio-label input[type='radio'] {
  width: auto;
  min-width: 0;
}

.data-table {
  white-space: nowrap;
}

.price-cell.price-pending {
  color: var(--color-success);
  font-weight: 700;
}

.price-cell.price-cancelled {
  color: var(--color-destructive);
  font-weight: 700;
}

.price-prefix {
  margin-right: 0.3rem;
  font-weight: 800;
}

.price-prefix.extended {
  color: var(--color-success);
}

.price-prefix.early {
  color: var(--color-warning);
}

.sortable-th {
  cursor: pointer;
  user-select: none;
}

.sortable-th:hover {
  color: var(--color-primary);
}

.sort-arrow {
  margin-left: 0.25rem;
  font-size: 0.7rem;
  color: var(--color-primary);
}

.row-actions {
  display: flex;
  gap: 0.4rem;
  white-space: nowrap;
}

.icon-action-button {
  width: 32px;
  height: 32px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-muted);
}

.icon-action-button:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.row-icon {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
}

.history-subtitle {
  margin: 0 0 1.25rem;
  color: var(--color-muted);
  font-weight: 600;
}

.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border);
}

.timeline-item:last-child {
  border-bottom: none;
}

.timeline-label {
  font-weight: 700;
  color: var(--color-foreground);
}

.timeline-date {
  font-size: 0.85rem;
  color: var(--color-muted);
}
</style>
