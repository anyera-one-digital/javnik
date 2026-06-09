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
  const period = (query.period as string | undefined) || 'daily'
  const mode = (query.mode as string | undefined) || 'actual'

  if (!start || !end) {
    throw createError({
      statusCode: 400,
      message: 'start and end query parameters are required'
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const params = new URLSearchParams({ start, end, period, mode })

  return await $fetch(`${apiBase}/api/analytics/revenue/?${params.toString()}`, {
    headers: {
      Authorization: authHeader
    }
  })
})
