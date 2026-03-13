<script setup lang="ts">
import { format, startOfDay, endOfDay, eachDayOfInterval, startOfWeek, endOfWeek, addDays, isSameDay, parse } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { Booking, Member, Event, Service, WorkSchedule } from '~/types'
import BookingCreateModal from '~/components/UserPersonalAccount/schedule/BookingCreateModal.vue'
import ScheduleEventModal from '~/components/UserPersonalAccount/schedule/EventModal.vue'
import ScheduleBookingDetailModal from '~/components/UserPersonalAccount/schedule/BookingDetailModal.vue'
import { formatWeekdayShort } from '~/utils'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const route = useRoute()
const router = useRouter()

const viewMode = ref<'day' | 'week'>('week')

// Нормализуем дату из query параметра
function parseDateFromQuery(dateStr: string | undefined): Date {
  if (!dateStr) return startOfDay(new Date())
  try {
    return startOfDay(parse(dateStr, 'yyyy-MM-dd', new Date()))
  } catch {
    return startOfDay(new Date())
  }
}

const selectedDate = ref<Date>(route.query.date ? parseDateFromQuery(route.query.date as string) : startOfDay(new Date()))

const { getAuthHeaders, refreshAccessToken, user } = useAuth()

const bookings = ref<Booking[]>([])
const services = ref<Service[]>([])
const allBookings = ref<Booking[]>([])
const allEvents = ref<Event[]>([])

async function loadBookings() {
  if (!process.client) return
  
  try {
    let headers = getAuthHeaders()
    if (!headers.Authorization) {
      const { getAuthHeaders: refreshHeaders } = useAuth()
      headers = refreshHeaders()
      if (!headers.Authorization) return
    }

    try {
      const date = viewMode.value === 'day' ? format(selectedDate.value, 'yyyy-MM-dd') : undefined
      const url = date ? `/api/bookings/?date=${date}` : '/api/bookings/'
      const data = await $fetch<any>(url, { headers })

      // Обрабатываем разные форматы ответа
      let bookingsArray: Booking[] = []

      if (Array.isArray(data)) {
        bookingsArray = data
      } else if (data && typeof data === 'object') {
        if (Array.isArray(data.results)) {
          bookingsArray = data.results
        } else if (Array.isArray(data.data)) {
          bookingsArray = data.data
        } else if (Array.isArray(data.bookings)) {
          bookingsArray = data.bookings
        } else if (data.id) {
          // Один объект бронирования
          bookingsArray = [data]
        }
      }

      bookings.value = bookingsArray
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const date = viewMode.value === 'day' ? format(selectedDate.value, 'yyyy-MM-dd') : undefined
          const url = date ? `/api/bookings/?date=${date}` : '/api/bookings/'
          const retryData = await $fetch<Booking[]>(url, { headers })
          bookings.value = retryData || []
          return
        }
      }
      bookings.value = []
    }
  } catch (error) {
    bookings.value = []
  }
}

async function loadServices() {
  if (!process.client) return
  
  try {
    let headers = getAuthHeaders()
    if (!headers.Authorization) return

    try {
      const data = await $fetch<Service[]>('/api/services/', { headers })
      services.value = data || []
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retryData = await $fetch<Service[]>('/api/services/', { headers })
          services.value = retryData || []
          return
        }
      }
      services.value = []
    }
  } catch (error) {
    services.value = []
  }
}

async function loadAllBookings() {
  if (!process.client) return
  
  try {
    let headers = getAuthHeaders()
    if (!headers.Authorization) {
      const { getAuthHeaders: refreshHeaders } = useAuth()
      headers = refreshHeaders()
      if (!headers.Authorization) return
    }

    try {
      const data = await $fetch<any>('/api/bookings/', { headers })

      // Обрабатываем разные форматы ответа
      let bookingsArray: Booking[] = []

      if (Array.isArray(data)) {
        bookingsArray = data
      } else if (data && typeof data === 'object') {
        if (Array.isArray(data.results)) {
          bookingsArray = data.results
        } else if (Array.isArray(data.data)) {
          bookingsArray = data.data
        } else if (Array.isArray(data.bookings)) {
          bookingsArray = data.bookings
        } else if (data.id) {
          // Один объект бронирования
          bookingsArray = [data]
        }
      }

      allBookings.value = bookingsArray
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retryData = await $fetch<Booking[]>('/api/bookings/', { headers })
          allBookings.value = retryData || []
          return
        }
      }
      allBookings.value = []
    }
  } catch (error) {
    allBookings.value = []
  }
}

async function loadAllEvents() {
  if (!process.client) return
  
  try {
    let headers = getAuthHeaders()
    if (!headers.Authorization) return
    
    try {
      const data = await $fetch<Event[]>('/api/events', { headers })
      allEvents.value = data || []
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retryData = await $fetch<Event[]>('/api/events', { headers })
          allEvents.value = retryData || []
          return
        }
      }
      allEvents.value = []
    }
  } catch (error) {
    allEvents.value = []
  }
}

async function refreshBookings() {
  // Загружаем все бронирования для недельного режима
  await loadAllBookings()
  // Загружаем бронирования для текущего дня/недели
  await loadBookings()
}

async function refreshEvents() {
  await loadAllEvents()
}

// Загружаем данные при монтировании
onMounted(async () => {
  if (process.client) {
    await nextTick()
    // Небольшая задержка для загрузки токена
    setTimeout(async () => {
      try {
        await Promise.all([
          loadBookings(),
          loadServices(),
          loadAllBookings(),
          loadAllEvents()
        ])
      } catch {
        // Данные загрузятся при следующем взаимодействии
      }
    }, 300)
  }
})

// Обновляем bookings при изменении даты или режима просмотра
watch([selectedDate, viewMode], async () => {
  if (process.client) {
    await nextTick()
    await loadBookings()
  }
}, { flush: 'post' })

// Загружаем график работы для отображаемых дат
const workSchedules = ref<Map<string, WorkSchedule>>(new Map())

