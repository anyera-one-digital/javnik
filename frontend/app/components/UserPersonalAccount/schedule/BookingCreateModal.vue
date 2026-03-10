<script setup lang="ts">
import type { Booking, Customer, Service, WorkSchedule } from '~/types'
import { format } from 'date-fns'
import { CalendarDate, DateFormatter, getLocalTimeZone, today } from '@internationalized/date'
import ServiceModal from '~/components/UserPersonalAccount/services/ServiceModal.vue'
import CustomersAddModal from '~/components/UserPersonalAccount/customers/AddModal.vue'

const dateFormatter = new DateFormatter('ru-RU', { dateStyle: 'long' })

const props = defineProps<{
  modelValue?: boolean
  defaultDate?: Date
  defaultTime?: string
  editBooking?: Booking | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
  close: []
}>()

const toast = useToast()
const { getAuthHeaders, refreshAccessToken } = useAuth()

const isOpen = computed({
  get: () => props.modelValue ?? false,
  set: (value) => emit('update:modelValue', value)
})

// Загружаем клиентов и услуги только на клиенте
const customers = ref<Customer[]>([])
const services = ref<Service[]>([])
const servicesError = ref<Error | null>(null)

// Расписание и бронирования для выбранной даты (для фильтрации доступного времени)
const workScheduleForDate = ref<WorkSchedule | null>(null)
const bookingsForDate = ref<Booking[]>([])

// При редактировании исключаем текущую запись из занятых слотов
const bookingsExcludingCurrent = computed(() => {
  const list = bookingsForDate.value
  if (!props.editBooking?.id) return list
  return list.filter(b => b.id !== props.editBooking!.id)
})

// Счетчик для принудительного обновления селекторов
const selectorsKey = ref(0)

function forceUpdateSelectors() {
  selectorsKey.value++
}

async function loadCustomers() {
  if (!process.client) return

  try {
    let headers = getAuthHeaders()
    
    if (!headers.Authorization) return
    
    try {
      const data = await $fetch<any>('/api/customers', {
        headers
      })
      
      // Убеждаемся, что data - это массив
      if (Array.isArray(data)) {
        customers.value = data as Customer[]
      } else if (data && typeof data === 'object' && 'results' in data) {
        // Если это пагинированный ответ
        customers.value = Array.isArray(data.results) ? (data.results as Customer[]) : []
      } else {
        customers.value = []
      }
      
      // Принудительно обновляем селекторы
      forceUpdateSelectors()
    } catch (error: any) {
      // Если получили 401, пытаемся обновить токен
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        
        if (refreshed) {
          headers = getAuthHeaders()
          
          try {
            const retryData = await $fetch<any>('/api/customers', {
              headers
            })
            
            // Убеждаемся, что retryData - это массив
            if (Array.isArray(retryData)) {
              customers.value = retryData as Customer[]
            } else if (retryData && typeof retryData === 'object' && 'results' in retryData) {
              customers.value = Array.isArray(retryData.results) ? (retryData.results as Customer[]) : []
            } else {
              customers.value = []
            }
            
            // Принудительно обновляем селекторы
            forceUpdateSelectors()
            return
          } catch (retryError) {
            console.error('BookingCreateModal: Retry customers after refresh failed:', retryError)
          }
        }
      }
      
      console.error('Error loading customers:', error)
      customers.value = []
    }
  } catch (error: any) {
    console.error('Unexpected error loading customers:', error)
    customers.value = []
  }
}

