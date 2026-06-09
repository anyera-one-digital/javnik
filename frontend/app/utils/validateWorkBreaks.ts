import type { WorkBreak } from '~/types'

/**
 * Минуты от полуночи. Поддержка "HH:MM" и "HH:MM:SS".
 */
function timeToMinutes(t: string): number {
  const s = t.trim().split(':').slice(0, 2).map(Number)
  const h = s[0] ?? 0
  const m = s[1] ?? 0
  return h * 60 + m
}

/**
 * Два полуинтервала [a,b) и [c,d) в минутах пересекаются ⟺ a < d && c < b.
 * Смежные (12:00–13:00 и 13:00–14:00) не пересекаются.
 */
function intervalsOverlapMinutes(a: number, b: number, c: number, d: number): boolean {
  return a < d && c < b
}

/**
 * @returns null если ок, иначе текст ошибки
 */
export function validateWorkBreaksNoOverlap(breaks: WorkBreak[]): string | null {
  if (breaks.length < 2) {
    for (const b of breaks) {
      const s = timeToMinutes(b.startTime)
      const e = timeToMinutes(b.endTime)
      if (s >= e) {
        return 'В перерыве время начала должно быть раньше окончания'
      }
    }
    return null
  }

  const parts: { s: number, e: number }[] = []
  for (const b of breaks) {
    const s = timeToMinutes(b.startTime)
    const e = timeToMinutes(b.endTime)
    if (s >= e) {
      return 'В перерыве время начала должно быть раньше окончания'
    }
    parts.push({ s, e })
  }

  for (let i = 0; i < parts.length; i++) {
    for (let j = i + 1; j < parts.length; j++) {
      const p = parts[i]
      const q = parts[j]
      if (!p || !q) continue
      if (intervalsOverlapMinutes(p.s, p.e, q.s, q.e)) {
        return 'Перерывы не могут пересекаться. Смежные по времени (например 12:00–13:00 и 13:00–14:00) — можно.'
      }
    }
  }

  return null
}
