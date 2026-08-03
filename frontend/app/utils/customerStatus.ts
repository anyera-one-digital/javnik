import type { Customer } from '~/types'

export type CustomerStatus = NonNullable<Customer['status']>
export type CustomerStatusSelectValue = 'auto' | CustomerStatus

/** Auto rules: >50 → VIP, >5 → постоянный, иначе новый/обычный */
export function autoCustomerStatus(visits: number): CustomerStatus {
  if (visits > 50) return 'vip'
  if (visits > 5) return 'loyal'
  if (visits <= 1) return 'first-time'
  return 'regular'
}

/** Manual status wins; otherwise derive from completed visits */
export function resolveCustomerStatus(c: Pick<Customer, 'status' | 'status_manual' | 'visits_count'>): CustomerStatus {
  if (c.status_manual && c.status) return c.status
  return autoCustomerStatus(c.visits_count ?? 0)
}

export function customerStatusLabel(status: CustomerStatus): string {
  switch (status) {
    case 'vip':
      return 'VIP'
    case 'loyal':
      return 'Постоянный клиент'
    case 'first-time':
      return 'Новый клиент'
    default:
      return 'Обычный клиент'
  }
}

export function customerStatusIcon(status: CustomerStatusSelectValue): string {
  switch (status) {
    case 'vip':
      return 'i-lucide-crown'
    case 'loyal':
      return 'i-lucide-star'
    case 'first-time':
      return 'i-lucide-user-plus'
    case 'regular':
      return 'i-lucide-user'
    case 'auto':
      return 'i-lucide-sparkles'
  }
}

export const CUSTOMER_STATUS_SELECT_ITEMS: Array<{
  label: string
  value: CustomerStatusSelectValue
  icon: string
}> = [
  { label: 'Автоматически', value: 'auto', icon: customerStatusIcon('auto') },
  { label: 'Новый клиент', value: 'first-time', icon: customerStatusIcon('first-time') },
  { label: 'Обычный клиент', value: 'regular', icon: customerStatusIcon('regular') },
  { label: 'Постоянный клиент', value: 'loyal', icon: customerStatusIcon('loyal') },
  { label: 'VIP', value: 'vip', icon: customerStatusIcon('vip') }
]
