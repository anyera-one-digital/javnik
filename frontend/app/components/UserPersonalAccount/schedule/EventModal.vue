<script setup lang="ts">
import type { Event, Service } from '~/types'
import { format } from 'date-fns'
import { CalendarDate, DateFormatter, getLocalTimeZone, today } from '@internationalized/date'
import { formatDurationMinutes } from '~/utils/formatDuration'
import { onlyActiveServices } from '~/utils/activeServices'

const dateFormatter = new DateFormatter('ru-RU', { dateStyle: 'long' })

const props = defineProps<{
  event?: Event | null
  defaultDate?: Date
  defaultTime?: string | null
  modelValue?: boolean
}>()

const emit = defineEmits<{
  saved: []
  close: []
  'update:modelValue': [value: boolean]
}>()

const toast = useToast()
const isOpen = computed({
  get: () => props.modelValue ?? false,
  set: (value) => emit('update:modelValue', value)
})
const { getAuthHeaders, refreshAccessToken } = useAuth()

const services = ref<Service[]>([])
const servicesError = ref<Error | null>(null)
const isSubmitting = ref(false)

async function loadServices() {
  if (!import.meta.client) return

  try {
    servicesError.value = null
    let headers = getAuthHeaders()
    if (!headers.Authorization) return

    try {
      const data = await $fetch<Service[]>('/api/services', { headers })
      if (Array.isArray(data)) {
        services.value = onlyActiveServices(data)
      } else if (data && typeof data === 'object' && 'results' in data) {
        services.value = onlyActiveServices((data as { results?: Service[] }).results || [])
      } else {
        services.value = []
      }
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retryData = await $fetch<Service[]>('/api/services', { headers })
          if (Array.isArray(retryData)) {
            services.value = onlyActiveServices(retryData)
          } else if (retryData && typeof retryData === 'object' && 'results' in retryData) {
            services.value = onlyActiveServices((retryData as { results?: Service[] }).results || [])
          } else {
            services.value = []
          }
          return
        }
      }
      console.error('EventModal: Error loading services:', error)
      servicesError.value = error
      services.value = []
    }
  } catch (error: any) {
    console.error('EventModal: Unexpected error:', error)
    servicesError.value = error
    services.value = []
  }
}

const form = reactive({
  name: '',
  description: '',
  maxParticipants: 10,
  date: format(new Date(), 'yyyy-MM-dd'),
  startTime: '10:00',
  duration: 60,
  serviceId: null as number | null,
  price: undefined as number | undefined
})

const calendarDate = computed({
  get: () => {
    if (!form.date || form.date.length < 10) {
      const d = new Date()
      return new CalendarDate(d.getFullYear(), d.getMonth() + 1, d.getDate())
    }
    const [y, m, d] = form.date.split('-').map(Number)
    return new CalendarDate(y!, m!, d!)
  },
  set: (value: CalendarDate | null) => {
    if (value) {
      form.date = `${String(value.year).padStart(4, '0')}-${String(value.month).padStart(2, '0')}-${String(value.day).padStart(2, '0')}`
    }
  }
})

const showManualFields = computed(() => !form.serviceId)

const selectedService = computed(() => {
  if (!form.serviceId) return null
  return services.value.find(s => s.id === form.serviceId) || null
})

const serviceSelectItems = computed(() => {
  const items: Array<{ label: string, value: number | null, disabled?: boolean }> = [
    { label: 'Без услуги (указать вручную)', value: null }
  ]
  if (!services.value.length) {
    items.push({ label: 'Нет доступных услуг', value: -1, disabled: true })
    return items
  }
  for (const s of services.value) {
    if (!s?.id) continue
    const duration = s.duration ? ` (${formatDurationMinutes(s.duration)})` : ''
    const price = s.price != null ? `, ${Math.round(Number(s.price)).toLocaleString('ru-RU')} ₽` : ''
    items.push({ label: `${s.name}${duration}${price}`, value: s.id })
  }
  return items
})

const durationOptions = [30, 45, 60, 90, 120].map(value => ({
  label: formatDurationMinutes(value),
  value
}))

const timeSelectItems = computed(() => {
  const items: Array<{ label: string, value: string }> = []
  for (let h = 6; h <= 22; h++) {
    for (const m of [0, 15, 30, 45]) {
      if (h === 22 && m > 0) continue
      const value = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
      items.push({ label: value, value })
    }
  }
  return items
})

