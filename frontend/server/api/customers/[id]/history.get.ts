export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({ statusCode: 400, message: 'Customer ID is required' })
  }

  const headers = getHeaders(event)
  let authHeader = headers.authorization || headers.Authorization
  if (authHeader && !authHeader.startsWith('Bearer ')) {
    authHeader = `Bearer ${authHeader}`
  }
  if (!authHeader) {
    throw createError({ statusCode: 401, message: 'Unauthorized' })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  return await $fetch(`${apiBase}/api/customers/${id}/history/`, {
    headers: { Authorization: authHeader }
  })
})
