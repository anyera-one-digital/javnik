<script setup lang="ts">
import { format, startOfDay, isSameDay, startOfWeek, endOfWeek, eachDayOfInterval, parse } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { DropdownMenuItem } from '@nuxt/ui'
import { computeWorkTimeRange } from '~/utils/workTimeRange'
import { normalizeApiList } from '~/utils/normalizeApiList'
import { getBookingCardStyle, getEventCardStyle } from '~/utils/bookingColors'
import type { Booking, Event, Service, WorkSchedule } from '~/types'
import BookingCreateModal from '~/components/UserPersonalAccount/schedule/BookingCreateModal.vue'
import ScheduleEventModal from '~/components/UserPersonalAccount/schedule/EventModal.vue'
import ScheduleBookingDetailModal from '~/components/UserPersonalAccount/schedule/BookingDetailModal.vue'
import WorkScheduleEditor from '~/components/UserPersonalAccount/schedule/WorkScheduleEditor.vue'
import { formatWeekdayShort } from '~/utils'

/** Высота часа в сетке: 30 мин ≈ одна строка текста, 60 мин — время+услуга+клиент */
const SCHEDULE_HOUR_HEIGHT_PX = 72
const SCHEDULE_HALF_HOUR_PX = SCHEDULE_HOUR_HEIGHT_PX / 2
const SCHEDULE_MINUTE_HEIGHT_PX = SCHEDULE_HOUR_HEIGHT_PX / 60

type ScheduleCardDensity = 'compact' | 'medium' | 'full'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

useSeoMeta({
  title: 'Расписание'
})

const route = useRoute()
const router = useRouter()

const isScheduleMobile = useMediaQuery('(max-width: 767px)')

function readViewModeFromRoute(): 'day' | 'week' {
  const v = route.query.view
  const raw = Array.isArray(v) ? v[0] : v
  return raw === 'day' ? 'day' : 'week'
}

function parseDateKey(dateStr: string): Date {
  try {
    return startOfDay(parse(dateStr, 'yyyy-MM-dd', new Date()))
  } catch {
    return startOfDay(new Date())
  }
}

/** Сайдбар пишет сюда же; страница всегда читает дату из route + anchor */
const { pushScheduleDate, navigateScheduleDays, anchorDate } = useSchedulePageDate()

/** Единый источник даты: URL, иначе anchor */
const dateKey = computed(() => {
  const raw = route.query.date
  const fromRoute = Array.isArray(raw) ? raw[0] : raw
  if (typeof fromRoute === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(fromRoute)) {
    return fromRoute
  }
  if (typeof anchorDate.value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(anchorDate.value)) {
    return anchorDate.value
  }
  return format(startOfDay(new Date()), 'yyyy-MM-dd')
})

const selectedDate = computed(() => parseDateKey(dateKey.value))

/**
 * Одна модель недели: шапка и колонки берутся из одного computed —
 * иначе после HMR/рассинхрона шапка 24–30, а колонки 3–9 (записи «пропадают»).
 */
const weekView = computed(() => {
  const start = startOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 })
  const end = endOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 })
  const days = eachDayOfInterval({ start, end }).map((d) => {
    const key = format(d, 'yyyy-MM-dd')
    return {
      key,
      date: d,
      weekday: formatWeekdayShort(d),
      dayNum: format(d, 'd')
    }
  })
  return {
    start,
    end,
    startKey: format(start, 'yyyy-MM-dd'),
    endKey: format(end, 'yyyy-MM-dd'),
    label: `${format(start, 'd MMM', { locale: ru })} - ${format(end, 'd MMM', { locale: ru })}`,
    days
  }
})

const weekRangeLabel = computed(() => weekView.value.label)
const weekStart = computed(() => weekView.value.start)
const weekEnd = computed(() => weekView.value.end)
const weekDays = computed(() => weekView.value.days.map(d => d.date))

/** Режим для десктопа; на мобиле всегда только «день» */
const viewMode = ref<'day' | 'week'>(readViewModeFromRoute())

/** Фактический режим сетки: на мобиле принудительно day */
const calendarViewMode = computed<'day' | 'week'>(() =>
  isScheduleMobile.value ? 'day' : viewMode.value
)

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

const { user, getAuthHeaders, refreshAccessToken, accessToken } = useAuth()
const toast = useToast()

const bookings = ref<Booking[]>([])
const services = ref<Service[]>([])
const allBookings = ref<Booking[]>([])
const allEvents = ref<Event[]>([])

const workSchedules = ref<Map<string, WorkSchedule>>(new Map())
/** Триггер пересчёта сетки после обновления Map */
const scheduleTick = ref(0)

/** Ключ активного запроса — применяем ответ только если ключ ещё актуален */
let bookingsRequestKey = ''
let schedulesRequestKey = ''
let bookingsReloadTimer: ReturnType<typeof setTimeout> | null = null

const workTimeRange = computed(() => {
  void scheduleTick.value
  const bookingsList = calendarViewMode.value === 'week' ? allBookings.value : bookings.value
  return computeWorkTimeRange(
    [...workSchedules.value.values()],
    normalizeApiList<Booking>(bookingsList),
    normalizeApiList<Event>(allEvents.value)
  )
})

/** Сегодня в текущем виде (день/неделя) — для линии «Сейчас» */
const isScheduleTodayInView = computed(() => {
  const today = startOfDay(new Date())
  if (calendarViewMode.value === 'day') return isSameDay(selectedDate.value, today)
  return weekView.value.days.some(d => isSameDay(d.date, today))
})