watch(() => form.serviceId, (serviceId) => {
  if (serviceId) {
    const service = services.value.find(s => s.id === serviceId)
    if (service) {
      form.duration = service.duration || 60
      form.price = undefined
    }
  }
})

function resetCreateForm() {
  form.name = ''
  form.description = ''
  form.maxParticipants = 10
  form.date = props.defaultDate
    ? format(props.defaultDate, 'yyyy-MM-dd')
    : format(new Date(), 'yyyy-MM-dd')
  const rawTime = props.defaultTime || '10:00'
  form.startTime = rawTime.slice(0, 5)
  form.duration = 60
  form.serviceId = null
  form.price = undefined
}

function fillFormFromEvent(event: Event) {
  form.name = event.name
  form.description = event.description || ''
  form.maxParticipants = event.maxParticipants || 10
  form.date = event.date
  form.startTime = (event.startTime || '10:00').slice(0, 5)
  form.duration = event.duration
  form.serviceId = event.serviceId ?? null
  form.price = event.price
}

watch(() => props.event, (event) => {
  if (event) fillFormFromEvent(event)
  else if (isOpen.value) resetCreateForm()
}, { immediate: true })

watch(() => props.defaultDate, (date) => {
  if (date && !props.event && isOpen.value) {
    form.date = format(date, 'yyyy-MM-dd')
  }
})

watch(isOpen, async (open) => {
  if (!open) {
    isSubmitting.value = false
    return
  }
  if (props.event) fillFormFromEvent(props.event)
  else resetCreateForm()
  if (import.meta.client) {
    await nextTick()
    await loadServices()
  }
})

