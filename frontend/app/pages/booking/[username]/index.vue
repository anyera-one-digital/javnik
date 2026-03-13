<script setup lang="ts">
import { format, addDays, startOfDay, isSameDay } from 'date-fns'
import { ru } from 'date-fns/locale'
import { formatWeekdayShort } from '~/utils'
import type { User, Service, Booking, WorkSchedule, Review } from '~/types'
import StarIcon from '~/components/UserPublicPage/StarIcon.vue'

definePageMeta({
  layout: false,
  middleware: ['public-page-color-mode']
})

const route = useRoute()
const router = useRouter()
const colorMode = useColorMode()
const { toggle } = usePublicPageColorMode()
const toast = useToast()

// Определяем базовый URL для API
const getApiUrl = () => {
  if (process.server) {
    const config = useRuntimeConfig()
    return config.apiBase || 'http://backend:8000'
  }
  if (process.env.NODE_ENV === 'production') {
    return ''
  }
  const config = useRuntimeConfig()
  return config.public.apiBase || 'http://localhost:8000'
}

const username = computed(() => route.params.username as string)

// Проверяем, находимся ли мы на странице календаря
const isCalendarPage = computed(() => {
  const isCalendar = route.path.endsWith('/calendar')
  console.log('[username].vue - Route path:', route.path, 'isCalendar:', isCalendar)
  return isCalendar
})

// Состояния для загрузки данных
const publicUser = ref<User | null>(null)
const userError = ref<any>(null)
const userPending = ref(true)
const services = ref<Service[]>([])
const servicesPending = ref(false)
const reviews = ref<Review[]>([])
const reviewsPending = ref(false)
const selectedServiceFilter = ref<number | null>(null)
const sortOrder = ref<'newest' | 'oldest' | 'highest' | 'lowest' | 'with-photo'>('newest')
const upcomingBookings = ref<Booking[]>([])

// Выбранная услуга для модального окна
const selectedService = ref<Service | null>(null)
const serviceModalOpen = ref(false)

// Данные для календаря в модалке услуги (график работы и брони)
const serviceModalSchedules = ref<Map<string, WorkSchedule>>(new Map())
const serviceModalBookings = ref<Booking[]>([])
const serviceModalSlotsLoading = ref(false)
const selectedServiceDate = ref<Date | null>(null)
const selectedServiceTime = ref<string | null>(null)

// Шаг в модалке услуги: 0 — список услуг, 1 — выбор даты/времени, 2 — данные клиента
const serviceModalStep = ref<0 | 1 | 2>(1)
const portfolioAccordionOpen = ref(false)
const bookingClientForm = reactive({
  name: '',
  email: '',
  phone: '',
  privacyAccepted: false,
  notes: ''
})
const isBookingSubmitting = ref(false)