const events = computed(() => {
  if (!allEvents.value || !Array.isArray(allEvents.value) || allEvents.value.length === 0) return []
  if (viewMode.value === 'day') {
    const dateStr = format(selectedDate.value, 'yyyy-MM-dd')
    return allEvents.value.filter(e => e && e.date === dateStr)
  }
  // Для недельного вида возвращаем все события для отображения в календаре
  return allEvents.value.filter(e => e)
})

const eventModalOpen = ref(false)
const selectedEvent = ref<Event | null>(null)

const bookingModalOpen = ref(false)
const selectedBooking = ref<Booking | null>(null)
const selectedBookingForEdit = ref<Booking | null>(null)
const bookingDetailModalOpen = ref(false)

// Для открытия модалки создания брони из слота (дата и время слота)
const slotDateForModal = ref<Date | null>(null)
const slotTimeForModal = ref<string | null>(null)

function openBookingDetail(booking: Booking) {
  selectedBooking.value = booking
  bookingDetailModalOpen.value = true
}

function openEventDetail(event: Event) {
  selectedEvent.value = event
  eventModalOpen.value = true
}

function openBookingEdit(booking: Booking) {
  selectedBookingForEdit.value = booking
  bookingDetailModalOpen.value = false
  bookingModalOpen.value = true
}

function openBookingForSlot(date: Date, hour: number, minute: number) {
  if (!isTimeSlotAvailable(date, hour, minute)) return
  slotDateForModal.value = date
  slotTimeForModal.value = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
  selectedBookingForEdit.value = null
  bookingModalOpen.value = true
}

watch(bookingModalOpen, (open) => {
  if (!open) {
    selectedBookingForEdit.value = null
    slotDateForModal.value = null
    slotTimeForModal.value = null
  }
})

watch(eventModalOpen, (open) => {
  if (!open) selectedEvent.value = null
})

async function handleBookingDetailUpdated() {
  await nextTick()
  await refreshBookings()
}

// Получаем все даты с бронированиями для календаря
const bookingsDates = computed(() => {
  if (!allBookings.value || !Array.isArray(allBookings.value)) return []
  return [...new Set(allBookings.value.filter(b => b && b.date).map(b => b.date))]
})

// Для недельного вида
const weekStart = computed(() => startOfWeek(selectedDate.value, { locale: ru }))
const weekEnd = computed(() => endOfWeek(selectedDate.value, { locale: ru }))
const weekDays = computed(() => eachDayOfInterval({ start: weekStart.value, end: weekEnd.value }))

async function loadWorkSchedules() {
  if (!process.client) return
  
  try {
    const datesToLoad = viewMode.value === 'day' 
      ? [selectedDate.value]
      : weekDays.value
    
    if (!datesToLoad || datesToLoad.length === 0) return
    
    const startDate = format(datesToLoad[0], 'yyyy-MM-dd')
    const endDate = format(datesToLoad[datesToLoad.length - 1], 'yyyy-MM-dd')
    
    const headers = getAuthHeaders()
    if (!headers || !headers.Authorization) {
      console.warn('No auth headers available for loading work schedules')
      return
    }

    const response = await $fetch<WorkSchedule[]>('/api/schedule/', {
      query: {
        start_date: startDate,
        end_date: endDate
      },
      headers
    })
    
    // Очищаем графики только для текущего диапазона дат
    datesToLoad.forEach(date => {
      const dateStr = format(date, 'yyyy-MM-dd')
      workSchedules.value.delete(dateStr)
    })
    
    // Загружаем новые графики
    if (Array.isArray(response)) {
      response.forEach(schedule => {
        if (schedule && schedule.date) {
          workSchedules.value.set(schedule.date, schedule)
        }
      })
    }
  } catch (error) {
    console.error('Error loading work schedules:', error)
    // Не очищаем существующие графики при ошибке, чтобы не потерять данные
  }
}

// Загружаем график работы при изменении даты или режима просмотра
watch([selectedDate, viewMode], () => {
  if (process.client) {
    nextTick(() => {
      loadWorkSchedules()
    })
  }
})

// Загружаем график работы при монтировании компонента
onMounted(() => {
  nextTick(() => {
    loadWorkSchedules()
  })
})

// Для дневного вида - мини-календарь дней недели
const dayViewWeekDays = computed(() => {
  const start = startOfWeek(selectedDate.value, { locale: ru })
  const end = endOfWeek(selectedDate.value, { locale: ru })
  return eachDayOfInterval({ start, end })
})

// Вычисляем минимальное и максимальное рабочее время из всех графиков
const workTimeRange = computed(() => {
  if (workSchedules.value.size === 0) {
    // Если графиков нет, возвращаем стандартный рабочий день (9:00 - 21:00)
    return { minHour: 9, maxHour: 21 }
  }
  
  let minHour: number | null = null
  let maxHour: number | null = null
  let maxEndMinute: number = 0
  
  // Проходим по всем графикам и находим минимальное и максимальное рабочее время
  for (const schedule of workSchedules.value.values()) {
    if (schedule.type === 'workday' && schedule.startTime && schedule.endTime) {
      const [startHour] = schedule.startTime.split(':').map(Number)
      const [endHour, endMinute = 0] = schedule.endTime.split(':').map(Number)
      
      // Находим минимальный час начала рабочего дня
      if (minHour === null || startHour < minHour) {
        minHour = startHour
      }
      
      // Находим максимальное время окончания (если график до 22:00 — не показываем час 22)
      const endMinutes = endHour * 60 + endMinute
      const currentMaxMinutes = maxHour !== null ? maxHour * 60 + maxEndMinute : 0
      if (maxHour === null || endMinutes > currentMaxMinutes) {
        maxHour = endHour
        maxEndMinute = endMinute
      }
    }
  }
  
  // Если не найдено ни одного рабочего дня, возвращаем стандартный диапазон
  if (minHour === null || maxHour === null) {
    return { minHour: 9, maxHour: 21 }
  }
  
  // Если график заканчивается ровно на часу (22:00), последний час не показываем
  const maxDisplayHour = maxEndMinute === 0 ? maxHour - 1 : maxHour
  return { minHour, maxHour: Math.max(minHour, maxDisplayHour) }
})

