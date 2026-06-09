export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)

  const headers = getHeaders(event)
  const authHeader = headers.authorization || headers.Authorization

  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  const start = query.start as string | undefined
  const end = query.end as string | undefined

  if (!start || !end) {
    throw createError({
      statusCode: 400,
      message: 'start and end query parameters are required'
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const params = new URLSearchParams({ start, end })

  return await $fetch(`${apiBase}/api/analytics/services-breakdown/?${params.toString()}`, {
    headers: {
      Authorization: authHeader
    }
  })
})
