<template>
  <form class="driver-form" @submit.prevent="submit">
    <label>
      Ad
      <input v-model="form.first_name" type="text" required />
    </label>
    <label>
      Soyad
      <input v-model="form.last_name" type="text" required />
    </label>
    <label>
      E-Posta
      <input v-model="form.email" type="email" required />
    </label>
    <label>
      Telefon
      <input
        v-model="form.phone"
        type="tel"
        inputmode="numeric"
        maxlength="11"
        placeholder="5XXXXXXXXX"
        @input="sanitizeDigits('phone', 11)"
      />
    </label>
    <label>
      TC Kimlik No
      <input
        v-model="form.tc_no"
        type="text"
        inputmode="numeric"
        maxlength="11"
        @input="sanitizeDigits('tc_no', 11)"
      />
    </label>
    <label>
      Doğum Tarihi
      <input v-model="form.birth_date" type="date" />
    </label>
    <label>
      Ehliyet Sınıfı
      <select v-model="form.license_class">
        <option value="">Seç</option>
        <option v-for="option in licenseClasses" :key="option" :value="option">{{ option }}</option>
      </select>
    </label>
    <label>
      Ehliyet Numarası
      <input v-model="form.license_number" type="text" placeholder="Ehliyet üzerindeki seri no" />
    </label>
    <label>
      Ehliyet Veriliş Tarihi
      <input v-model="form.license_issue_date" type="date" />
    </label>

    <div class="form-actions">
      <button type="submit" :disabled="isSaving">{{ isSaving ? 'Kaydediliyor...' : 'Kaydet' }}</button>
      <button type="button" class="cancel-link" @click="$emit('cancel')">Vazgeç</button>
    </div>
  </form>
  <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
</template>

<script setup>
import { ref } from 'vue'
import { createDriver } from '../../auth/services'

// Sadece YENİ sürücü oluşturma — hem Sürücüler sayfasının "+ Yeni" formu
// hem de Yeni Rezervasyon akışındaki "sürücü bulunamadıysa" adımı bu
// component'i paylaşıyor, aynı alanları iki yerde tekrar yazmamak için.
const emit = defineEmits(['created', 'cancel'])

const licenseClasses = ['A1', 'A2', 'A', 'B1', 'B', 'BE', 'C1', 'C', 'D1', 'D']

const isSaving = ref(false)
const errorMessage = ref('')

function emptyForm() {
  return {
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    tc_no: '',
    birth_date: '',
    license_class: '',
    license_number: '',
    license_issue_date: '',
  }
}

const form = ref(emptyForm())

// inputmode="numeric" sadece MOBİL klavyeyi sayısal gösterir, fiziksel
// klavyeyle harf girmeyi ENGELLEMEZ — bu yüzden her girişte rakam
// olmayan karakterleri eleyip gerçek bir kısıtlama uyguluyoruz.
function sanitizeDigits(field, maxLength) {
  form.value[field] = form.value[field].replace(/\D/g, '').slice(0, maxLength)
}

async function submit() {
  isSaving.value = true
  errorMessage.value = ''
  try {
    const response = await createDriver(form.value)
    emit('created', response.data)
  } catch (error) {
    const data = error.response?.data
    const firstError = data && Object.values(data)[0]
    errorMessage.value = Array.isArray(firstError) ? firstError[0] : firstError || 'Kaydedilemedi.'
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
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

.form-actions {
  flex-basis: 100%;
  display: flex;
  gap: 0.75rem;
}
</style>
