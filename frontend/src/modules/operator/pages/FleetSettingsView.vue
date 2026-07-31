<template>
  <div class="fleet-page">
    <div class="page-header">
      <h1>Ayarlar</h1>
    </div>

    <section class="panel-card">
      <h2>Hesabım</h2>
      <p v-if="meError" class="error">{{ meError }}</p>
      <dl v-else-if="me" class="info-grid">
        <div class="info-item">
          <dt>Ad Soyad</dt>
          <dd>{{ me.first_name }} {{ me.last_name }}</dd>
        </div>
        <div class="info-item">
          <dt>E-Posta</dt>
          <dd>{{ me.email }}</dd>
        </div>
        <div class="info-item">
          <dt>Telefon</dt>
          <dd>{{ me.phone || '—' }}</dd>
        </div>
        <div class="info-item">
          <dt>Rol</dt>
          <dd>{{ roleLabels[me.role] || me.role }}</dd>
        </div>
      </dl>
    </section>

    <section class="panel-card">
      <div class="section-header">
        <h2>Personel</h2>
        <button type="button" class="btn-icon" @click="openAddStaffForm">
          <svg viewBox="0 0 24 24" v-html="ICONS.plus"></svg>
          Personel Ekle
        </button>
      </div>

      <Modal v-if="staffForm" title="Yeni Personel" @close="staffForm = null">
        <form class="staff-form" @submit.prevent="submitStaffForm">
          <label>
            Ad
            <input v-model="staffForm.first_name" type="text" required />
          </label>
          <label>
            Soyad
            <input v-model="staffForm.last_name" type="text" required />
          </label>
          <label>
            E-Posta
            <input v-model="staffForm.email" type="email" required />
          </label>
          <label>
            Telefon
            <input v-model="staffForm.phone" type="tel" inputmode="numeric" maxlength="11" placeholder="5XXXXXXXXX" />
          </label>
          <label>
            Şifre
            <input v-model="staffForm.password" type="password" required />
          </label>

          <div class="form-actions">
            <button type="submit" :disabled="isSavingStaff">
              {{ isSavingStaff ? 'Kaydediliyor...' : 'Kaydet' }}
            </button>
            <button type="button" class="cancel-link" @click="staffForm = null">Vazgeç</button>
          </div>
        </form>
        <p v-if="staffFormError" class="error">{{ staffFormError }}</p>
      </Modal>

      <p v-if="staffError" class="error">{{ staffError }}</p>
      <p v-else-if="isLoadingStaff">Yükleniyor...</p>
      <table v-else-if="staff.length" class="data-table">
        <thead>
          <tr>
            <th>Ad Soyad</th>
            <th>E-Posta</th>
            <th>Telefon</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="person in staff" :key="person.id">
            <td>{{ person.first_name }} {{ person.last_name }}</td>
            <td>{{ person.email }}</td>
            <td>{{ person.phone || '—' }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty-state">Henüz başka bir operatör personeli yok.</p>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Modal from '../../../components/Modal.vue'
import { ICONS } from '../../../icons'
import { createStaff, fetchMe, fetchStaff } from '../../auth/services'

const me = ref(null)
const meError = ref('')

const staff = ref([])
const isLoadingStaff = ref(false)
const staffError = ref('')

const staffForm = ref(null)
const staffFormError = ref('')
const isSavingStaff = ref(false)

const roleLabels = {
  operator: 'Operatör',
  admin: 'Yönetici',
  customer: 'Müşteri',
}

function emptyStaffForm() {
  return { first_name: '', last_name: '', email: '', phone: '', password: '' }
}

function openAddStaffForm() {
  staffForm.value = emptyStaffForm()
  staffFormError.value = ''
}

async function submitStaffForm() {
  isSavingStaff.value = true
  staffFormError.value = ''
  try {
    await createStaff(staffForm.value)
    staffForm.value = null
    await loadStaff()
  } catch (error) {
    const data = error.response?.data
    const firstError = data && Object.values(data)[0]
    staffFormError.value = Array.isArray(firstError) ? firstError[0] : firstError || 'Kaydedilemedi.'
  } finally {
    isSavingStaff.value = false
  }
}

async function loadMe() {
  meError.value = ''
  try {
    const response = await fetchMe()
    me.value = response.data
  } catch (error) {
    meError.value = 'Hesap bilgileri yüklenemedi.'
  }
}

async function loadStaff() {
  isLoadingStaff.value = true
  staffError.value = ''
  try {
    const response = await fetchStaff()
    staff.value = response.data
  } catch (error) {
    staffError.value = 'Personel listesi yüklenemedi.'
  } finally {
    isLoadingStaff.value = false
  }
}

onMounted(() => {
  loadMe()
  loadStaff()
})
</script>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h2 {
  margin: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin: 0;
}

.info-item {
  background: var(--color-bg);
  border-radius: var(--radius-md);
  padding: 0.8rem 1rem;
}

.info-item dt {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-muted);
  margin-bottom: 0.3rem;
}

.info-item dd {
  margin: 0;
  font-weight: 700;
  color: var(--color-foreground);
}

.staff-form {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.staff-form label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: var(--color-muted);
  flex: 1;
  min-width: 180px;
}

.form-actions {
  flex-basis: 100%;
  display: flex;
  gap: 0.75rem;
}
</style>
