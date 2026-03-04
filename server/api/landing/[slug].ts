/**
 * Прокси к Django API для контента лендинга.
 * GET /api/landing/index — возвращает контент главной страницы.
 */
export default defineEventHandler(async (event) => {
  const slug = getRouterParam(event, 'slug') || 'index'
  const config = useRuntimeConfig()
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/landing/${slug}/`

  try {
    const data = await $fetch<Record<string, unknown>>(url)
    return data
  } catch (err) {
    // Если Django недоступен (например при build), возвращаем null
    // Фронтенд сделает fallback на Nuxt Content
    console.warn('[landing] Django API unavailable, using content fallback:', err)
    return null
  }
})
