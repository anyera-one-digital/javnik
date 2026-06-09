/**
 * Прокси к Django API для юридических страниц.
 * GET /api/landing/legal/privacy | /api/landing/legal/terms
 */
export default defineEventHandler(async (event) => {
  const slug = getRouterParam(event, 'slug')
  if (!slug) {
    throw createError({ statusCode: 400, statusMessage: 'Slug is required' })
  }

  const config = useRuntimeConfig()
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/landing/legal/${slug}/`

  try {
    return await $fetch<Record<string, unknown>>(url)
  } catch (err) {
    console.warn('[legal] Django API unavailable:', err)
    return null
  }
})