async function loadServices() {
  if (!process.client) return
  
  try {
    servicesError.value = null
    
    // Даем время для загрузки токена из localStorage
    await new Promise(resolve => setTimeout(resolve, 100))
    
    let headers = getAuthHeaders()
    
    if (!headers.Authorization) {
      services.value = []
      return
    }
    
    try {
      const data = await $fetch<Service[]>('/api/services', {
        headers
      })
      
      // Убеждаемся, что data - это массив
      if (Array.isArray(data)) {
        services.value = [...data] // Создаем новый массив для реактивности
      } else if (data && typeof data === 'object' && 'results' in data) {
        // Обработка пагинированного ответа
        const results = (data as any).results
        services.value = Array.isArray(results) ? [...results] : []
      } else {
        services.value = []
      }
      
      forceUpdateSelectors()
      await nextTick()
    } catch (error: any) {
      // Если получили 401, пытаемся обновить токен
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        
        if (refreshed) {
          headers = getAuthHeaders()
          
          try {
            const retryData = await $fetch<Service[]>('/api/services', {
              headers
            })
            
            // Убеждаемся, что retryData - это массив
            if (Array.isArray(retryData)) {
              services.value = [...retryData] // Создаем новый массив для реактивности
            } else if (retryData && typeof retryData === 'object' && 'results' in retryData) {
              const results = (retryData as any).results
              services.value = Array.isArray(results) ? [...results] : []
            } else {
              services.value = []
            }
            
            await nextTick()
            return
          } catch (retryError) {
            console.error('BookingCreateModal: Retry after refresh failed:', retryError)
          }
        } else {
          console.error('BookingCreateModal: Failed to refresh token')
        }
      }
      
      // Если обновление не помогло или ошибка не 401, сохраняем ошибку
      console.error('BookingCreateModal: Error loading services:', error)
      console.error('BookingCreateModal: Error status:', error.statusCode || error.status)
      console.error('BookingCreateModal: Error data:', error.data)
      servicesError.value = error
      services.value = []
    }
  } catch (error: any) {
    console.error('BookingCreateModal: Unexpected error:', error)
    servicesError.value = error
    services.value = []
  }
}

async function refreshCustomers() {
  await loadCustomers()
}

// Загружаем данные при открытии модала
watch(isOpen, async (open) => {
  if (open && process.client) {
    // Небольшая задержка для гарантии, что токен загружен
    await nextTick()
    // Дополнительная задержка для загрузки токена из localStorage
    setTimeout(async () => {
      await Promise.all([
        loadServices(),
        loadCustomers()
      ])
      await nextTick()
    }, 300)
  }
})

// Загружаем данные при монтировании компонента (только если модал открыт)
onMounted(async () => {
  if (process.client && isOpen.value) {
    await nextTick()
    setTimeout(async () => {
      await Promise.all([
        loadServices(),
        loadCustomers()
      ])
      await nextTick()
    }, 200)
  }
})

const form = reactive({
  customerId: null as number | null,
  serviceId: null as number | null,
  date: '',
  time: '',
  notes: ''
})

// Синхронизация form.date (yyyy-MM-dd) с CalendarDate для UCalendar
const calendarDate = computed({
  get: () => {
    if (!form.date || form.date.length < 10) {
      const today = new Date()
      return new CalendarDate(today.getFullYear(), today.getMonth() + 1, today.getDate())
    }
    const [y, m, d] = form.date.split('-').map(Number)
    return new CalendarDate(y, m, d)
  },
  set: (value: CalendarDate | null) => {
    if (value) {
      form.date = `${String(value.year).padStart(4, '0')}-${String(value.month).padStart(2, '0')}-${String(value.day).padStart(2, '0')}`
    }
  }
})

const isSubmitting = ref(false)
const createCustomerModalOpen = ref(false)
const createServiceModalOpen = ref(false)

// Элементы для выбора клиентов
const customerSelectItems = computed(() => {
  const items = [
    { label: 'Выберите клиента', value: null }
  ]
  
  if (!customers.value || !Array.isArray(customers.value) || customers.value.length === 0) {
    items.push({ label: 'Нет доступных клиентов', value: 'no-customers', disabled: true })
    return items
  }
  
  try {
    const customerItems = customers.value.map(c => {
      if (!c || !c.id) return null
      return { 
        label: `${c.name || 'Без имени'}${c.email ? ` (${c.email})` : ''}`, 
        value: c.id 
      }
    }).filter(Boolean)
    
    items.push(...customerItems)
    return items
  } catch (error) {
    console.error('BookingCreateModal: Error creating customer select items:', error)
    items.push({ label: 'Ошибка загрузки клиентов', value: 'error', disabled: true })
    return items
  }
})

// Проверка наличия доступных клиентов для селектора
const hasAvailableCustomers = computed(() => {
  return customerSelectItems.value.some(item => !item.disabled && item.value !== null)
})

// Выбранный клиент
const selectedCustomer = computed(() => {
  if (!form.customerId || !customers.value) return null
  return customers.value.find(c => c.id === form.customerId) || null
})

// Выбранная услуга
const selectedService = computed(() => {
  if (!form.serviceId || !services.value) return null
  return services.value.find(s => s.id === form.serviceId) || null
})