async function onSubmit() {
  if (!form.name || !form.date || !form.startTime || !form.maxParticipants) {
    toast.add({
      title: 'Ошибка',
      description: 'Заполните все обязательные поля',
      color: 'error'
    })
    return
  }

  if (!form.serviceId) {
    if (!form.duration || !form.price || form.price <= 0) {
      toast.add({
        title: 'Ошибка',
        description: 'Укажите продолжительность и стоимость события',
        color: 'error'
      })
      return
    }
  }

  isSubmitting.value = true

  try {
    const headers = getAuthHeaders()
    const body: Record<string, unknown> = {
      name: form.name,
      description: form.description || '',
      date: form.date,
      startTime: form.startTime,
      duration: form.duration,
      maxParticipants: form.maxParticipants
    }

    if (form.serviceId) {
      body.serviceId = form.serviceId
    } else {
      body.price = Number(form.price)
    }

    if (props.event) {
      await $fetch('/api/events', {
        method: 'PATCH',
        headers,
        body: {
          id: props.event.id,
          ...body
        }
      })
    } else {
      await $fetch('/api/events', {
        method: 'POST',
        headers,
        body
      })
    }

    toast.add({
      title: 'Успешно',
      description: props.event ? 'Событие обновлено' : 'Событие создано',
      color: 'success'
    })

    emit('saved')
    isOpen.value = false
  } catch (error: any) {
    console.error('EventModal: Error saving event:', error)

    let errorMessage = 'Не удалось сохранить событие'

    if (error.data !== undefined && error.data !== null) {
      if (error.data === true || error.data === false) {
        errorMessage = 'Ошибка при создании события. Попробуйте ещё раз.'
      } else if (typeof error.data === 'string') {
        errorMessage = error.data
      } else if (typeof error.data === 'object') {
        if (error.data.non_field_errors) {
          errorMessage = Array.isArray(error.data.non_field_errors)
            ? error.data.non_field_errors.join(', ')
            : String(error.data.non_field_errors)
        } else if (error.data.error) {
          errorMessage = typeof error.data.error === 'string' ? error.data.error : JSON.stringify(error.data.error)
        } else if (error.data.message) {
          errorMessage = typeof error.data.message === 'string' ? error.data.message : JSON.stringify(error.data.message)
        } else if (error.data.detail) {
          errorMessage = typeof error.data.detail === 'string' ? error.data.detail : JSON.stringify(error.data.detail)
        } else {
          const validationErrors = Object.entries(error.data)
            .filter(([field]) => field !== 'non_field_errors')
            .map(([field, errors]: [string, unknown]) => {
              const fieldName = field === 'date'
                ? 'Дата'
                : field === 'start_time' || field === 'startTime'
                  ? 'Время начала'
                  : field === 'duration'
                    ? 'Продолжительность'
                    : field === 'max_participants' || field === 'maxParticipants'
                      ? 'Количество мест'
                      : field === 'service' || field === 'serviceId'
                        ? 'Услуга'
                        : field === 'price'
                          ? 'Стоимость'
                          : field
              const errorList = Array.isArray(errors) ? errors.join(', ') : String(errors)
              return `${fieldName}: ${errorList}`
            })
          if (validationErrors.length > 0) {
            errorMessage = validationErrors.join('\n')
          }
        }
      }
    } else if (error.message) {
      errorMessage = error.message
    }

    toast.add({
      title: 'Ошибка',
      description: errorMessage,
      color: 'error',
      timeout: 10000
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="isOpen"
    :title="event ? 'Редактировать событие' : 'Создать событие'"
    :description="event ? 'Изменить данные группового занятия' : 'Создать групповое занятие или событие'"
    :ui="{ width: 'sm:max-w-lg' }"
  >
    <template #body>
      <form class="space-y-4" @submit.prevent="onSubmit">
        <UFormField label="Название" required>
          <UInput
            v-model="form.name"
            class="w-full"
            placeholder="Например: Йога для начинающих"
            required
          />
        </UFormField>

        <UFormField label="Описание">
          <UTextarea
            v-model="form.description"
            class="w-full"
            placeholder="Описание события..."
            :rows="3"
          />
        </UFormField>

        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Дата" required>
            <UPopover :content="{ align: 'start' }">
              <UButton
                color="neutral"
                variant="outline"
                icon="i-lucide-calendar"
                class="w-full justify-start"
              >
                {{ form.date ? dateFormatter.format(calendarDate.toDate(getLocalTimeZone())) : 'Выберите дату' }}
              </UButton>
              <template #content>
                <div class="flex flex-col">
                  <UCalendar
                    v-model="calendarDate"
                    color="neutral"
                    variant="subtle"
                    class="p-2"
                  />
                  <div class="flex justify-end gap-2 border-t border-default p-2">
                    <UButton
                      color="neutral"
                      variant="ghost"
                      size="sm"
                      label="Сегодня"
                      @click="calendarDate = today(getLocalTimeZone())"
                    />
                  </div>
                </div>
              </template>
            </UPopover>
          </UFormField>

          <UFormField label="Время начала" required>
            <USelect
              v-model="form.startTime"
              class="w-full"
              :items="timeSelectItems"
              placeholder="Выберите время"
            />
          </UFormField>
        </div>

        <UFormField label="Услуга">
          <USelect
            v-model="form.serviceId"
            class="w-full"
            :items="serviceSelectItems"
            placeholder="Выберите услугу"
          />
          <template v-if="servicesError" #hint>
            <span class="text-xs text-error">Не удалось загрузить услуги</span>
          </template>
          <template v-else-if="services.length === 0" #hint>
            <span class="text-xs text-muted">Или укажите продолжительность и стоимость вручную</span>
          </template>
        </UFormField>

        <div v-if="selectedService" class="space-y-1 rounded-lg bg-muted/30 p-3 text-sm">
          <div class="flex justify-between gap-3">
            <span class="text-muted">Продолжительность:</span>
            <span class="font-medium">{{ formatDurationMinutes(selectedService.duration) }}</span>
          </div>
          <div v-if="selectedService.price != null" class="flex justify-between gap-3">
            <span class="text-muted">Стоимость:</span>
            <span class="font-medium">{{ Math.round(Number(selectedService.price)).toLocaleString('ru-RU') }} ₽</span>
          </div>
        </div>

        <div v-else class="grid grid-cols-2 gap-4">
          <UFormField label="Продолжительность" required>
            <USelect
              v-model="form.duration"
              class="w-full"
              :items="durationOptions"
              required
            />
          </UFormField>

          <UFormField label="Стоимость (₽)" required>
            <UInput
              v-model.number="form.price"
              class="w-full"
              type="number"
              min="0"
              step="100"
              placeholder="0"
              required
            />
          </UFormField>
        </div>

        <UFormField label="Количество мест" required>
          <UInput
            v-model.number="form.maxParticipants"
            class="w-full"
            type="number"
            min="1"
            required
          />
        </UFormField>

        <div class="flex justify-end gap-2 pt-4">
          <UButton
            label="Отмена"
            color="neutral"
            variant="ghost"
            type="button"
            :disabled="isSubmitting"
            @click="isOpen = false"
          />
          <UButton
            type="submit"
            :label="event ? 'Сохранить' : 'Создать событие'"
            color="neutral"
            variant="solid"
            class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
            :loading="isSubmitting"
            :disabled="isSubmitting"
          />
        </div>
      </form>
    </template>
  </UModal>
</template>
