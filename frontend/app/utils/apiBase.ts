/**
 * Базовый URL API для клиентских запросов.
 * В production — пустая строка (относительные пути через nginx).
 * В dev — localhost или значение из runtimeConfig.
 */
export function getClientApiBase(): string {
  const config = useRuntimeConfig()
  const base = config.public.apiBase

  if (base !== undefined && base !== null) {
    return base
  }

  return import.meta.dev ? 'http://localhost:8000' : ''
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
