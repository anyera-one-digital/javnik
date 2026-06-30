<script setup lang="ts">
import { format, startOfDay, startOfWeek, endOfWeek, eachDayOfInterval, isSameDay, addDays, parse } from 'date-fns'
import { ru } from 'date-fns/locale'
import { computeWorkTimeRange } from '~/utils/workTimeRange'
import { normalizeApiList } from '~/utils/normalizeApiList'
import type { Booking, Event, Service, WorkSchedule } from '~/types'
import BookingCreateModal from '~/components/UserPersonalAccount/schedule/BookingCreateModal.vue'
import ScheduleEventModal from '~/components/UserPersonalAccount/schedule/EventModal.vue'
import ScheduleBookingDetailModal from '~/components/UserPersonalAccount/schedule/BookingDetailModal.vue'
import WorkScheduleEditor from '~/components/UserPersonalAccount/schedule/WorkScheduleEditor.vue'
import { formatWeekdayShort } from '~/utils'
/** Круглые кнопки в шапке расписания (+ и настройки) */
const scheduleHeaderIconBtnClass
  = '!size-9 !min-h-9 !min-w-9 !max-h-9 !max-w-9 !shrink-0 !p-0 !rounded-full !aspect-square !bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const route = useRoute()
const router = useRouter()

function parseDateFromQuery(dateStr: string | undefined): Date {
  if (!dateStr) return startOfDay(new Date())
  try {
    return startOfDay(parse(dateStr, 'yyyy-MM-dd', new Date()))
  } catch {
    return startOfDay(new Date())
  }
}

const isScheduleMobile = useMediaQuery('(max-width: 767px)')

function readViewModeFromRoute(): 'day' | 'week' {
  const v = route.query.view
  const raw = Array.isArray(v) ? v[0] : v
  return raw === 'day' ? 'day' : 'week'
}

/** Режим для десктопа; на мобиле всегда только «день» */
const viewMode = ref<'day' | 'week'>('day')

/** Фактический режим сетки: на мобиле принудительно day */
const calendarViewMode = computed<'day' | 'week'>(() =>
  isScheduleMobile.value ? 'day' : viewMode.value
)

const selectedDate = ref<Date>(
  route.query.date ? parseDateFromQuery(route.query.date as string) : startOfDay(new Date())
)

const weekStart = computed(() => startOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 }))
const weekEnd = computed(() => endOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 }))
const weekDays = computed(() => eachDayOfInterval({ start: weekStart.value, end: weekEnd.value }))

const weekViewBeforeMobile = ref<'day' | 'week' | null>(null)

function applyMobileViewMode(mobile: boolean) {
  if (import.meta.server) return
  if (mobile) {
    if (viewMode.value === 'week') {
      weekViewBeforeMobile.value = 'week'
    } else {
      weekViewBeforeMobile.value = null
    }
    if (viewMode.value !== 'day') {
      viewMode.value = 'day'
    }
  } else if (weekViewBeforeMobile.value === 'week') {
    viewMode.value = 'week'
    weekViewBeforeMobile.value = null
  }
}

watch(isScheduleMobile, applyMobileViewMode, { immediate: true })

const { user, getAuthHeaders, refreshAccessToken } = useAuth()
const toast = useToast()

const bookings = ref<Booking[]>([])
const services = ref<Service[]>([])
const allBookings = ref<Booking[]>([])
const allEvents = ref<Event[]>([])

const workSchedules = ref<Map<string, WorkSchedule>>(new Map())
/** Триггер пересчёта сетки после обновления Map */
const scheduleTick = ref(0)

const workTimeRange = computed(() => {
  void scheduleTick.value
  const bookingsList = calendarViewMode.value === 'week' ? allBookings.value : bookings.value
  return computeWorkTimeRange(
    [...workSchedules.value.values()],
    normalizeApiList<Booking>(bookingsList),
    normalizeApiList<Event>(allEvents.value)
  )
})

const dayHours = computed(() => {
  void scheduleTick.value
  const hours: number[] = []
  const { minHour, maxHour } = workTimeRange.value
  for (let i = minHour; i <= maxHour; i++) {
    hours.push(i)
  }
  return hours
})

const daySlots = computed(() => {
  const slots: { hour: number, minute: number }[] = []
  for (const hour of dayHours.value) {
    slots.push({ hour, minute: 0 })
    slots.push({ hour, minute: 30 })
  }
  return slots
})

