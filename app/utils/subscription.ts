import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { UserSubscription } from '~/types'

export function formatSubscriptionExpiry(expiresAt: string | null | undefined): string | null {
  if (!expiresAt) return null
  try {
    return format(parseISO(expiresAt), 'd MMMM yyyy', { locale: ru })
  } catch {
    return null
  }
}

export function subscriptionStatusText(sub: UserSubscription | null | undefined): string | null {
  if (!sub) return null

  if (sub.effectivePlan === 'free') {
    if (sub.plan === 'pro' && sub.expiresAt) {
      return 'Пробный период Pro завершён. Оформите подписку, чтобы вернуть лимиты Pro.'
    }
    return 'Тариф Free — без срока действия'
  }

  const dateStr = formatSubscriptionExpiry(sub.expiresAt)
  if (sub.isTrial) {
    if (sub.daysRemaining === 0) {
      return dateStr
        ? `Пробный Pro заканчивается сегодня (${dateStr})`
        : 'Пробный Pro заканчивается сегодня'
    }
    if (sub.daysRemaining != null && sub.daysRemaining > 0) {
      const daysWord = sub.daysRemaining === 1
        ? 'день'
        : sub.daysRemaining >= 2 && sub.daysRemaining <= 4
          ? 'дня'
          : 'дней'
      return `Пробный Pro · осталось ${sub.daysRemaining} ${daysWord}${dateStr ? ` (до ${dateStr})` : ''}`
    }
  }

  if (!sub.expiresAt) {
    return 'Тариф Pro — без ограничения по сроку'
  }

  if (sub.daysRemaining === 0) {
    return dateStr ? `Pro действует до ${dateStr} (сегодня последний день)` : 'Pro заканчивается сегодня'
  }

  if (sub.daysRemaining != null && sub.daysRemaining > 0) {
    const daysWord = sub.daysRemaining === 1
      ? 'день'
      : sub.daysRemaining >= 2 && sub.daysRemaining <= 4
        ? 'дня'
        : 'дней'
    return `Pro · осталось ${sub.daysRemaining} ${daysWord}${dateStr ? ` (до ${dateStr})` : ''}`
  }

  return dateStr ? `Pro действует до ${dateStr}` : 'Тариф Pro'
}
