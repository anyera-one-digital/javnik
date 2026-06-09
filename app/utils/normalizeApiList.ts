/** Приводит ответ API (массив или DRF `{ results }`) к массиву. */
export function normalizeApiList<T>(data: unknown): T[] {
  if (Array.isArray(data)) {
    return data
  }
  if (data && typeof data === 'object') {
    const obj = data as Record<string, unknown>
    if (Array.isArray(obj.results)) {
      return obj.results as T[]
    }
    if (Array.isArray(obj.data)) {
      return obj.data as T[]
    }
    if (Array.isArray(obj.bookings)) {
      return obj.bookings as T[]
    }
    if ('id' in obj && obj.id != null) {
      return [data as T]
    }
  }
  return []
}
