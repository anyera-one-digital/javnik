import type { Event } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)
  const query = getQuery(event)

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
  let url = `${apiBase}/api/events/`

  // Добавляем query параметры
  const params = new URLSearchParams()
  if (query.date) {
    params.append('date', query.date as string)
  }
  if (params.toString()) {
    url += `?${params.toString()}`
  }

  if (method === 'GET') {
    const response = await $fetch<Event[]>(url, {
      headers: {
        Authorization: authHeader
      }
    })
    return response
  }

  if (method === 'POST') {
    const body = await readBody(event)
    console.log('Events API: POST request body:', JSON.stringify(body, null, 2))
    try {
      const response = await $fetch<Event>(url, {
        method: 'POST',
        headers: {
          Authorization: authHeader,
          'Content-Type': 'application/json'
        },
        body
      })
      return response
    } catch (error: any) {
      console.error('Events API: Error creating event:', error)
      console.error('Events API: Error status:', error.statusCode || error.status)
      console.error('Events API: Error data:', error.data)
      console.error('Events API: Error response:', error.response)
      console.error('Events API: Error message:', error.message)
      
      // Пробрасываем ошибку дальше с правильным форматом
      const statusCode = error.statusCode || error.status || 500
      const errorData = error.data || error.response?.data || { error: error.message || 'Unknown error' }
      
      // Если errorData это просто true или false, преобразуем в объект
      if (errorData === true || errorData === false) {
        throw createError({
          statusCode,
          statusMessage: error.statusMessage || error.message || 'Bad Request',
          data: { error: 'Ошибка при создании события. Проверьте логи сервера.' }
        })
      }
      
      throw createError({
        statusCode,
        statusMessage: error.statusMessage || error.message || 'Bad Request',
        data: errorData
      })
    }
  }

  if (method === 'PATCH') {
    const body = await readBody(event)
    const id = body.id
    const response = await $fetch<Event>(`${apiBase}/api/events/${id}/`, {
      method: 'PATCH',
      headers: {
        Authorization: authHeader,
        'Content-Type': 'application/json'
      },
      body
    })
    return response
  }

  if (method === 'DELETE') {
    const id = query.id as string
    await $fetch(`${apiBase}/api/events/${id}/`, {
      method: 'DELETE',
      headers: {
        Authorization: authHeader
      }
    })
    return { success: true }
  }

  throw createError({
    statusCode: 405,
    message: 'Method not allowed'
  })
})