// Элементы для выбора услуг (computed для реактивности)
const serviceSelectItems = computed(() => {
  // Всегда возвращаем массив с placeholder, чтобы селектор мог открываться
  const items = [
    { label: 'Выберите услугу', value: null }
  ]
  
  if (!services.value || !Array.isArray(services.value) || services.value.length === 0) {
    items.push({ label: 'Нет доступных услуг', value: 'no-services', disabled: true })
    return items
  }
  
  try {
    const serviceItems = services.value.map(s => {
      if (!s || !s.id) return null
      return { 
        label: `${s.name || 'Без названия'} (${s.duration || 0} мин, ${Math.round(s.price || 0).toLocaleString('ru-RU')} ₽)`, 
        value: s.id 
      }
    }).filter(Boolean)
    
    items.push(...serviceItems)
    return items
  } catch (error) {
    console.error('BookingCreateModal: Error creating service select items:', error)
    items.push({ label: 'Ошибка загрузки услуг', value: 'error', disabled: true })
    return items
  }
})

// Проверка наличия доступных услуг для селектора
const hasAvailableServices = computed(() => {
  return serviceSelectItems.value.some(item => !item.disabled && item.value !== null)
})

// Открытие модала создания услуги
function openServiceModal() {
  createServiceModalOpen.value = true
}

// Обработчик создания услуги
async function handleServiceCreated() {
  createServiceModalOpen.value = false
  // Небольшая задержка перед перезагрузкой, чтобы модал успел закрыться
  await nextTick()
  setTimeout(async () => {
    await loadServices()
  }, 100)
}

function resetForm() {
  form.customerId = null
  form.serviceId = null
  form.date = ''
  form.time = ''
  form.notes = ''
}

// Округление времени до 15 минут (ч:00, ч:15, ч:30, ч:45)
function roundTimeTo15Min(timeStr: string): string {
  if (!timeStr || !timeStr.includes(':')) return '09:00'
  const [h, m] = timeStr.split(':').map(Number)
  const roundedM = Math.floor(m / 15) * 15
  return `${String(h).padStart(2, '0')}:${String(roundedM).padStart(2, '0')}`
}

// Блоки занятого времени (нерабочие часы, перерывы, брони)
function getUnavailableBlocks(): Array<{ start: number; end: number }> {
  const schedule = workScheduleForDate.value
  const dayStart = 0
  const dayEnd = 24 * 60
  const blocks: Array<{ start: number; end: number }> = []

  // Если графика нет — весь день доступен, учитываем только брони
  if (!schedule || schedule.type !== 'workday' || !schedule.startTime || !schedule.endTime) {
    const dateStr = form.date
    for (const b of bookingsExcludingCurrent.value) {
      const d = typeof b.date === 'string' ? b.date.split('T')[0] : b.date
      if (d === dateStr && b.startTime && b.endTime) {
        const [bsh, bsm] = b.startTime.split(':').map(Number)
        const [beh, bem] = b.endTime.split(':').map(Number)
        blocks.push({ start: bsh * 60 + bsm, end: beh * 60 + bem })
      }
    }
    return blocks
  }

  const [sh, sm] = schedule.startTime.split(':').map(Number)
  const [eh, em] = schedule.endTime.split(':').map(Number)
  const workStart = sh * 60 + sm
  const workEnd = eh * 60 + em

  if (workStart > dayStart) blocks.push({ start: dayStart, end: workStart })
  if (workEnd < dayEnd) blocks.push({ start: workEnd, end: dayEnd })

  if (schedule.breaks?.length) {
    for (const b of schedule.breaks) {
      const [bsh, bsm] = (b.startTime || '00:00').split(':').map(Number)
      const [beh, bem] = (b.endTime || '00:00').split(':').map(Number)
      blocks.push({ start: bsh * 60 + bsm, end: beh * 60 + bem })
    }
  }

  const dateStr = form.date
  for (const b of bookingsExcludingCurrent.value) {
    const d = typeof b.date === 'string' ? b.date.split('T')[0] : b.date
    if (d === dateStr && b.startTime && b.endTime) {
      const [bsh, bsm] = b.startTime.split(':').map(Number)
      const [beh, bem] = b.endTime.split(':').map(Number)
      blocks.push({ start: bsh * 60 + bsm, end: beh * 60 + bem })
    }
  }
  return blocks
}

