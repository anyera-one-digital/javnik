<script setup lang="ts">
import { format, startOfWeek, endOfWeek, eachDayOfInterval, addDays, isSameDay, startOfDay, parse } from 'date-fns'
import { ru } from 'date-fns/locale'
import { formatWeekdayShort } from '~/utils'
import type { Event, Service, User, Booking, WorkSchedule } from '~/types'
import BookingModal from '~/components/UserPublicPage/public/BookingModal.vue'

definePageMeta({
  layout: false,
  middleware: ['public-page-color-mode']
  // Не используем middleware subdomain здесь, чтобы избежать конфликтов
})

const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()
const colorMode = useColorMode()
const toast = useToast()

const username = computed(() => route.params.username as string)

// Состояния для загрузки данных
const publicUser = ref<User | null>(null)
const userError = ref<any>(null)
const userPending = ref(true)

// Загружаем публичный профиль пользователя через Nuxt server API
// Используем прямой вызов в onMounted, чтобы избежать автоматических редиректов
const loadUserProfile = async () => {
  if (!username.value) {
    userError.value = { statusCode: 400, message: 'Username is required' }
    userPending.value = false
    return
  }

  userPending.value = true
  userError.value = null
  
  try {
    const apiUrl = `/api/public/profile/${username.value}`
    console.log('Loading user profile from:', apiUrl)
    
    const response = await $fetch<User>(apiUrl)
    publicUser.value = response
    console.log('User profile loaded:', response)
    console.log('Avatar URL:', response.avatar_url)
    console.log('Avatar field:', response.avatar)
    
    // Исправляем URL аватара, если он содержит внутренние Docker имена
    if (response.avatar_url) {
      const config = useRuntimeConfig()
      const baseUrl = config.public.apiBase || 'http://localhost:8000'
      
      // Если URL содержит внутренний хост backend, заменяем на localhost
      if (response.avatar_url.includes('://backend:') || response.avatar_url.includes('://backend/')) {
        // Извлекаем путь из URL
        const urlPath = response.avatar_url.replace(/^https?:\/\/[^\/]+/, '')
        publicUser.value.avatar_url = `${baseUrl}${urlPath}`
        console.log('Fixed avatar URL (replaced backend):', publicUser.value.avatar_url)
      } else if (!response.avatar_url.startsWith('http')) {
        // Если URL не полный, формируем его
        if (response.avatar_url.startsWith('/')) {
          publicUser.value.avatar_url = `${baseUrl}${response.avatar_url}`
        } else {
          publicUser.value.avatar_url = `${baseUrl}/${response.avatar_url}`
        }
        console.log('Fixed avatar URL (added base):', publicUser.value.avatar_url)
      }
    }
  } catch (error: any) {
    console.error('Error loading user profile:', error)
    userError.value = {
      statusCode: error.statusCode || 404,
      message: error.data?.error || error.message || 'User not found'
    }
    publicUser.value = null
  } finally {
    userPending.value = false
  }
}

// Загружаем профиль при монтировании компонента
onMounted(() => {
  console.log('=== CALENDAR.VUE MOUNTED ===')
  console.log('Route path:', route.path)
  console.log('Route params:', route.params)
  console.log('Username:', username.value)
  console.log('Loading profile for:', username.value)
  loadUserProfile()
})

// Флаг загрузки данных (объявляем до watch, который его использует)
const dataLoading = ref(false)

// Логируем изменения состояний
watch([userPending, dataLoading, publicUser, userError], ([pending, loading, user, error]) => {
  console.log('Calendar states:', {
    userPending: pending,
    dataLoading: loading,
    hasUser: !!user,
    hasError: !!error
  })
}, { immediate: true })

// Перезагружаем при изменении username
watch(() => username.value, (newUsername) => {
  if (newUsername) {
    console.log('Username changed, reloading profile:', newUsername)
    loadUserProfile()
  }
})

// Нормализуем дату из query параметра
function parseDateFromQuery(dateStr: string | undefined): Date {
  if (!dateStr) return startOfDay(new Date())
  try {
    return startOfDay(parse(dateStr, 'yyyy-MM-dd', new Date()))
  } catch {
    return startOfDay(new Date())
  }
}

