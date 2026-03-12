<script setup lang="ts">
import type { Event, Service } from '~/types'
import { format } from 'date-fns'

const props = defineProps<{
  event?: Event
  defaultDate?: Date
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

// Загружаем услуги только на клиенте
async function loadServices() {
  if (!process.client) return
  
  try {
    servicesError.value = null
    
    // Даем время для загрузки токена из localStorage
    await new Promise(resolve => setTimeout(resolve, 100))
    
    let headers = getAuthHeaders()
    
    console.log('EventModal: Loading services...')
    console.log('EventModal: Headers:', headers.Authorization ? 'Present' : 'Missing')
    
    if (!headers.Authorization) {
      console.warn('EventModal: No auth token available for loading services')
      return
    }
    
    try {
      const data = await $fetch<Service[]>('/api/services', {
        headers
      })
      
      console.log('EventModal: Services loaded:', data)
      console.log('EventModal: Services count:', data?.length || 0)
      console.log('EventModal: Services type:', Array.isArray(data) ? 'array' : typeof data)
      
      if (Array.isArray(data)) {
        services.value = data
      } else if (data && typeof data === 'object' && 'results' in data) {
        // Обработка пагинированного ответа
        services.value = (data as any).results || []
        console.log('EventModal: Extracted from paginated response:', services.value.length)
      } else {
        services.value = []
        console.warn('EventModal: Unexpected data format:', data)
      }
      
      console.log('EventModal: Final services.value:', services.value)
      console.log('EventModal: Final services.value.length:', services.value.length)
    } catch (error: any) {
      // Если получили 401, пытаемся обновить токен
      if (error.statusCode === 401 || error.status === 401) {
        console.log('EventModal: Got 401, attempting to refresh token...')
        const refreshed = await refreshAccessToken()
        
        if (refreshed) {
          console.log('EventModal: Token refreshed, retrying request...')
          headers = getAuthHeaders()
          
          try {
            const retryData = await $fetch<Service[]>('/api/services', {
              headers
            })
            
            if (Array.isArray(retryData)) {
              services.value = retryData
            } else if (retryData && typeof retryData === 'object' && 'results' in retryData) {
              services.value = (retryData as any).results || []
            } else {
              services.value = []
            }
            return
          } catch (retryError) {
            console.error('EventModal: Retry after refresh failed:', retryError)
          }
        } else {
          console.error('EventModal: Failed to refresh token')
        }
      }
      
      // Если обновление не помогло или ошибка не 401, сохраняем ошибку
      console.error('EventModal: Error loading services:', error)
      console.error('EventModal: Error status:', error.statusCode || error.status)
      console.error('EventModal: Error data:', error.data)
      servicesError.value = error
      services.value = []
    }
  } catch (error: any) {
    console.error('EventModal: Unexpected error:', error)
    servicesError.value = error
    services.value = []
  }
}

// Загружаем услуги при открытии модала
watch(isOpen, async (open) => {
  console.log('EventModal: isOpen changed to:', open)
  if (open && process.client) {
    console.log('EventModal: Modal opened, loading services...')
    // Небольшая задержка для гарантии, что токен загружен
    await nextTick()
    // Дополнительная задержка для загрузки токена из localStorage
    setTimeout(() => {
      loadServices()
    }, 200)
  } else {
    console.log('EventModal: Modal closed or not on client')
  }
})

// Загружаем услуги при монтировании компонента (только если модал открыт)
onMounted(async () => {
  console.log('EventModal: Component mounted, isOpen:', isOpen.value)
  if (process.client && isOpen.value) {
    console.log('EventModal: Modal is open on mount, loading services...')
    await nextTick()
    setTimeout(() => {
      loadServices()
    }, 200)
  }
})


const form = reactive({
  name: '',
  description: '',
  maxParticipants: 10,
  date: props.defaultDate ? format(props.defaultDate, 'yyyy-MM-dd') : format(new Date(), 'yyyy-MM-dd'),
  startTime: '10:00',
  duration: 60,
  serviceId: undefined as number | undefined,
  price: undefined as number | undefined
})

// Вычисляемое свойство: показывать ли поля для ручного ввода
const showManualFields = computed(() => !form.serviceId)

// При выборе услуги автоматически заполняем продолжительность и стоимость
watch(() => form.serviceId, (serviceId) => {
  if (serviceId && services.value) {
    const service = services.value.find(s => s.id === serviceId)
    if (service) {
      form.duration = service.duration || 60
      // При выборе услуги не используем price (берется из услуги)
      form.price = undefined
    }
  } else {
    // При снятии выбора услуги очищаем price, чтобы пользователь ввел вручную
    if (!form.price) {
      form.price = undefined
    }
  }
})

const durationOptions = [
  { label: '30 минут', value: 30 },
  { label: '45 минут', value: 45 },
  { label: '1 час', value: 60 },
  { label: '1.5 часа', value: 90 },
  { label: '2 часа', value: 120 }
]

watch(() => props.event, (event) => {
  if (event) {
    form.name = event.name
    form.description = event.description || ''
    form.maxParticipants = event.maxParticipants || 10
    form.date = event.date
    form.startTime = event.startTime
    form.duration = event.duration
    form.serviceId = event.serviceId
    form.price = event.price
  }
}, { immediate: true })

watch(() => props.defaultDate, (date) => {
  if (date) {
    form.date = format(date, 'yyyy-MM-dd')
  }
})

async function onSubmit() {
  console.log('EventModal: onSubmit called')
  console.log('EventModal: Form values:', {
    name: form.name,
    date: form.date,
    startTime: form.startTime,
    duration: form.duration,
    maxParticipants: form.maxParticipants,
    serviceId: form.serviceId,
    price: form.price
  })
  
  // Валидация формы
  if (!form.name || !form.date || !form.startTime || !form.maxParticipants) {
    console.log('EventModal: Validation failed - missing required fields')
    toast.add({
      title: 'Ошибка',
      description: 'Заполните все обязательные поля',
      color: 'error'
    })
    return
  }

  // Если услуга не выбрана, требуем стоимость и продолжительность
  if (!form.serviceId) {
    console.log('EventModal: No service selected, checking price and duration')
    console.log('EventModal: duration:', form.duration, 'price:', form.price)
    if (!form.duration || !form.price || form.price <= 0) {
      console.log('EventModal: Validation failed - missing price or duration')
      toast.add({
        title: 'Ошибка',
        description: 'Укажите продолжительность и стоимость события',
        color: 'error'
      })
      return
    }
  }
  
  console.log('EventModal: Validation passed, proceeding with request')

  try {
    const headers = getAuthHeaders()
    
    // Вычисляем время окончания для проверки конфликтов
    const [startHour, startMinute] = form.startTime.split(':').map(Number)
    const startMinutes = startHour * 60 + startMinute
    const endMinutes = startMinutes + form.duration
    const endHour = Math.floor(endMinutes / 60)
    const endMin = endMinutes % 60
    const endTime = `${String(endHour).padStart(2, '0')}:${String(endMin).padStart(2, '0')}`

    // Подготавливаем тело запроса
    const body: any = {
      name: form.name,
      description: form.description || '',
      date: form.date,
      startTime: form.startTime,
      duration: form.duration,
      maxParticipants: form.maxParticipants
    }
    
    // Если услуга выбрана, добавляем serviceId (цена берется из услуги)
    // Если услуга не выбрана, добавляем price (цена указывается вручную)
    if (form.serviceId) {
      body.serviceId = form.serviceId
      // Не передаем price при выборе услуги
    } else {
      // При отсутствии услуги обязательно передаем price
      if (!form.price || form.price <= 0) {
        toast.add({
          title: 'Ошибка',
          description: 'Укажите стоимость события',
          color: 'error'
        })
        return
      }
      body.price = Number(form.price)
    }

    console.log('EventModal: Sending event data:', JSON.stringify(body, null, 2))
    console.log('EventModal: Form state:', {
      serviceId: form.serviceId,
      price: form.price,
      duration: form.duration
    })

    console.log('EventModal: Headers:', headers.Authorization ? 'Present' : 'Missing')

    if (props.event) {
      console.log('EventModal: Updating event:', props.event.id)
      const response = await $fetch('/api/events/', {
        method: 'PATCH',
        headers,
        body: {
          id: props.event.id,
          ...body
        }
      })
      console.log('EventModal: Update response:', response)
    } else {
      console.log('EventModal: Creating new event')
      console.log('EventModal: Request URL: /api/events/')
      console.log('EventModal: Request method: POST')
      console.log('EventModal: Request headers:', headers)
      console.log('EventModal: Request body:', body)

      const response = await $fetch('/api/events/', {
        method: 'POST',
        headers,
        body
      })
      console.log('EventModal: Create response:', response)
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
    console.error('EventModal: Error status:', error.statusCode || error.status)
    console.error('EventModal: Error data:', error.data)
    console.error('EventModal: Error data type:', typeof error.data)
    console.error('EventModal: Full error object:', JSON.stringify(error, null, 2))
    
    let errorMessage = 'Не удалось сохранить событие'
    
    // Обрабатываем разные форматы ошибок
    if (error.data !== undefined && error.data !== null) {
      // Если error.data это boolean true, значит ошибка не была правильно сериализована
      if (error.data === true || error.data === false) {
        errorMessage = 'Ошибка при создании события. Проверьте консоль для деталей.'
        console.error('EventModal: Error data is boolean, this indicates a serialization issue')
      } else if (typeof error.data === 'string') {
        errorMessage = error.data
      } else if (typeof error.data === 'object') {
        // Проверяем non_field_errors сначала
        if (error.data.non_field_errors) {
          const nonFieldErrors = Array.isArray(error.data.non_field_errors) 
            ? error.data.non_field_errors.join(', ')
            : String(error.data.non_field_errors)
          errorMessage = nonFieldErrors
        } else if (error.data.error) {
          errorMessage = typeof error.data.error === 'string' ? error.data.error : JSON.stringify(error.data.error)
        } else if (error.data.message) {
          errorMessage = typeof error.data.message === 'string' ? error.data.message : JSON.stringify(error.data.message)
        } else if (error.data.detail) {
          errorMessage = typeof error.data.detail === 'string' ? error.data.detail : JSON.stringify(error.data.detail)
        } else {
          // Обрабатываем ошибки полей
          const validationErrors = Object.entries(error.data)
            .filter(([field]) => field !== 'non_field_errors')
            .map(([field, errors]: [string, any]) => {
              const fieldName = field === 'date' ? 'Дата' : 
                               field === 'start_time' || field === 'startTime' ? 'Время начала' :
                               field === 'duration' ? 'Продолжительность' :
                               field === 'max_participants' || field === 'maxParticipants' ? 'Количество мест' :
                               field === 'service' || field === 'serviceId' ? 'Услуга' :
                               field === 'price' ? 'Стоимость' : field
              const errorList = Array.isArray(errors) ? errors.join(', ') : String(errors)
              return `${fieldName}: ${errorList}`
            })
          if (validationErrors.length > 0) {
            errorMessage = validationErrors.join('\n')
          } else {
            // Если есть какие-то данные, но не распознаны, показываем их
            errorMessage = JSON.stringify(error.data)
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
  }
}
</script>

<template>
  <UModal
    v-model:open="isOpen"
    :title="event ? 'Редактировать событие' : 'Создать событие'"
    :description="event ? 'Обновить информацию о событии' : 'Создать новое групповое занятие или событие'"
    :ui="{ width: 'sm:max-w-2xl' }"
  >
    <template #body>
      <form @submit.prevent="onSubmit" class="space-y-4">
        <UFormField label="Название" required>
          <UInput
            v-model="form.name"
            placeholder="Например: Йога для начинающих"
            required
          />
        </UFormField>

        <UFormField label="Описание">
          <UTextarea
            v-model="form.description"
            placeholder="Описание события..."
            :rows="3"
          />
        </UFormField>

        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Дата" required>
            <UInput
              v-model="form.date"
              type="date"
              required
            />
          </UFormField>

          <UFormField label="Время начала" required>
            <UInput
              v-model="form.startTime"
              type="time"
              required
            />
          </UFormField>
        </div>

        <UFormField label="Услуга">
          <USelect
            v-model="form.serviceId"
            :items="services.value && services.value.length > 0 ? [
              { label: 'Без услуги', value: undefined },
              ...services.value.map(s => ({ 
                label: `${s.name}${s.duration ? ` (${s.duration} мин)` : ''}${s.price ? `, ${Math.round(s.price).toLocaleString('ru-RU')} ₽` : ''}`, 
                value: s.id 
              }))
            ] : [
              { label: 'Без услуги', value: undefined },
              { label: 'Нет доступных услуг', value: null, disabled: true }
            ]"
            placeholder="Выберите услугу"
          />
          <template v-if="servicesError" #hint>
            <span class="text-xs text-error">Ошибка загрузки услуг. Проверьте консоль для деталей.</span>
          </template>
          <template v-else-if="services.value && services.value.length === 0" #hint>
            <span class="text-xs text-muted">Создайте услуги в разделе "Услуги" или укажите стоимость и продолжительность вручную</span>
          </template>
        </UFormField>

        <div v-if="showManualFields" class="grid grid-cols-2 gap-4 p-4 bg-elevated rounded-lg border border-default">
          <UFormField label="Продолжительность (минуты)" required>
            <USelect
              v-model="form.duration"
              :items="durationOptions"
              required
            />
          </UFormField>

          <UFormField label="Стоимость (₽)" required>
            <UInput
              v-model.number="form.price"
              type="number"
              min="0"
              step="100"
              placeholder="0"
              required
            />
          </UFormField>
        </div>

        <div v-else class="grid grid-cols-2 gap-4">
          <UFormField label="Продолжительность" required>
            <USelect
              v-model="form.duration"
              :items="durationOptions"
              required
              :disabled="true"
            />
            <template #hint>
              <span class="text-xs text-muted">Автоматически из услуги</span>
            </template>
          </UFormField>

          <UFormField label="Стоимость (₽)" required>
            <UInput
              v-model.number="form.price"
              type="number"
              min="0"
              step="100"
              placeholder="0"
              required
              :disabled="true"
            />
            <template #hint>
              <span class="text-xs text-muted">Автоматически из услуги</span>
            </template>
          </UFormField>
        </div>

        <UFormField label="Количество мест" required>
          <UInput
            v-model.number="form.maxParticipants"
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
            @click="isOpen = false"
          />
          <UButton
            type="submit"
            label="Сохранить"
            color="neutral"
            variant="solid"
            class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
          />
        </div>
      </form>
    </template>
  </UModal>
</template>
