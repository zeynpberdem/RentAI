<template>
  <div class="fleet-page">
    <div class="page-header">
      <div class="title-row">
        <h1>Sürücüler</h1>
        <button type="button" class="new-button btn-icon" @click="showNewDriverModal = true">
          <svg viewBox="0 0 24 24" v-html="ICONS.plus"></svg>
          Yeni
        </button>
      </div>
      <div class="header-actions">
        <input
          v-model="searchInput"
          type="search"
          placeholder="Ad, email veya telefon ara..."
          class="search-input"
          @keyup.enter="runSearch"
        />
        <button type="button" class="secondary btn-icon" @click="runSearch">
          <svg viewBox="0 0 24 24" v-html="ICONS.search"></svg>
          Ara
        </button>
      </div>
    </div>

    <Modal v-if="showNewDriverModal" title="Yeni Sürücü" @close="showNewDriverModal = false">
      <NewDriver @created="handleDriverCreated" @cancel="showNewDriverModal = false" />
    </Modal>

    <Modal v-if="editDriverForm" title="Sürücüyü Düzenle" @close="editDriverForm = null">
      <form class="driver-form" @submit.prevent="submitEditDriverForm">
        <label>
          Ad
          <input v-model="editDriverForm.first_name" type="text" required />
        </label>
        <label>
          Soyad
          <input v-model="editDriverForm.last_name" type="text" required />
        </label>
        <label>
          E-Posta
          <input v-model="editDriverForm.email" type="email" required disabled />
        </label>
        <label>
          Telefon
          <input
            v-model="editDriverForm.phone"
            type="tel"
            inputmode="numeric"
            maxlength="11"
            placeholder="5XXXXXXXXX"
            @input="sanitizeDigits(editDriverForm, 'phone', 11)"
          />
        </label>
        <label>
          TC Kimlik No
          <input
            v-model="editDriverForm.tc_no"
            type="text"
            inputmode="numeric"
            maxlength="11"
            @input="sanitizeDigits(editDriverForm, 'tc_no', 11)"
          />
        </label>
        <label>
          Doğum Tarihi
          <input v-model="editDriverForm.birth_date" type="date" />
        </label>
        <label>
          Ehliyet Sınıfı
          <select v-model="editDriverForm.license_class">
            <option value="">Seç</option>
            <option v-for="option in licenseClasses" :key="option" :value="option">{{ option }}</option>
          </select>
        </label>
        <label>
          Ehliyet Numarası
          <input v-model="editDriverForm.license_number" type="text" placeholder="Ehliyet üzerindeki seri no" />
        </label>
        <label>
          Ehliyet Veriliş Tarihi
          <input v-model="editDriverForm.license_issue_date" type="date" />
        </label>

        <div class="form-actions">
          <button type="submit" :disabled="isSavingDriver">
            {{ isSavingDriver ? 'Kaydediliyor...' : 'Kaydet' }}
          </button>
          <button type="button" class="cancel-link" @click="editDriverForm = null">Vazgeç</button>
        </div>
      </form>
      <p v-if="driverFormError" class="error">{{ driverFormError }}</p>
    </Modal>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="isLoading">Yükleniyor...</p>

    <section v-else class="panel-card">
      <p v-if="!drivers.length" class="empty-state">Sürücü bulunamadı.</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Ad Soyad</th>
            <th>E-Posta</th>
            <th>Telefon</th>
            <th class="sortable-th" @click="toggleSort('created_at')">
              Kayıt Tarihi
              <span v-if="sortField === 'created_at'" class="sort-arrow">{{ sortDirection === 'asc' ? '▲' : '▼' }}</span>
            </th>
            <ColumnFilterHeader label="Profil Durumu" :options="profileStatusOptions" v-model="profileFilter" />
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="driver in drivers" :key="driver.id">
            <td class="driver-name">{{ driver.first_name }} {{ driver.last_name }}</td>
            <td>{{ driver.email }}</td>
            <td>{{ driver.phone || '—' }}</td>
            <td>{{ formatDate(driver.created_at) }}</td>
            <td>
              <span
                class="profile-badge"
                :class="driver.is_profile_complete ? 'complete' : 'incomplete'"
              >
                {{ driver.is_profile_complete ? 'Profil Tamam' : 'Profil Eksik' }}
              </span>
            </td>
            <td class="row-actions">
              <button type="button" class="icon-action-button" title="Düzenle" @click="openEditDriverForm(driver)">
                <svg viewBox="0 0 24 24" class="row-icon" v-html="ICONS.edit"></svg>
              </button>
              <button type="button" class="icon-action-button danger" title="Sil" @click="removeDriver(driver)">
                <svg viewBox="0 0 24 24" class="row-icon" v-html="ICONS.trash"></svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination-row">
        <span class="count-badge">{{ totalCount }} sürücü</span>
        <div v-if="totalPages > 1" class="pagination-controls">
          <button type="button" class="secondary" :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">‹ Önceki</button>
          <span class="page-label">Sayfa {{ currentPage }} / {{ totalPages }}</span>
          <button type="button" class="secondary" :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">Sonraki ›</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import ColumnFilterHeader from '../../../components/ColumnFilterHeader.vue'