// Свободные слоты, вмещающие durationMinutes минут (шаг 15 мин: 0, 15, 30, 45)
function getAvailableTimeSlots(durationMinutes: number): string[] {
  const unavailable = getUnavailableBlocks()
  const occupied = [...unavailable].sort((a, b) => a.start - b.start)
  const free: Array<{ start: number; end: number }> = []
  let cur = 0
  for (const o of occupied) {
    if (o.start > cur) free.push({ start: cur, end: o.start })
    cur = Math.max(cur, o.end)
  }
  if (cur < 24 * 60) free.push({ start: cur, end: 24 * 60 })

  const step = 15
  const slots: string[] = []
  for (const f of free) {
    let s = f.start
    while (s + durationMinutes <= f.end) {
      const h = Math.floor(s / 60)
      const m = s % 60
      slots.push(`${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`)
      s += step
    }
  }
  return slots
}

// Варианты времени: только доступные слоты для выбранной услуги на выбранную дату
// SelectItem не принимает value: '', используем плейсхолдеры с уникальными значениями
const timeSelectItems = computed(() => {
  const svc = selectedService.value
  const dateStr = form.date

  if (!svc || !dateStr) {
    return [{ label: 'Сначала выберите услугу и дату', value: '__pick_service__', disabled: true }]
  }

  const slots = getAvailableTimeSlots(svc.duration)
  if (slots.length === 0) {
    return [{ label: 'Нет доступного времени на эту дату', value: '__no_slots__', disabled: true }]
  }

  return slots.map(t => ({ label: t, value: t }))
})

// Сбрасываем время, если выбранный слот больше недоступен
watch(timeSelectItems, (items) => {
  const validValues = items
    .filter(i => !i.disabled && i.value && !String(i.value).startsWith('__'))
    .map(i => i.value)
  if (validValues.length > 0 && form.time && !validValues.includes(form.time)) {
    form.time = validValues[0]
  }
}, { deep: true })

watch(isOpen, async (open) => {
  if (open) {
    if (props.editBooking) {
      const b = props.editBooking
      form.customerId = (b.customerId ?? b.customer) ?? null
      form.serviceId = (b.serviceId ?? b.service) ?? null
      form.date = typeof b.date === 'string' ? b.date.split('T')[0] : b.date
      form.time = b.startTime ? roundTimeTo15Min(b.startTime.slice(0, 5)) : '09:00'
      form.notes = b.notes || ''
    } else {
      form.date = props.defaultDate ? format(props.defaultDate, 'yyyy-MM-dd') : format(new Date(), 'yyyy-MM-dd')
      const rawTime = props.defaultTime || new Date().toTimeString().slice(0, 5)
      form.time = roundTimeTo15Min(rawTime)
    }
  } else {
    resetForm()
  }
})

// Загружаем расписание и бронирования при смене даты
watch(() => form.date, async (dateStr) => {
  if (!dateStr || !process.client) {
    workScheduleForDate.value = null
    bookingsForDate.value = []
    return
  }
  const headers = getAuthHeaders()
  if (!headers.Authorization) return
  try {
    const [schedulesRes, bookingsRes] = await Promise.all([
      $fetch<WorkSchedule[]>(`/api/schedule`, {
        query: { start_date: dateStr, end_date: dateStr },
        headers
      }),
      $fetch<Booking[]>(`/api/bookings`, {
        query: { date: dateStr },
        headers
      })
    ])
    workScheduleForDate.value = Array.isArray(schedulesRes) && schedulesRes[0] ? schedulesRes[0] : null
    let arr: Booking[] = []
    if (Array.isArray(bookingsRes)) arr = bookingsRes
    else if (bookingsRes && typeof bookingsRes === 'object' && 'results' in bookingsRes) arr = (bookingsRes as any).results || []
    else if (bookingsRes && typeof bookingsRes === 'object' && 'data' in bookingsRes) arr = (bookingsRes as any).data || []
    bookingsForDate.value = arr
  } catch (e) {
    console.error('BookingCreateModal: Error loading schedule/bookings:', e)
    workScheduleForDate.value = null
    bookingsForDate.value = []
  }
}, { immediate: false })

// Обработка создания нового клиента
async function handleCustomerCreated() {
  await loadCustomers()
  createCustomerModalOpen.value = false
  // Если был создан клиент, можно автоматически выбрать его
  // Но для простоты оставим выбор клиента пользователю
}