const dayHours = computed(() => {
  const hours = []
  const { minHour, maxHour } = workTimeRange.value
  for (let i = minHour; i <= maxHour; i++) {
    hours.push(i)
  }
  return hours
})

// Слоты по 30 минут для hover/click (добавить бронь)
const daySlots = computed(() => {
  const slots: { hour: number, minute: number }[] = []
  for (const hour of dayHours.value) {
    slots.push({ hour, minute: 0 })
    slots.push({ hour, minute: 30 })
  }
  return slots
})

// Индикатор текущего времени (обновляется каждую минуту)
const now = useNow({ interval: 60000 })
const currentTimeFormatted = computed(() => format(now.value, 'HH:mm'))
const currentTimeIndicatorVisible = computed(() => {
  const today = startOfDay(new Date())
  if (viewMode.value === 'day') return isSameDay(selectedDate.value, today)
  return weekDays.value.some(d => isSameDay(d, today))
})
const currentTimeTopPx = computed(() => {
  const hours = dayHours.value
  if (hours.length === 0) return 0
  const firstHour = hours[0]
  const lastHour = hours[hours.length - 1]
  const dayStartMinutes = firstHour * 60
  const dayEndMinutes = (lastHour + 1) * 60
  const currentMinutes = now.value.getHours() * 60 + now.value.getMinutes()
  if (currentMinutes < dayStartMinutes || currentMinutes >= dayEndMinutes) return -1
  const HOUR_HEIGHT_PX = 48
  const MINUTE_HEIGHT_PX = HOUR_HEIGHT_PX / 60
  return (currentMinutes - dayStartMinutes) * MINUTE_HEIGHT_PX
})

function getBookingsForDate(date: Date): Booking[] {
  const bookingsList = viewMode.value === 'week' ? allBookings.value : bookings.value
  if (!bookingsList || !Array.isArray(bookingsList)) return []
  const dateStr = format(date, 'yyyy-MM-dd')
  return bookingsList.filter(b => {
    if (!b || !b.date) return false
    const bookingDate = typeof b.date === 'string' ? b.date.split('T')[0] : b.date
    return bookingDate === dateStr
  })
}

/**
 * Определяет цвет брони на основе услуги (только для подтвержденных броней)
 * Использует цвета из палитры Tailwind 500 и 600
 */
function getBookingColorClass(booking: Booking): string {
  // Неподтвержденные остаются желтыми
  if (booking.status !== 'confirmed') {
    if (booking.status === 'pending') return 'bg-yellow-500'
    if (booking.status === 'cancelled') return 'bg-red-500'
    if (booking.status === 'completed') return 'bg-blue-500'
    return 'bg-yellow-500'
  }
  
  // Для подтвержденных - определяем цвет по названию услуги
  const serviceName = (booking.serviceName || '').toLowerCase()
  
  // Маппинг услуг на цвета (Tailwind 500/600)
  if (serviceName.includes('маникюр') || serviceName.includes('маникюра')) {
    return 'bg-blue-500'
  }
  if (serviceName.includes('педикюр') || serviceName.includes('педикюра')) {
    return 'bg-indigo-500'
  }
  if (serviceName.includes('стрижк') || serviceName.includes('стрижк')) {
    return 'bg-green-600'
  }
  if (serviceName.includes('наращивани') || serviceName.includes('наращивани')) {
    return 'bg-purple-500'
  }
  if (serviceName.includes('окрашивани') || serviceName.includes('окрашивани') || serviceName.includes('окраск')) {
    return 'bg-pink-500'
  }
  if (serviceName.includes('укладк') || serviceName.includes('укладк')) {
    return 'bg-cyan-500'
  }
  if (serviceName.includes('брови') || serviceName.includes('бров')) {
    return 'bg-orange-500'
  }
  if (serviceName.includes('ресниц') || serviceName.includes('ресниц')) {
    return 'bg-rose-500'
  }
  
  // Цвет по умолчанию для других услуг
  return 'bg-teal-500'
}

