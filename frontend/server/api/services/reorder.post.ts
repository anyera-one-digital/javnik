export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const headers = getHeaders(event)
  let authHeader = headers.authorization || headers.Authorization
  if (authHeader && !authHeader.startsWith('Bearer ')) {
    authHeader = `Bearer ${authHeader}`
  }
  if (!authHeader) {
    throw createError({ statusCode: 401, message: 'Unauthorized' })
  }

  const body = await readBody(event)
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  return await $fetch(`${apiBase}/api/services/reorder/`, {
    method: 'POST',
    headers: {
      Authorization: authHeader,
      'Content-Type': 'application/json'
    },
    body
  })
})
