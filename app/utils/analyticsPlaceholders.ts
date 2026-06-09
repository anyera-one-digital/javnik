import { addDays, differenceInDays } from 'date-fns'
import type { Range, Stat } from '~/types'

export function placeholderStats(): Stat[] {
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
