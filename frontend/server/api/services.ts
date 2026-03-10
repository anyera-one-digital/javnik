import type { Service } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)

  // Получаем токен из заголовков запроса
  const headers = getHeaders(event)
  let authHeader = headers.authorization || headers.Authorization
  
  // Логируем заголовки для отладки
  console.log('Request headers:', {
    authorization: headers.authorization ? 'Present' : 'Missing',
    Authorization: headers.Authorization ? 'Present' : 'Missing',
    method
  })
  
  // Убеждаемся, что токен в правильном формате
  if (authHeader) {
    // Если токен уже содержит Bearer, не добавляем еще раз
    if (!authHeader.startsWith('Bearer ')) {
      authHeader = `Bearer ${authHeader}`
    }
    console.log('Auth header format:', authHeader.substring(0, 20) + '...')
  } else {
    console.error('No authorization header found')
  }
  
  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  // На сервере используем приватную конфигурацию (может быть backend:8000 внутри Docker)
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/services/`

  if (method === 'GET') {
    console.log('Making GET request to:', url)
    console.log('With auth header:', authHeader.substring(0, 30) + '...')
    
    try {
      const response = await $fetch<Service[]>(url, {
        headers: {
          Authorization: authHeader,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        // Не выбрасываем ошибку автоматически, чтобы обработать ответ вручную
        onResponseError({ response }) {
          console.error('Response error in onResponseError:', response.status, response.statusText)
          console.error('Response body:', response._data)
        }
      })
      
      // Django REST Framework с пагинацией возвращает объект {count, results, ...}
      // Проверяем, является ли ответ массивом или объектом с results
      let servicesData: Service[]
      if (Array.isArray(response)) {
        servicesData = response
      } else if (response && typeof response === 'object' && 'results' in response) {
        // Это пагинированный ответ, извлекаем массив results
        servicesData = (response as any).results || []
      } else {
        servicesData = []
      }
      
      console.log('GET request successful, received', servicesData.length, 'services')
      console.log('Response structure:', Array.isArray(response) ? 'array' : typeof response)
      return servicesData
    } catch (error: any) {
      // Логируем полную информацию об ошибке
      console.error('=== Django GET Error Details ===')
      // Пытаемся получить полную информацию об ошибке
      try {
        console.error('Error object keys:', Object.keys(error))
        console.error('Error object:', JSON.stringify(error, Object.getOwnPropertyNames(error), 2))
      } catch (e) {
        console.error('Cannot stringify error:', e)
      }
      
      console.error('Error status:', error.statusCode || error.status)
      console.error('Error statusText:', error.statusText)
      console.error('Error data:', error.data)
      console.error('Error data (stringified):', error.data ? JSON.stringify(error.data, null, 2) : 'no data')
      console.error('Error response:', error.response)
      console.error('Error response data:', error.response?.data)
      console.error('Error response _data:', error.response?._data)
      console.error('Error response status:', error.response?.status)
      console.error('Error response statusCode:', error.response?.statusCode)
      console.error('Error message:', error.message)
      
      // Пробуем получить данные из разных мест
      if (error.cause) {
        console.error('Error cause:', error.cause)
      }
      if (error.request) {
        console.error('Error request:', error.request)
      }
      
      // Пытаемся получить тело ответа от Django
      let errorData: any = { detail: 'Ошибка при загрузке услуг' }
      let statusCode = 400
      
      // Пробуем разные способы извлечения данных об ошибке
      if (error.data) {
        errorData = error.data
        statusCode = error.statusCode || error.status || 400
        console.error('Error data found:', errorData)
      } 
      
      if (error.response) {
        const responseData = error.response.data || error.response._data
        if (responseData) {
          errorData = responseData
          console.error('Response data found:', responseData)
        }
        const responseStatus = error.response.status || error.response.statusCode
        if (responseStatus) {
          statusCode = responseStatus
          console.error('Response status found:', responseStatus)
        }
      }
      
      if (error.statusCode) {
        statusCode = error.statusCode
      }
      
      // Если это ошибка авторизации (токен невалидный), меняем статус на 401
      if (errorData && typeof errorData === 'object') {
        const errorText = JSON.stringify(errorData).toLowerCase()
        if (errorText.includes('token') || errorText.includes('authentication') || errorText.includes('unauthorized')) {
          statusCode = 401
          console.error('Detected authentication error, changing status to 401')
        }
      }
      
      console.error('Final error data:', JSON.stringify(errorData, null, 2))
      console.error('Final error data type:', typeof errorData)
      console.error('Final error data keys:', errorData && typeof errorData === 'object' ? Object.keys(errorData) : 'not an object')
      console.error('Final status code:', statusCode)
      
      // Если errorData - это строка, пытаемся распарсить
      if (typeof errorData === 'string') {
        try {
          const parsed = JSON.parse(errorData)
          console.error('Parsed error data:', parsed)
          errorData = parsed
        } catch (e) {
          console.error('Cannot parse error data as JSON:', e)
        }
      }
      
      // Пробрасываем ошибку с деталями от Django
      throw createError({
        statusCode,
        statusMessage: error.statusMessage || 'Bad Request',
        data: errorData,
        message: error.message || JSON.stringify(errorData)
      })
    }
  }

  if (method === 'POST') {
    // Проверяем, является ли запрос multipart/form-data (для загрузки файлов)
    const contentType = headers['content-type'] || headers['Content-Type'] || ''
    const isMultipart = contentType.includes('multipart/form-data')
    
    if (isMultipart) {
      // Для multipart/form-data проксируем запрос напрямую в Django
      // Читаем raw body и передаем его с правильными заголовками
      try {
        const rawBody = await readRawBody(event, false)
        
        console.log('Creating service with multipart FormData, content-type:', contentType)
        
        // Проксируем multipart запрос напрямую в Django
        const response = await $fetch<Service>(url, {
          method: 'POST',
          headers: {
            Authorization: authHeader,
            'Content-Type': contentType
          },
          body: rawBody
        })
        
        console.log('Service created successfully:', response)
        return response
      } catch (error: any) {
        console.error('Django POST FormData error:', error)
        console.error('Django POST error status:', error.statusCode || error.status)
        console.error('Django POST error data:', error.data)
        console.error('Django POST error response:', error.response)
        console.error('Django POST error message:', error.message)
        
        const statusCode = error.statusCode || error.status || 400
        const errorData = error.data || error.response?.data || { detail: 'Ошибка при создании услуги' }
        
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
      
      console.log('Creating service with JSON payload:', JSON.stringify(body, null, 2))
      console.log('Auth header:', authHeader ? 'Present' : 'Missing')
      
      try {
        const response = await $fetch<Service>(url, {
          method: 'POST',
          headers: {
            Authorization: authHeader,
            'Content-Type': 'application/json'
          },
          body
        })
        console.log('Service created successfully:', response)
        return response
      } catch (error: any) {
        console.error('Django POST error:', error)
        console.error('Django POST error status:', error.statusCode || error.status)
        console.error('Django POST error data:', error.data)
        console.error('Django POST error response:', error.response)
        console.error('Django POST error message:', error.message)
        
        const statusCode = error.statusCode || error.status || 400
        const errorData = error.data || error.response?.data || { detail: 'Ошибка при создании услуги' }
        
        throw createError({
          statusCode,
          statusMessage: error.statusMessage || 'Bad Request',
          data: errorData,
          message: error.message || JSON.stringify(errorData)
        })
      }
    }
  }

  throw createError({
    statusCode: 405,
    message: 'Method not allowed'
  })
})
