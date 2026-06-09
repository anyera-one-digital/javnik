import { useRuntimeConfig } from '#imports'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = event.method || 'GET'
  
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
  const url = `${apiBase}/api/schedule/`

  try {
    if (method === 'GET') {
      // Получаем query параметры для фильтрации
      const query = getQuery(event)
      const queryString = new URLSearchParams(query as Record<string, string>).toString()
      const fullUrl = queryString ? `${url}?${queryString}` : url
      
      const response = await $fetch(fullUrl, {
        headers: {
          Authorization: normalizedAuth,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      })
      
      return response
    } else if (method === 'POST') {
      const body = await readBody(event)
      const schedules = Array.isArray(body) ? body : [body]

      const results = []
      for (const schedule of schedules) {
        try {
          const response = await $fetch(url, {
            method: 'POST',
            headers: {
              Authorization: normalizedAuth,
              'Content-Type': 'application/json',
              Accept: 'application/json'
            },
            body: schedule
          })
          results.push(response)
        } catch (djangoError: any) {
          console.error('Schedule POST error:', djangoError.statusCode || djangoError.status, djangoError.data)
          throw djangoError
        }
      }
      
      return Array.isArray(body) ? results : results[0]
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