const viewMode = ref<'day' | 'week'>('week')
const selectedDate = ref<Date>(route.query.date ? parseDateFromQuery(route.query.date as string) : startOfDay(new Date()))
const selectedEvent = ref<Event | null>(null)
const selectedService = ref<Service | null>(null)
const clickedTimeSlot = ref<{ date: Date, time: string } | null>(null)
const bookingModalOpen = ref(false)

const weekStart = computed(() => startOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 }))
const weekEnd = computed(() => endOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 }))
const weekDays = computed(() => eachDayOfInterval({ start: weekStart.value, end: weekEnd.value }))

// Получаем публичные данные пользователя
const allEvents = ref<Event[]>([])
const services = ref<Service[]>([])
const bookings = ref<Booking[]>([])
const allBookings = ref<Booking[]>([])
const workSchedules = ref<Map<string, WorkSchedule>>(new Map())

// Загружаем все данные только если пользователь найден
const loadAllData = async () => {
  if (!publicUser.value || userError.value) {
    console.log('Cannot load data: user not loaded or error exists')
    return
  }

  console.log('Loading all data for calendar...')
  
  try {
    // Загружаем события
    let eventsUrl = `/api/public/events/${username.value}`
    if (viewMode.value === 'day') {
      eventsUrl += `?date=${format(selectedDate.value, 'yyyy-MM-dd')}`
    }
    console.log('Loading events from:', eventsUrl)
    const eventsData = await $fetch<any>(eventsUrl)
    allEvents.value = Array.isArray(eventsData) ? eventsData : []
    console.log('Events loaded:', allEvents.value.length)
    
    // Загружаем услуги
    const servicesUrl = `/api/public/services/${username.value}`
    console.log('Loading services from:', servicesUrl)
    const servicesData = await $fetch<any>(servicesUrl)
    services.value = Array.isArray(servicesData) ? servicesData : []
    console.log('Services loaded:', services.value.length)
    
    // Загружаем бронирования
    console.log('Loading bookings...')
    await loadBookings()
    console.log('Bookings loaded')
    
    // Загружаем график работы
    console.log('Loading work schedules...')
    await loadWorkSchedules()
    console.log('Work schedules loaded')
    
    console.log('All data loaded successfully')
  } catch (error: any) {
    console.error('Error loading data:', error)
    console.error('Error details:', {
      status: error.statusCode || error.status,
      message: error.message,
      data: error.data
    })
    allEvents.value = []
    services.value = []
    bookings.value = []
    allBookings.value = []
  }
}

// Загружаем бронирования
async function loadBookings() {
  if (!publicUser.value || userError.value) return
  
  try {
    const date = viewMode.value === 'day' ? format(selectedDate.value, 'yyyy-MM-dd') : undefined
    const startDate = viewMode.value === 'week' ? format(weekStart.value, 'yyyy-MM-dd') : undefined
    const endDate = viewMode.value === 'week' ? format(weekEnd.value, 'yyyy-MM-dd') : undefined
    
    let url = `/api/public/bookings/${username.value}`
    const params = new URLSearchParams()
    if (date) {
      params.append('date', date)
    }
    if (startDate) {
      params.append('start_date', startDate)
    }
    if (endDate) {
      params.append('end_date', endDate)
    }
    if (params.toString()) {
      url += `?${params.toString()}`
    }
    
    const data = await $fetch<any>(url)
    
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
        bookingsArray = [data]
      }
    }
    
    if (viewMode.value === 'day') {
      bookings.value = bookingsArray
    } else {
      allBookings.value = bookingsArray
    }
  } catch (error: any) {
    console.error('Error loading bookings:', error)
    bookings.value = []
    allBookings.value = []
  }
}

// Загружаем график работы
async function loadWorkSchedules() {
  if (!publicUser.value || userError.value) return
  
  try {
    const datesToLoad = viewMode.value === 'day' 
      ? [selectedDate.value]
      : weekDays.value
    
    if (!datesToLoad || datesToLoad.length === 0) return
    
    const startDate = format(datesToLoad[0], 'yyyy-MM-dd')
    const endDate = format(datesToLoad[datesToLoad.length - 1], 'yyyy-MM-dd')
    
    const url = `/api/public/schedule/${username.value}?start_date=${startDate}&end_date=${endDate}`
    const response = await $fetch<WorkSchedule[]>(url)
    
    if (Array.isArray(response)) {
      workSchedules.value.clear()
      response.forEach(schedule => {
        if (schedule && schedule.date) {
          workSchedules.value.set(schedule.date, schedule)
        }
      })
    }
  } catch (error) {
    console.error('Error loading work schedules:', error)
  }
}

