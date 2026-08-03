/** Минимальный срок до записи для клиентов (публичная страница). */

export type BookingLeadId =
  | 'same_day_1h'
  | 'next_day'
  | 'skip_one_day'
  | 'skip_two_days'

export const DEFAULT_BOOKING_LEAD: BookingLeadId = 'same_day_1h'

export const bookingLeadOptions: { value: BookingLeadId, label: string, hint: string }[] = [
  {
    value: 'same_day_1h',
    label: 'За час',
    hint: 'В тот же день, ближайший слот не раньше чем через час'
  },
  {
    value: 'next_day',
    label: 'На следующий день',
    hint: 'Только завтра и позже'
  },
  {
    value: 'skip_one_day',
    label: 'Через день',
    hint: 'Не раньше чем через день (сегодня + 2)'
  },
  {
    value: 'skip_two_days',
    label: 'Через два дня',
    hint: 'Не раньше чем через два дня (сегодня + 3)'
  }
]

const MIN_CALENDAR_DAYS: Record<Exclude<BookingLeadId, 'same_day_1h'>, number> = {
  next_day: 1,
  skip_one_day: 2,
  skip_two_days: 3
}

export function normalizeBookingLead(value: string | null | undefined): BookingLeadId {
  const v = (value || '').trim()
  if (bookingLeadOptions.some(o => o.value === v)) {
    return v as BookingLeadId
  }
  return DEFAULT_BOOKING_LEAD
}

/** Первая календарная дата, доступная для записи. */
export function earliestBookableDate(lead: BookingLeadId, now = new Date()): Date {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  if (lead === 'same_day_1h') return today
  const days = MIN_CALENDAR_DAYS[lead]
  const d = new Date(today)
  d.setDate(d.getDate() + days)
  return d
}

/**
 * Можно ли показать/забронировать слот с учётом горизонта записи.
 * `timeHHMM` — "HH:MM", `date` — календарный день слота.
 */
export function isBookingSlotAllowed(
  lead: BookingLeadId,
  date: Date,
  timeHHMM: string,
  now = new Date()
): boolean {
  const normalized = normalizeBookingLead(lead)
  const [h, m] = timeHHMM.split(':').map(Number)
  const slot = new Date(date.getFullYear(), date.getMonth(), date.getDate(), h || 0, m || 0, 0, 0)

  if (normalized === 'same_day_1h') {
    return slot.getTime() >= now.getTime() + 60 * 60 * 1000
  }

  const minDate = earliestBookableDate(normalized, now)
  const day = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  return day.getTime() >= minDate.getTime()
}
