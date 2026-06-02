<template>
  <section class="commerce-panel">
    <header class="section-header">
      <div>
        <p class="eyebrow">地址管理</p>
        <h2>收货地址</h2>
        <p>当前支持地址列表、新增、编辑、删除，以及默认地址标记。</p>
      </div>
      <button type="button" class="primary-link button-reset" @click="startCreate">新增地址</button>
    </header>

    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="inline-success">{{ successMessage }}</p>

    <section v-if="editing" class="commerce-card commerce-card--summary">
      <form class="stack-form" @submit.prevent="submitAddress">
        <label class="form-field">
          <span>收件人</span>
          <input v-model="form.name" />
        </label>
        <label class="form-field">
          <span>手机号</span>
          <input v-model="form.phone" />
        </label>
        <label class="form-field">
          <span>省份</span>
          <input v-model="form.province" />
        </label>
        <label class="form-field">
          <span>城市</span>
          <input v-model="form.city" />
        </label>
        <label class="form-field">
          <span>区县</span>
          <input v-model="form.region" />
        </label>
        <label class="form-field">
          <span>详细地址</span>
          <textarea v-model="form.detailAddress" rows="3" />
        </label>
        <label class="checkbox-field">
          <input v-model="isDefault" type="checkbox" />
          <span>设为默认地址</span>
        </label>
        <div class="hero__actions">
          <button type="submit" class="primary-link button-reset">保存地址</button>
          <button type="button" class="secondary-link button-reset" @click="cancelEdit">取消</button>
        </div>
      </form>
    </section>

    <section v-if="addresses.length" class="commerce-grid">
      <article v-for="address in addresses" :key="address.id" class="commerce-card">
        <strong>{{ address.name }} {{ address.defaultStatus === 1 ? '（默认）' : '' }}</strong>
        <p>{{ address.phone }}</p>
        <p>{{ joinAddress(address) }}</p>
        <div class="hero__actions">
          <button type="button" class="secondary-link button-reset" @click="startEdit(address)">编辑</button>
          <button type="button" class="link-button" @click="removeAddress(address.id)">删除</button>
        </div>
      </article>
    </section>
    <section v-else class="empty-block">
      <h2>还没有收货地址</h2>
      <p>先新增一个地址，再继续下单。</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { createAddress, deleteAddress, fetchAddresses, updateAddress } from '@/services/addresses'
import type { UserAddress } from '@/types/auth'

const addresses = ref<UserAddress[]>([])
const editing = ref(false)
const currentId = ref<number | null>(null)
const isDefault = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const form = reactive<UserAddress>({
  name: '',
  phone: '',
  province: '',
  city: '',
  region: '',
  detailAddress: '',
  defaultStatus: 0,
})

onMounted(loadAddresses)

async function loadAddresses() {
  addresses.value = await fetchAddresses()
}

function startCreate() {
  editing.value = true
  currentId.value = null
  isDefault.value = false
  resetForm()
}

function startEdit(address: UserAddress) {
  editing.value = true
  currentId.value = Number(address.id)
  form.name = address.name
  form.phone = address.phone
  form.province = address.province || ''
  form.city = address.city || ''
  form.region = address.region || ''
  form.detailAddress = address.detailAddress
  isDefault.value = address.defaultStatus === 1
}

function cancelEdit() {
  editing.value = false
  currentId.value = null
  resetForm()
}

async function submitAddress() {
  errorMessage.value = ''
  successMessage.value = ''
  const payload: UserAddress = {
    ...form,
    defaultStatus: isDefault.value ? 1 : 0,
  }
  try {
    if (currentId.value) {
      await updateAddress(currentId.value, payload)
      successMessage.value = '地址已更新'
    } else {
      await createAddress(payload)
      successMessage.value = '地址已新增'
    }
    cancelEdit()
    await loadAddresses()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '地址保存失败'
  }
}

async function removeAddress(addressId?: number) {
  if (!addressId) return
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await deleteAddress(addressId)
    successMessage.value = '地址已删除'
    await loadAddresses()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '删除地址失败'
  }
}

function joinAddress(address: UserAddress) {
  return [address.province, address.city, address.region, address.detailAddress].filter(Boolean).join('')
}

function resetForm() {
  form.name = ''
  form.phone = ''
  form.province = ''
  form.city = ''
  form.region = ''
  form.detailAddress = ''
  form.defaultStatus = 0
}
</script>