async function onSubmit() {
  if (!form.customerId) {
    toast.add({
      title: 'Ошибка',
      description: 'Пожалуйста, выберите клиента',
      color: 'error'
    })
    return
  }

  if (!form.serviceId) {
    toast.add({
      title: 'Ошибка',
      description: 'Пожалуйста, выберите услугу',
      color: 'error'
    })
    return
  }

  const customer = selectedCustomer.value
  const service = selectedService.value

  // Проверка корректности времени (не плейсхолдер)
  if (!form.time || String(form.time).startsWith('__')) {
    toast.add({
      title: 'Ошибка',
      description: 'Пожалуйста, выберите время',
      color: 'error'
    })
    return
  }

  if (!customer || !service) {
    toast.add({
      title: 'Ошибка',
      description: 'Клиент или услуга не найдены',
      color: 'error'
    })
    return
  }

  // Проверка комментария
  if (form.notes && form.notes.length > 150) {
    toast.add({
      title: 'Ошибка',
      description: 'Комментарий не может превышать 150 символов',
      color: 'error'
    })
    return
  }

  isSubmitting.value = true

  // Округляем время до 15 минут перед отправкой
  const roundedTime = roundTimeTo15Min(form.time)

  const body: Record<string, unknown> = {
    customerId: customer.id,
    serviceId: service.id,
    customerName: customer.name,
    customerEmail: customer.email,
    customerPhone: customer.phone || '',
    notes: form.notes || '',
    date: form.date,
    startTime: roundedTime,
    duration: service.duration
  }

  // Для PATCH бэкенд ожидает endTime (модель Booking использует start_time и end_time)
  if (props.editBooking?.id) {
    const [h, m] = roundedTime.split(':').map(Number)
    const endMinutes = h * 60 + m + service.duration
    const endH = Math.floor(endMinutes / 60)
    const endM = endMinutes % 60
    body.endTime = `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}`
  }

  try {
    if (props.editBooking?.id) {
      await $fetch(`/api/bookings/${props.editBooking.id}`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body
      })
      toast.add({
        title: 'Успешно',
        description: 'Запись обновлена',
        color: 'success'
      })
    } else {
      await $fetch('/api/bookings', {
        method: 'POST',
        headers: getAuthHeaders(),
        body
      })
      toast.add({
        title: 'Успешно',
        description: 'Запись успешно создана',
        color: 'success'
      })
    }

    // Небольшая задержка перед закрытием модала и обновлением данных
    await nextTick()
    emit('saved')
    isOpen.value = false
  } catch (error: any) {
    console.error('BookingCreateModal: Error creating booking:', error)
    
    // Извлекаем сообщение об ошибке из разных возможных мест
    let errorMessage = 'Не удалось создать запись. Попробуйте позже.'
    
    const toStr = (v: unknown): string => {
      if (typeof v === 'string') return v
      if (typeof v === 'object' && v !== null) return JSON.stringify(v)
      return String(v)
    }
    
    if (error.data) {
      if (typeof error.data === 'string') {
        errorMessage = error.data
      } else if (error.data.error !== undefined) {
        errorMessage = toStr(error.data.error)
      } else if (error.data.message !== undefined) {
        errorMessage = toStr(error.data.message)
      } else if (error.data.detail !== undefined) {
        errorMessage = toStr(error.data.detail)
      } else if (typeof error.data === 'object') {
        const errorKeys = Object.keys(error.data)
        if (errorKeys.length > 0) {
          const firstError = error.data[errorKeys[0]]
          if (Array.isArray(firstError)) {
            errorMessage = toStr(firstError[0])
          } else if (firstError !== undefined) {
            errorMessage = toStr(firstError)
          }
        }
      }
    } else if (error.message) {
      errorMessage = String(error.message)
    } else if (error.statusMessage) {
      errorMessage = String(error.statusMessage)
    }
    
    // Не показываем "true"/"false" — это бесполезно для пользователя
    const isUnhelpful = errorMessage === 'true' || errorMessage === 'false' || errorMessage === ''
    const status500 = error?.statusCode === 500 || error?.status === 500
    let safeDescription: string
    if (typeof errorMessage === 'string' && !isUnhelpful) {
      safeDescription = errorMessage.length > 300 ? errorMessage.slice(0, 300) + '...' : errorMessage
    } else {
      safeDescription = status500
        ? 'Ошибка сервера. Проверьте терминал backend и Nuxt для деталей.'
        : 'Не удалось создать запись. Попробуйте позже.'
    }
    
    toast.add({
      title: 'Ошибка',
      description: safeDescription,
      color: 'error',
      timeout: 5000
    })
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <UModal
    v-model:open="isOpen"
    :title="editBooking ? 'Редактировать запись' : 'Создать запись'"
    :description="editBooking ? 'Изменить данные записи' : 'Создать новую запись для клиента'"
    :ui="{ width: 'sm:max-w-lg' }"
  >
    <template #body>
      <form @submit.prevent="onSubmit" class="space-y-4">
        <!-- Выбор клиента -->
        <UFormField label="Клиент" required>
          <div class="flex gap-2">
              <USelect
                :key="`customer-select-${selectorsKey}-${customers.value?.length || 0}`"
                v-model="form.customerId"
                :items="customerSelectItems"
                placeholder="Выберите клиента"
                class="flex-1"
                required
              />
              <UButton
                icon="i-lucide-plus"
                color="neutral"
                variant="outline"
                square
                @click="createCustomerModalOpen = true"
              />
            </div>
        </UFormField>

        <!-- Данные клиента (автозаполнение) -->
        <div v-if="selectedCustomer" class="p-3 bg-muted/30 rounded-lg space-y-1 text-sm">
          <div class="flex justify-between">
            <span class="text-muted">Имя:</span>
            <span class="font-medium">{{ selectedCustomer.name }}</span>
          </div>
          <div v-if="selectedCustomer.email" class="flex justify-between">
            <span class="text-muted">Email:</span>
            <span class="font-medium">{{ selectedCustomer.email }}</span>
          </div>
          <div v-if="selectedCustomer.phone" class="flex justify-between">
            <span class="text-muted">Телефон:</span>
            <span class="font-medium">{{ selectedCustomer.phone }}</span>
          </div>
        </div>

        <!-- Выбор услуги -->
        <UFormField label="Услуга" required>
          <div class="flex gap-2">
            <USelect
              :key="`service-select-${selectorsKey}-${services.value?.length || 0}-${isOpen}`"
              v-model="form.serviceId"
              :items="serviceSelectItems"
              placeholder="Выберите услугу"
              class="flex-1"
              required
            />
            <UButton
              icon="i-lucide-plus"
              color="neutral"
              variant="outline"
              square
              @click="openServiceModal"
            />
          </div>
          <template v-if="servicesError" #hint>
            <span class="text-xs text-error">Ошибка загрузки услуг. Проверьте консоль для деталей.</span>
          </template>
          <template v-else-if="services.value && services.value.length === 0" #hint>
            <span class="text-xs text-muted">Создайте услуги в разделе "Услуги"</span>
          </template>
        </UFormField>

        <!-- Продолжительность (автоматически из услуги) -->
        <div v-if="selectedService" class="p-3 bg-muted/30 rounded-lg text-sm">
          <div class="flex justify-between">
            <span class="text-muted">Продолжительность:</span>
            <span class="font-medium">{{ selectedService.duration }} минут</span>
          </div>
        </div>

        <!-- Дата и время -->
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
                  <div class="flex justify-end gap-2 p-2 border-t border-default">
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
              v-model="form.time"
              :items="timeSelectItems"
              placeholder="Выберите время"
            />
          </UFormField>
        </div>

        <!-- Комментарий -->
        <UFormField label="Комментарий (необязательно, до 150 символов)">
          <UTextarea
            v-model="form.notes"
            placeholder="Дополнительная информация..."
            :rows="3"
            :maxlength="150"
            class="w-full"
          />
          <template #hint>
            <span class="text-xs text-muted">
              {{ form.notes.length }}/150 символов
            </span>
          </template>
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
            :label="editBooking ? 'Сохранить' : 'Создать запись'"
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

  <!-- Модал создания нового клиента -->
  <CustomersAddModal
    v-model="createCustomerModalOpen"
    @saved="handleCustomerCreated"
  />

  <!-- Модал создания новой услуги -->
  <ServiceModal
    v-model="createServiceModalOpen"
    @saved="handleServiceCreated"
  />
</template>
