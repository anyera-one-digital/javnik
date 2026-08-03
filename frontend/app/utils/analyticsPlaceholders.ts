import { addDays, differenceInDays } from 'date-fns'
import type {
  AnalyticsLoadResponse,
  AnalyticsOverviewResponse,
  Range
} from '~/types'

export function placeholderOverview(range: Range): AnalyticsOverviewResponse {
  const totalDays = Math.max(1, differenceInDays(range.end, range.start) + 1)
  const points = []
  let totalReceived = 0
  let totalExpected = 0

  for (let i = 0; i < totalDays; i++) {
    const date = addDays(range.start, i)
    const received = i % 5 === 2 ? 4000 + (i % 3) * 500 : i % 7 === 0 ? 1700 : 0
    const expected = i % 6 === 1 ? 2500 : 0
    totalReceived += received
    totalExpected += expected
    points.push({
      date: date.toISOString().slice(0, 10),
      received,
      expected
    })
  }

  return {
    revenue: { value: totalReceived || 5700, variation: 100, previousValue: 0 },
    bookings: { value: 42, variation: 27, previousValue: 33 },
    newClients: { value: 8, variation: 12, previousValue: 7 },
    completedBookings: { value: 38, variation: 8, previousValue: 35 },
    successRate: 90,
    periodSummary: {
      averageCheck: 2850,
      cancellations: 2,
      returningClients: 12,
      bookingsCount: 42,
      trendReady: true,
      trendHint: null
    },
    clientsBreakdown: {
      total: 28,
      new: 8,
      returning: 20,
      regular: 12,
      items: [
        { label: 'Новые', value: 8 },
        { label: 'Повторные', value: 20 }
      ]
    },
    revenueByService: {
      total: totalReceived || 118400,
      items: [
        { label: 'Индивидуальная консультация', value: 50000 },
        { label: 'Расширенная сессия 90 мин', value: 41800 },
        { label: 'Онлайн-консультация', value: 17500 },
        { label: 'Разбор кейса', value: 9100 }
      ]
    },
    revenueChart: {
      totalReceived: totalReceived || 5700,
      totalExpected,
      points
    },
    previousRange: {
      start: addDays(range.start, -totalDays).toISOString().slice(0, 10),
      end: addDays(range.start, -1).toISOString().slice(0, 10)
    }
  }
}

export function placeholderLoad(): AnalyticsLoadResponse {
  const hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00']
  const days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
  const pattern = [
    [0, 1, 1, 0, 1, 0, 0],
    [1, 0, 2, 1, 2, 1, 0],
    [1, 1, 2, 1, 3, 1, 1],
    [2, 1, 3, 2, 3, 2, 1],
    [1, 0, 2, 1, 2, 1, 0],
    [2, 1, 3, 2, 4, 2, 1],
    [1, 0, 2, 1, 3, 1, 0],
    [2, 1, 3, 2, 4, 2, 1],
    [3, 1, 4, 2, 5, 2, 1],
    [2, 1, 3, 2, 4, 3, 1],
    [1, 0, 2, 1, 3, 2, 0]
  ]

  return {
    load: { value: 64, variation: 7, previousValue: 57 },
    freeSlots: { value: 12, variation: 4, previousValue: 8 },
    bookings: { value: 42, variation: 27, previousValue: 33 },
    revenue: { value: 118400, variation: 14, previousValue: 104100 },
    heatmap: {
      hours,
      days,
      cells: pattern,
      max: 5
    },
    loadByDay: [
      { day: 'Пн', weekday: 0, loadPercent: 58, availableMinutes: 600, bookedMinutes: 348 },
      { day: 'Вт', weekday: 1, loadPercent: 42, availableMinutes: 600, bookedMinutes: 252 },
      { day: 'Ср', weekday: 2, loadPercent: 76, availableMinutes: 600, bookedMinutes: 456 },
      { day: 'Чт', weekday: 3, loadPercent: 61, availableMinutes: 600, bookedMinutes: 366 },
      { day: 'Пт', weekday: 4, loadPercent: 82, availableMinutes: 600, bookedMinutes: 492 },
      { day: 'Сб', weekday: 5, loadPercent: 55, availableMinutes: 600, bookedMinutes: 330 },
      { day: 'Вс', weekday: 6, loadPercent: 35, availableMinutes: 480, bookedMinutes: 168 }
    ],
    insights: [
      { icon: 'trending-up', text: 'Пятница загружена на 82%' },
      { icon: 'clock', text: 'Свободнее всего во вторник после 15:00' },
      { icon: 'moon', text: 'Длинные сессии чаще выбирают вечером' }
    ],
    popularServices: [
      { name: 'Индивидуальная консультация', bookings: 20, revenue: 50000 },
      { name: 'Расширенная сессия 90 мин', bookings: 11, revenue: 41800 },
      { name: 'Онлайн-консультация', bookings: 7, revenue: 17500 },
      { name: 'Разбор кейса', bookings: 4, revenue: 9100 }
    ],
    previousRange: { start: '2026-06-01', end: '2026-06-30' }
  }
}

/** @deprecated legacy placeholders for old components */
export function placeholderStats() {
  return [
    { title: 'Новые клиенты', icon: 'i-lucide-user-plus', value: 8, variation: 12 },
    { title: 'Постоянные клиенты', icon: 'i-lucide-users', value: 24, variation: 5 },
    { title: 'Записи', icon: 'i-lucide-calendar-check', value: 42, variation: -3, to: '/schedule' },
    { title: 'Успешные записи', icon: 'i-lucide-circle-check-big', value: 38, variation: 8, to: '/schedule' }
  ]
}

export function placeholderRevenuePoints(range: Range) {
  const totalDays = Math.max(1, differenceInDays(range.end, range.start) + 1)
  const points: { date: Date, amount: number }[] = []
  let total = 0

  for (let i = 0; i < totalDays; i++) {
    const date = addDays(range.start, i)
    const amount = 8500 + ((i * 1737) % 9000)
    points.push({ date, amount })
    total += amount
  }

  return { points, total }
}

export function placeholderServicesBreakdown() {
  return {
    bookingsByService: [
      { label: 'Стрижка', value: 18 },
      { label: 'Окрашивание', value: 12 },
      { label: 'Укладка', value: 8 }
    ],
    revenueByService: [
      { label: 'Стрижка', value: 54000 },
      { label: 'Окрашивание', value: 72000 },
      { label: 'Укладка', value: 24000 }
    ],
    bookingsTotal: 38,
    revenueTotal: 150000
  }
}