/** Тик каждую минуту — позиция линии «Сейчас» */
const now = useNow({ interval: 60000 })

const dayHours = computed(() => {
  void scheduleTick.value
  void now.value
  let { minHour, maxHour } = workTimeRange.value

  // Если сегодня в видимом диапазоне — расширяем сетку, чтобы линия «Сейчас» не пропадала вечером/утром
  if (import.meta.client && isScheduleTodayInView.value) {
    const nh = now.value.getHours()
    minHour = Math.min(minHour, nh)
    maxHour = Math.max(maxHour, nh)
  }

  const hours: number[] = []
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

  return {
    top: `${relativeStart * SCHEDULE_MINUTE_HEIGHT_PX}px`,
    height: `${duration * SCHEDULE_MINUTE_HEIGHT_PX}px`
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

async function fetchBookingsWithAuth(url: string): Promise<Booking[] | null> {
  let headers = getAuthHeaders()
  if (!headers.Authorization) {
    const refreshed = await refreshAccessToken()
    if (refreshed) headers = getAuthHeaders()
    if (!headers.Authorization) return null
  }

  try {
    const data = await $fetch<unknown>(url, { headers })
    return normalizeApiList<Booking>(data)
  } catch (error: any) {
    if (error.statusCode === 401 || error.status === 401) {
      const refreshed = await refreshAccessToken()
      if (refreshed) {
        headers = getAuthHeaders()
        const retryData = await $fetch<unknown>(url, { headers })
        return normalizeApiList<Booking>(retryData)
      }
    }
    throw error
  }
}

function currentBookingsUrl(): string {
  if (calendarViewMode.value === 'week') {
    return `/api/bookings/?start_date=${weekView.value.startKey}&end_date=${weekView.value.endKey}`
  }
  return `/api/bookings/?date=${dateKey.value}`
}

/** Загрузка записей для текущего вида (trailing slash обязателен — иначе Django 301) */
async function reloadVisibleBookings() {
  if (!import.meta.client) return

  const mode = calendarViewMode.value
  const url = currentBookingsUrl()
  const requestId = `${mode}:${url}:${Date.now()}`
  bookingsRequestKey = requestId

  try {
    const list = await fetchBookingsWithAuth(url)
    // Ответ устарел только если уже ушёл другой запрос
    if (bookingsRequestKey !== requestId) return
    if (list == null) return

    if (mode === 'week') {
      allBookings.value = list
    } else {
      bookings.value = list
    }
  } catch (error) {
    if (bookingsRequestKey !== requestId) return
    console.error('Failed to load bookings:', error)
  }
}

function scheduleReloadVisibleBookings(delayMs = 40) {
  if (!import.meta.client) return
  if (bookingsReloadTimer) clearTimeout(bookingsReloadTimer)
  bookingsReloadTimer = setTimeout(() => {
    bookingsReloadTimer = null
    void reloadVisibleBookings()
  }, delayMs)
}

async function loadBookings() {
  await reloadVisibleBookings()
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
  await reloadVisibleBookings()
}

async function loadAllEvents() {
  if (!process.client) return

  try {
    let headers = getAuthHeaders()
    if (!headers.Authorization) return

    try {
      const data = await $fetch<unknown>('/api/events/', { headers })
      allEvents.value = normalizeApiList<Event>(data).map(normalizeScheduleEvent)
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retryData = await $fetch<unknown>('/api/events/', { headers })
          allEvents.value = normalizeApiList<Event>(retryData).map(normalizeScheduleEvent)
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
  await reloadVisibleBookings()
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

  const mode = calendarViewMode.value
  const datesToLoad = mode === 'day'
    ? [selectedDate.value]
    : weekDays.value
  if (!datesToLoad.length) return

  const startDate = format(datesToLoad[0]!, 'yyyy-MM-dd')
  const endDate = format(datesToLoad[datesToLoad.length - 1]!, 'yyyy-MM-dd')
  const requestKey = `${mode}:${startDate}:${endDate}`
  schedulesRequestKey = requestKey

  const fetchOnce = (authHeaders: Record<string, string>) => $fetch<WorkSchedule[]>('/api/schedule/', {
    query: { start_date: startDate, end_date: endDate },
    headers: authHeaders
  })

  try {
    const response = await fetchOnce(headers)
    if (schedulesRequestKey !== requestKey) return

    const next = new Map(workSchedules.value)
    for (const date of datesToLoad) {
      next.delete(format(date, 'yyyy-MM-dd'))
    }
    if (response?.length) {
      for (const schedule of response) {
        if (schedule?.date) {
          next.set(schedule.date, schedule)
        }
      }
    }
    workSchedules.value = next
    scheduleTick.value++
  } catch (error: any) {
    if (error?.statusCode === 401 || error?.status === 401) {
      const refreshed = await refreshAccessToken()
      if (!refreshed) return
      headers = getAuthHeaders()
      try {
        const response = await fetchOnce(headers)
        if (schedulesRequestKey !== requestKey) return
        const next = new Map(workSchedules.value)
        for (const date of datesToLoad) {
          next.delete(format(date, 'yyyy-MM-dd'))
        }
        if (response?.length) {
          for (const schedule of response) {
            if (schedule?.date) {
              next.set(schedule.date, schedule)
            }
          }
        }
        workSchedules.value = next
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

function syncViewToRoute() {
  if (!import.meta.client) return
  const nextView = isScheduleMobile.value ? 'day' : viewMode.value
  if (route.query.view === nextView) return
  void router.replace({
    path: '/schedule',
    query: {
      ...route.query,
      date: format(selectedDate.value, 'yyyy-MM-dd'),
      view: nextView
    }
  })
}

watch(viewMode, () => {
  syncViewToRoute()
})

watch(
  () => route.query.view,
  (viewQ) => {
    if (isScheduleMobile.value) {
      if (viewMode.value !== 'day') viewMode.value = 'day'
      return
    }
    const raw = Array.isArray(viewQ) ? viewQ[0] : viewQ
    const mode: 'day' | 'week' = raw === 'day' ? 'day' : 'week'
    if (viewMode.value !== mode) viewMode.value = mode
  }
)

watch(
  [dateKey, viewMode, isScheduleMobile],
  () => {
    if (!import.meta.client) return
    if (anchorDate.value !== dateKey.value) {
      anchorDate.value = dateKey.value
    }
    void loadWorkSchedules()
    scheduleReloadVisibleBookings(0)
  },
  { flush: 'post' }
)

// Токен появился позже гидрации — догружаем записи
watch(accessToken, (token, prev) => {
  if (!import.meta.client) return
  if (token && token !== prev) {
    scheduleReloadVisibleBookings(0)
    void loadWorkSchedules()
    void loadServices()
    void loadAllEvents()
  }
})

onMounted(async () => {
  if (!import.meta.client) return
  applyMobileViewMode(isScheduleMobile.value)
  if (!isScheduleMobile.value) {
    viewMode.value = readViewModeFromRoute()
  } else {
    viewMode.value = 'day'
  }
  syncViewToRoute()

  await Promise.all([
    loadWorkSchedules(),
    reloadVisibleBookings(),
    loadServices(),
    loadAllEvents()
  ])
})

const events = computed(() => {
  if (!allEvents.value || !Array.isArray(allEvents.value) || allEvents.value.length === 0) return []
  if (calendarViewMode.value === 'day') {
    return allEvents.value.filter(e => e && e.date === dateKey.value)
  }
  const start = weekView.value.startKey
  const end = weekView.value.endKey
  return allEvents.value.filter(e => e?.date && e.date >= start && e.date <= end)
})

// Для дневного вида - мини-календарь дней недели
const dayViewWeekDays = computed(() => weekView.value.days.map(d => d.date))

const currentTimeIndicatorVisible = computed(() => isScheduleTodayInView.value)

const eventModalOpen = ref(false)
const selectedEvent = ref<Event | null>(null)

const bookingModalOpen = ref(false)
const selectedBooking = ref<Booking | null>(null)
const selectedBookingForEdit = ref<Booking | null>(null)
const bookingDetailModalOpen = ref(false)

// Для открытия модалки создания брони из слота (дата и время слота)
const slotDateForModal = ref<Date | null>(null)
const slotTimeForModal = ref<string | null>(null)
const slotCreateChoiceOpen = ref(false)

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
  await Promise.all([
    loadWorkSchedules(),
    reloadVisibleBookings(),
    loadAllEvents()
  ])
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

function openCreateChoiceForSlot(date: Date, hour: number, minute: number) {
  if (!isTimeSlotAvailable(date, hour, minute)) return
  slotDateForModal.value = date
  slotTimeForModal.value = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
  selectedBookingForEdit.value = null
  selectedEvent.value = null
  slotCreateChoiceOpen.value = true
}

function openCreateBooking() {
  slotDateForModal.value = null
  slotTimeForModal.value = null
  selectedBookingForEdit.value = null
  bookingModalOpen.value = true
}

function openCreateEvent() {
  slotDateForModal.value = null
  slotTimeForModal.value = null
  selectedEvent.value = null
  eventModalOpen.value = true
}

function chooseCreateBookingFromSlot() {
  slotCreateChoiceOpen.value = false
  selectedBookingForEdit.value = null
  bookingModalOpen.value = true
}

function chooseCreateEventFromSlot() {
  slotCreateChoiceOpen.value = false
  selectedEvent.value = null
  eventModalOpen.value = true
}

const createMenuItems = computed<DropdownMenuItem[][]>(() => [[
  {
    label: 'Запись',
    icon: 'i-lucide-calendar-plus',
    description: 'Индивидуальная запись клиента',
    onSelect: () => openCreateBooking()
  },
  {
    label: 'Событие',
    icon: 'i-lucide-users',
    description: 'Групповое занятие с лимитом мест',
    onSelect: () => openCreateEvent()
  }
]])

watch(bookingModalOpen, (open) => {
  if (!open) {
    selectedBookingForEdit.value = null
    if (!eventModalOpen.value && !slotCreateChoiceOpen.value) {
      slotDateForModal.value = null
      slotTimeForModal.value = null
    }
  }
})

watch(eventModalOpen, (open) => {
  if (!open) {
    selectedEvent.value = null
    if (!bookingModalOpen.value && !slotCreateChoiceOpen.value) {
      slotDateForModal.value = null
      slotTimeForModal.value = null
    }
  }
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

// Индикатор текущего времени (обновляется каждую минуту)
const currentTimeFormatted = computed(() => format(now.value, 'HH:mm'))
const currentTimeTopPx = computed(() => {
  if (!isScheduleTodayInView.value) return -1

  const hours = dayHours.value
  if (hours.length === 0) return -1

  const firstHour = hours[0]!
  const lastHour = hours[hours.length - 1]!
  const dayStartMinutes = firstHour * 60
  const dayEndMinutes = (lastHour + 1) * 60
  const currentMinutes = now.value.getHours() * 60 + now.value.getMinutes()

  // В пределах сетки (сетка уже расширена под «сейчас» в dayHours)
  if (currentMinutes < dayStartMinutes) return 0
  if (currentMinutes >= dayEndMinutes) {
    return Math.max(0, (dayEndMinutes - dayStartMinutes - 1) * SCHEDULE_MINUTE_HEIGHT_PX)
  }
  return (currentMinutes - dayStartMinutes) * SCHEDULE_MINUTE_HEIGHT_PX
})

/** Высота шапки колонок недели (пн / число) — для линии «Сейчас» */
const weekDayHeaderHeightPx = 52
const weekNowLineTopPx = computed(() => {
  if (currentTimeTopPx.value < 0) return -1
  return weekDayHeaderHeightPx + currentTimeTopPx.value
})

function getBookingsForDate(date: Date): Booking[] {
  const bookingsList = calendarViewMode.value === 'week' ? allBookings.value : bookings.value
  if (!bookingsList || !Array.isArray(bookingsList)) return []
  const dateStr = format(date, 'yyyy-MM-dd')
  return bookingsList.filter(b => {
    if (!b || b.status === 'cancelled') return false
    const raw = b.date as string | Date | undefined
    if (!raw) return false
    const bookingDate = typeof raw === 'string'
      ? raw.slice(0, 10)
      : format(raw, 'yyyy-MM-dd')
    return bookingDate === dateStr
  })
}

function getBookingsForDateKey(dateStr: string): Booking[] {
  const bookingsList = calendarViewMode.value === 'week' ? allBookings.value : bookings.value
  if (!bookingsList || !Array.isArray(bookingsList)) return []
  return bookingsList.filter(b => {
    if (!b || b.status === 'cancelled' || !b.date) return false
    const bookingDate = typeof b.date === 'string' ? b.date.slice(0, 10) : format(b.date as Date, 'yyyy-MM-dd')
    return bookingDate === dateStr
  })
}

/**
 * Графитовая карточка записи: фон + цветной маркер услуги слева
 */
function getBookingColorStyle(booking: Booking): Record<string, string> {
  return getBookingCardStyle(booking, services.value)
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
  
  const topPx = relativeStart * SCHEDULE_MINUTE_HEIGHT_PX
  const heightPx = duration * SCHEDULE_MINUTE_HEIGHT_PX
  
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

/** Плотность текста в карточке по длительности — без обрезки по вертикали */
function getBookingDensity(booking: Booking): ScheduleCardDensity {
  const d = getBookingDuration(booking)
  if (d <= 30) return 'compact'
  if (d < 60) return 'medium'
  return 'full'
}

function getEventDensity(ev: Event): ScheduleCardDensity {
  const d = Number(ev.duration) || 60
  if (d <= 30) return 'compact'
  if (d < 60) return 'medium'
  return 'full'
}

function isShortBookingBlock(booking: Booking): boolean {
  return getBookingDensity(booking) === 'compact'
}

function normalizeScheduleEvent(raw: Event | Record<string, unknown>): Event {
  const e = raw as Record<string, unknown>
  const startRaw = (e.startTime ?? e.start_time ?? '') as string
  const startTime = String(startRaw).slice(0, 5)
  const serviceName = String(e.serviceName ?? e.service_name ?? '').trim()
  const name = String(e.name ?? serviceName ?? 'Событие').trim() || 'Событие'
  return {
    ...(raw as Event),
    id: Number(e.id),
    name,
    date: String(e.date ?? '').slice(0, 10),
    startTime,
    duration: Number(e.duration) || 60,
    serviceId: (e.serviceId ?? e.service ?? null) as number | null | undefined,
    maxParticipants: Number(e.maxParticipants ?? e.max_participants ?? 0) || undefined,
    bookedSlots: Number(e.bookedSlots ?? e.booked_slots ?? 0) || undefined
  }
}

function isShortEventBlock(ev: Event): boolean {
  return getEventDensity(ev) === 'compact'
}

function getEventTitle(ev: Event): string {
  return (ev.name || 'Событие').trim() || 'Событие'
}

function getEventBlockStyle(ev: Event, date: Date): Record<string, string> {
  return {
    ...getEventPosition(ev, date),
    ...getEventCardStyle()
  }
}

function getEventPosition(event: Event, _date: Date): { top: string, height: string } {
  const startRaw = event.startTime || ''
  const [startHour = 0, startMinute = 0] = startRaw.split(':').map(Number)
  const startMinutes = startHour * 60 + startMinute
  const endMinutes = startMinutes + (Number(event.duration) || 60)

  const hours = dayHours.value
  if (hours.length === 0) {
    return { top: '0px', height: '0px' }
  }

  const firstDisplayedHour = hours[0]!
  const lastDisplayedHour = hours[hours.length - 1]!
  const dayStartMinutes = firstDisplayedHour * 60
  const dayEndMinutes = (lastDisplayedHour + 1) * 60

  const clampedStartMinutes = Math.max(startMinutes, dayStartMinutes)
  const clampedEndMinutes = Math.min(endMinutes, dayEndMinutes)

  if (clampedStartMinutes >= clampedEndMinutes) {
    return { top: '0px', height: '0px' }
  }

  const relativeStart = clampedStartMinutes - dayStartMinutes
  const duration = clampedEndMinutes - clampedStartMinutes

  const topPx = relativeStart * SCHEDULE_MINUTE_HEIGHT_PX
  const heightPx = duration * SCHEDULE_MINUTE_HEIGHT_PX

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
  void navigateScheduleDays(delta)
}

function goToToday() {
  void pushScheduleDate(startOfDay(new Date()))
}

function navigateDay(direction: 'prev' | 'next') {
  void navigateScheduleDays(direction === 'prev' ? -1 : 1)
}

function selectScheduleDay(day: Date) {
  void pushScheduleDate(startOfDay(day))
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
          <div class="flex items-center gap-1.5 min-w-0">
            <div class="hidden"><UDashboardSidebarCollapse /></div>

            <!-- Навигация по дате + Сегодня -->
            <div class="hidden md:flex items-center gap-1 min-w-0">
              <UButton
                icon="i-lucide-chevron-left"
                color="neutral"
                variant="ghost"
                square
                size="sm"
                @click="calendarViewMode === 'week' ? navigateDate('prev') : navigateDay('prev')"
              />
              <UButton
                icon="i-lucide-chevron-right"
                color="neutral"
                variant="ghost"
                square
                size="sm"
                @click="calendarViewMode === 'week' ? navigateDate('next') : navigateDay('next')"
              />
              <UButton
                label="Сегодня"
                color="neutral"
                variant="outline"
                size="sm"
                class="shrink-0"
                @click="goToToday"
              />
              <span class="text-sm font-medium px-2 truncate">
                <template v-if="calendarViewMode === 'week'">Неделя {{ weekRangeLabel }}</template>
                <template v-else>{{ format(selectedDate, 'd MMMM yyyy', { locale: ru }) }}</template>
              </span>
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
              variant="ghost"
              size="sm"
              aria-label="Настройки расписания"
              class="hidden sm:inline-flex"
              @click="openWorkSchedulePanel"
            />

            <UDropdownMenu
              :items="createMenuItems"
              :content="{ align: 'end', collisionPadding: 12 }"
              :ui="{ content: 'w-64' }"
            >
              <UButton
                icon="i-lucide-plus"
                label="Новая запись"
                size="sm"
                class="shrink-0 !bg-violet-500 !text-white hover:!bg-violet-400 dark:!bg-violet-500 dark:hover:!bg-violet-400"
              />
            </UDropdownMenu>

            <div
              v-show="!isScheduleMobile"
              class="flex h-9 min-h-9 shrink-0 items-center gap-0.5 rounded-full border border-default bg-elevated p-0.5 box-border"
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
                :style="{ height: `${SCHEDULE_HOUR_HEIGHT_PX}px`, minHeight: `${SCHEDULE_HOUR_HEIGHT_PX}px`, maxHeight: `${SCHEDULE_HOUR_HEIGHT_PX}px`, boxSizing: 'border-box' }"
              >
                <div class="flex items-baseline gap-0.5" style="padding-top: 2px;">
                  <span class="text-sm font-medium">{{ String(hour).padStart(2, '0') }}</span>
                  <span class="text-[10px] -translate-y-0.5">00</span>
                </div>
                <span class="text-[10px] absolute max-md:right-1 md:right-2" :style="{ top: `${SCHEDULE_HALF_HOUR_PX}px` }">30</span>
              </div>
            </div>

            <!-- Расписание -->
            <div class="flex-1 relative min-w-0 px-1.5 md:px-4">
              <!-- Сетка часов (pointer-events-none чтобы клики проходили к бронированиям) -->
              <div
                v-for="hour in dayHours"
                :key="hour"
                class="border-b border-default relative pointer-events-none"
                :style="{ height: `${SCHEDULE_HOUR_HEIGHT_PX}px`, minHeight: `${SCHEDULE_HOUR_HEIGHT_PX}px`, maxHeight: `${SCHEDULE_HOUR_HEIGHT_PX}px`, boxSizing: 'border-box', margin: 0 }"
              >
                <!-- Полчаса (30 минут) -->
                <div class="absolute left-0 right-0 border-t border-dashed border-default/50" :style="{ top: `${SCHEDULE_HALF_HOUR_PX}px`, height: 0, boxSizing: 'border-box' }" />
                <!-- 15 минут -->
                <div class="absolute left-0 right-0 border-t border-dashed border-default/30 opacity-50" :style="{ top: `${SCHEDULE_HOUR_HEIGHT_PX * 0.25}px`, height: 0, boxSizing: 'border-box' }" />
                <!-- 45 минут -->
                <div class="absolute left-0 right-0 border-t border-dashed border-default/30 opacity-50" :style="{ top: `${SCHEDULE_HOUR_HEIGHT_PX * 0.75}px`, height: 0, boxSizing: 'border-box' }" />
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

              <!-- Слоты для добавления (hover + click → выбор: запись или событие) -->
              <div
                class="absolute inset-0 z-10 grid"
                :style="{ gridTemplateRows: `repeat(${daySlots.length}, ${SCHEDULE_HALF_HOUR_PX}px)` }"
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
                  @click="isTimeSlotAvailable(selectedDate, slot.hour, slot.minute) && openCreateChoiceForSlot(selectedDate, slot.hour, slot.minute)"
                >
                  <span
                    v-if="isTimeSlotAvailable(selectedDate, slot.hour, slot.minute)"
                    class="opacity-0 group-hover:opacity-100 transition-opacity text-primary text-xs font-medium"
                  >
                    + Добавить
                  </span>
                </div>
              </div>

              <!-- Бронирования -->
              <div class="absolute inset-0 z-20 pointer-events-none">
                <div
                  v-for="booking in getBookingsForDate(selectedDate)"
                  :key="booking.id"
                  class="absolute left-2 right-2 flex min-h-0 flex-col justify-center overflow-hidden rounded-md cursor-pointer hover:opacity-90 transition-opacity pointer-events-auto shadow-sm"
                  :style="{ ...getBookingPosition(booking, selectedDate), ...getBookingColorStyle(booking) }"
                  :class="{
                    'px-1.5 py-0.5': getBookingDensity(booking) === 'compact',
                    'px-2 py-1 gap-0.5': getBookingDensity(booking) === 'medium',
                    'px-2 py-1.5 gap-0.5': getBookingDensity(booking) === 'full'
                  }"
                  @click.stop="openBookingDetail(booking)"
                >
                  <div
                    v-if="getBookingDensity(booking) === 'compact'"
                    class="flex min-h-0 min-w-0 items-center gap-1.5"
                  >
                    <span class="shrink-0 text-[11px] font-medium tabular-nums leading-none">{{ booking.startTime }}</span>
                    <span class="min-w-0 flex-1 truncate text-xs font-medium leading-none">{{ booking.serviceName }}</span>
                  </div>
                  <template v-else-if="getBookingDensity(booking) === 'medium'">
                    <div class="truncate text-[11px] font-medium tabular-nums leading-none">{{ booking.startTime }}</div>
                    <div class="truncate text-xs font-medium leading-tight">{{ booking.serviceName }}</div>
                  </template>
                  <template v-else>
                    <div class="text-[11px] font-medium tabular-nums leading-none">{{ booking.startTime }}</div>
                    <div class="truncate text-sm font-medium leading-tight">{{ booking.serviceName }}</div>
                    <div
                      v-if="booking.customerName"
                      class="truncate text-xs leading-tight"
                      style="color: var(--schedule-card-muted)"
                    >
                      {{ booking.customerName }}
                    </div>
                  </template>
                </div>
              </div>

              <!-- События -->
              <div class="absolute inset-0 z-30 pointer-events-none">
                <div
                  v-for="ev in getEventsForDate(selectedDate)"
                  :key="`event-${ev.id}`"
                  class="absolute left-2 right-2 flex min-h-0 flex-col justify-center overflow-hidden rounded-md cursor-pointer hover:opacity-90 transition-opacity pointer-events-auto shadow-sm"
                  :style="getEventBlockStyle(ev, selectedDate)"
                  :class="{
                    'px-1.5 py-0.5': getEventDensity(ev) === 'compact',
                    'px-2 py-1 gap-0.5': getEventDensity(ev) === 'medium',
                    'px-2 py-1.5 gap-0.5': getEventDensity(ev) === 'full'
                  }"
                  @click.stop="openEventDetail(ev)"
                >
                  <div
                    v-if="getEventDensity(ev) === 'compact'"
                    class="flex min-h-0 min-w-0 items-center gap-1.5"
                  >
                    <span class="shrink-0 text-[11px] font-medium tabular-nums leading-none">{{ ev.startTime }}</span>
                    <span class="min-w-0 flex-1 truncate text-xs font-medium leading-none">{{ getEventTitle(ev) }}</span>
                  </div>
                  <template v-else-if="getEventDensity(ev) === 'medium'">
                    <div class="truncate text-[11px] font-medium tabular-nums leading-none">{{ ev.startTime }}</div>
                    <div class="truncate text-xs font-medium leading-tight">{{ getEventTitle(ev) }}</div>
                  </template>
                  <template v-else>
                    <div class="text-[11px] font-medium tabular-nums leading-none">{{ ev.startTime }}</div>
                    <div class="truncate text-sm font-medium leading-tight">{{ getEventTitle(ev) }}</div>
                    <div
                      class="truncate text-xs leading-tight"
                      style="color: var(--schedule-card-muted)"
                    >
                      <span v-if="ev.serviceId">{{ getServiceName(ev.serviceId) }}</span>
                      <span v-if="ev.maxParticipants"> · {{ ev.bookedSlots || 0 }}/{{ ev.maxParticipants }} мест</span>
                    </div>
                  </template>
                </div>
              </div>

              <!-- Индикатор текущего времени -->
              <div
                v-if="currentTimeIndicatorVisible && currentTimeTopPx >= 0"
                class="absolute left-0 right-0 pointer-events-none z-40 flex items-center gap-1.5"
                :style="{ top: `${currentTimeTopPx}px` }"
              >
                <span
                  class="shrink-0 -translate-y-1/2 rounded px-1.5 py-0.5 text-[10px] font-medium text-white"
                  style="background-color: var(--schedule-now)"
                >
                  Сейчас {{ currentTimeFormatted }}
                </span>
                <div
                  class="h-px flex-1 -translate-y-1/2"
                  style="background-color: var(--schedule-now)"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Недельный вид: одна модель weekView — шапка и колонки всегда совпадают -->
        <div
          v-else
          :key="`week-grid-${weekView.startKey}`"
          class="flex-1 overflow-auto"
        >
          <div class="relative flex">
            <div class="w-16 shrink-0 border-r border-default/30" :style="{ paddingTop: `${weekDayHeaderHeightPx}px` }">
              <div
                v-for="hour in dayHours"
                :key="hour"
                class="relative flex flex-col items-end pr-2 text-muted"
                :style="{ height: `${SCHEDULE_HOUR_HEIGHT_PX}px`, minHeight: `${SCHEDULE_HOUR_HEIGHT_PX}px`, maxHeight: `${SCHEDULE_HOUR_HEIGHT_PX}px`, boxSizing: 'border-box' }"
              >
                <div class="flex items-baseline gap-0.5" style="padding-top: 2px;">
                  <span class="text-sm font-medium">{{ String(hour).padStart(2, '0') }}</span>
                  <span class="text-[10px] -translate-y-0.5">00</span>
                </div>
                <span class="absolute right-2 text-[10px]" :style="{ top: `${SCHEDULE_HALF_HOUR_PX}px` }">30</span>
              </div>
            </div>

            <!-- Линия «Сейчас» на всю ширину недели -->
            <div
              v-if="currentTimeIndicatorVisible && weekNowLineTopPx >= 0"
              class="pointer-events-none absolute left-0 right-0 z-40 flex items-center gap-1.5 pr-1"
              :style="{ top: `${weekNowLineTopPx}px` }"
            >
              <span
                class="ml-0.5 shrink-0 -translate-y-1/2 rounded px-1.5 py-0.5 text-[10px] font-medium text-white"
                style="background-color: var(--schedule-now)"
              >
                Сейчас {{ currentTimeFormatted }}
              </span>
              <div
                class="h-px min-w-0 flex-1 -translate-y-1/2"
                style="background-color: var(--schedule-now)"
              />
            </div>

            <div class="flex-1 grid grid-cols-7">
              <div
                v-for="dayCol in weekView.days"
                :key="dayCol.key"
                class="border-l border-default"
                :class="isSameDay(dayCol.date, new Date()) ? 'bg-[var(--schedule-today-col)]' : ''"
              >
                <div
                  class="flex flex-col items-center justify-center border-b border-default text-center"
                  :class="isSameDay(dayCol.date, new Date()) ? 'bg-gray-900/5 dark:bg-white/5' : ''"
                  :style="{ height: `${weekDayHeaderHeightPx}px`, boxSizing: 'border-box' }"
                >
                  <div class="text-xs text-muted uppercase tracking-wide">{{ dayCol.weekday }}</div>
                  <div
                    class="text-sm font-medium"
                    :class="isSameDay(dayCol.date, new Date()) ? 'text-highlighted' : ''"
                  >
                    {{ dayCol.dayNum }}
                  </div>
                </div>

                <div
                  class="relative"
                  style="box-sizing: border-box;"
                  :class="isDayNonWork(dayCol.date) ? 'bg-gray-400/25 dark:bg-gray-600/25' : ''"
                >
                  <div
                    v-for="hour in dayHours"
                    :key="`${dayCol.key}-h-${hour}`"
                    class="border-b border-default relative"
                    :style="{ height: `${SCHEDULE_HOUR_HEIGHT_PX}px`, minHeight: `${SCHEDULE_HOUR_HEIGHT_PX}px`, maxHeight: `${SCHEDULE_HOUR_HEIGHT_PX}px`, boxSizing: 'border-box' }"
                  >
                    <div class="absolute left-0 right-0 border-t border-dashed border-default/50" :style="{ top: `${SCHEDULE_HALF_HOUR_PX}px`, height: 0, boxSizing: 'border-box' }" />
                    <div class="absolute left-0 right-0 border-t border-dashed border-default/30 opacity-50" :style="{ top: `${SCHEDULE_HOUR_HEIGHT_PX * 0.25}px`, height: 0, boxSizing: 'border-box' }" />
                    <div class="absolute left-0 right-0 border-t border-dashed border-default/30 opacity-50" :style="{ top: `${SCHEDULE_HOUR_HEIGHT_PX * 0.75}px`, height: 0, boxSizing: 'border-box' }" />
                  </div>

                  <div class="absolute inset-0 z-[8] pointer-events-none">
                    <template
                      v-for="block in getUnavailableTimeBlocks(dayCol.date)"
                      :key="`unavailable-${dayCol.key}-${block.start}-${block.end}`"
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

                  <div
                    class="absolute inset-0 z-[5] grid"
                    :style="{ gridTemplateRows: `repeat(${daySlots.length}, ${SCHEDULE_HALF_HOUR_PX}px)` }"
                  >
                    <div
                      v-for="slot in daySlots"
                      :key="`slot-${dayCol.key}-${slot.hour}-${slot.minute}`"
                      class="flex items-center justify-center cursor-pointer transition-colors"
                      :class="[
                        isTimeSlotAvailable(dayCol.date, slot.hour, slot.minute)
                          ? 'hover:bg-primary/10 group'
                          : 'cursor-default pointer-events-none'
                      ]"
                      @click="isTimeSlotAvailable(dayCol.date, slot.hour, slot.minute) && openCreateChoiceForSlot(dayCol.date, slot.hour, slot.minute)"
                    >
                      <span
                        v-if="isTimeSlotAvailable(dayCol.date, slot.hour, slot.minute)"
                        class="opacity-0 group-hover:opacity-100 transition-opacity text-primary text-[10px] font-medium"
                      >
                        +
                      </span>
                    </div>
                  </div>

                  <div class="absolute inset-0 z-20 pointer-events-none">
                    <div
                      v-for="booking in getBookingsForDateKey(dayCol.key)"
                      :key="booking.id"
                      class="absolute left-0.5 right-0.5 flex min-h-0 flex-col justify-center overflow-hidden rounded-md text-xs cursor-pointer hover:opacity-90 transition-opacity pointer-events-auto shadow-sm"
                      :style="{ ...getBookingPosition(booking, dayCol.date), ...getBookingColorStyle(booking) }"
                      :class="{
                        'px-1 py-0.5': getBookingDensity(booking) === 'compact',
                        'px-1.5 py-0.5 gap-0.5': getBookingDensity(booking) === 'medium',
                        'px-1.5 py-1 gap-0.5': getBookingDensity(booking) === 'full'
                      }"
                      @click.stop="openBookingDetail(booking)"
                    >
                      <div
                        v-if="getBookingDensity(booking) === 'compact'"
                        class="flex min-h-0 min-w-0 items-center gap-1"
                      >
                        <span class="shrink-0 text-[9px] font-medium tabular-nums leading-none">{{ booking.startTime }}</span>
                        <span class="min-w-0 flex-1 truncate font-medium leading-none">{{ booking.serviceName }}</span>
                      </div>
                      <template v-else-if="getBookingDensity(booking) === 'medium'">
                        <div class="truncate font-medium tabular-nums leading-none">{{ booking.startTime }}</div>
                        <div class="truncate font-medium leading-tight">{{ booking.serviceName }}</div>
                      </template>
                      <template v-else>
                        <div class="truncate font-medium tabular-nums leading-none">{{ booking.startTime }}</div>
                        <div class="truncate font-medium leading-tight">{{ booking.serviceName }}</div>
                        <div
                          v-if="booking.customerName"
                          class="truncate leading-tight"
                          style="color: var(--schedule-card-muted)"
                        >
                          {{ booking.customerName }}
                        </div>
                      </template>
                    </div>

                    <div
                      v-for="ev in getEventsForDate(dayCol.date)"
                      :key="`event-${ev.id}`"
                      class="absolute left-0.5 right-0.5 z-[1] flex min-h-0 flex-col justify-center overflow-hidden rounded-md text-xs cursor-pointer hover:opacity-90 transition-opacity pointer-events-auto shadow-sm"
                      :style="getEventBlockStyle(ev, dayCol.date)"
                      :class="{
                        'px-1 py-0.5': getEventDensity(ev) === 'compact',
                        'px-1.5 py-0.5 gap-0.5': getEventDensity(ev) === 'medium',
                        'px-1.5 py-1 gap-0.5': getEventDensity(ev) === 'full'
                      }"
                      @click.stop="openEventDetail(ev)"
                    >
                      <div
                        v-if="getEventDensity(ev) === 'compact'"
                        class="flex min-h-0 min-w-0 items-center gap-1"
                      >
                        <span class="shrink-0 text-[9px] font-medium tabular-nums leading-none">{{ ev.startTime }}</span>
                        <span class="min-w-0 flex-1 truncate font-medium leading-none">{{ getEventTitle(ev) }}</span>
                      </div>
                      <template v-else-if="getEventDensity(ev) === 'medium'">
                        <div class="truncate font-medium tabular-nums leading-none">{{ ev.startTime }}</div>
                        <div class="truncate font-medium leading-tight">{{ getEventTitle(ev) }}</div>
                      </template>
                      <template v-else>
                        <div class="truncate font-medium tabular-nums leading-none">{{ ev.startTime }}</div>
                        <div class="truncate font-medium leading-tight">{{ getEventTitle(ev) }}</div>
                      </template>
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

  <UModal
    v-model:open="slotCreateChoiceOpen"
    title="Что создать?"
    description="Выберите тип для выбранного слота"
    :ui="{ width: 'sm:max-w-sm' }"
  >
    <template #body>
      <div class="flex flex-col gap-2">
        <button
          type="button"
          class="flex w-full items-start gap-3 rounded-lg border border-default bg-elevated/50 px-3 py-3 text-left transition-colors hover:bg-elevated"
          @click="chooseCreateBookingFromSlot"
        >
          <UIcon name="i-lucide-calendar-plus" class="mt-0.5 size-5 shrink-0 text-highlighted" />
          <span class="min-w-0">
            <span class="block text-sm font-medium text-highlighted">Запись</span>
            <span class="mt-0.5 block text-xs text-muted">Индивидуальная запись клиента</span>
          </span>
        </button>
        <button
          type="button"
          class="flex w-full items-start gap-3 rounded-lg border border-default bg-elevated/50 px-3 py-3 text-left transition-colors hover:bg-elevated"
          @click="chooseCreateEventFromSlot"
        >
          <UIcon name="i-lucide-users" class="mt-0.5 size-5 shrink-0 text-highlighted" />
          <span class="min-w-0">
            <span class="block text-sm font-medium text-highlighted">Событие</span>
            <span class="mt-0.5 block text-xs text-muted">Групповое занятие с лимитом мест</span>
          </span>
        </button>
      </div>
    </template>
  </UModal>

  <ScheduleEventModal
    v-model="eventModalOpen"
    :event="selectedEvent"
    :default-date="slotDateForModal ?? selectedDate"
    :default-time="slotTimeForModal"
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
