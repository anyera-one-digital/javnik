import { format, startOfDay, parse, startOfWeek, endOfWeek, eachDayOfInterval, addDays } from 'date-fns'
import { ru } from 'date-fns/locale'

const SCHEDULE_ANCHOR_DATE_KEY = 'schedule-anchor-date'

export function parseScheduleDateFromQuery(dateStr: string | undefined): Date {
  if (!dateStr) return startOfDay(new Date())
  try {
    return startOfDay(parse(dateStr, 'yyyy-MM-dd', new Date()))
  } catch {
    return startOfDay(new Date())
  }
}

function readDateKeyFromRoute(): string {
  const route = useRoute()
  const raw = route.query.date
  const dateStr = Array.isArray(raw) ? raw[0] : raw
  if (typeof dateStr === 'string') return dateStr
  return format(startOfDay(new Date()), 'yyyy-MM-dd')
}

/** Дата расписания — общий useState + URL (layout и /schedule) */
export function useSchedulePageDate() {
  const route = useRoute()
  const router = useRouter()

  const anchorDate = useState(SCHEDULE_ANCHOR_DATE_KEY, readDateKeyFromRoute)

  watch(
    () => [route.path, route.query.date] as const,
    ([path]) => {
      if (path !== '/schedule') return
      const fromRoute = readDateKeyFromRoute()
      if (anchorDate.value !== fromRoute) {
        anchorDate.value = fromRoute
      }
    },
    { immediate: true }
  )

  const selectedDate = computed(() => parseScheduleDateFromQuery(anchorDate.value))

  const weekStart = computed(() =>
    startOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 })
  )
  const weekEnd = computed(() =>
    endOfWeek(selectedDate.value, { locale: ru, weekStartsOn: 1 })
  )
  const weekDays = computed(() =>
    eachDayOfInterval({ start: weekStart.value, end: weekEnd.value })
  )

  async function pushScheduleDate(date: Date, extraQuery?: Record<string, string | undefined>) {
    const normalized = startOfDay(date)
    const dateKey = format(normalized, 'yyyy-MM-dd')

    anchorDate.value = dateKey

    const query: Record<string, string> = { date: dateKey }
    const view = route.query.view
    if (typeof view === 'string') {
      query.view = view
    }
    if (extraQuery) {
      for (const [k, v] of Object.entries(extraQuery)) {
        if (v !== undefined) query[k] = v
      }
    }

    if (route.path === '/schedule' && route.query.date === dateKey) {
      return
    }

    await router.push({
      path: '/schedule',
      query
    })
  }

  async function navigateScheduleDays(deltaDays: number) {
    await pushScheduleDate(addDays(selectedDate.value, deltaDays))
  }

  return {
    anchorDate,
    selectedDate,
    weekStart,
    weekEnd,
    weekDays,
    pushScheduleDate,
    navigateScheduleDays
  }
}