function getWorkScheduleForDate(date: Date): WorkSchedule | undefined {
  const dateStr = format(date, 'yyyy-MM-dd')
  return workSchedules.value.get(dateStr)
}

function isDayNonWork(date: Date): boolean {
  const schedule = getWorkScheduleForDate(date)
  return Boolean(schedule && schedule.type !== 'workday')
}

function getUnavailableTimeBlocks(date: Date): Array<{ start: number, end: number }> {
  void scheduleTick.value
  const schedule = getWorkScheduleForDate(date)
  const blocks: Array<{ start: number, end: number }> = []
  const { minHour, maxHour } = workTimeRange.value
  const displayStartMinutes = minHour * 60
  const displayEndMinutes = (maxHour + 1) * 60

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

  if (schedule.breaks?.length) {
    for (const breakItem of schedule.breaks) {
      const [breakStartHour, breakStartMinute] = breakItem.startTime.split(':').map(Number)
      const [breakEndHour, breakEndMinute] = breakItem.endTime.split(':').map(Number)
      const breakStartMinutes = breakStartHour * 60 + breakStartMinute
      const breakEndMinutes = breakEndHour * 60 + breakEndMinute

      if (
        breakStartMinutes >= workStartMinutes
        && breakEndMinutes <= workEndMinutes
        && breakStartMinutes < displayEndMinutes
        && breakEndMinutes > displayStartMinutes
      ) {
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

function getUnavailableTimePosition(
  startHour: number,
  startMinute: number,
  endHour: number,
  endMinute: number
): { top: string, height: string } {
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = endHour * 60 + endMinute
  const { minHour, maxHour } = workTimeRange.value
  const dayStartMinutes = minHour * 60
  const dayEndMinutes = (maxHour + 1) * 60

  const clampedStartMinutes = Math.max(startMinutes, dayStartMinutes)
  const clampedEndMinutes = Math.min(endMinutes, dayEndMinutes)

  if (clampedStartMinutes >= clampedEndMinutes) {
    return { top: '0px', height: '0px' }
  }

  const relativeStart = clampedStartMinutes - dayStartMinutes
  const duration = clampedEndMinutes - clampedStartMinutes
  const HOUR_HEIGHT_PX = 48
  const MINUTE_HEIGHT_PX = HOUR_HEIGHT_PX / 60

  return {
    top: `${relativeStart * MINUTE_HEIGHT_PX}px`,
    height: `${duration * MINUTE_HEIGHT_PX}px`
  }
}

function isTimeSlotAvailable(date: Date, hour: number, minute: number = 0): boolean {
  const schedule = getWorkScheduleForDate(date)

  if (!schedule) {
    return true
  }

  if (schedule.type !== 'workday') {
    return false
  }

  if (!schedule.startTime || !schedule.endTime) {
    return false
  }

  const [startHour, startMinute] = schedule.startTime.split(':').map(Number)
  const [endHour, endMinute] = schedule.endTime.split(':').map(Number)
  const slotMinutes = hour * 60 + minute
  const workStartMinutes = startHour * 60 + startMinute
  const workEndMinutes = endHour * 60 + endMinute

  if (slotMinutes < workStartMinutes || slotMinutes >= workEndMinutes) {
    return false
  }

  if (schedule.breaks?.length) {
    for (const breakItem of schedule.breaks) {
      const [breakStartHour, breakStartMinute] = breakItem.startTime.split(':').map(Number)
      const [breakEndHour, breakEndMinute] = breakItem.endTime.split(':').map(Number)
      const breakStartMinutes = breakStartHour * 60 + breakStartMinute
      const breakEndMinutes = breakEndHour * 60 + breakEndMinute

      if (slotMinutes >= breakStartMinutes && slotMinutes < breakEndMinutes) {
        return false
      }
    }
  }

  return true
}

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
      const date = calendarViewMode.value === 'day' ? format(selectedDate.value, 'yyyy-MM-dd') : undefined
      const url = date ? `/api/bookings?date=${date}` : '/api/bookings'
      const data = await $fetch<unknown>(url, { headers })
      bookings.value = normalizeApiList<Booking>(data)
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const date = calendarViewMode.value === 'day' ? format(selectedDate.value, 'yyyy-MM-dd') : undefined
          const url = date ? `/api/bookings?date=${date}` : '/api/bookings'
          const retryData = await $fetch<unknown>(url, { headers })
          bookings.value = normalizeApiList<Booking>(retryData)
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
      const data = await $fetch<Service[]>('/api/services', { headers })
      services.value = data || []
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retryData = await $fetch<Service[]>('/api/services', { headers })
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
      const params = new URLSearchParams()
      if (calendarViewMode.value === 'week') {
        params.set('start_date', format(weekStart.value, 'yyyy-MM-dd'))
        params.set('end_date', format(weekEnd.value, 'yyyy-MM-dd'))
      }
      const query = params.toString()
      const url = query ? `/api/bookings?${query}` : '/api/bookings'
      const data = await $fetch<unknown>(url, { headers })
      allBookings.value = normalizeApiList<Booking>(data)
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const params = new URLSearchParams()
          if (calendarViewMode.value === 'week') {
            params.set('start_date', format(weekStart.value, 'yyyy-MM-dd'))
            params.set('end_date', format(weekEnd.value, 'yyyy-MM-dd'))
          }
          const query = params.toString()
          const retryUrl = query ? `/api/bookings?${query}` : '/api/bookings'
          const retryData = await $fetch<unknown>(retryUrl, { headers })
          allBookings.value = normalizeApiList<Booking>(retryData)
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
      const data = await $fetch<unknown>('/api/events', { headers })
      allEvents.value = normalizeApiList<Event>(data)
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retryData = await $fetch<unknown>('/api/events', { headers })
          allEvents.value = normalizeApiList<Event>(retryData)
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

async function loadWorkSchedules() {
  if (!import.meta.client) return

  let headers = getAuthHeaders()
  if (!headers.Authorization) {
    const refreshed = await refreshAccessToken()
    if (!refreshed) return
    headers = getAuthHeaders()
    if (!headers.Authorization) return
  }

  const datesToLoad = calendarViewMode.value === 'day'
    ? [selectedDate.value]
    : weekDays.value
  if (!datesToLoad.length) return

  const startDate = format(datesToLoad[0], 'yyyy-MM-dd')
  const endDate = format(datesToLoad[datesToLoad.length - 1], 'yyyy-MM-dd')

  const fetchOnce = (authHeaders: Record<string, string>) => $fetch<WorkSchedule[]>('/api/schedule', {
    query: { start_date: startDate, end_date: endDate },
    headers: authHeaders
  })

  try {
    let response = await fetchOnce(headers)

    for (const date of datesToLoad) {
      const dateStr = format(date, 'yyyy-MM-dd')
      workSchedules.value.delete(dateStr)
    }

    if (response?.length) {
      for (const schedule of response) {
        if (schedule?.date) {
          workSchedules.value.set(schedule.date, schedule)
        }
      }
    }

    scheduleTick.value++
  } catch (error: any) {
    if (error?.statusCode === 401 || error?.status === 401) {
      const refreshed = await refreshAccessToken()
      if (!refreshed) return
      headers = getAuthHeaders()
      try {
        const response = await fetchOnce(headers)
        for (const date of datesToLoad) {
          const dateStr = format(date, 'yyyy-MM-dd')
          workSchedules.value.delete(dateStr)
        }
        if (response?.length) {
          for (const schedule of response) {
            if (schedule?.date) {
              workSchedules.value.set(schedule.date, schedule)
            }
          }
        }
        scheduleTick.value++
        return
      } catch (retryError) {
        console.error('Error loading work schedules after refresh:', retryError)
        return
      }
    }
    console.error('Error loading work schedules:', error)
  }
}

let isUpdatingFromRoute = false

function updateRoute() {
  if (!import.meta.client) return
  isUpdatingFromRoute = true
  void router.replace({
    path: '/schedule',
    query: {
      date: format(selectedDate.value, 'yyyy-MM-dd'),
      view: isScheduleMobile.value ? 'day' : viewMode.value
    }
  }).finally(() => {
    isUpdatingFromRoute = false
  })
}

watch(selectedDate, () => {
  if (!import.meta.client || isUpdatingFromRoute) return
  updateRoute()
})

watch(viewMode, () => {
  if (!import.meta.client || isUpdatingFromRoute) return
  updateRoute()
})

watch(
  () => route.query.date,
  (dateQ) => {
    if (isUpdatingFromRoute) return
    const raw = Array.isArray(dateQ) ? dateQ[0] : dateQ
    if (typeof raw !== 'string') return
    const parsed = parseDateFromQuery(raw)
    if (!isSameDay(parsed, selectedDate.value)) {
      selectedDate.value = parsed
    }
  }
)

watch(
  () => route.query.view,
  (viewQ) => {
    if (isUpdatingFromRoute) return
    if (isScheduleMobile.value) {
      if (viewMode.value !== 'day') {
        viewMode.value = 'day'
      }
      return
    }
    const raw = Array.isArray(viewQ) ? viewQ[0] : viewQ
    const mode: 'day' | 'week' = raw === 'day' ? 'day' : 'week'
    if (viewMode.value !== mode) {
      viewMode.value = mode
    }
  }
)

watch([selectedDate, viewMode], () => {
  if (!import.meta.client) return
  void nextTick(() => loadWorkSchedules())
})

watch([selectedDate, viewMode, isScheduleMobile], async () => {
  if (!import.meta.client) return
  await nextTick()
  await loadBookings()
  if (calendarViewMode.value === 'week') {
    await loadAllBookings()
  }
}, { flush: 'post' })

onMounted(async () => {
  if (!import.meta.client) return
  const rawDate = route.query.date
  const dateStr = Array.isArray(rawDate) ? rawDate[0] : rawDate
  if (typeof dateStr === 'string') {
    selectedDate.value = parseDateFromQuery(dateStr)
  }
  applyMobileViewMode(isScheduleMobile.value)
  if (!isScheduleMobile.value) {
    viewMode.value = readViewModeFromRoute()
  } else {
    viewMode.value = 'day'
  }

  await loadWorkSchedules()
  await loadBookings()
  if (calendarViewMode.value === 'week') {
    await loadAllBookings()
  }
  await loadServices()
  await loadAllEvents()
})

const events = computed(() => {
  if (!allEvents.value || !Array.isArray(allEvents.value) || allEvents.value.length === 0) return []
  if (calendarViewMode.value === 'day') {
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

const workScheduleOpen = ref(false)

const workScheduleSlideoverUi = {
  content: 'w-full min-w-0 sm:max-w-2xl md:max-w-3xl overflow-visible',
  body: 'flex-1 min-h-0 overflow-y-auto overflow-x-visible p-4 sm:p-6',
  header: 'shrink-0 border-b border-default',
  title: 'text-base sm:text-lg pr-10',
  close: 'absolute top-4 end-4 z-10'
}

function openWorkSchedulePanel() {
  workScheduleOpen.value = true
}

async function onWorkScheduleSaved() {
  await loadWorkSchedules()
  await loadBookings()
  if (calendarViewMode.value === 'week') {
    await loadAllBookings()
  }
  await loadAllEvents()
}

function stripWorkScheduleQuery() {
  const q = { ...route.query } as Record<string, string | string[] | undefined>
  if ('workSchedule' in q) {
    delete q.workSchedule
    void router.replace({ path: '/schedule', query: q })
  }
}

watch(
  () => route.query.workSchedule,
  (v) => {
    if (v === '1' || v === 'true') {
      workScheduleOpen.value = true
      stripWorkScheduleQuery()
    }
  },
  { immediate: true }
)

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

// Для дневного вида - мини-календарь дней недели
const dayViewWeekDays = computed(() => {
  const start = startOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 })
  const end = endOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 })
  return eachDayOfInterval({ start, end })
})

// Индикатор текущего времени (обновляется каждую минуту)
const now = useNow({ interval: 60000 })
const currentTimeFormatted = computed(() => format(now.value, 'HH:mm'))
const currentTimeIndicatorVisible = computed(() => {
  const today = startOfDay(new Date())
  if (calendarViewMode.value === 'day') return isSameDay(selectedDate.value, today)
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
  const bookingsList = calendarViewMode.value === 'week' ? allBookings.value : bookings.value
  if (!bookingsList || !Array.isArray(bookingsList)) return []
  const dateStr = format(date, 'yyyy-MM-dd')
  return bookingsList.filter(b => {
    if (!b || !b.date || b.status === 'cancelled') return false
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

/** Короткий блок (меньше 45 мин): время слева, название справа в одной строке с обрезкой */
function isShortBookingBlock(booking: Booking): boolean {
  return getBookingDuration(booking) < 45
}

function isShortEventBlock(event: Event): boolean {
  return event.duration < 45
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

function handleEventSaved() {
  refreshEvents()
}

async function handleBookingSaved() {
  selectedBookingForEdit.value = null
  await nextTick()
  await refreshBookings()
}

function navigateDate(direction: 'prev' | 'next') {
  const delta = calendarViewMode.value === 'day'
    ? (direction === 'prev' ? -1 : 1)
    : (direction === 'prev' ? -7 : 7)
  selectedDate.value = addDays(selectedDate.value, delta)
}

function navigateDay(direction: 'prev' | 'next') {
  selectedDate.value = addDays(selectedDate.value, direction === 'prev' ? -1 : 1)
}

function selectScheduleDay(day: Date) {
  selectedDate.value = startOfDay(day)
}

function setViewMode(mode: 'day' | 'week') {
  if (isScheduleMobile.value || mode === 'day') {
    if (viewMode.value !== 'day') {
      viewMode.value = 'day'
    }
    return
  }
  if (viewMode.value === mode) return
  viewMode.value = mode
}

function openPublicProfilePreview() {
  if (!user.value?.username) {
    toast.add({
      title: 'Ошибка',
      description: 'Не удалось получить имя пользователя',
      color: 'error'
    })
    return
  }
  window.open(`/booking/${user.value.username}`, '_blank')
}
</script>

<template>
  <UDashboardPanel id="schedule-page" :ui="{ body: 'max-md:px-0 md:px-4' }">
    <template #header>
      <UDashboardNavbar>
        <template #leading>
          <div class="flex items-center gap-2">
            <div class="hidden"><UDashboardSidebarCollapse /></div>
            
            <!-- Переключатель недели — desktop, только в режиме «Неделя» -->
            <div v-if="calendarViewMode === 'week'" class="hidden md:flex items-center gap-1">
              <UButton
                icon="i-lucide-chevron-left"
                color="neutral"
                variant="ghost"
                square
                size="sm"
                @click="navigateDate('prev')"
              />
              <span class="text-sm font-medium px-2">
                Неделя {{ format(weekStart, 'd MMM', { locale: ru }) }} - {{ format(weekEnd, 'd MMM', { locale: ru }) }}
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

            <!-- Мобилка: превью публичной страницы вместо переключателя даты в шапке -->
            <div class="flex flex-1 justify-center min-w-0 md:hidden">
              <UButton
                icon="i-lucide-external-link"
                color="neutral"
                variant="ghost"
                size="sm"
                label="Как это выглядит"
                :disabled="!user?.username"
                class="max-w-full"
                @click="openPublicProfilePreview"
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
              class="hidden md:inline-flex shrink-0"
              @click="openPublicProfilePreview"
            />

            <UButton
              icon="i-lucide-cog"
              color="neutral"
              variant="solid"
              size="sm"
              aria-label="Настройки расписания"
              :class="scheduleHeaderIconBtnClass"
              @click="openWorkSchedulePanel"
            />

            <UButton
              icon="i-lucide-plus"
              color="neutral"
              variant="solid"
              size="sm"
              :class="scheduleHeaderIconBtnClass"
              @click="slotDateForModal = null; slotTimeForModal = null; bookingModalOpen = true"
            />

            <div
              v-show="!isScheduleMobile"
              class="flex h-11 min-h-11 shrink-0 items-center gap-0.5 rounded-full border border-default bg-elevated p-1 box-border"
              role="tablist"
              aria-label="Режим календаря"
            >
              <button
                type="button"
                role="tab"
                :aria-selected="viewMode === 'day'"
                class="flex min-w-0 flex-1 items-center justify-center self-stretch rounded-full px-3 text-sm font-medium transition-colors"
                :class="viewMode === 'day' ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900' : 'text-muted hover:text-highlighted'"
                @click="setViewMode('day')"
              >
                День
              </button>
              <button
                type="button"
                role="tab"
                :aria-selected="viewMode === 'week'"
                class="flex min-w-0 flex-1 items-center justify-center self-stretch rounded-full px-3 text-sm font-medium transition-colors"
                :class="viewMode === 'week' ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900' : 'text-muted hover:text-highlighted'"
                @click="setViewMode('week')"
              >
                Неделя
              </button>
            </div>
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex-1 overflow-auto">
        <!-- Дневной вид -->
        <div v-if="calendarViewMode === 'day'" class="relative h-full">
          <!-- Мини-календарь дней недели (на мобиле без пустой колонки под шкалу времени) -->
          <div class="flex border-b border-default mb-2">
            <div class="hidden md:block w-16 shrink-0 border-r border-default/30" />
            <div class="flex-1 flex items-center min-w-0 max-md:pl-0 max-md:pr-0">
              <!-- Кнопка переключения назад -->
              <UButton
                icon="i-lucide-chevron-left"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                @click="navigateDay('prev')"
                class="shrink-0 max-md:mx-0.5 md:mx-1"
              />
              
              <!-- Дни недели -->
              <div class="flex-1 min-w-0 grid grid-cols-7">
                <div
                  v-for="(day, index) in dayViewWeekDays"
                  :key="day.getTime()"
                  class="p-1.5 md:p-2 text-center cursor-pointer transition-colors"
                  :class="{
                    'bg-gray-900/10 dark:bg-white/10': isSameDay(day, selectedDate),
                    'hover:bg-elevated/50': !isSameDay(day, selectedDate),
                    'border-l border-default': index > 0
                  }"
                  @click="void selectScheduleDay(day)"
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
                class="shrink-0 max-md:mx-0.5 md:mx-1"
              />
            </div>
          </div>

          <div class="flex min-w-0 max-md:pl-0">
            <!-- Временная шкала (формат как на референсе: 10 00, 30) -->
            <div class="w-12 shrink-0 border-r border-default/30 md:w-16">
              <div
                v-for="hour in dayHours"
                :key="hour"
                class="relative flex flex-col items-end pr-1 text-muted md:pr-2"
                style="height: 48px; min-height: 48px; max-height: 48px; box-sizing: border-box;"
              >
                <div class="flex items-baseline gap-0.5" style="padding-top: 2px;">
                  <span class="text-sm font-medium">{{ String(hour).padStart(2, '0') }}</span>
                  <span class="text-[10px] -translate-y-0.5">00</span>
                </div>
                <span class="text-[10px] absolute max-md:right-1 md:right-2" style="top: 24px;">30</span>
              </div>
            </div>

            <!-- Расписание -->
            <div class="flex-1 relative min-w-0 px-1.5 md:px-4">
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
                  <div
                    class="absolute inset-0 z-[8] pointer-events-none"
                    :class="isDayNonWork(selectedDate) ? 'bg-gray-400/25 dark:bg-gray-600/25' : ''"
                  >
                    <template
                      v-for="block in getUnavailableTimeBlocks(selectedDate)"
                      :key="`unavailable-${format(selectedDate, 'yyyy-MM-dd')}-${block.start}-${block.end}`"
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
                class="absolute inset-0 z-10 grid"
                :style="{ gridTemplateRows: `repeat(${daySlots.length}, 24px)` }"
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
              <div class="absolute inset-0 z-20 pointer-events-none">
                <div
                  v-for="booking in getBookingsForDate(selectedDate)"
                  :key="booking.id"
                  class="absolute left-2 right-2 flex flex-col overflow-hidden rounded-md text-white text-sm cursor-pointer hover:opacity-90 transition-opacity pointer-events-auto"
                  :style="{ ...getBookingPosition(booking, selectedDate), boxSizing: 'border-box' }"
                  :class="[
                    getBookingColorClass(booking),
                    {
                      'p-2': !isShortBookingBlock(booking),
                      'px-1.5 py-0.5': isShortBookingBlock(booking)
                    }
                  ]"
                  @click.stop="openBookingDetail(booking)"
                >
                  <div
                    v-if="isShortBookingBlock(booking)"
                    class="flex min-h-0 min-w-0 flex-1 items-center gap-1.5"
                  >
                    <span class="shrink-0 text-[10px] font-medium tabular-nums leading-none sm:text-xs">{{ booking.startTime }}</span>
                    <span class="min-w-0 flex-1 truncate text-xs font-medium leading-tight">{{ booking.serviceName }}</span>
                  </div>
                  <template v-else>
                    <div class="font-medium">{{ booking.startTime }} {{ booking.serviceName }}</div>
                    <div class="text-xs opacity-90">{{ booking.customerName }}</div>
                  </template>
                </div>
              </div>

              <!-- События (pointer-events-none на контейнере — клики проходят к бронированиям; pointer-events-auto на элементах) -->
              <div class="absolute inset-0 z-20 pointer-events-none">
                <div
                  v-for="event in getEventsForDate(selectedDate)"
                  :key="`event-${event.id}`"
                  class="absolute left-2 right-2 flex flex-col overflow-hidden rounded-md bg-purple-500 text-white text-sm cursor-pointer hover:opacity-90 transition-opacity border-2 border-purple-600 pointer-events-auto"
                  :style="{ ...getEventPosition(event, selectedDate), boxSizing: 'border-box' }"
                  :class="isShortEventBlock(event) ? 'px-1.5 py-0.5' : 'p-2'"
                  @click.stop="openEventDetail(event)"
                >
                  <div
                    v-if="isShortEventBlock(event)"
                    class="flex min-h-0 min-w-0 flex-1 items-center gap-1.5"
                  >
                    <span class="shrink-0 text-[10px] font-medium tabular-nums leading-none sm:text-xs">{{ event.startTime }}</span>
                    <span class="min-w-0 flex-1 truncate text-xs font-medium leading-tight">{{ event.name }}</span>
                  </div>
                  <template v-else>
                    <div class="font-medium">{{ event.startTime }} {{ event.name }}</div>
                    <div class="text-xs opacity-90">
                      <span v-if="event.serviceId">{{ getServiceName(event.serviceId) }}</span>
                      <span class="ml-2">{{ event.bookedSlots }}/{{ event.maxParticipants }} мест</span>
                    </div>
                  </template>
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
                <div
                  class="relative"
                  style="box-sizing: border-box;"
                  :class="isDayNonWork(day) ? 'bg-gray-400/25 dark:bg-gray-600/25' : ''"
                >
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
                  <div class="absolute inset-0 z-[8] pointer-events-none">
                    <template
                      v-for="block in getUnavailableTimeBlocks(day)"
                      :key="`unavailable-${format(day, 'yyyy-MM-dd')}-${block.start}-${block.end}`"
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
                      :key="`slot-${format(day, 'yyyy-MM-dd')}-${slot.hour}-${slot.minute}`"
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
                      class="absolute left-1 right-1 flex flex-col overflow-hidden rounded-md text-white text-xs cursor-pointer hover:opacity-90 transition-opacity pointer-events-auto"
                      :style="{ ...getBookingPosition(booking, day), boxSizing: 'border-box' }"
                      :class="[
                        getBookingColorClass(booking),
                        isShortBookingBlock(booking) ? 'px-1 py-0.5' : 'p-1'
                      ]"
                      @click.stop="openBookingDetail(booking)"
                    >
                      <div
                        v-if="isShortBookingBlock(booking)"
                        class="flex min-h-0 min-w-0 flex-1 items-center gap-1"
                      >
                        <span class="shrink-0 text-[9px] font-medium tabular-nums leading-none">{{ booking.startTime }}</span>
                        <span class="min-w-0 flex-1 truncate font-medium leading-tight">{{ booking.serviceName }}</span>
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
                      class="absolute left-1 right-1 flex flex-col overflow-hidden rounded-md bg-purple-500 text-white text-xs cursor-pointer hover:opacity-90 transition-opacity border border-purple-600 pointer-events-auto"
                      :style="{ ...getEventPosition(event, day), boxSizing: 'border-box' }"
                      :class="isShortEventBlock(event) ? 'px-1 py-0.5' : 'p-1.5'"
                      @click.stop="openEventDetail(event)"
                    >
                      <div
                        v-if="isShortEventBlock(event)"
                        class="flex min-h-0 min-w-0 flex-1 items-center gap-1"
                      >
                        <span class="shrink-0 text-[9px] font-medium tabular-nums leading-none">{{ event.startTime }}</span>
                        <span class="min-w-0 flex-1 truncate font-medium leading-tight">{{ event.name }}</span>
                      </div>
                      <template v-else>
                        <div class="font-medium truncate">{{ event.startTime }} {{ event.name }}</div>
                        <div class="truncate text-xs/90">
                          <span v-if="event.serviceId">{{ getServiceName(event.serviceId) }}</span>
                        </div>
                      </template>
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

  <USlideover
    v-model:open="workScheduleOpen"
    title="Настройки расписания"
    side="right"
    :ui="workScheduleSlideoverUi"
  >
    <template #body>
      <WorkScheduleEditor
        v-if="workScheduleOpen"
        @saved="onWorkScheduleSaved"
      />
    </template>
  </USlideover>
</template>