// Флаг для предотвращения повторных загрузок
let isInitialLoad = true

// Загружаем данные когда пользователь найден
watch([publicUser, userError], ([user, error]) => {
  if (user && !error && !dataLoading.value) {
    console.log('User loaded, starting data load...')
    dataLoading.value = true
    isInitialLoad = false
    loadAllData().finally(() => {
      dataLoading.value = false
      console.log('Data load completed')
    })
  }
}, { immediate: true })

// Обновляем данные при изменении даты или режима просмотра
watch([viewMode, selectedDate], () => {
  // Пропускаем первую загрузку, так как она уже произошла в watch([publicUser, userError])
  if (isInitialLoad) {
    isInitialLoad = false
    return
  }
  
  if (publicUser.value && !userError.value && !dataLoading.value) {
    console.log('View mode or date changed, reloading data...')
    dataLoading.value = true
    loadAllData().finally(() => {
      dataLoading.value = false
    })
  }
})

const refreshEvents = () => {
  loadAllData()
}

// Функция для перезагрузки профиля (используется в кнопке "Попробовать снова")
const refresh = () => {
  loadUserProfile()
}

const events = computed(() => {
  if (!allEvents.value) return []
  if (viewMode.value === 'day') {
    const dateStr = format(selectedDate.value, 'yyyy-MM-dd')
    return allEvents.value.filter(e => e.date === dateStr)
  }
  return allEvents.value
})

function getEventsForDate(date: Date): Event[] {
  if (!allEvents.value) return []
  const dateStr = format(date, 'yyyy-MM-dd')
  return allEvents.value.filter(e => e.date === dateStr)
}

