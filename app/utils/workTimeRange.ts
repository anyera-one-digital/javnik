import type { Booking, Event, WorkSchedule } from '~/types'
import { normalizeApiList } from '~/utils/normalizeApiList'

const DEFAULT_RANGE = { minHour: 9, maxHour: 21 }

function asArray<T>(value: Iterable<T> | T[] | unknown): T[] {
  if (Array.isArray(value)) {
    return value
  }
  if (value != null && typeof value === 'object' && Symbol.iterator in value) {
    return [...(value as Iterable<T>)]
  }
  return normalizeApiList<T>(value)
}

function absorbInterval(
  minHour: number | null,
  maxHour: number | null,
  maxEndMinute: number,
  startTime: string,
  endTime: string
): { minHour: number | null, maxHour: number | null, maxEndMinute: number } {
  const [startHour] = startTime.split(':').map(Number)
  const [endH, endMinute = 0] = endTime.split(':').map(Number)
  const endMinutes = endH * 60 + endMinute

  let nextMin = minHour
  let nextMax = maxHour
  let nextEndMinute = maxEndMinute

  if (nextMin === null || startHour < nextMin) {
    nextMin = startHour
  }

  const currentMaxMinutes = nextMax !== null ? nextMax * 60 + nextEndMinute : 0
  if (nextMax === null || endMinutes > currentMaxMinutes) {
    nextMax = endH
    nextEndMinute = endMinute
  }

  return { minHour: nextMin, maxHour: nextMax, maxEndMinute: nextEndMinute }
}

/** Диапазон часов для сетки расписания: график + брони + события. */
export function computeWorkTimeRange(
  schedules: Iterable<WorkSchedule>,
  bookings: Booking[] = [],
  events: Event[] = []
): { minHour: number, maxHour: number } {
  let minHour: number | null = null
  let maxHour: number | null = null
  let maxEndMinute = 0

  const scheduleList = asArray(schedules)
  const bookingList = asArray(bookings)
  const eventList = asArray(events)

  for (const schedule of scheduleList) {
    if (schedule.type === 'workday' && schedule.startTime && schedule.endTime) {
      ({ minHour, maxHour, maxEndMinute } = absorbInterval(
        minHour, maxHour, maxEndMinute, schedule.startTime, schedule.endTime
      ))
    }
  }

  for (const booking of bookingList) {
    if (booking.startTime && booking.endTime) {
      ({ minHour, maxHour, maxEndMinute } = absorbInterval(
        minHour, maxHour, maxEndMinute, booking.startTime, booking.endTime
      ))
    }
  }

  for (const event of eventList) {
    if (!event.startTime || !event.duration) continue
    const [sh, sm] = event.startTime.split(':').map(Number)
    const endTotal = sh * 60 + sm + event.duration
    const endH = Math.floor(endTotal / 60)
    const endM = endTotal % 60
    const endTime = `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}`
    ({ minHour, maxHour, maxEndMinute } = absorbInterval(
      minHour, maxHour, maxEndMinute, event.startTime, endTime
    ))
  }

  if (minHour === null || maxHour === null) {
    return DEFAULT_RANGE
  }

  // Конец в HH:00 — последняя строка сетки = час (endHour - 1), т.к. строка N = интервал N:00–(N+1):00
  // Конец с минутами (например 20:30) — показываем и час endHour
  const maxDisplayHour = maxEndMinute === 0
    ? Math.max(minHour, maxHour - 1)
    : maxHour
  return { minHour, maxHour: maxDisplayHour }
}
