<script setup lang="ts">
import type { Event, Service } from '~/types'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'

const props = defineProps<{
  modelValue?: boolean
  event?: Event | null
  service?: Service | null
  timeSlot?: { date: Date, time: string } | null
  username?: string
  /** Показывать галочку согласия с политикой конфиденциальности (для публичной записи) */
  showPrivacy?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
  close: []
}>()

const toast = useToast()

const isOpen = computed({
  get: () => props.modelValue ?? false,
  set: (value) => emit('update:modelValue', value)
})

const form = reactive({
  name: '',
  email: '',
  phone: '',
  notes: '',
  date: '',
  time: '',
  privacyAccepted: false
})

const isSubmitting = ref(false)
const config = useRuntimeConfig()

// Загружаем услуги - либо публичные по username, либо авторизованные
const servicesUrl = props.username 
  ? `/api/public/services/${props.username}`
  : '/api/services'

const { data: services } = await useFetch<Service[]>(servicesUrl, {
  default: () => []
})

const selectedServiceId = ref<number | null>(null)

function resetForm() {
  form.name = ''
  form.email = ''
  form.phone = ''
  form.notes = ''
  form.date = ''
  form.time = ''
  form.privacyAccepted = false
}

/** Режим «из модалки услуги»: уже выбраны услуга, дата и время — показываем только форму клиента */
const isFromServiceModal = computed(() => Boolean(props.service && props.timeSlot))

watch(isOpen, (open) => {
  if (open) {
    if (props.service && props.timeSlot) {
      form.date = format(props.timeSlot.date, 'yyyy-MM-dd')
      form.time = props.timeSlot.time
      selectedServiceId.value = props.service.id
    } else if (props.timeSlot) {
      form.date = format(props.timeSlot.date, 'yyyy-MM-dd')
      form.time = props.timeSlot.time
      selectedServiceId.value = null
    } else if (props.event) {
      form.date = props.event.date
      form.time = props.event.startTime
      selectedServiceId.value = props.event.serviceId || null
    } else {
      form.date = format(new Date(), 'yyyy-MM-dd')
      form.time = '10:00'
      selectedServiceId.value = null
    }
  } else {
    resetForm()
    selectedServiceId.value = null
  }
})

async function onSubmit() {
  if (!form.name || !form.email || !form.phone) {
    toast.add({
      title: 'Ошибка',
      description: 'Пожалуйста, заполните все обязательные поля',
      color: 'error'
    })
    return
  }

  // Если запись на свободное время без переданной услуги — требуется выбор услуги
  if (props.timeSlot && !props.service && !selectedServiceId.value) {
    toast.add({
      title: 'Ошибка',
      description: 'Пожалуйста, выберите услугу',
      color: 'error'
    })
    return
  }

  if (props.showPrivacy && !form.privacyAccepted) {
    toast.add({
      title: 'Ошибка',
      description: 'Необходимо согласие с политикой конфиденциальности',
      color: 'error'
    })
    return
  }

  isSubmitting.value = true

  try {
    // Определяем URL для создания бронирования
    // Для публичных бронирований — POST на /create/ (GET на том же path только список)
    const apiBase = config.public.apiBase || 'http://localhost:8000'
    const bookingUrl = props.username
      ? `${apiBase}/api/public/bookings/${props.username}/create/`
      : '/api/bookings'
    
    if (props.event) {
      // Запись на событие
      await $fetch(bookingUrl, {
        method: 'POST',
        body: {
          eventId: props.event.id,
          customerName: form.name,
          customerEmail: form.email,
          customerPhone: form.phone,
          notes: form.notes,
          date: props.event.date,
          startTime: props.event.startTime,
          duration: props.event.duration
        }
      })
    } else if (props.service || selectedServiceId.value) {
      // Запись на услугу (из модалки услуги передаётся service, иначе ищем по selectedServiceId)
      const service = props.service || services.value?.find(s => s.id === selectedServiceId.value)
      
      if (!service) {
        throw new Error('Услуга не найдена')
      }

      await $fetch(bookingUrl, {
        method: 'POST',
        body: {
          serviceId: service.id,
          customerName: form.name,
          customerEmail: form.email,
          customerPhone: form.phone,
          notes: form.notes,
          date: form.date || format(new Date(), 'yyyy-MM-dd'),
          startTime: form.time || '10:00',
          duration: service.duration
        }
      })
    }

    toast.add({
      title: 'Заявка отправлена',
      description: props.username
        ? 'Бронь создана и ожидает подтверждения администратором в течение 24 часов. Мы свяжемся с вами после подтверждения.'
        : 'Запись успешно создана. Мы свяжемся с вами в ближайшее время.',
      color: 'success'
    })

    emit('saved')
    isOpen.value = false
  } catch (error: any) {
    const msg = error.data?.error || error.data?.message || error.message || 'Не удалось создать запись. Попробуйте позже.'
    const detail = error.data?.detail
    const trace = error.data?.traceback
    let description = typeof msg === 'string' ? msg : JSON.stringify(msg)
    if (detail) description += `. ${detail}`
    if (trace) description += `\n\n${String(trace).slice(0, 400)}`
    toast.add({
      title: 'Ошибка',
      description,
      color: 'error',
      timeout: 12000
    })
  } finally {
    isSubmitting.value = false
  }
}

