export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)
  const q = query.q as string

  if (!q || typeof q !== 'string' || q.trim().length < 2) {
    return { results: [] }
  }

  const headers = getHeaders(event)
  const authHeader = headers.authorization || headers.Authorization

  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/auth/address-suggest/?q=${encodeURIComponent(q.trim())}`

  try {
    const response = await $fetch<{ results: unknown[] }>(url, {
      headers: {
        Authorization: authHeader as string
      }
    })
    return response
  } catch (error: unknown) {
    console.error('Address suggest proxy error:', error)
    throw createError({
      statusCode: 500,
      message: 'Ошибка при получении подсказок адресов'
    })
  }
})
