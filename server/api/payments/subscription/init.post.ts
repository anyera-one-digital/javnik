export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const headers = getHeaders(event)
  const authHeader = headers.authorization || headers.Authorization

  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  const body = await readBody(event)
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'

  try {
    return await $fetch(`${apiBase}/api/auth/payments/subscription/init/`, {
      method: 'POST',
      headers: {
        Authorization: authHeader as string,
        'Content-Type': 'application/json'
      },
      body
    })
  } catch (error: any) {
    const statusCode = error.statusCode || error.status || 500
    const data = error.data || error.response?._data
    throw createError({
      statusCode,
      message: data?.error || data?.detail || error.message || 'Не удалось создать платёж'
    })
  }
})