// Вычисляем минимальное и максимальное рабочее время из всех графиков (как во внутреннем расписании)
const workTimeRange = computed(() => {
  if (workSchedules.value.size === 0) {
    return { minHour: 9, maxHour: 21 }
  }
  
  let minHour: number | null = null
  let maxHour: number | null = null
  let maxEndMinute: number = 0
  
  for (const schedule of workSchedules.value.values()) {
    if (schedule.type === 'workday' && schedule.startTime && schedule.endTime) {
      const [startHour] = schedule.startTime.split(':').map(Number)
      const [endHour, endMinute = 0] = schedule.endTime.split(':').map(Number)
      
      if (minHour === null || startHour < minHour) {
        minHour = startHour
      }
      
      const endMinutes = endHour * 60 + endMinute
      const currentMaxMinutes = maxHour !== null ? maxHour * 60 + maxEndMinute : 0
      if (maxHour === null || endMinutes > currentMaxMinutes) {
        maxHour = endHour
        maxEndMinute = endMinute
      }
    }
  }
  
  if (minHour === null || maxHour === null) {
    return { minHour: 9, maxHour: 21 }
  }
  
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

// Для дневного вида - дни недели для мини-календаря
const dayViewWeekDays = computed(() => {
  const start = startOfWeek(selectedDate.value, { locale: ru })
  const end = endOfWeek(selectedDate.value, { locale: ru })
  return eachDayOfInterval({ start, end })
})

// Получаем график работы для даты
function getWorkScheduleForDate(date: Date): WorkSchedule | undefined {
  const dateStr = format(date, 'yyyy-MM-dd')
  return workSchedules.value.get(dateStr)
}

// Получаем бронирования для даты
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

// Вычисляем позицию бронирования
function getBookingPosition(booking: Booking, date: Date): { top: string, height: string } {
  const [startHour, startMinute] = booking.startTime.split(':').map(Number)
  const [endHour, endMinute] = booking.endTime.split(':').map(Number)
  
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = endHour * 60 + endMinute
  
  const hours = dayHours.value
  if (hours.length === 0) {
    return { top: '0px', height: '0px' }
  }
  
  const firstDisplayedHour = hours[0]
  const lastDisplayedHour = hours[hours.length - 1]
  const dayStartMinutes = firstDisplayedHour * 60
  const dayEndMinutes = (lastDisplayedHour + 1) * 60
  
  const clampedStartMinutes = Math.max(startMinutes, dayStartMinutes)
  const clampedEndMinutes = Math.min(endMinutes, dayEndMinutes)
  
  if (clampedStartMinutes >= clampedEndMinutes) {
    return { top: '0px', height: '0px' }
  }
  
  const relativeStart = clampedStartMinutes - dayStartMinutes
  const duration = clampedEndMinutes - clampedStartMinutes
  
  const HOUR_HEIGHT_PX = 48
  const MINUTE_HEIGHT_PX = HOUR_HEIGHT_PX / 60
  
  const topPx = relativeStart * MINUTE_HEIGHT_PX
  const heightPx = duration * MINUTE_HEIGHT_PX
  
  return {
    top: `${topPx}px`,
    height: `${heightPx}px`
  }
}

/**
 * Цвет брони по статусу и услуге (как во внутреннем расписании)
 */
function getBookingColorClass(booking: Booking): string {
  if (booking.status !== 'confirmed') {
    if (booking.status === 'pending') return 'bg-yellow-500'
    if (booking.status === 'cancelled') return 'bg-red-500'
    if (booking.status === 'completed') return 'bg-blue-500'
    return 'bg-yellow-500'
  }
  const serviceName = (booking.serviceName || '').toLowerCase()
  if (serviceName.includes('маникюр') || serviceName.includes('маникюра')) return 'bg-blue-500'
  if (serviceName.includes('педикюр') || serviceName.includes('педикюра')) return 'bg-indigo-500'
  if (serviceName.includes('стрижк')) return 'bg-green-600'
  if (serviceName.includes('наращивани')) return 'bg-purple-500'
  if (serviceName.includes('окрашивани') || serviceName.includes('окраск')) return 'bg-pink-500'
  if (serviceName.includes('укладк')) return 'bg-cyan-500'
  if (serviceName.includes('брови') || serviceName.includes('бров')) return 'bg-orange-500'
  if (serviceName.includes('ресниц')) return 'bg-rose-500'
  return 'bg-teal-500'
}

// Вычисляем длительность бронирования
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
  
  const hours = dayHours.value
  if (hours.length === 0) {
    return { top: '0px', height: '0px' }
  }
  
  const firstDisplayedHour = hours[0]
  const lastDisplayedHour = hours[hours.length - 1]
  const dayStartMinutes = firstDisplayedHour * 60
  const dayEndMinutes = (lastDisplayedHour + 1) * 60
  
  const clampedStartMinutes = Math.max(startMinutes, dayStartMinutes)
  const clampedEndMinutes = Math.min(endMinutes, dayEndMinutes)
  
  if (clampedStartMinutes >= clampedEndMinutes) {
    return { top: '0px', height: '0px' }
  }
  
  const relativeStart = clampedStartMinutes - dayStartMinutes
  const duration = clampedEndMinutes - clampedStartMinutes
  
  const HOUR_HEIGHT_PX = 48
  const MINUTE_HEIGHT_PX = HOUR_HEIGHT_PX / 60
  
  const topPx = (relativeStart * MINUTE_HEIGHT_PX)
  const heightPx = (duration * MINUTE_HEIGHT_PX)
  
  return {
    top: `${topPx}px`,
    height: `${heightPx}px`
  }
}

// Получаем блоки недоступного времени
function getUnavailableTimeBlocks(date: Date): Array<{ start: number, end: number }> {
  const schedule = getWorkScheduleForDate(date)
  const blocks: Array<{ start: number, end: number }> = []
  
  const { minHour, maxHour } = workTimeRange.value
  const displayStartMinutes = minHour * 60
  const displayEndMinutes = maxHour * 60
  
  if (!schedule) {
    return blocks
  }
  
  if (schedule.type !== 'workday') {
    return [{ start: displayStartMinutes, end: displayEndMinutes }]
  }
  
  if (!schedule.startTime || !schedule.endTime) {
    return [{ start: displayStartMinutes, end: displayEndMinutes }]
  }
  
  const [startHour, startMinute] = schedule.startTime.split(':').map(Number)
  const [endHour, endMinute] = schedule.endTime.split(':').map(Number)
  const workStartMinutes = startHour * 60 + startMinute
  const workEndMinutes = endHour * 60 + endMinute
  
  if (workStartMinutes > displayStartMinutes) {
    blocks.push({ start: displayStartMinutes, end: Math.min(workStartMinutes, displayEndMinutes) })
  }
  
  if (schedule.breaks && schedule.breaks.length > 0) {
    for (const breakItem of schedule.breaks) {
      const [breakStartHour, breakStartMinute] = breakItem.startTime.split(':').map(Number)
      const [breakEndHour, breakEndMinute] = breakItem.endTime.split(':').map(Number)
      const breakStartMinutes = breakStartHour * 60 + breakStartMinute
      const breakEndMinutes = breakEndHour * 60 + breakEndMinute
      
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
  
  if (workEndMinutes < displayEndMinutes) {
    blocks.push({ start: Math.max(workEndMinutes, displayStartMinutes), end: displayEndMinutes })
  }
  
  return blocks
}

// Получаем позицию для блока недоступного времени
function getUnavailableTimePosition(startHour: number, startMinute: number, endHour: number, endMinute: number): { top: string, height: string } {
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = endHour * 60 + endMinute
  
  const { minHour, maxHour } = workTimeRange.value
  const dayStartMinutes = minHour * 60
  const dayEndMinutes = maxHour * 60
  
  const clampedStartMinutes = Math.max(startMinutes, dayStartMinutes)
  const clampedEndMinutes = Math.min(endMinutes, dayEndMinutes)
  
  if (clampedStartMinutes >= clampedEndMinutes) {
    return { top: '0px', height: '0px' }
  }
  
  const relativeStart = clampedStartMinutes - dayStartMinutes
  const duration = clampedEndMinutes - clampedStartMinutes
  
  const HOUR_HEIGHT_PX = 48
  const MINUTE_HEIGHT_PX = HOUR_HEIGHT_PX / 60
  
  const topPx = (relativeStart * MINUTE_HEIGHT_PX)
  const heightPx = (duration * MINUTE_HEIGHT_PX)
  
  return {
    top: `${topPx}px`,
    height: `${heightPx}px`
  }
}

function getServiceName(serviceId?: number): string {
  if (!serviceId || !services.value) return ''
  const service = services.value.find(s => s.id === serviceId)
  return service?.name || ''
}

function openBookingModal(event?: Event, date?: Date, time?: string) {
  selectedEvent.value = event || null
  selectedService.value = null
  
  if (!event && date && time) {
    clickedTimeSlot.value = { date, time }
  } else {
    clickedTimeSlot.value = null
  }
  
  bookingModalOpen.value = true
}

async function handleBookingSaved() {
  bookingModalOpen.value = false
  selectedEvent.value = null
  selectedService.value = null
  clickedTimeSlot.value = null
  await loadAllData()
}

function navigateDate(direction: 'prev' | 'next') {
  const days = viewMode.value === 'day' ? 1 : 7
  selectedDate.value = addDays(selectedDate.value, direction === 'prev' ? -days : days)
  router.push({
    query: {
      ...route.query,
      date: format(selectedDate.value, 'yyyy-MM-dd')
    }
  })
}

function goToToday() {
  selectedDate.value = new Date()
  router.push({
    query: {
      ...route.query,
      date: format(selectedDate.value, 'yyyy-MM-dd')
    }
  })
}

function handleTimeSlotClick(day: Date, hour: number) {
  const time = `${hour.toString().padStart(2, '0')}:00`
  openBookingModal(undefined, day, time)
}

const { toggle } = usePublicPageColorMode()

// SEO метаданные
const displayName = computed(() => {
  if (!publicUser.value) return username.value
  return publicUser.value.display_name || publicUser.value.first_name || username.value
})

// Устанавливаем SEO только если пользователь загружен
watch([publicUser, userError], ([user, error]) => {
  if (user && !error) {
    useSeoMeta({
      title: `Календарь бронирований - ${displayName.value}`,
      description: `Публичный календарь бронирований ${displayName.value}. Запишитесь на удобное время.`,
      ogTitle: `Календарь бронирований - ${displayName.value}`,
      ogDescription: `Публичный календарь бронирований ${displayName.value}. Запишитесь на удобное время.`,
      ogImage: user.avatar_url
    })
  }
}, { immediate: true })
</script>

<template>
  <div class="min-h-screen bg-background">
    <div v-if="userPending || dataLoading" class="flex items-center justify-center min-h-screen">
      <div class="text-center space-y-4">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-muted mx-auto"></div>
        <p class="text-muted">{{ userPending ? 'Загрузка профиля...' : 'Загрузка календаря...' }}</p>
      </div>
    </div>
    <div v-else-if="userError && !publicUser" class="flex items-center justify-center min-h-screen p-4">
    <UPageCard variant="subtle" class="max-w-md w-full">
      <div class="text-center space-y-4">
        <div class="text-6xl">😕</div>
        <h2 class="text-2xl font-bold">Пользователь не найден</h2>
        <p class="text-muted">
          Пользователь с именем "<strong>{{ username }}</strong>" не существует или его календарь недоступен.
        </p>
        <UButton
          :to="`/booking/${username}`"
          color="neutral"
          label="Вернуться к профилю"
        />
      </div>
    </UPageCard>
  </div>
  <UDashboardPanel v-else id="schedule" class="h-screen flex flex-col">
    <template #header>
      <UDashboardNavbar>
        <template #leading>
          <div class="flex items-center gap-3">
            <UButton
              icon="i-lucide-arrow-left"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              :to="`/booking/${username}`"
              class="shrink-0"
            />
            <div v-if="publicUser" class="flex items-center gap-3">
              <UAvatar
                :src="publicUser.avatar_url || null"
                :alt="displayName"
                size="md"
              >
                <template v-if="displayName" #fallback>
                  {{ displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) }}
                </template>
              </UAvatar>
              <span class="text-lg font-semibold">{{ displayName }}</span>
            </div>
            <div v-else-if="userError" class="flex items-center gap-3">
              <UAvatar
                alt="Ошибка"
                size="md"
              />
              <span class="text-lg font-semibold text-red-500">Пользователь не найден</span>
            </div>
            <div v-else class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-gray-200 animate-pulse"></div>
              <div class="h-5 w-32 bg-gray-200 rounded animate-pulse"></div>
            </div>

            <!-- Переключатель недель/дней (слева, как в ЛК) -->
            <div class="flex items-center gap-1 ml-2">
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
              :icon="colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon'"
              color="neutral"
              variant="ghost"
              square
              @click="toggle"
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
      <!-- Сообщение об ошибке, если пользователь не найден -->
      <div v-if="userError && !publicUser" class="flex items-center justify-center min-h-[400px] p-4">
        <UPageCard variant="subtle" class="max-w-md w-full">
          <div class="text-center space-y-4">
            <div class="text-6xl">😕</div>
            <h2 class="text-2xl font-bold">Пользователь не найден</h2>
            <p class="text-muted">
              Пользователь с именем "<strong>{{ username }}</strong>" не существует или его календарь недоступен.
            </p>
            <div class="flex gap-2 justify-center">
              <UButton
                to="/"
                color="neutral"
                label="Вернуться на главную"
              />
              <UButton
                color="neutral"
                variant="ghost"
                label="Попробовать снова"
                @click="refresh"
              />
            </div>
          </div>
        </UPageCard>
      </div>
      
      <!-- Загрузка -->
      <div v-else-if="userPending || (!publicUser && !userError)" class="flex items-center justify-center min-h-[400px]">
        <div class="text-center space-y-4">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-muted mx-auto"></div>
          <p class="text-muted">Загрузка календаря пользователя "{{ username }}"...</p>
        </div>
      </div>
      
      <!-- Календарь -->
      <div v-else-if="publicUser" class="flex-1 min-h-0 pb-4" style="padding-bottom: 16px;">
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
                @click="navigateDate('prev')"
                class="shrink-0 mx-1"
              />
              
              <!-- Дни недели -->
              <div class="flex-1 grid grid-cols-7">
                <div
                  v-for="(day, index) in dayViewWeekDays"
                  :key="day.getTime()"
                  class="p-2 text-center cursor-pointer transition-colors"
                  :class="{
                    'bg-muted/50': isSameDay(day, selectedDate),
                    'hover:bg-elevated/50': !isSameDay(day, selectedDate),
                    'border-l border-default': index > 0
                  }"
                  @click="selectedDate = day; router.push({ query: { ...route.query, date: format(day, 'yyyy-MM-dd') } })"
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
                @click="navigateDate('next')"
                class="shrink-0 mx-1"
              />
            </div>
          </div>

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

            <!-- Расписание -->
            <div class="flex-1 relative pt-12" style="padding-top: 3rem; padding-left: 1rem; padding-right: 1rem;">
              <div
                v-for="hour in dayHours"
                :key="hour"
                class="border-b border-default relative"
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
              <div class="absolute pointer-events-none" style="top: 3rem; left: 1rem; right: 1rem; bottom: 0;">
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

              <!-- Бронирования -->
              <div class="absolute" style="top: 3rem; left: 1rem; right: 1rem; bottom: 0;">
                <div
                  v-for="booking in getBookingsForDate(selectedDate)"
                  :key="booking.id"
                  class="absolute left-2 right-2 rounded-md text-white text-sm cursor-pointer hover:opacity-90 transition-opacity"
                  :style="{ ...getBookingPosition(booking, selectedDate), boxSizing: 'border-box', maxHeight: '100%' }"
                  :class="[
                    getBookingColorClass(booking),
                    {
                      'p-2': getBookingDuration(booking) > 30,
                      'p-1.5': getBookingDuration(booking) === 30
                    }
                  ]"
                >
                  <div v-if="getBookingDuration(booking) === 30" class="font-medium truncate text-xs leading-tight">
                    {{ booking.startTime }} Забронировано
                  </div>
                  <template v-else>
                    <div class="font-medium truncate">{{ booking.startTime }} Забронировано</div>
                  </template>
                </div>
              </div>

              <!-- События -->
              <div class="absolute" style="top: 3rem; left: 1rem; right: 1rem; bottom: 0;">
                <div
                  v-for="event in getEventsForDate(selectedDate)"
                  :key="`event-${event.id}`"
                  class="absolute left-2 right-2 rounded-md p-2 bg-purple-500 text-white text-sm cursor-pointer hover:opacity-90 transition-opacity border-2 border-purple-600"
                  :style="{ ...getEventPosition(event, selectedDate), boxSizing: 'border-box' }"
                  @click.stop="openBookingModal(event)"
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
                :style="{ top: `calc(3rem + ${currentTimeTopPx}px)` }"
              >
                <span class="bg-gray-700 dark:bg-gray-600 text-white text-[10px] px-1.5 py-0.5 rounded shrink-0 -translate-y-1/2">{{ currentTimeFormatted }}</span>
                <div class="flex-1 h-px bg-gray-600 dark:bg-gray-500 -translate-y-1/2" />
              </div>
            </div>
          </div>
        </div>

        <!-- Недельный вид -->
        <div v-else class="flex-1 pb-4" style="padding-bottom: 16px;">
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

                  <!-- Бронирования -->
                  <div class="absolute inset-0" style="top: 0; left: 0; right: 0; bottom: 0;">
                    <div
                      v-for="booking in getBookingsForDate(day)"
                      :key="booking.id"
                      class="absolute left-1 right-1 rounded-md text-white text-xs cursor-pointer hover:opacity-90 transition-opacity"
                      :style="{ ...getBookingPosition(booking, day), boxSizing: 'border-box', maxHeight: '100%' }"
                      :class="[
                        getBookingColorClass(booking),
                        {
                          'p-1.5': getBookingDuration(booking) <= 30,
                          'p-2': getBookingDuration(booking) > 30
                        }
                      ]"
                    >
                      <div v-if="getBookingDuration(booking) <= 30" class="font-medium truncate text-xs leading-tight">
                        {{ booking.startTime }} Забронировано
                      </div>
                      <template v-else>
                        <div class="font-medium truncate text-xs">{{ booking.startTime }} Забронировано</div>
                      </template>
                    </div>
                  </div>

                  <!-- События для этого дня -->
                  <div class="absolute inset-0" style="top: 0; left: 0; right: 0; bottom: 0;">
                    <div
                      v-for="event in getEventsForDate(day)"
                      :key="`event-${event.id}`"
                      class="absolute left-1 right-1 rounded-md p-1.5 bg-purple-500 text-white text-xs cursor-pointer hover:opacity-90 transition-opacity border border-purple-600"
                      :style="{ ...getEventPosition(event, day), boxSizing: 'border-box' }"
                      @click.stop="openBookingModal(event)"
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
  </div>

  <!-- Booking Modal (только если пользователь загружен) -->
  <BookingModal
    v-if="publicUser && !userPending && !dataLoading"
    v-model="bookingModalOpen"
    :event="selectedEvent"
    :service="selectedService"
    :time-slot="clickedTimeSlot"
    :username="username"
    @saved="handleBookingSaved"
  />
</template>
