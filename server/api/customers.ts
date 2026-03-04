import type { User } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)

  // Получаем токен из заголовков запроса
  const headers = getHeaders(event)
  const authHeader = headers.authorization || headers.Authorization
  
  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  // На сервере используем приватную конфигурацию (может быть backend:8000 внутри Docker)
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/customers/`

  if (method === 'GET') {
    const response = await $fetch<User[]>(url, {
      headers: {
        Authorization: authHeader
      }
    })
    return response
  }

  if (method === 'POST') {
    const body = await readBody(event)
    const response = await $fetch<User>(url, {
      method: 'POST',
      headers: {
        Authorization: authHeader,
        'Content-Type': 'application/json'
      },
      body
    })
    return response
  }

  throw createError({
    statusCode: 405,
    message: 'Method not allowed'
  })
})
