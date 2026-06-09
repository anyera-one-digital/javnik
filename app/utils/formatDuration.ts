/** Длительность в минутах → «30 мин», «1 ч», «1 ч 30 мин», «2 ч». */
export function formatDurationMinutes(minutes: number | null | undefined): string {
  if (minutes == null || Number.isNaN(Number(minutes))) {
    return '—'
  }

  const total = Math.max(0, Math.round(Number(minutes)))
  if (total === 0) {
    return '0 мин'
  }

  const hours = Math.floor(total / 60)
  const mins = total % 60

  if (hours === 0) {
    return `${mins} мин`
  }
  if (mins === 0) {
    return `${hours} ч`
  }
  return `${hours} ч ${mins} мин`
}
