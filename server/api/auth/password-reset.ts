export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)

  // На сервере используем приватную конфигурацию
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/auth/password-reset/`

  if (method === 'POST') {
    const body = await readBody(event)
    try {
      const response = await $fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body
      })
      return response
    } catch (error: any) {
      throw createError({
        statusCode: error.statusCode || error.status || 400,
        statusMessage: error.statusMessage || error.message,
        data: error.data || error.response?._data || { error: error.message || 'Ошибка отправки кода' }
      })
    }
  }

  throw createError({
    statusCode: 405,
    message: 'Method not allowed'
  })
})
