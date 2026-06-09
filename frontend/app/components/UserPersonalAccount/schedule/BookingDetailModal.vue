<script setup lang="ts">
import type { Booking } from '~/types'
import { format, parseISO, isBefore } from 'date-fns'
import { ru } from 'date-fns/locale'

const props = defineProps<{
  modelValue?: boolean
  booking?: Booking | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  updated: []
  edit: [booking: Booking]
}>()

const toast = useToast()
const { getAuthHeaders, refreshAccessToken } = useAuth()

const isOpen = computed({
  get: () => props.modelValue ?? false,
  set: (v) => emit('update:modelValue', v)
})

const statusLabels: Record<string, string> = {
  pending: 'Ожидает подтверждения',
  confirmed: 'Подтверждено',
  completed: 'Завершено',
  cancelled: 'Отменено'
}

const statusColor: Record<string, string> = {
  pending: 'warning',
  confirmed: 'success',
  completed: 'primary',
  cancelled: 'error'
}

/** Можно ли нажать «Подтвердить» — только для pending */
const canConfirm = computed(() => props.booking?.status === 'pending')

/** Можно ли нажать «Услуга оказана» — confirmed и дата/время брони уже прошли */
const canMarkCompleted = computed(() => {
  const b = props.booking
  if (!b || b.status !== 'confirmed') return false
  const dateStr = typeof b.date === 'string' ? b.date.split('T')[0] : b.date
  const endTime = b.endTime || b.startTime
  const endStr = `${dateStr}T${endTime.includes(':') ? endTime : endTime + ':00'}`
  let endDate: Date
  try {
    endDate = parseISO(endStr)
  } catch {
    return false
  }
  return isBefore(endDate, new Date())
})

const isSubmitting = ref(false)

async function setStatus(newStatus: 'confirmed' | 'completed') {
  if (!props.booking?.id) return
  isSubmitting.value = true
  try {
    let headers = getAuthHeaders()
    if (!headers.Authorization) {
      const ok = await refreshAccessToken()
      if (ok) headers = getAuthHeaders()
    }
    if (!headers.Authorization) throw new Error('Нет авторизации')
    await $fetch(`/api/bookings/${props.booking.id}/`, {
      method: 'PATCH',
      headers,
      body: { status: newStatus }
    })
    toast.add({
      title: newStatus === 'confirmed' ? 'Бронь подтверждена' : 'Услуга отмечена как оказанная',
      color: 'success'
    })
    emit('updated')
    isOpen.value = false
  } catch (e: any) {
    toast.add({
      title: 'Ошибка',
      description: e.data?.error || e.data?.detail || e.message || 'Не удалось обновить статус',
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

const isDeleting = ref(false)
const deleteConfirmOpen = ref(false)

function openDeleteConfirm() {
  deleteConfirmOpen.value = true
}

function cancelDelete() {
  deleteConfirmOpen.value = false
}

async function confirmDelete() {
  if (!props.booking?.id) return
  isDeleting.value = true
  try {
    let headers = getAuthHeaders()
    if (!headers.Authorization) {
      const ok = await refreshAccessToken()
      if (ok) headers = getAuthHeaders()
    }
    if (!headers.Authorization) throw new Error('Нет авторизации')
    await $fetch(`/api/bookings/${props.booking.id}/`, {
      method: 'DELETE',
      headers
    })
    toast.add({ title: 'Запись удалена', color: 'success' })
    deleteConfirmOpen.value = false
    emit('updated')
    isOpen.value = false
  } catch (e: any) {
    toast.add({
      title: 'Ошибка',
      description: e.data?.error || e.data?.detail || e.message || 'Не удалось удалить запись',
      color: 'error'
    })
  } finally {
    isDeleting.value = false
  }
}

function onEdit() {
  if (props.booking) {
    emit('edit', props.booking)
    isOpen.value = false
  }
}

watch(() => props.modelValue, (open) => {
  if (!open) deleteConfirmOpen.value = false
})
</script>

<template>
  <UModal v-model:open="isOpen" :ui="{ width: 'sm:max-w-md' }">
    <template #header>
      <div class="flex items-center justify-between">
        <h2 class="text-xl font-semibold">{{ deleteConfirmOpen ? 'Удалить запись' : 'Бронь' }}</h2>
        <UButton
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          square
          @click="deleteConfirmOpen ? cancelDelete() : (isOpen = false)"
        />
      </div>
    </template>
    <template #body>
      <!-- Окно подтверждения удаления -->
      <div v-if="deleteConfirmOpen && booking" class="flex flex-col gap-4">
        <p class="text-sm text-muted">
          Вы точно хотите удалить эту запись?
        </p>
        <p class="text-sm text-muted">
          Запись «<strong>{{ booking.serviceName || 'Услуга' }}</strong>» для {{ booking.customerName || 'клиента' }}
          {{ booking.date ? format(new Date(booking.date), 'd MMMM', { locale: ru }) : '' }}
          {{ booking.startTime }}–{{ booking.endTime }}
          будет удалена без возможности восстановления.
        </p>
        <div class="flex justify-end gap-2">
          <UButton
            label="Нет"
            color="neutral"
            variant="subtle"
            :disabled="isDeleting"
            @click="cancelDelete"
          />
          <UButton
            label="Да"
            color="error"
            variant="solid"
            :loading="isDeleting"
            @click="confirmDelete"
          />
        </div>
      </div>
      <!-- Детали записи -->
      <div v-else-if="booking" class="space-y-4">
        <div>
          <p class="text-sm text-muted mb-1">Услуга</p>
          <p class="font-medium">{{ booking.serviceName || '—' }}</p>
        </div>
        <div>
          <p class="text-sm text-muted mb-1">Клиент</p>
          <p class="font-medium">{{ booking.customerName || '—' }}</p>
        </div>
        <div>
          <p class="text-sm text-muted mb-1">Дата и время</p>
          <p class="font-medium">
            {{ booking.date ? format(new Date(booking.date), 'd MMMM yyyy', { locale: ru }) : '—' }}
            {{ booking.startTime }}–{{ booking.endTime }}
          </p>
        </div>
        <div>
          <p class="text-sm text-muted mb-1">Статус</p>
          <UBadge
            :color="(statusColor[booking.status || 'pending'] as 'warning'|'success'|'primary'|'error') || 'neutral'"
            :label="statusLabels[booking.status || 'pending'] || booking.status"
          />
        </div>
        <div v-if="booking.notes" class="pt-2 border-t border-default">
          <p class="text-sm text-muted mb-1">Комментарий</p>
          <p class="text-sm">{{ booking.notes }}</p>
        </div>
        <div class="flex flex-wrap gap-2 pt-4">
          <UButton
            v-if="canConfirm"
            label="Подтвердить"
            color="neutral"
            variant="solid"
            class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
            :loading="isSubmitting"
            :disabled="isSubmitting"
            @click="setStatus('confirmed')"
          />
          <UButton
            v-if="canMarkCompleted"
            label="Услуга оказана"
            color="neutral"
            variant="solid"
            class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
            :loading="isSubmitting"
            :disabled="isSubmitting"
            @click="setStatus('completed')"
          />
          <UButton
            label="Редактировать"
            color="neutral"
            variant="outline"
            icon="i-lucide-pencil"
            :disabled="isSubmitting || isDeleting"
            @click="onEdit"
          />
          <UButton
            label="Удалить"
            color="error"
            variant="outline"
            icon="i-lucide-trash-2"
            :loading="isDeleting"
            :disabled="isSubmitting"
            @click="openDeleteConfirm"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