import Modal from '../../../components/Modal.vue'
import { ICONS } from '../../../icons'
import { deleteDriver, fetchDrivers, updateDriver } from '../../auth/services'
import NewDriver from '../components/NewDriver.vue'

const licenseClasses = ['A1', 'A2', 'A', 'B1', 'B', 'BE', 'C1', 'C', 'D1', 'D']

const PAGE_SIZE = 20

const drivers = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const isLoading = ref(false)
const errorMessage = ref('')

// Araçlar sayfasındaki desenle tutarlı: yazarken filtrelemiyor, sadece
// Enter'a basılınca ya da "Ara" butonuna tıklanınca uygulanıyor (backend'de).
const searchInput = ref('')
const appliedSearch = ref('')

function runSearch() {
  appliedSearch.value = searchInput.value.trim()
  currentPage.value = 1
  loadDrivers()
}

const profileStatusOptions = [
  { value: 'complete', label: 'Profil Tamam' },
  { value: 'incomplete', label: 'Profil Eksik' },
]
const profileFilter = ref('')

// Araçlar/Rezervasyonlar ile aynı desen: başlangıçta seçili sıralama yok,
// backend zaten varsayılan olarak -created_at döndürüyor (en yeni üstte).
const sortField = ref(null)
const sortDirection = ref('asc')

function toggleSort(field) {
  if (sortField.value === field) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortDirection.value = 'asc'
  }
  currentPage.value = 1
  loadDrivers()
}

const totalPages = computed(() => Math.max(Math.ceil(totalCount.value / PAGE_SIZE), 1))

const showNewDriverModal = ref(false)
const editDriverForm = ref(null)
const driverFormError = ref('')
const isSavingDriver = ref(false)

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('tr-TR')
}

function handleDriverCreated() {
  showNewDriverModal.value = false
  loadDrivers()
}

function openEditDriverForm(driver) {
  editDriverForm.value = { ...driver }
  driverFormError.value = ''
}

// inputmode="numeric" sadece MOBİL klavyeyi sayısal gösterir, fiziksel
// klavyeyle harf girmeyi ENGELLEMEZ — bu yüzden her girişte rakam
// olmayan karakterleri eleyip gerçek bir kısıtlama uyguluyoruz.
function sanitizeDigits(formRef, field, maxLength) {
  formRef.value[field] = formRef.value[field].replace(/\D/g, '').slice(0, maxLength)
}

async function submitEditDriverForm() {
  isSavingDriver.value = true
  driverFormError.value = ''
  try {
    await updateDriver(editDriverForm.value.id, editDriverForm.value)
    editDriverForm.value = null
    await loadDrivers()
  } catch (error) {
    const data = error.response?.data
    const firstError = data && Object.values(data)[0]
    driverFormError.value = Array.isArray(firstError) ? firstError[0] : firstError || 'Kaydedilemedi.'
  } finally {
    isSavingDriver.value = false
  }
}

async function removeDriver(driver) {
  const label = `${driver.first_name} ${driver.last_name}`
  if (!window.confirm(`${label} adlı sürücüyü silmek istediğine emin misin?`)) return

  try {
    await deleteDriver(driver.id)
    await loadDrivers()
  } catch (error) {
    errorMessage.value = 'Sürücü silinemedi, lütfen tekrar deneyin.'
  }
}

function buildParams() {
  const params = { page: currentPage.value }
  if (appliedSearch.value) params.search = appliedSearch.value
  if (profileFilter.value) params.profile_status = profileFilter.value
  if (sortField.value) params.ordering = sortDirection.value === 'desc' ? `-${sortField.value}` : sortField.value
  return params
}

async function loadDrivers() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await fetchDrivers(buildParams())
    drivers.value = response.data.results
    totalCount.value = response.data.count
  } catch (error) {
    errorMessage.value = 'Sürücüler yüklenemedi, lütfen tekrar deneyin.'
  } finally {
    isLoading.value = false
  }
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadDrivers()
}

watch(profileFilter, () => {
  currentPage.value = 1
  loadDrivers()
})

onMounted(() => {
  loadDrivers()
})
</script>

<style scoped>
.title-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.driver-form {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.driver-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--color-muted);
  flex: 1;
  min-width: 180px;
}

.driver-form select,
.driver-form input {
  min-width: 180px;
}

.driver-form input:disabled {
  background: var(--color-bg);
  color: var(--color-muted);
}

.form-actions {
  flex-basis: 100%;
  display: flex;
  gap: 0.75rem;
}

.panel-card {
  overflow-x: auto;
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

.driver-name {
  font-weight: 700;
  color: var(--color-foreground);
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

.icon-action-button.danger:hover {
  border-color: var(--color-destructive);
  color: var(--color-destructive);
  background: var(--color-destructive-soft);
}

.row-icon {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
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
</style>