function getBookingsForTimeSlot(date: Date, hour: number, minute: number = 0): Booking[] {
  if (!bookings.value || !Array.isArray(bookings.value)) return []
  const dateStr = format(date, 'yyyy-MM-dd')
  const timeStr = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`
  
  return bookings.value.filter(b => {
    if (!b || b.date !== dateStr || !b.startTime || !b.endTime) return false
    try {
      const [startHour, startMinute] = b.startTime.split(':').map(Number)
      const [endHour, endMinute] = b.endTime.split(':').map(Number)
      
      const slotTime = hour * 60 + minute
      const startTime = startHour * 60 + startMinute
      const endTime = endHour * 60 + endMinute
      
      return slotTime >= startTime && slotTime < endTime
    } catch {
      return false
    }
  })
}

function getBookingPosition(booking: Booking, date: Date): { top: string, height: string } {
  const [startHour, startMinute] = booking.startTime.split(':').map(Number)
  const [endHour, endMinute] = booking.endTime.split(':').map(Number)
  
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = endHour * 60 + endMinute
  
  // Используем первый час из отображаемых часов как базовый для расчета позиции
  const hours = dayHours.value
  if (hours.length === 0) {
    return { top: '0px', height: '0px' }
  }
  
  const firstDisplayedHour = hours[0]
  const lastDisplayedHour = hours[hours.length - 1]
  
  // Базовое время - начало первого отображаемого часа (например, 9:00 = 540 минут)
  const dayStartMinutes = firstDisplayedHour * 60
  const dayEndMinutes = (lastDisplayedHour + 1) * 60 // +1 чтобы включить последний час полностью
  
  // Обрезаем бронирование по границам отображаемого диапазона
  const clampedStartMinutes = Math.max(startMinutes, dayStartMinutes)
  const clampedEndMinutes = Math.min(endMinutes, dayEndMinutes)
  
  // Если бронирование полностью вне диапазона, не отображаем его
  if (clampedStartMinutes >= clampedEndMinutes) {
    return { top: '0px', height: '0px' }
  }
  
  // Вычисляем относительную позицию от начала дня (в минутах)
  const relativeStart = clampedStartMinutes - dayStartMinutes
  const duration = clampedEndMinutes - clampedStartMinutes
  
  // Фиксированная высота одного часа в пикселях (48px = 3rem)
  const HOUR_HEIGHT_PX = 48
  const MINUTE_HEIGHT_PX = HOUR_HEIGHT_PX / 60
  
  // Вычисляем позицию в пикселях для точного выравнивания
  // relativeStart уже в минутах от начала дня, умножаем на высоту одной минуты
  const topPx = relativeStart * MINUTE_HEIGHT_PX
  const heightPx = duration * MINUTE_HEIGHT_PX
  
  return {
    top: `${topPx}px`,
    height: `${heightPx}px`
  }
}

// Вычисляем длительность бронирования в минутах
function getBookingDuration(booking: Booking): number {
  const [startHour, startMinute] = booking.startTime.split(':').map(Number)
  const [endHour, endMinute] = booking.endTime.split(':').map(Number)
  
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = endHour * 60 + endMinute
  
  return endMinutes - startMinutes
}

function getEventPosition(event: Event, date: Date): { top: string, height: string } {
  const [startHour, startMinute] = event.startTime.split(':').map(Number)
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = startMinutes + event.duration
  
  // Используем первый час из отображаемых часов как базовый для расчета позиции
  const hours = dayHours.value
  if (hours.length === 0) {
    return { top: '0px', height: '0px' }
  }
  
  const firstDisplayedHour = hours[0]
  const lastDisplayedHour = hours[hours.length - 1]
  const dayStartMinutes = firstDisplayedHour * 60
  const dayEndMinutes = (lastDisplayedHour + 1) * 60 // +1 чтобы включить последний час полностью
  
  // Обрезаем событие по границам отображаемого диапазона
  const clampedStartMinutes = Math.max(startMinutes, dayStartMinutes)
  const clampedEndMinutes = Math.min(endMinutes, dayEndMinutes)
  
  // Если событие полностью вне диапазона, не отображаем его
  if (clampedStartMinutes >= clampedEndMinutes) {
    return { top: '0px', height: '0px' }
  }
  
  const relativeStart = clampedStartMinutes - dayStartMinutes
  const duration = clampedEndMinutes - clampedStartMinutes
  
  // Фиксированная высота одного часа в пикселях (48px = 3rem)
  const HOUR_HEIGHT_PX = 48
  const MINUTE_HEIGHT_PX = HOUR_HEIGHT_PX / 60
  
  // Вычисляем позицию в пикселях для точного выравнивания
  const topPx = (relativeStart * MINUTE_HEIGHT_PX)
  const heightPx = (duration * MINUTE_HEIGHT_PX)
  
  return {
    top: `${topPx}px`,
    height: `${heightPx}px`
  }
}

function getEventsForDate(date: Date): Event[] {
  if (!allEvents.value || !Array.isArray(allEvents.value)) return []
  const dateStr = format(date, 'yyyy-MM-dd')
  return allEvents.value.filter(e => e && e.date === dateStr)
}

function getServiceName(serviceId?: number): string {
  if (!serviceId || !services.value) return ''
  const service = services.value.find(s => s.id === serviceId)
  return service?.name || ''
}

// Получаем график работы для даты
function getWorkScheduleForDate(date: Date): WorkSchedule | undefined {
  const dateStr = format(date, 'yyyy-MM-dd')
  return workSchedules.value.get(dateStr)
}

// Проверяем, доступен ли временной слот для бронирования
function isTimeSlotAvailable(date: Date, hour: number, minute: number = 0): boolean {
  const schedule = getWorkScheduleForDate(date)
  
  // Если графика нет, считаем что день доступен полностью
  if (!schedule) return true
  
  // Если день не рабочий, слот недоступен
  if (schedule.type !== 'workday') return false
  
  // Если нет рабочего времени, слот недоступен
  if (!schedule.startTime || !schedule.endTime) return false
  
  // Конвертируем время в минуты
  const [startHour, startMinute] = schedule.startTime.split(':').map(Number)
  const [endHour, endMinute] = schedule.endTime.split(':').map(Number)
  const slotMinutes = hour * 60 + minute
  const workStartMinutes = startHour * 60 + startMinute
  const workEndMinutes = endHour * 60 + endMinute
  
  // Проверяем, находится ли слот в рабочем времени
  // slotMinutes < workEndMinutes: слот доступен если его начало строго до конца работы
  // (слот 22:00 при работе до 22:00 недоступен; при работе до 23:00 — доступен)
  if (slotMinutes < workStartMinutes || slotMinutes >= workEndMinutes) {
    return false
  }
  
  // Проверяем, не попадает ли слот в перерыв
  if (schedule.breaks && schedule.breaks.length > 0) {
    for (const breakItem of schedule.breaks) {
      const [breakStartHour, breakStartMinute] = breakItem.startTime.split(':').map(Number)
      const [breakEndHour, breakEndMinute] = breakItem.endTime.split(':').map(Number)
      const breakStartMinutes = breakStartHour * 60 + breakStartMinute
      const breakEndMinutes = breakEndHour * 60 + breakEndMinute
      
      // Если слот попадает в перерыв, он недоступен
      if (slotMinutes >= breakStartMinutes && slotMinutes < breakEndMinutes) {
        return false
      }
    }
  }
  
  return true
}

// Получаем позицию для блока недоступного времени
function getUnavailableTimePosition(startHour: number, startMinute: number, endHour: number, endMinute: number): { top: string, height: string } {
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = endHour * 60 + endMinute
  
  // Используем диапазон отображаемых часов (включая последний час полностью: 22:00-23:00)
  const { minHour, maxHour } = workTimeRange.value
  const dayStartMinutes = minHour * 60
  const dayEndMinutes = (maxHour + 1) * 60
  
  // Ограничиваем блок диапазоном отображаемых часов
  const clampedStartMinutes = Math.max(startMinutes, dayStartMinutes)
  const clampedEndMinutes = Math.min(endMinutes, dayEndMinutes)
  
  // Если блок полностью вне диапазона, не отображаем его
  if (clampedStartMinutes >= clampedEndMinutes) {
    return { top: '0px', height: '0px' }
  }
  
  const relativeStart = clampedStartMinutes - dayStartMinutes
  const duration = clampedEndMinutes - clampedStartMinutes
  
  // Фиксированная высота одного часа в пикселях (48px = 3rem)
  const HOUR_HEIGHT_PX = 48
  const MINUTE_HEIGHT_PX = HOUR_HEIGHT_PX / 60
  
  // Вычисляем позицию в пикселях для точного выравнивания
  const topPx = (relativeStart * MINUTE_HEIGHT_PX)
  const heightPx = (duration * MINUTE_HEIGHT_PX)
  
  return {
    top: `${topPx}px`,
    height: `${heightPx}px`
  }
}

// Получаем блоки недоступного времени для даты
function getUnavailableTimeBlocks(date: Date): Array<{ start: number, end: number }> {
  const schedule = getWorkScheduleForDate(date)
  const blocks: Array<{ start: number, end: number }> = []
  
  // Получаем диапазон отображаемых часов (включая последний час полностью: 22:00-23:00)
  const { minHour, maxHour } = workTimeRange.value
  const displayStartMinutes = minHour * 60
  const displayEndMinutes = (maxHour + 1) * 60
  
  if (!schedule) {
    // Если графика нет, весь отображаемый диапазон доступен
    return blocks
  }
  
  if (schedule.type !== 'workday') {
    // Если день не рабочий, весь отображаемый диапазон недоступен
    return [{ start: displayStartMinutes, end: displayEndMinutes }]
  }
  
  if (!schedule.startTime || !schedule.endTime) {
    // Если нет рабочего времени, весь отображаемый диапазон недоступен
    return [{ start: displayStartMinutes, end: displayEndMinutes }]
  }
  
  const [startHour, startMinute] = schedule.startTime.split(':').map(Number)
  const [endHour, endMinute] = schedule.endTime.split(':').map(Number)
  const workStartMinutes = startHour * 60 + startMinute
  const workEndMinutes = endHour * 60 + endMinute
  
  // Время до начала рабочего дня (только в пределах отображаемого диапазона)
  if (workStartMinutes > displayStartMinutes) {
    blocks.push({ start: displayStartMinutes, end: Math.min(workStartMinutes, displayEndMinutes) })
  }
  
  // Перерывы в рабочем времени
  if (schedule.breaks && schedule.breaks.length > 0) {
    for (const breakItem of schedule.breaks) {
      const [breakStartHour, breakStartMinute] = breakItem.startTime.split(':').map(Number)
      const [breakEndHour, breakEndMinute] = breakItem.endTime.split(':').map(Number)
      const breakStartMinutes = breakStartHour * 60 + breakStartMinute
      const breakEndMinutes = breakEndHour * 60 + breakEndMinute
      
      // Проверяем, что перерыв находится в рабочем времени и в отображаемом диапазоне
      if (breakStartMinutes >= workStartMinutes && 
          breakEndMinutes <= workEndMinutes &&
          breakStartMinutes < displayEndMinutes &&
          breakEndMinutes > displayStartMinutes) {
        blocks.push({ 
          start: Math.max(breakStartMinutes, displayStartMinutes), 
          end: Math.min(breakEndMinutes, displayEndMinutes) 
        })
      }
    }
  }
  
  // Время после окончания рабочего дня (только в пределах отображаемого диапазона)
  if (workEndMinutes < displayEndMinutes) {
    blocks.push({ start: Math.max(workEndMinutes, displayStartMinutes), end: displayEndMinutes })
  }
  
  return blocks
}

function handleEventSaved() {
  refreshEvents()
}

async function handleBookingSaved() {
  selectedBookingForEdit.value = null
  await nextTick()
  await refreshBookings()
}

function navigateDate(direction: 'prev' | 'next') {
  if (viewMode.value === 'day') {
    selectedDate.value = addDays(selectedDate.value, direction === 'prev' ? -1 : 1)
  } else {
    selectedDate.value = addDays(selectedDate.value, direction === 'prev' ? -7 : 7)
  }
  updateRoute()
}

// Функции для переключения дней в дневном виде
function navigateDay(direction: 'prev' | 'next') {
  selectedDate.value = addDays(selectedDate.value, direction === 'prev' ? -1 : 1)
  updateRoute()
}

function goToToday() {
  // Переключаем на режим "День" и устанавливаем сегодняшнюю дату
  viewMode.value = 'day'
  selectedDate.value = new Date()
  updateRoute()
}

function updateRoute() {
  router.push({
    path: '/schedule',
    query: {
      date: format(selectedDate.value, 'yyyy-MM-dd'),
      view: viewMode.value
    }
  })
}

function openPublicCalendar() {
  if (!user.value?.username) {
    const toast = useToast()
    toast.add({
      title: 'Ошибка',
      description: 'Не удалось получить имя пользователя',
      color: 'red'
    })
    return
  }
  
  // Открываем страницу профиля, а не календаря напрямую
  const publicProfileUrl = `/booking/${user.value.username}`
  window.open(publicProfileUrl, '_blank')
}

// Синхронизируем selectedDate с route.query.date
const isUpdatingFromRoute = ref(false)
watch(() => route.query.date, (dateStr) => {
  if (dateStr && typeof dateStr === 'string') {
    const newDate = parseDateFromQuery(dateStr)
    if (!isSameDay(newDate, selectedDate.value)) {
      isUpdatingFromRoute.value = true
      selectedDate.value = newDate
      nextTick(() => {
        isUpdatingFromRoute.value = false
      })
    }
  }
}, { immediate: true })

watch(selectedDate, () => {
  if (!isUpdatingFromRoute.value) {
    updateRoute()
  }
})
watch(viewMode, () => updateRoute())
</script>

<template>
  <UDashboardPanel id="schedule">
    <template #header>
      <UDashboardNavbar>
        <template #leading>
          <div class="flex items-center gap-2">
            <div class="hidden"><UDashboardSidebarCollapse /></div>
            
            <!-- Стрелки навигации и дата/неделя -->
            <div class="flex items-center gap-1">
              <UButton
                icon="i-lucide-chevron-left"
                color="neutral"
                variant="ghost"
                square
                size="sm"
                @click="navigateDate('prev')"
              />
              <span class="text-sm font-medium px-2">
                {{ viewMode === 'day' ? format(selectedDate, 'd MMMM, EEEE', { locale: ru }) : `Неделя ${format(weekStart, 'd MMM', { locale: ru })} - ${format(weekEnd, 'd MMM', { locale: ru })}` }}
              </span>
              <UButton
                icon="i-lucide-chevron-right"
                color="neutral"
                variant="ghost"
                square
                size="sm"
                @click="navigateDate('next')"
              />
            </div>
          </div>
        </template>

        <template #right>
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-external-link"
              color="neutral"
              variant="ghost"
              size="sm"
              label="Как это выглядит"
              :disabled="!user?.username"
              @click="openPublicCalendar"
            />
            <UButton
              icon="i-lucide-plus"
              color="neutral"
              variant="solid"
              size="sm"
              square
              class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100 h-9 w-9"
              @click="slotDateForModal = null; slotTimeForModal = null; bookingModalOpen = true"
            />

            <UButton
              label="Сегодня"
              color="neutral"
              variant="ghost"
              size="sm"
              class="h-9"
              @click="goToToday"
            />

            <UTabs
              v-model="viewMode"
              :items="[
                { label: 'День', value: 'day' },
                { label: 'Неделя', value: 'week' }
              ]"
              size="sm"
              color="neutral"
              variant="pill"
              :content="false"
              :ui="{ list: 'h-9 p-0.5', trigger: 'h-8 px-2.5' }"
            />
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex-1 overflow-auto">
        <!-- Дневной вид -->
        <div v-if="viewMode === 'day'" class="relative h-full">
          <!-- Мини-календарь дней недели -->
          <div class="flex border-b border-default mb-2">
            <div class="w-16 shrink-0 border-r border-default/30"></div>
            <div class="flex-1 flex items-center">
              <!-- Кнопка переключения назад -->
              <UButton
                icon="i-lucide-chevron-left"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                @click="navigateDay('prev')"
                class="shrink-0 mx-1"
              />
              
              <!-- Дни недели -->
              <div class="flex-1 grid grid-cols-7">
                <div
                  v-for="(day, index) in dayViewWeekDays"
                  :key="day.getTime()"
                  class="p-2 text-center cursor-pointer transition-colors"
                  :class="{
                    'bg-gray-900/10 dark:bg-white/10': isSameDay(day, selectedDate),
                    'hover:bg-elevated/50': !isSameDay(day, selectedDate),
                    'border-l border-default': index > 0
                  }"
                  @click="selectedDate = day; updateRoute()"
                >
                  <div class="text-xs text-muted">{{ formatWeekdayShort(day) }}</div>
                  <div class="text-sm font-medium">{{ format(day, 'd') }}</div>
                </div>
              </div>
              
              <!-- Кнопка переключения вперед -->
              <UButton
                icon="i-lucide-chevron-right"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                @click="navigateDay('next')"
                class="shrink-0 mx-1"
              />
            </div>
          </div>

          <div class="flex">
            <!-- Временная шкала (формат как на референсе: 10 00, 30) -->
            <div class="w-16 shrink-0 border-r border-default/30">
              <div
                v-for="hour in dayHours"
                :key="hour"
                class="relative flex flex-col items-end pr-2 text-muted"
                style="height: 48px; min-height: 48px; max-height: 48px; box-sizing: border-box;"
              >
                <div class="flex items-baseline gap-0.5" style="padding-top: 2px;">
                  <span class="text-sm font-medium">{{ String(hour).padStart(2, '0') }}</span>
                  <span class="text-[10px] -translate-y-0.5">00</span>
                </div>
                <span class="text-[10px] absolute right-2" style="top: 24px;">30</span>
              </div>
            </div>

            <!-- Расписание -->
            <div class="flex-1 relative" style="padding-left: 1rem; padding-right: 1rem;">
              <!-- Сетка часов (pointer-events-none чтобы клики проходили к бронированиям) -->
              <div
                v-for="hour in dayHours"
                :key="hour"
                class="border-b border-default relative pointer-events-none"
                style="height: 48px; min-height: 48px; max-height: 48px; box-sizing: border-box; margin: 0;"
              >
                <!-- Полчаса (30 минут) -->
                <div class="absolute left-0 right-0 border-t border-dashed border-default/50" style="top: 24px; height: 0; box-sizing: border-box;" />
                <!-- 15 минут -->
                <div class="absolute left-0 right-0 border-t border-dashed border-default/30 opacity-50" style="top: 12px; height: 0; box-sizing: border-box;" />
                <!-- 45 минут -->
                <div class="absolute left-0 right-0 border-t border-dashed border-default/30 opacity-50" style="top: 36px; height: 0; box-sizing: border-box;" />
              </div>

              <!-- Недоступное время (блоки на основе графика работы) -->
              <div class="absolute pointer-events-none" style="top: 0; left: 1rem; right: 1rem; bottom: 0;">
                <template
                  v-for="block in getUnavailableTimeBlocks(selectedDate)"
                  :key="`unavailable-${block.start}-${block.end}`"
                >
                  <div
                    class="absolute left-0 right-0 bg-gray-400/40 dark:bg-gray-600/40 border-l-2 border-r-2 border-gray-400/50 dark:border-gray-500/50"
                    :style="getUnavailableTimePosition(
                      Math.floor(block.start / 60),
                      block.start % 60,
                      Math.floor(block.end / 60),
                      block.end % 60
                    )"
                  />
                </template>
              </div>

              <!-- Слоты для добавления брони (hover + click, z-10 — ниже бронирований) -->
              <div
                class="absolute z-10 grid w-full"
                :style="{ top: 0, left: '1rem', right: '1rem', bottom: 0, gridTemplateRows: `repeat(${daySlots.length}, 24px)` }"
              >
                <div
                  v-for="(slot, idx) in daySlots"
                  :key="`slot-${slot.hour}-${slot.minute}`"
                  class="flex items-center justify-center cursor-pointer transition-colors"
                  :class="[
                    isTimeSlotAvailable(selectedDate, slot.hour, slot.minute)
                      ? 'hover:bg-primary/10 group'
                      : 'cursor-default pointer-events-none'
                  ]"
                  @click="isTimeSlotAvailable(selectedDate, slot.hour, slot.minute) && openBookingForSlot(selectedDate, slot.hour, slot.minute)"
                >
                  <span
                    v-if="isTimeSlotAvailable(selectedDate, slot.hour, slot.minute)"
                    class="opacity-0 group-hover:opacity-100 transition-opacity text-primary text-xs font-medium"
                  >
                    + Добавить бронь
                  </span>
                </div>
              </div>

              <!-- Бронирования (pointer-events-none на контейнере — клики в пустых местах проходят к слотам) -->
              <div class="absolute z-20 pointer-events-none" style="top: 0; left: 1rem; right: 1rem; bottom: 0;">
                <div
                  v-for="booking in getBookingsForDate(selectedDate)"
                  :key="booking.id"
                  class="absolute left-2 right-2 rounded-md text-white text-sm cursor-pointer hover:opacity-90 transition-opacity pointer-events-auto"
                  :style="{ ...getBookingPosition(booking, selectedDate), boxSizing: 'border-box' }"
                  :class="[
                    getBookingColorClass(booking),
                    {
                      'p-2': getBookingDuration(booking) > 30,
                      'p-1.5': getBookingDuration(booking) === 30
                    }
                  ]"
                  @click.stop="openBookingDetail(booking)"
                >
                  <div v-if="getBookingDuration(booking) === 30" class="font-medium truncate text-xs leading-tight">
                    {{ booking.startTime }} {{ booking.serviceName }}
                  </div>
                  <template v-else>
                    <div class="font-medium">{{ booking.startTime }} {{ booking.serviceName }}</div>
                    <div class="text-xs opacity-90">{{ booking.customerName }}</div>
                  </template>
                </div>
              </div>

              <!-- События (pointer-events-none на контейнере — клики проходят к бронированиям; pointer-events-auto на элементах) -->
              <div class="absolute z-20 pointer-events-none" style="top: 0; left: 1rem; right: 1rem; bottom: 0;">
                <div
                  v-for="event in getEventsForDate(selectedDate)"
                  :key="`event-${event.id}`"
                  class="absolute left-2 right-2 rounded-md p-2 bg-purple-500 text-white text-sm cursor-pointer hover:opacity-90 transition-opacity border-2 border-purple-600 pointer-events-auto"
                  :style="{ ...getEventPosition(event, selectedDate), boxSizing: 'border-box' }"
                  @click.stop="openEventDetail(event)"
                >
                  <div class="font-medium">{{ event.startTime }} {{ event.name }}</div>
                  <div class="text-xs opacity-90">
                    <span v-if="event.serviceId">{{ getServiceName(event.serviceId) }}</span>
                    <span class="ml-2">{{ event.bookedSlots }}/{{ event.maxParticipants }} мест</span>
                  </div>
                </div>
              </div>

              <!-- Индикатор текущего времени -->
              <div
                v-if="currentTimeIndicatorVisible && currentTimeTopPx >= 0"
                class="absolute left-0 right-0 pointer-events-none z-10 flex items-center"
                :style="{ top: `${currentTimeTopPx}px` }"
              >
                <span class="bg-gray-700 dark:bg-gray-600 text-white text-[10px] px-1.5 py-0.5 rounded shrink-0 -translate-y-1/2">{{ currentTimeFormatted }}</span>
                <div class="flex-1 h-px bg-gray-600 dark:bg-gray-500 -translate-y-1/2" />
              </div>
            </div>
          </div>
        </div>

        <!-- Недельный вид -->
        <div v-else class="flex-1 overflow-auto">
          <div class="flex">
            <!-- Временная шкала (формат как на референсе: 10 00, 30) -->
            <div class="w-16 shrink-0 pt-12 border-r border-default/30" style="padding-top: 3rem;">
              <div
                v-for="hour in dayHours"
                :key="hour"
                class="relative flex flex-col items-end pr-2 text-muted"
                style="height: 48px; min-height: 48px; max-height: 48px; box-sizing: border-box;"
              >
                <div class="flex items-baseline gap-0.5" style="padding-top: 2px;">
                  <span class="text-sm font-medium">{{ String(hour).padStart(2, '0') }}</span>
                  <span class="text-[10px] -translate-y-0.5">00</span>
                </div>
                <span class="text-[10px] absolute right-2" style="top: 24px;">30</span>
              </div>
            </div>

            <!-- Дни недели -->
            <div class="flex-1 grid grid-cols-7">
              <div
                v-for="day in weekDays"
                :key="day.getTime()"
                class="border-l border-default"
              >
                <!-- Заголовок дня -->
                <div
                  class="border-b border-default p-2 text-center"
                  :class="isSameDay(day, new Date()) ? 'bg-gray-900/10 dark:bg-white/10' : ''"
                  style="box-sizing: border-box;"
                >
                  <div class="text-xs text-muted">{{ formatWeekdayShort(day) }}</div>
                  <div class="text-sm font-medium">{{ format(day, 'd') }}</div>
                </div>

                <!-- Временные слоты -->
                <div class="relative" style="box-sizing: border-box;">
                  <div
                    v-for="hour in dayHours"
                    :key="hour"
                    class="border-b border-default relative"
                    style="height: 48px; min-height: 48px; max-height: 48px; box-sizing: border-box;"
                  >
                    <!-- Полчаса (30 минут) -->
                    <div class="absolute left-0 right-0 border-t border-dashed border-default/50" style="top: 24px; height: 0; box-sizing: border-box;" />
                    <!-- 15 минут -->
                    <div class="absolute left-0 right-0 border-t border-dashed border-default/30 opacity-50" style="top: 12px; height: 0; box-sizing: border-box;" />
                    <!-- 45 минут -->
                    <div class="absolute left-0 right-0 border-t border-dashed border-default/30 opacity-50" style="top: 36px; height: 0; box-sizing: border-box;" />
                  </div>

                  <!-- Недоступное время (блоки на основе графика работы) -->
                  <div class="absolute inset-0 pointer-events-none">
                    <template
                      v-for="block in getUnavailableTimeBlocks(day)"
                      :key="`unavailable-${day.getTime()}-${block.start}-${block.end}`"
                    >
                      <div
                        class="absolute left-0 right-0 bg-gray-400/40 dark:bg-gray-600/40 border-l border-r border-gray-400/50 dark:border-gray-500/50"
                        :style="getUnavailableTimePosition(
                          Math.floor(block.start / 60),
                          block.start % 60,
                          Math.floor(block.end / 60),
                          block.end % 60
                        )"
                      />
                    </template>
                  </div>

                  <!-- Слоты для добавления брони (hover + click) -->
                  <div
                    class="absolute inset-0 z-[5] grid"
                    :style="{ gridTemplateRows: `repeat(${daySlots.length}, 24px)` }"
                  >
                    <div
                      v-for="(slot, idx) in daySlots"
                      :key="`slot-${day.getTime()}-${slot.hour}-${slot.minute}`"
                      class="flex items-center justify-center cursor-pointer transition-colors"
                      :class="[
                        isTimeSlotAvailable(day, slot.hour, slot.minute)
                          ? 'hover:bg-primary/10 group'
                          : 'cursor-default pointer-events-none'
                      ]"
                      @click="isTimeSlotAvailable(day, slot.hour, slot.minute) && openBookingForSlot(day, slot.hour, slot.minute)"
                    >
                      <span
                        v-if="isTimeSlotAvailable(day, slot.hour, slot.minute)"
                        class="opacity-0 group-hover:opacity-100 transition-opacity text-primary text-[10px] font-medium"
                      >
                        +
                      </span>
                    </div>
                  </div>

                  <!-- Бронирования и события (pointer-events-none на контейнере — клики в пустых местах проходят к слотам) -->
                  <div class="absolute inset-0 z-10 pointer-events-none" style="top: 0; left: 0; right: 0; bottom: 0;">
                    <div
                      v-for="booking in getBookingsForDate(day)"
                      :key="booking.id"
                      class="absolute left-1 right-1 rounded-md text-white text-xs cursor-pointer hover:opacity-90 transition-opacity pointer-events-auto"
                      :style="{ ...getBookingPosition(booking, day), boxSizing: 'border-box' }"
                      :class="[
                        getBookingColorClass(booking),
                        {
                          'p-1.5': getBookingDuration(booking) === 30,
                          'p-1': getBookingDuration(booking) > 30
                        }
                      ]"
                      @click.stop="openBookingDetail(booking)"
                    >
                      <div v-if="getBookingDuration(booking) === 30" class="font-medium truncate leading-tight">
                        {{ booking.startTime }} {{ booking.serviceName }}
                      </div>
                      <template v-else>
                        <div class="font-medium truncate">{{ booking.startTime }}</div>
                        <div class="truncate">{{ booking.serviceName }}</div>
                      </template>
                    </div>

                    <!-- События для этого дня -->
                    <div
                      v-for="event in getEventsForDate(day)"
                      :key="`event-${event.id}`"
                      class="absolute left-1 right-1 rounded-md p-1.5 bg-purple-500 text-white text-xs cursor-pointer hover:opacity-90 transition-opacity border border-purple-600 pointer-events-auto"
                      :style="{ ...getEventPosition(event, day), boxSizing: 'border-box' }"
                      @click.stop="openEventDetail(event)"
                    >
                      <div class="font-medium truncate">{{ event.startTime }} {{ event.name }}</div>
                      <div class="truncate text-xs/90">
                        <span v-if="event.serviceId">{{ getServiceName(event.serviceId) }}</span>
                      </div>
                    </div>

                    <!-- Индикатор текущего времени (только для сегодня) -->
                    <div
                      v-if="isSameDay(day, new Date()) && currentTimeIndicatorVisible && currentTimeTopPx >= 0"
                      class="absolute left-0 right-0 pointer-events-none z-10 flex items-center"
                      :style="{ top: `${currentTimeTopPx}px` }"
                    >
                      <span class="bg-gray-700 dark:bg-gray-600 text-white text-[10px] px-1.5 py-0.5 rounded shrink-0 -translate-y-1/2">{{ currentTimeFormatted }}</span>
                      <div class="flex-1 h-px bg-gray-600 dark:bg-gray-500 -translate-y-1/2" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <ScheduleEventModal
    v-model="eventModalOpen"
    :event="selectedEvent"
    :default-date="selectedDate"
    @saved="handleEventSaved"
  />

  <BookingCreateModal
    v-model="bookingModalOpen"
    :default-date="slotDateForModal ?? selectedDate"
    :default-time="slotTimeForModal ?? new Date().toTimeString().slice(0, 5)"
    :edit-booking="selectedBookingForEdit"
    @saved="handleBookingSaved"
  />

  <ScheduleBookingDetailModal
    v-model="bookingDetailModalOpen"
    :booking="selectedBooking"
    @updated="handleBookingDetailUpdated"
    @edit="openBookingEdit"
  />
</template>
