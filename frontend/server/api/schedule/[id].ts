import { useRuntimeConfig } from '#imports'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = event.method || 'GET'
  const id = getRouterParam(event, 'id')
  
  if (!id) {
    throw createError({
      statusCode: 400,
      message: 'Schedule ID is required'
    })
  }
  
  // Получаем токен авторизации из заголовков
  const authHeader = event.headers.get('authorization')
  
  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  // Нормализуем токен
  let normalizedAuth = authHeader
  if (!normalizedAuth.startsWith('Bearer ')) {
    normalizedAuth = `Bearer ${normalizedAuth}`
  }

  // На сервере используем приватную конфигурацию
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/schedule/${id}/`

  try {
    if (method === 'PUT' || method === 'PATCH') {
      const body = await readBody(event)
      
      const response = await $fetch(url, {
        method: method,
        headers: {
          Authorization: normalizedAuth,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body
      })
      
      return response
    } else if (method === 'DELETE') {
      await $fetch(url, {
        method: 'DELETE',
        headers: {
          Authorization: normalizedAuth,
          'Accept': 'application/json'
        }
      })
      
      return { success: true }
    } else {
      throw createError({
        statusCode: 405,
        message: 'Method not allowed'
      })
    }
  } catch (error: any) {
    console.error('Schedule API error:', error)
    throw createError({
      statusCode: error.statusCode || error.status || 500,
      statusMessage: error.statusMessage || error.message || 'Internal Server Error',
      data: error.data || error.message
    })
  }
})