// Загружаем публичный профиль пользователя
const loadUserProfile = async () => {
  if (!username.value) {
    userError.value = { statusCode: 400, message: 'Username is required' }
    userPending.value = false
    return
  }

  userPending.value = true
  userError.value = null
  
  try {
    const apiUrl = `/api/public/profile/${username.value}/`
    const response = await $fetch<User>(apiUrl)
    publicUser.value = response
    
    // Исправляем URL аватара, если он содержит внутренние Docker имена
    if (response.avatar_url) {
      const config = useRuntimeConfig()
      const baseUrl = getApiUrl()
      
      if (response.avatar_url.includes('://backend:') || response.avatar_url.includes('://backend/')) {
        const urlPath = response.avatar_url.replace(/^https?:\/\/[^\/]+/, '')
        publicUser.value.avatar_url = `${baseUrl}${urlPath}`
      } else if (!response.avatar_url.startsWith('http')) {
        if (response.avatar_url.startsWith('/')) {
          publicUser.value.avatar_url = `${baseUrl}${response.avatar_url}`
        } else {
          publicUser.value.avatar_url = `${baseUrl}/${response.avatar_url}`
        }
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

// Загружаем услуги
const loadServices = async () => {
  if (!publicUser.value || userError.value) return
  
  servicesPending.value = true
  try {
    const servicesUrl = `/api/public/services/${username.value}/`
    console.log('Loading services from:', servicesUrl)
    const response = await $fetch<Service[]>(servicesUrl)
    console.log('Services loaded:', response)
    console.log('Services count:', response?.length || 0)
    console.log('Services with images:', response?.filter(s => s.cover_image_url).length || 0)
    console.log('Services without images:', response?.filter(s => !s.cover_image_url).length || 0)
    
    // Логируем каждую услугу
    if (response && Array.isArray(response)) {
      response.forEach((service, index) => {
        console.log(`Service [${index}]:`, {
          id: service.id,
          name: service.name,
          has_cover_image: !!service.cover_image_url,
          cover_image_url: service.cover_image_url,
          portfolio_count: service.portfolio_images?.length || 0
        })
      })
    }
    
    services.value = response || []
  } catch (error: any) {
    console.error('Error loading services:', error)
    console.error('Error status:', error.statusCode || error.status)
    console.error('Error data:', error.data)
    console.error('Error response:', error.response)
    services.value = []
  } finally {
    servicesPending.value = false
  }
}

// Статистика отзывов
const reviewsStats = computed(() => {
  const total = reviews.value.length
  const average = total > 0
    ? reviews.value.reduce((sum, r) => sum + (r.rating || 0), 0) / total
    : 0
  const distribution = {
    5: reviews.value.filter(r => r.rating === 5).length,
    4: reviews.value.filter(r => r.rating === 4).length,
    3: reviews.value.filter(r => r.rating === 3).length,
    2: reviews.value.filter(r => r.rating === 2).length,
    1: reviews.value.filter(r => r.rating === 1).length
  }
  return { total, average, distribution }
})

// Извлекаем serviceId из отзыва (поддержка number, string, object)
function getReviewServiceId(review: Review): number | null {
  const sid = review.serviceId ?? review.service
  if (sid == null || sid === '') return null
  if (typeof sid === 'object' && sid !== null && 'id' in sid) {
    const id = Number((sid as { id: number }).id)
    return Number.isNaN(id) ? null : id
  }
  const id = Number(sid)
  return Number.isNaN(id) ? null : id
}

// Статистика по услугам для фильтров (нормализуем id для совместимости number/string)
const serviceFilterStats = computed(() => {
  const stats: Record<number, number> = {}
  reviews.value.forEach(review => {
    const id = getReviewServiceId(review)
    if (id != null) {
      stats[id] = (stats[id] || 0) + 1
    }
  })
  return stats
})

// Услуги с отзывами для табов — строим из serviceFilterStats, чтобы не пропустить услуги
const servicesWithReviewsForTabs = computed(() => {
  const stats = serviceFilterStats.value
  const result: { id: number, name: string, count: number }[] = []

  Object.entries(stats).forEach(([key, count]) => {
    const id = Number(key)
    if (Number.isNaN(id) || count <= 0) return
    const reviewWithService = reviews.value.find(r => getReviewServiceId(r) === id)
    const name =
      reviewWithService?.serviceName ??
      (reviewWithService as { service_name?: string } | undefined)?.service_name ??
      services.value?.find(s => Number(s.id) === id)?.name ??
      `Услуга #${id}`
    result.push({ id, name, count })
  })

  return result.sort((a, b) => a.name.localeCompare(b.name))
})

// Фильтрованные и отсортированные отзывы
const filteredAndSortedReviews = computed(() => {
  let result = [...reviews.value]
  if (selectedServiceFilter.value !== null) {
    const filterId = Number(selectedServiceFilter.value)
    result = result.filter(r => getReviewServiceId(r) === filterId)
  }
  result.sort((a, b) => {
    switch (sortOrder.value) {
      case 'newest':
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
      case 'oldest':
        return new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime()
      case 'highest':
        return (b.rating || 0) - (a.rating || 0)
      case 'lowest':
        return (a.rating || 0) - (b.rating || 0)
      case 'with-photo':
        const aHas = a.photos && a.photos.length > 0
        const bHas = b.photos && b.photos.length > 0
        if (aHas && !bHas) return -1
        if (!aHas && bHas) return 1
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
      default:
        return 0
    }
  })
  return result
})

// Название услуги для отзыва (из API или по serviceId из списка услуг)
function getReviewServiceName(review: Review & { service_name?: string }): string | undefined {
  if (review.serviceName) return review.serviceName
  if (review.service_name) return review.service_name
  const id = getReviewServiceId(review)
  if (id != null && services.value?.length) {
    const svc = services.value.find(s => Number(s.id) === id)
    return svc?.name
  }
  return undefined
}

// Загружаем отзывы
const loadReviews = async () => {
  if (!username.value) return
  reviewsPending.value = true
  try {
    const response = await $fetch<Review[]>(`/api/public/reviews/${username.value}/`)
    reviews.value = Array.isArray(response) ? response : []
  } catch {
    reviews.value = []
  } finally {
    reviewsPending.value = false
  }
}

// Загружаем данные при монтировании
onMounted(async () => {
  await loadUserProfile()
  if (publicUser.value && !userError.value) {
    await Promise.all([loadServices(), loadReviews()])
  }
})

// Перезагружаем при изменении username
watch(() => username.value, async (newUsername) => {
  if (newUsername) {
    await loadUserProfile()
    if (publicUser.value && !userError.value) {
      await Promise.all([loadServices(), loadReviews()])
    }
  }
})

// Загружаем график и брони при открытии модалки услуги
watch([serviceModalOpen, selectedService], ([open, svc]) => {
  if (open && svc && username.value) {
    loadServiceModalScheduleAndBookings()
  }
})

// Открываем модальное окно услуги
function openServiceModal(service: Service) {
  selectedService.value = service
  selectedServiceDate.value = null
  selectedServiceTime.value = null
  serviceModalStep.value = 1
  portfolioAccordionOpen.value = false
  serviceModalOpen.value = true
}

// Открываем модальное окно записи на этапе выбора услуги
function openBookingModalForServiceSelection() {
  selectedService.value = null
  selectedServiceDate.value = null
  selectedServiceTime.value = null
  serviceModalStep.value = 0
  serviceModalOpen.value = true
}

// Выбрать услугу и перейти к шагу даты/времени (из списка на шаге 0)
function selectServiceAndGoToDateStep(service: Service) {
  selectedService.value = service
  selectedServiceDate.value = null
  selectedServiceTime.value = null
  serviceModalStep.value = 1
  portfolioAccordionOpen.value = false
}

// Закрываем модальное окно
function closeServiceModal() {
  serviceModalOpen.value = false
  selectedService.value = null
  selectedServiceDate.value = null
  selectedServiceTime.value = null
  serviceModalStep.value = 1
  bookingClientForm.name = ''
  bookingClientForm.email = ''
  bookingClientForm.phone = ''
  bookingClientForm.privacyAccepted = false
  bookingClientForm.notes = ''
}

// Загрузка графика и бронирований для модалки услуги (ближайшие 14 дней)
async function loadServiceModalScheduleAndBookings() {
  if (!username.value || !selectedService.value) return
  serviceModalSlotsLoading.value = true
  const today = startOfDay(new Date())
  const endDate = addDays(today, 14)
  const startStr = format(today, 'yyyy-MM-dd')
  const endStr = format(endDate, 'yyyy-MM-dd')
  try {
    const [schedulesRes, bookingsRes] = await Promise.all([
      $fetch<WorkSchedule[]>(`/api/public/schedule/${username.value}?start_date=${startStr}&end_date=${endStr}`),
      $fetch<Booking[]>(`/api/public/bookings/${username.value}?start_date=${startStr}&end_date=${endStr}`)
    ])
    serviceModalSchedules.value = new Map()
    if (Array.isArray(schedulesRes)) {
      schedulesRes.forEach(s => { if (s?.date) serviceModalSchedules.value.set(s.date, s) })
    }
    serviceModalBookings.value = Array.isArray(bookingsRes) ? bookingsRes : []
  } catch (e) {
    console.error('loadServiceModalScheduleAndBookings', e)
    serviceModalSchedules.value = new Map()
    serviceModalBookings.value = []
  } finally {
    serviceModalSlotsLoading.value = false
  }
}

// Блоки занятого времени на дату (нерабочие часы, перерывы, брони)
function getServiceModalUnavailableBlocks(date: Date): Array<{ start: number, end: number }> {
  const dateStr = format(date, 'yyyy-MM-dd')
  const schedule = serviceModalSchedules.value.get(dateStr)
  const blocks: Array<{ start: number, end: number }> = []
  const dayStart = 0
  const dayEnd = 24 * 60

  if (!schedule || schedule.type !== 'workday' || !schedule.startTime || !schedule.endTime) {
    return [{ start: dayStart, end: dayEnd }]
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

  const bookings = serviceModalBookings.value.filter(b => {
    const d = typeof b.date === 'string' ? b.date.split('T')[0] : b.date
    return d === dateStr
  })
  for (const b of bookings) {
    const [sh, sm] = (b.startTime || '00:00').split(':').map(Number)
    const [eh, em] = (b.endTime || '00:00').split(':').map(Number)
    blocks.push({ start: sh * 60 + sm, end: eh * 60 + em })
  }

  return blocks
}

// Свободные слоты на дату, вмещающие durationMinutes минут (шаг 30 мин)
function getServiceModalAvailableSlots(date: Date, durationMinutes: number): string[] {
  const unavailable = getServiceModalUnavailableBlocks(date)
  const occupied = unavailable.flatMap(b => [{ start: b.start, end: b.end }])
  occupied.sort((a, b) => a.start - b.start)
  const free: Array<{ start: number, end: number }> = []
  let cur = 0
  for (const o of occupied) {
    if (o.start > cur) free.push({ start: cur, end: o.start })
    cur = Math.max(cur, o.end)
  }
  if (cur < 24 * 60) free.push({ start: cur, end: 24 * 60 })

  const step = 30
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

// Даты с хотя бы одним свободным слотом для длительности услуги
const serviceModalAvailableDates = computed(() => {
  const svc = selectedService.value
  if (!svc || serviceModalSlotsLoading.value) return []
  const today = startOfDay(new Date())
  const out: { date: string, dateObj: Date }[] = []
  for (let i = 0; i < 14; i++) {
    const d = addDays(today, i)
    const slots = getServiceModalAvailableSlots(d, svc.duration)
    if (slots.length > 0) {
      out.push({ date: format(d, 'yyyy-MM-dd'), dateObj: d })
    }
  }
  return out
})

// Доступные слоты времени для выбранной даты в модалке услуги
const serviceModalAvailableTimeSlots = computed(() => {
  const svc = selectedService.value
  const d = selectedServiceDate.value
  if (!svc || !d) return []
  return getServiceModalAvailableSlots(d, svc.duration)
})

// По умолчанию выбираем завтрашний день (или первый доступный), чтобы активный день всегда был выбран
watch(
  () => ({
    open: serviceModalOpen.value,
    loading: serviceModalSlotsLoading.value,
    dates: serviceModalAvailableDates.value,
    current: selectedServiceDate.value
  }),
  (state) => {
    if (!state.open || state.loading || !state.dates?.length) return
    if (state.current) return
    const tomorrow = addDays(startOfDay(new Date()), 1)
    const tomorrowInList = state.dates.find(d => isSameDay(d.dateObj, tomorrow))
    selectedServiceDate.value = tomorrowInList ? tomorrowInList.dateObj : state.dates[0].dateObj
    selectedServiceTime.value = null
  },
  { deep: true }
)

// Перейти ко второму шагу (данные клиента)
function goToBookingStep() {
  if (!selectedService.value || !selectedServiceDate.value || !selectedServiceTime.value) {
    toast.add({ title: 'Выберите дату и время', color: 'warning' })
    return
  }
  serviceModalStep.value = 2
}

// Вернуться к шагу выбора даты/времени (со шага 2)
function goBackToDateStep() {
  serviceModalStep.value = 1
}

// Вернуться к списку услуг (со шага 1)
function goBackToServicesList() {
  serviceModalStep.value = 0
}

// Отправить бронирование
async function submitBooking() {
  if (!selectedService.value || !selectedServiceDate.value || !selectedServiceTime.value || !username.value) return
  if (!bookingClientForm.name || !bookingClientForm.email || !bookingClientForm.phone) {
    toast.add({ title: 'Заполните все обязательные поля', color: 'error' })
    return
  }
  if (!bookingClientForm.privacyAccepted) {
    toast.add({ title: 'Необходимо согласие с политикой конфиденциальности', color: 'error' })
    return
  }

  isBookingSubmitting.value = true
  try {
    const config = useRuntimeConfig()
    const apiBase = getApiUrl()
    const bookingUrl = `${apiBase}/api/public/bookings/${username.value}/create/`

    await $fetch(bookingUrl, {
      method: 'POST',
      body: {
        serviceId: selectedService.value.id,
        customerName: bookingClientForm.name,
        customerEmail: bookingClientForm.email,
        customerPhone: bookingClientForm.phone,
        notes: bookingClientForm.notes,
        date: format(selectedServiceDate.value, 'yyyy-MM-dd'),
        startTime: selectedServiceTime.value,
        duration: selectedService.value.duration
      }
    })

    toast.add({
      title: 'Заявка отправлена',
      description: 'Бронь создана и ожидает подтверждения. Мы свяжемся с вами после подтверждения.',
      color: 'success'
    })
    closeServiceModal()
  } catch (error: any) {
    const msg = error.data?.error || error.data?.message || error.message || 'Не удалось создать запись.'
    toast.add({ title: 'Ошибка', description: msg, color: 'error', timeout: 8000 })
  } finally {
    isBookingSubmitting.value = false
  }
}

// Получаем отображаемое имя
const displayName = computed(() => {
  if (!publicUser.value) return username.value
  return publicUser.value.display_name || 
         (publicUser.value.first_name && publicUser.value.last_name 
           ? `${publicUser.value.first_name} ${publicUser.value.last_name}`
           : publicUser.value.first_name || username.value)
})

// Получаем специальность
const specialty = computed(() => {
  return publicUser.value?.specialty || ''
})

// URL публичного календаря
const calendarUrl = computed(() => `/booking/${username.value}/calendar`)

// Состояние для разворачивания списка услуг
const isServicesExpanded = ref(false)

// Активная вкладка: Услуги | Портфолио | Отзывы
const activeTab = ref<'services' | 'portfolio' | 'reviews'>('services')

// Фильтр по услугам для портфолио (отдельный от отзывов)
const selectedPortfolioServiceFilter = ref<number | null>(null)

// Все изображения портфолио из всех услуг
const allPortfolioImages = computed(() => {
  const images: Array<{ id: number; service_id: number; image_url: string; service_name: string; order: number }> = []
  services.value.forEach(service => {
    if (service.portfolio_images && Array.isArray(service.portfolio_images)) {
      service.portfolio_images.forEach((img: any) => {
        if (img.image_url) {
          images.push({
            id: img.id || images.length,
            service_id: service.id,
            image_url: img.image_url,
            service_name: service.name,
            order: img.order ?? 0
          })
        }
      })
    }
  })
  return images.sort((a, b) => a.order - b.order)
})

// Услуги с портфолио для фильтров
const servicesWithPortfolioForTabs = computed(() => {
  const stats: Record<number, number> = {}
  allPortfolioImages.value.forEach(img => {
    stats[img.service_id] = (stats[img.service_id] || 0) + 1
  })
  return Object.entries(stats)
    .map(([id, count]) => {
      const serviceId = Number(id)
      const service = services.value.find(s => Number(s.id) === serviceId)
      return { id: serviceId, name: service?.name ?? `Услуга #${id}`, count }
    })
    .sort((a, b) => a.name.localeCompare(b.name))
})

// Фильтрованные изображения портфолио
const filteredPortfolioImages = computed(() => {
  if (selectedPortfolioServiceFilter.value === null) return allPortfolioImages.value
  const filterId = Number(selectedPortfolioServiceFilter.value)
  return allPortfolioImages.value.filter(img => img.service_id === filterId)
})

// SEO метаданные
watch([publicUser, userError], ([user, error]) => {
  if (user && !error) {
    useSeoMeta({
      title: `Профиль - ${displayName.value}`,
      description: `Публичный профиль ${displayName.value}. Просмотрите услуги и портфолио.`,
      ogTitle: `Профиль - ${displayName.value}`,
      ogDescription: `Публичный профиль ${displayName.value}. Просмотрите услуги, портфолио и отзывы.`,
      ogImage: user.avatar_url
    })
  }
}, { immediate: true })
</script>

<template>
  <!-- Не рендерим профиль на странице календаря, календарь рендерится отдельно -->
  <div v-if="!isCalendarPage" class="min-h-screen bg-background relative">
    <!-- Кнопка переключения темы -->
    <div class="fixed top-4 right-4 z-50">
      <UButton
        :icon="colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon'"
        color="neutral"
        variant="ghost"
        square
        size="sm"
        aria-label="Переключить тему"
        @click="toggle"
      />
    </div>
    <div v-if="userPending || (!publicUser && !userError)" class="flex items-center justify-center min-h-screen">
      <div class="text-center space-y-4">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-muted mx-auto"></div>
        <p class="text-muted">Загрузка профиля...</p>
      </div>
    </div>
    <div v-else-if="userError && !publicUser" class="flex items-center justify-center min-h-screen p-4">
      <UPageCard variant="subtle" class="max-w-md w-full">
        <div class="text-center space-y-4">
          <div class="text-6xl">😕</div>
          <h2 class="text-2xl font-bold">Пользователь не найден</h2>
          <p class="text-muted">
            Пользователь с именем "<strong>{{ username }}</strong>" не существует или его профиль недоступен.
          </p>
          <UButton
            to="/"
            color="neutral"
            label="Вернуться на главную"
          />
        </div>
      </UPageCard>
    </div>
    <div v-else-if="publicUser" class="max-w-[1024px] mx-auto px-4 py-8">
      <div class="mb-4">
        <div class="flex flex-col md:flex-row items-start gap-8">
          <!-- Аватар (большой круглый) -->
          <UAvatar
            :src="publicUser.avatar_url || null"
            :alt="displayName"
            class="shrink-0 w-[133px] h-[133px] min-w-[133px] min-h-[133px] md:w-[200px] md:h-[200px] md:min-w-[200px] md:min-h-[200px]"
            size="2xl"
          >
            <template v-if="displayName" #fallback>
              <span class="text-4xl md:text-[4rem]">
                {{ displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) }}
              </span>
            </template>
          </UAvatar>

          <!-- Информация -->
          <div class="flex-1 flex flex-col">
            <!-- Имя и город -->
            <div class="flex items-baseline gap-3 mb-2">
              <h1 class="text-xl font-bold md:text-3xl">{{ displayName }}</h1>
              <span v-if="publicUser.city" class="text-base text-muted">г.{{ publicUser.city }}</span>
            </div>
            
            <!-- Специальность -->
            <p v-if="specialty" class="text-base text-muted mb-4 md:text-lg">{{ specialty }}</p>
            
            <!-- Рейтинг и отзывы -->
            <div v-if="reviewsStats.total > 0" class="flex items-center gap-2 mb-4">
              <div class="flex items-center gap-0.5">
                <StarIcon
                  v-for="i in 5"
                  :key="i"
                  :filled="i <= Math.round(reviewsStats.average)"
                  size="1.25rem"
                  :class="[
                    'transition-colors',
                    i <= Math.round(reviewsStats.average) ? 'text-amber-500' : 'text-muted/50'
                  ]"
                />
              </div>
              <span class="font-semibold ml-1">{{ reviewsStats.average.toFixed(1) }}</span>
              <button
                type="button"
                class="text-muted hover:text-foreground hover:underline cursor-pointer transition-colors"
                @click="activeTab = 'reviews'"
              >
                ({{ reviewsStats.total }} {{ reviewsStats.total === 1 ? 'отзыв' : reviewsStats.total < 5 ? 'отзыва' : 'отзывов' }})
              </button>
            </div>

            <!-- Кнопки действий -->
            <div class="flex items-center gap-3 mb-4">
              <UButton
                color="neutral"
                size="lg"
                class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
                @click="openBookingModalForServiceSelection"
              >
                <Icon name="i-lucide-calendar-plus" class="w-5 h-5 mr-2" />
                Записаться
              </UButton>
              <UButton
                color="neutral"
                size="lg"
                variant="outline"
                :to="calendarUrl"
              >
                <Icon name="i-lucide-calendar" class="w-5 h-5 mr-2" />
                Расписание
              </UButton>
            </div>
            
            <!-- Описание -->
            <p v-if="publicUser.bio" class="text-base text-muted mb-4 leading-relaxed max-w-2xl">
              {{ publicUser.bio }}
            </p>
            <p v-else-if="publicUser.first_name" class="text-base text-muted mb-4 leading-relaxed max-w-2xl">
              Профессиональный специалист с опытом работы. Помогу создать идеальный результат для любого случая!
            </p>
            
            <!-- Адрес оказания услуг -->
            <div v-if="publicUser.service_address" class="text-base text-foreground max-w-2xl flex flex-wrap items-center gap-x-2 gap-y-1">
              <span class="font-semibold">Адрес оказания услуг:</span>
              <span class="font-normal">{{ publicUser.service_address }}</span>
              <a
                v-if="publicUser.service_address_lat != null && publicUser.service_address_lon != null"
                :href="`https://yandex.ru/maps/?pt=${publicUser.service_address_lon},${publicUser.service_address_lat}&z=16&l=map`"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md border border-default hover:bg-elevated transition-colors"
              >
                <Icon name="i-lucide-map-pin" class="w-3.5 h-3.5" />
                Смотреть на карте
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Вкладки (в стиле Threads) -->
      <div class="pt-1.5">
        <nav class="flex items-center gap-1 mb-6 border-b border-default">
          <button
            type="button"
            class="relative py-3 px-4 text-sm font-medium transition-colors -mb-px"
            :class="activeTab === 'services' ? 'text-foreground' : 'text-muted hover:text-foreground'"
            @click="activeTab = 'services'"
          >
            Услуги
            <span
              class="absolute bottom-0 left-0 right-0 h-[3px] rounded-full transition-opacity bg-foreground dark:bg-white z-[1]"
              :class="activeTab === 'services' ? 'opacity-100' : 'opacity-0'"
            />
          </button>
          <button
            type="button"
            class="relative py-3 px-4 text-sm font-medium transition-colors -mb-px"
            :class="activeTab === 'portfolio' ? 'text-foreground' : 'text-muted hover:text-foreground'"
            @click="activeTab = 'portfolio'"
          >
            Портфолио
            <span
              class="absolute bottom-0 left-0 right-0 h-[3px] rounded-full transition-opacity bg-foreground dark:bg-white z-[1]"
              :class="activeTab === 'portfolio' ? 'opacity-100' : 'opacity-0'"
            />
          </button>
          <button
            type="button"
            class="relative py-3 px-4 text-sm font-medium transition-colors -mb-px"
            :class="activeTab === 'reviews' ? 'text-foreground' : 'text-muted hover:text-foreground'"
            @click="activeTab = 'reviews'"
          >
            Отзывы
            <span
              class="absolute bottom-0 left-0 right-0 h-[3px] rounded-full transition-opacity bg-foreground dark:bg-white z-[1]"
              :class="activeTab === 'reviews' ? 'opacity-100' : 'opacity-0'"
            />
          </button>
        </nav>

        <!-- Услуги -->
        <div v-show="activeTab === 'services'" class="mb-12">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold">
              Услуги и цены <span class="font-normal text-muted">{{ services.length }}</span>
            </h2>
          </div>
          <div v-if="servicesPending" class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-muted"></div>
          </div>
          <div v-else-if="services.length === 0" class="text-center py-12">
            <p class="text-muted">Услуги пока не добавлены</p>
          </div>
          <div v-else>
            <div class="space-y-0">
              <div
                v-for="service in (isServicesExpanded || services.length <= 7 ? services : services.slice(0, 7))"
                :key="service.id"
                class="cursor-pointer hover:bg-elevated/50 transition-colors border-b border-default last:border-b-0"
                @click="openServiceModal(service)"
              >
                <div class="grid grid-cols-1 gap-2 p-4 md:grid-cols-[1fr_auto_auto_auto] md:items-center md:gap-6">
                  <h3 class="text-base font-semibold text-highlighted">{{ service.name }}</h3>
                  <div class="flex items-center justify-between gap-x-4 w-full md:contents">
                    <div class="flex items-center gap-x-4 gap-y-1 md:contents">
                      <div class="flex items-center gap-1 text-muted md:justify-self-end">
                        <Icon name="i-lucide-clock" class="w-4 h-4 shrink-0" />
                        <span class="text-sm">{{ service.duration }} мин</span>
                      </div>
                      <div class="text-base font-semibold text-foreground md:text-left">
                        {{ Math.round(service.price).toLocaleString('ru-RU') }} ₽
                      </div>
                    </div>
                    <UButton
                      label="Записаться"
                      size="sm"
                      color="neutral"
                      class="shrink-0 md:ml-auto"
                    />
                  </div>
                </div>
              </div>
            </div>
            <div v-if="services.length > 7" class="mt-4 flex justify-center">
              <UButton
                variant="ghost"
                color="neutral"
                class="!bg-transparent hover:!bg-transparent active:!bg-transparent"
                @click="isServicesExpanded = !isServicesExpanded"
              >
                {{ isServicesExpanded ? 'Свернуть' : 'Смотреть еще' }}
              </UButton>
            </div>
          </div>
        </div>

        <!-- Портфолио -->
        <div v-show="activeTab === 'portfolio'" class="mb-12">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold">
              Портфолио <span class="font-normal text-muted">{{ filteredPortfolioImages.length }}</span>
            </h2>
          </div>

          <!-- Фильтры по услугам (только услуги с портфолио) -->
          <div v-if="allPortfolioImages.length > 0" class="flex flex-wrap items-center gap-2 mb-6">
            <UButton
              :variant="selectedPortfolioServiceFilter === null ? 'solid' : 'outline'"
              :color="selectedPortfolioServiceFilter === null ? 'neutral' : 'neutral'"
              size="sm"
              @click="selectedPortfolioServiceFilter = null"
            >
              Все услуги {{ allPortfolioImages.length }}
            </UButton>
            <UButton
              v-for="item in servicesWithPortfolioForTabs"
              :key="item.id"
              :variant="selectedPortfolioServiceFilter === item.id ? 'solid' : 'outline'"
              :color="selectedPortfolioServiceFilter === item.id ? 'neutral' : 'neutral'"
              size="sm"
              @click="selectedPortfolioServiceFilter = item.id"
            >
              {{ item.name }} {{ item.count }}
            </UButton>
          </div>

          <div v-if="allPortfolioImages.length === 0" class="text-center py-12">
            <p class="text-muted">Портфолио пока пусто</p>
            <p class="text-sm text-muted mt-2">Изображения появятся здесь, когда будут добавлены примеры работ к услугам</p>
          </div>
          <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div
              v-for="image in filteredPortfolioImages"
              :key="image.id"
              class="aspect-square bg-muted rounded-lg overflow-hidden group relative"
            >
              <img
                :src="image.image_url"
                :alt="`Пример работы: ${image.service_name}`"
                class="w-full h-full object-cover"
                @error="(e: Event) => { (e.target as HTMLImageElement).style.display = 'none' }"
              />
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-end">
                <div class="p-2 text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ image.service_name }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Отзывы -->
        <div v-show="activeTab === 'reviews'" class="mb-8">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold">
              Отзывы <span class="font-normal text-muted">{{ reviewsStats.total }}</span>
            </h2>
            <div v-if="reviewsStats.total > 0" class="flex items-center gap-2">
              <span class="text-sm text-muted">{{ reviewsStats.average.toFixed(2) }}</span>
              <StarIcon filled size="1.25rem" class="text-amber-500" />
            </div>
          </div>

          <!-- Фильтры по услугам (только услуги с отзывами) -->
          <div v-if="reviews.length > 0" class="flex flex-wrap items-center gap-2 mb-6">
            <UButton
              :variant="selectedServiceFilter === null ? 'solid' : 'outline'"
              :color="selectedServiceFilter === null ? 'neutral' : 'neutral'"
              size="sm"
              @click="selectedServiceFilter = null"
            >
              Все услуги {{ reviewsStats.total }}
            </UButton>
            <UButton
              v-for="item in servicesWithReviewsForTabs"
              :key="item.id"
              :variant="selectedServiceFilter === item.id ? 'solid' : 'outline'"
              :color="selectedServiceFilter === item.id ? 'neutral' : 'neutral'"
              size="sm"
              @click="selectedServiceFilter = item.id"
            >
              {{ item.name }} {{ item.count }}
            </UButton>
          </div>

          <!-- Распределение рейтингов -->
          <div v-if="reviews.length > 0" class="mb-6 space-y-2">
            <div
              v-for="rating in [5, 4, 3, 2, 1]"
              :key="rating"
              class="flex items-center gap-3"
            >
              <div class="flex items-center gap-1 w-12">
                <span class="text-sm">{{ rating }}</span>
                <StarIcon filled size="1.25rem" class="text-amber-500" />
              </div>
              <div class="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  class="h-full bg-amber-500 transition-all"
                  :style="{ width: `${reviewsStats.total > 0 ? (reviewsStats.distribution[rating] / reviewsStats.total) * 100 : 0}%` }"
                />
              </div>
              <span class="text-sm text-muted w-12 text-right">{{ reviewsStats.distribution[rating] }}</span>
            </div>
          </div>

          <!-- Сортировка -->
          <div v-if="reviews.length > 0" class="flex items-center justify-end gap-2 mb-4">
            <USelect
              v-model="sortOrder"
              variant="ghost"
              :items="[
                { label: 'Сначала новые', value: 'newest' },
                { label: 'Сначала старые', value: 'oldest' },
                { label: 'Сначала хорошие', value: 'highest' },
                { label: 'Сначала плохие', value: 'lowest' },
                { label: 'Сначала с фото', value: 'with-photo' }
              ]"
              class="w-48"
            />
          </div>

          <!-- Список отзывов -->
          <div v-if="reviewsPending" class="flex items-center justify-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-muted"></div>
          </div>
          <div v-else-if="filteredAndSortedReviews.length === 0" class="text-center py-12">
            <p class="text-muted">Отзывов пока нет</p>
          </div>
          <div v-else class="space-y-0">
            <div
              v-for="review in filteredAndSortedReviews"
              :key="review.id"
              class="border-b border-default last:border-b-0 py-4"
            >
              <div class="mb-2">
                <div class="font-semibold">{{ review.customerName || 'Клиент' }}</div>
                <p v-if="getReviewServiceName(review)" class="text-sm text-muted mt-0.5">
                  {{ getReviewServiceName(review) }}
                </p>
              </div>
              <div class="flex items-center gap-2 mb-2 flex-wrap">
                <div class="flex items-center gap-1 shrink-0">
                  <StarIcon
                    v-for="i in 5"
                    :key="i"
                    :filled="i <= (review.rating || 0)"
                    size="1.25rem"
                    :class="[
                      'transition-colors',
                      i <= (review.rating || 0) ? 'text-amber-500' : 'text-muted/50'
                    ]"
                  />
                </div>
              </div>
              <p v-if="review.comment" class="text-muted mb-2">{{ review.comment }}</p>
              <div v-if="review.reply" class="mt-2 pl-4 border-l-2 border-default">
                <p class="text-sm text-muted mb-1">Ответ специалиста:</p>
                <p class="text-sm">{{ review.reply }}</p>
              </div>
              <p v-if="review.created_at" class="text-xs text-muted">
                {{ format(new Date(review.created_at), 'd MMMM yyyy', { locale: ru }) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Модальное окно услуги (вне основного контейнера) -->
  <Teleport to="body">
    <div v-if="serviceModalOpen" class="fixed inset-0 z-50 flex items-center justify-center">
      <!-- Overlay -->
      <div class="fixed inset-0 bg-black/80 z-40" @click="closeServiceModal"></div>
      
      <!-- Modal -->
      <div class="relative z-50 rounded-lg shadow-xl max-w-[580px] w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col border border-default bg-white dark:bg-neutral-950">
        <!-- Header -->
        <div class="relative flex items-center gap-3 p-6 border-b border-default">
          <UButton
            v-if="serviceModalStep === 1"
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            square
            aria-label="Назад"
            @click="goBackToServicesList"
          />
          <UButton
            v-else-if="serviceModalStep === 2"
            icon="i-lucide-arrow-left"
            color="neutral"
            variant="ghost"
            square
            aria-label="Назад"
            @click="goBackToDateStep"
          />
          <div v-else-if="serviceModalStep !== 0" class="w-10 shrink-0" />
          <h2 class="text-2xl font-bold flex-1 pr-12 text-left">
            {{ serviceModalStep === 0 ? 'Выбор услуги' : serviceModalStep === 1 ? 'Дата и время' : 'Контакты' }}
          </h2>
          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            square
            class="absolute top-4 right-4"
            @click="closeServiceModal"
          />
        </div>
        
        <!-- Body -->
        <div class="p-6 overflow-y-auto flex-1">
          <!-- Шаг 0: Список услуг -->
          <div v-if="serviceModalStep === 0" class="space-y-0">
            <div
              v-for="service in services"
              :key="service.id"
              class="cursor-pointer hover:bg-elevated/50 transition-colors border-b border-default last:border-b-0"
              @click="selectServiceAndGoToDateStep(service)"
            >
              <div class="grid grid-cols-[1fr_auto_auto_auto] items-center gap-6 p-4">
                <div class="min-w-0">
                  <h3 class="text-base font-semibold text-highlighted">{{ service.name }}</h3>
                </div>
                <div class="flex items-center gap-1 text-muted justify-start" style="width: 100px;">
                  <Icon name="i-lucide-clock" class="w-4 h-4 shrink-0" />
                  <span class="text-sm">{{ service.duration }} мин</span>
                </div>
                <div class="text-base font-semibold text-foreground text-left" style="width: 120px;">
                  {{ Math.round(service.price).toLocaleString('ru-RU') }} ₽
                </div>
                <div class="flex items-center justify-start">
                  <UButton
                    label="Записаться"
                    size="sm"
                    color="neutral"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Шаг 1: Выбор даты и времени -->
          <div v-else-if="serviceModalStep === 1 && selectedService" class="space-y-6">
            <div class="space-y-3">
              <div class="space-y-1">
                <p class="text-sm font-medium text-muted">Об услуге</p>
                <h3 class="text-lg font-semibold">{{ selectedService.name }}</h3>
                <p v-if="selectedService.description" class="text-muted">{{ selectedService.description }}</p>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-sm text-muted mb-1">Длительность</p>
                <p class="font-semibold">{{ selectedService.duration }} минут</p>
              </div>
              <div>
                <p class="text-sm text-muted mb-1">Цена</p>
                <p class="font-semibold text-foreground">{{ Math.round(selectedService.price).toLocaleString('ru-RU') }} ₽</p>
              </div>
            </div>

            <!-- Примеры работ (аккордеон) -->
            <div v-if="selectedService.portfolio_images && selectedService.portfolio_images.length > 0" class="border-t border-default pt-6">
              <button
                type="button"
                class="w-full flex items-center justify-between gap-3 py-2 text-left hover:opacity-80 transition-opacity"
                @click="portfolioAccordionOpen = !portfolioAccordionOpen"
              >
                <h3 class="text-lg font-semibold">Примеры работ</h3>
                <Icon
                  :name="portfolioAccordionOpen ? 'i-lucide-minus' : 'i-lucide-plus'"
                  class="w-5 h-5 shrink-0 text-muted"
                />
              </button>
              <div v-show="portfolioAccordionOpen" class="grid grid-cols-3 gap-3 mt-3">
                <div
                  v-for="(image, index) in selectedService.portfolio_images"
                  :key="image.id || index"
                  class="aspect-square bg-muted rounded-lg overflow-hidden"
                >
                  <img
                    v-if="image.image_url"
                    :src="image.image_url"
                    :alt="`Пример работы ${index + 1}`"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center bg-elevated">
                    <Icon name="i-lucide-image" class="w-8 h-8 text-muted" />
                  </div>
                </div>
              </div>
            </div>

            <div class="border-t border-default pt-6">
              <h3 class="text-lg font-semibold mb-3">Ближайшие даты для записи</h3>
              <div v-if="serviceModalSlotsLoading" class="flex items-center gap-2 py-4">
                <div class="animate-spin rounded-full h-5 w-5 border-2 border-muted border-t-transparent"></div>
                <span class="text-muted">Загрузка доступных слотов...</span>
              </div>
              <template v-else>
                <div class="mb-4">
                  <p class="text-sm font-medium mb-2">Выберите день</p>
                  <div class="flex flex-wrap gap-2">
                    <UButton
                      v-for="{ date, dateObj } in serviceModalAvailableDates"
                      :key="date"
                      size="sm"
                      class="shrink-0"
                      :variant="selectedServiceDate && isSameDay(selectedServiceDate, dateObj) ? 'solid' : 'outline'"
                      :color="selectedServiceDate && isSameDay(selectedServiceDate, dateObj) ? 'neutral' : 'neutral'"
                      @click="selectedServiceDate = dateObj; selectedServiceTime = null"
                    >
                      <div class="text-center">
                        <div class="text-xs opacity-80">{{ formatWeekdayShort(dateObj) }}</div>
                        <div class="font-semibold">{{ format(dateObj, 'd') }}</div>
                      </div>
                    </UButton>
                  </div>
                  <p v-if="!serviceModalSlotsLoading && serviceModalAvailableDates.length === 0" class="text-muted text-sm mt-2">Нет доступных дат в ближайшие 14 дней</p>
                </div>
                <div v-if="selectedServiceDate" class="mb-4">
                  <p class="text-sm font-medium mb-2">Выберите время</p>
                  <div class="flex flex-wrap gap-2">
                    <UButton
                      v-for="time in serviceModalAvailableTimeSlots"
                      :key="time"
                      size="sm"
                      :variant="selectedServiceTime === time ? 'solid' : 'outline'"
                      :color="selectedServiceTime === time ? 'neutral' : 'neutral'"
                      @click="selectedServiceTime = time"
                    >
                      {{ time }}
                    </UButton>
                  </div>
                  <p v-if="serviceModalAvailableTimeSlots.length === 0" class="text-muted text-sm mt-2">На выбранную дату нет свободных окон</p>
                </div>
                <UButton
                  color="neutral"
                  variant="outline"
                  size="lg"
                  block
                  class="!bg-transparent hover:!bg-transparent active:!bg-transparent"
                  :disabled="!selectedServiceDate || !selectedServiceTime"
                  @click="goToBookingStep"
                >
                  <Icon name="i-lucide-arrow-right" class="w-5 h-5 mr-2" />
                  Далее
                </UButton>
              </template>
            </div>
          </div>

          <!-- Шаг 2: Данные клиента -->
          <div v-else class="space-y-4">
            <h3 class="text-lg font-semibold">{{ selectedService.name }}</h3>
            <div class="p-3 rounded-lg bg-muted/30 border border-default text-sm text-muted">
              {{ selectedService.name }} — {{ selectedServiceDate && format(selectedServiceDate, 'd MMMM', { locale: ru }) }} в {{ selectedServiceTime }}
            </div>

            <div class="space-y-4 w-full min-w-0">
              <UFormField label="Имя" required>
                <UInput
                  v-model="bookingClientForm.name"
                  placeholder="Введите ваше имя"
                  required
                  class="!w-full"
                />
              </UFormField>

              <UFormField label="Email" required>
                <UInput
                  v-model="bookingClientForm.email"
                  type="email"
                  placeholder="example@mail.com"
                  required
                  class="!w-full"
                />
              </UFormField>

              <UFormField label="Телефон" required>
                <UInput
                  v-model="bookingClientForm.phone"
                  type="tel"
                  placeholder="+7 (999) 999-99-99"
                  required
                  class="!w-full"
                />
              </UFormField>

              <UFormField required>
                <template #label>Согласие с политикой конфиденциальности</template>
                <label class="flex items-start gap-2 cursor-pointer">
                  <UCheckbox v-model="bookingClientForm.privacyAccepted" />
                  <span class="text-sm">
                    Я соглашаюсь с <ULink to="/privacy" target="_blank" class="underline hover:no-underline">политикой конфиденциальности</ULink> и даю согласие на обработку персональных данных
                  </span>
                </label>
              </UFormField>

              <UFormField label="Комментарий (необязательно)">
                <UTextarea
                  v-model="bookingClientForm.notes"
                  placeholder="Дополнительная информация..."
                  :rows="3"
                  class="!w-full"
                />
              </UFormField>
            </div>

            <UButton
              label="Записаться"
              color="neutral"
              :loading="isBookingSubmitting"
              :disabled="isBookingSubmitting"
              block
              class="mt-4"
              @click="submitBooking"
            />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
