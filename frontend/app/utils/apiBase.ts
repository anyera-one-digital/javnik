/**
 * Базовый URL API для клиентских запросов.
 * Пути в коде уже вида `/api/auth/...`, поэтому:
 * - '' / относительный origin через nginx
 * - 'http://backend:8000' на сервере
 * - значение `/api` нельзя клеить ещё раз (получится /api/api/...)
 */
export function getClientApiBase(): string {
  const config = useRuntimeConfig()
  const base = config.public.apiBase

  if (base === undefined || base === null || base === '') {
    return ''
  }

  const normalized = String(base).replace(/\/$/, '')

  // В Docker часто ставят NUXT_PUBLIC_API_BASE_URL=/api — это префикс nginx, не origin.
  if (normalized === '/api') {
    return ''
  }

  return normalized
}

/**
 * Нормализует URL медиа-файла: относительный путь остаётся как есть,
 * внутренние Docker-хосты заменяются на текущий origin.
 */
export function normalizeMediaUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined

  if (url.includes('://backend:') || url.includes('://backend/')) {
    const path = url.replace(/^https?:\/\/[^/]+/, '')
    if (import.meta.client && typeof window !== 'undefined') {
      return `${window.location.origin}${path}`
    }
    return path
  }

  if (url.startsWith('http://') || url.startsWith('https://')) {
    if (import.meta.client && typeof window !== 'undefined' && window.location.protocol === 'https:' && url.startsWith('http://')) {
      return url.replace(/^http:/, 'https:')
    }
    return url
  }

  if (url.startsWith('/')) {
    if (import.meta.client && typeof window !== 'undefined') {
      return `${window.location.origin}${url}`
    }
    return url
  }

  return url
}
