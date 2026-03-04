import type { Service } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      message: 'Service ID is required'
    })
  }

  // Получаем токен из заголовков запроса
  const headers = getHeaders(event)
  let authHeader = headers.authorization || headers.Authorization
  
  // Убеждаемся, что токен в правильном формате
  if (authHeader && !authHeader.startsWith('Bearer ')) {
    authHeader = `Bearer ${authHeader}`
  }
  
  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  // На сервере используем приватную конфигурацию (может быть backend:8000 внутри Docker)
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/services/${id}/`

  if (method === 'PUT' || method === 'PATCH') {
    // Проверяем, является ли запрос multipart/form-data (для загрузки файлов)
    const contentType = headers['content-type'] || headers['Content-Type'] || ''
    const isMultipart = contentType.includes('multipart/form-data')
    
    if (isMultipart) {
      // Для multipart/form-data проксируем запрос напрямую в Django
      try {
        const rawBody = await readRawBody(event, false)
        
        console.log('Updating service with multipart FormData, content-type:', contentType)
        
        // Проксируем multipart запрос напрямую в Django
        const response = await $fetch<Service>(url, {
          method: method,
          headers: {
            Authorization: authHeader,
            'Content-Type': contentType
          },
          body: rawBody
        })
        
        return response
      } catch (error: any) {
        console.error('Django PUT FormData error:', error)
        const statusCode = error.statusCode || error.status || 400
        const errorData = error.data || error.response?.data || { detail: 'Ошибка при обновлении услуги' }
        
        throw createError({
          statusCode,
          statusMessage: error.statusMessage || 'Bad Request',
          data: errorData,
          message: error.message || JSON.stringify(errorData)
        })
      }
    } else {
      // Обрабатываем обычный JSON запрос
      const body = await readBody(event)
      const response = await $fetch<Service>(url, {
        method: method,
        headers: {
          Authorization: authHeader,
          'Content-Type': 'application/json'
        },
        body
      })
      return response
    }
  }

  if (method === 'DELETE') {
    await $fetch(url, {
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
