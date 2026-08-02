/**
 * Цвета маркеров услуг в календаре (hex — не зависят от Tailwind purge).
 * Карточки — графитовые; цвет услуги — тонкая полоска слева.
 * pending / completed / cancelled — фиксированные маркеры;
 * confirmed — цвет услуги из палитры без reserved.
 */

export const BOOKING_STATUS_HEX = {
  pending: '#eab308', // yellow-500
  completed: '#3b82f6', // blue-500
  cancelled: '#ef4444' // red-500
} as const

export const EVENT_MARKER_HEX = '#a855f7' // purple-500

/** Палитра confirmed-услуг (без yellow/blue/red/purple событий) */
export const CONFIRMED_SERVICE_HEX_PALETTE = [
  '#38bdf8', // sky
  '#34d399', // emerald
  '#fbbf24', // amber
  '#fb923c', // orange
  '#2dd4bf', // teal
  '#818cf8', // indigo
  '#f472b6', // pink
  '#a3e635', // lime
  '#22d3ee', // cyan
  '#c084fc', // violet
  '#f87171', // soft red (not status red)
  '#4ade80' // green
] as const

type ServiceLike = { id: number }

function resolveServiceId(booking: {
  serviceId?: number | null
  service?: number | null
}): number | null {
  const raw = booking.serviceId ?? booking.service
  if (raw == null || Number.isNaN(Number(raw))) return null
  return Number(raw)
}

function hexForServiceId(serviceId: number, services?: ServiceLike[]): string {
  const palette = CONFIRMED_SERVICE_HEX_PALETTE
  if (services?.length) {
    const sortedIds = [...new Set(services.map(s => Number(s.id)))].sort((a, b) => a - b)
    const idx = sortedIds.indexOf(serviceId)
    if (idx >= 0) return palette[idx % palette.length]!
  }
  return palette[Math.abs(serviceId) % palette.length]!
}

function hexForServiceName(name: string): string {
  const palette = CONFIRMED_SERVICE_HEX_PALETTE
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = ((hash << 5) - hash) + name.charCodeAt(i)
    hash |= 0
  }
  return palette[Math.abs(hash) % palette.length]!
}

export function getBookingColorHex(
  booking: {
    status?: string | null
    serviceId?: number | null
    service?: number | null
    serviceName?: string | null
  },
  services?: ServiceLike[]
): string {
  if (booking.status !== 'confirmed') {
    if (booking.status === 'pending') return BOOKING_STATUS_HEX.pending
    if (booking.status === 'cancelled') return BOOKING_STATUS_HEX.cancelled
    if (booking.status === 'completed') return BOOKING_STATUS_HEX.completed
    return BOOKING_STATUS_HEX.pending
  }

  const serviceId = resolveServiceId(booking)
  if (serviceId != null) return hexForServiceId(serviceId, services)

  const name = (booking.serviceName || '').trim()
  if (name) return hexForServiceName(name.toLowerCase())

  return CONFIRMED_SERVICE_HEX_PALETTE[0]!
}

/** Стиль графитовой карточки записи: фон + цветной маркер слева */
export function getBookingCardStyle(
  booking: {
    status?: string | null
    serviceId?: number | null
    service?: number | null
    serviceName?: string | null
  },
  services?: ServiceLike[]
): Record<string, string> {
  const marker = getBookingColorHex(booking, services)
  return {
    backgroundColor: 'var(--schedule-card-bg)',
    borderLeft: `3px solid ${marker}`,
    color: 'var(--schedule-card-fg)',
    boxSizing: 'border-box'
  }
}

/** Стиль графитовой карточки события */
export function getEventCardStyle(): Record<string, string> {
  return {
    backgroundColor: 'var(--schedule-card-bg)',
    borderLeft: `3px solid ${EVENT_MARKER_HEX}`,
    color: 'var(--schedule-card-fg)',
    boxSizing: 'border-box'
  }
}

/** @deprecated используйте getBookingColorHex + style */
export function getBookingColorClass(
  booking: {
    status?: string | null
    serviceId?: number | null
    service?: number | null
    serviceName?: string | null
  },
  services?: ServiceLike[]
): string {
  void booking
  void services
  return ''
}