const modalTitle = computed(() => {
  if (props.event) {
    return `Запись на событие: ${props.event.name}`
  }
  if (props.service) {
    return `Запись на услугу: ${props.service.name}`
  }
  if (props.timeSlot) {
    return 'Запись на свободное время'
  }
  return 'Запись'
})

const modalDescription = computed(() => {
  if (props.event) {
    return `${props.event.description || ''} ${props.event.date} в ${props.event.startTime}`
  }
  if (props.service) {
    return props.service.description || ''
  }
  if (props.timeSlot) {
    return `${format(props.timeSlot.date, 'd MMMM', { locale: ru })} в ${props.timeSlot.time}`
  }
  return ''
})
</script>

<template>
  <UModal
    v-model:open="isOpen"
    :title="modalTitle"
    :description="modalDescription"
    :ui="{ width: 'sm:max-w-lg' }"
  >
    <template #body>
      <form @submit.prevent="onSubmit" class="space-y-4">
        <UFormField label="Имя" required>
          <UInput
            v-model="form.name"
            placeholder="Введите ваше имя"
            required
          />
        </UFormField>

        <UFormField label="Email" required>
          <UInput
            v-model="form.email"
            type="email"
            placeholder="example@mail.com"
            required
          />
        </UFormField>

        <UFormField label="Телефон" required>
          <UInput
            v-model="form.phone"
            type="tel"
            placeholder="+7 (999) 999-99-99"
            required
          />
        </UFormField>

        <!-- Поля даты/времени и выбора услуги — только если не открыто из модалки услуги -->
        <template v-if="timeSlot && !isFromServiceModal">
          <div class="grid grid-cols-2 gap-4">
            <UFormField label="Дата" required>
              <UInput
                v-model="form.date"
                type="date"
                required
              />
            </UFormField>

            <UFormField label="Время" required>
              <UInput
                v-model="form.time"
                type="time"
                required
              />
            </UFormField>
          </div>

          <UFormField label="Услуга" required>
            <USelect
              v-model="selectedServiceId"
              :items="[
                { label: 'Выберите услугу', value: null },
                ...(services || []).map(s => ({ label: `${s.name} (${s.duration} мин, ${s.price} ₽)`, value: s.id }))
              ]"
              placeholder="Выберите услугу"
              required
            />
          </UFormField>
        </template>

        <!-- Краткая сводка при записи из модалки услуги -->
        <div v-if="isFromServiceModal && service && timeSlot" class="p-3 rounded-lg bg-elevated text-sm text-muted">
          {{ service.name }} — {{ format(timeSlot.date, 'd MMMM', { locale: ru }) }} в {{ timeSlot.time }}
        </div>

        <!-- Согласие с политикой конфиденциальности -->
        <UFormField v-if="showPrivacy" required>
          <template #label>Согласие с политикой конфиденциальности</template>
          <label class="flex items-start gap-2 cursor-pointer">
            <UCheckbox v-model="form.privacyAccepted" />
            <span class="text-sm">
              Я соглашаюсь с <ULink to="/privacy" target="_blank" class="underline hover:no-underline">политикой конфиденциальности</ULink> и даю согласие на обработку персональных данных
            </span>
          </label>
        </UFormField>

        <UFormField label="Комментарий (необязательно)">
          <UTextarea
            v-model="form.notes"
            placeholder="Дополнительная информация..."
            :rows="3"
          />
        </UFormField>

        <div v-if="event" class="p-3 bg-gray-50 rounded-lg text-sm">
          <div class="flex justify-between mb-1">
            <span class="text-gray-600">Свободных мест:</span>
            <span class="font-medium">{{ event.maxParticipants - event.bookedSlots }} из {{ event.maxParticipants }}</span>
          </div>
        </div>

        <div class="flex justify-end gap-2 pt-4">
          <UButton
            label="Отмена"
            color="neutral"
            variant="ghost"
            type="button"
            @click="isOpen = false"
          />
          <UButton
            type="submit"
            label="Записаться"
            color="neutral"
            :loading="isSubmitting"
            :disabled="isSubmitting"
          />
        </div>
      </form>
    </template>
  </UModal>
</template>
