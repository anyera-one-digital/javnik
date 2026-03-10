import type { Booking } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)
  const query = getQuery(event)

  // Получаем токен из заголовков запроса
  const headers = getHeaders(event)
  const authHeader = headers.authorization || headers.Authorization
  
  console.log('Bookings API: Method:', method)
  console.log('Bookings API: Auth header present:', !!authHeader)
  console.log('Bookings API: Query params:', query)
  
  if (!authHeader) {
    console.error('Bookings API: No authorization header')
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  // На сервере используем приватную конфигурацию (может быть backend:8000 внутри Docker)
  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  let url = `${apiBase}/api/bookings/`

  // Добавляем query параметры
  const params = new URLSearchParams()
  if (query.date) {
    params.append('date', query.date as string)
  }
  if (query.employeeId) {
    params.append('employeeId', query.employeeId as string)
  }
  if (params.toString()) {
    url += `?${params.toString()}`
  }

  if (method === 'GET') {
    try {
      console.log('Bookings API: Fetching from Django:', url)
      const response = await $fetch<any>(url, {
        headers: {
          Authorization: authHeader
        }
      })
      console.log('Bookings API: Response type:', typeof response)
      console.log('Bookings API: Is array:', Array.isArray(response))
      console.log('Bookings API: Response keys:', response && typeof response === 'object' ? Object.keys(response) : 'N/A')
      console.log('Bookings API: Full response:', JSON.stringify(response, null, 2))
      
      // Обрабатываем разные форматы ответа от Django
      let bookings: Booking[] = []
      
      if (Array.isArray(response)) {
        // Если это массив - используем как есть
        bookings = response
        console.log('Bookings API: Response is array, length:', bookings.length)
      } else if (response && typeof response === 'object') {
        console.log('Bookings API: Response is object, keys:', Object.keys(response))
        // Если это объект, проверяем возможные поля
        if (Array.isArray(response.results)) {
          // Пагинированный ответ
          bookings = response.results
          console.log('Bookings API: Found results array, length:', bookings.length)
        } else if (Array.isArray(response.data)) {
          // Ответ с полем data
          bookings = response.data
          console.log('Bookings API: Found data array, length:', bookings.length)
        } else if (Array.isArray(response.bookings)) {
          // Ответ с полем bookings
          bookings = response.bookings
          console.log('Bookings API: Found bookings array, length:', bookings.length)
        } else if (response.id) {
          // Если это один объект бронирования
          bookings = [response]
          console.log('Bookings API: Single booking object found')
        } else {
          console.warn('Bookings API: Unknown response format:', response)
          bookings = []
        }
      } else {
        console.warn('Bookings API: Unexpected response type:', typeof response)
        bookings = []
      }
      
      console.log('Bookings API: Processed', bookings.length, 'bookings')
      if (bookings.length > 0) {
        console.log('Bookings API: First booking:', JSON.stringify(bookings[0], null, 2))
      }
      return bookings
    } catch (error: any) {
      console.error('Bookings API: Error fetching from Django:', error)
      console.error('Bookings API: Error status:', error.statusCode || error.status)
      console.error('Bookings API: Error data:', error.data)
      throw createError({
        statusCode: error.statusCode || error.status || 500,
        statusMessage: error.statusMessage || error.message,
        data: error.data || error.response?._data || { error: error.message || 'Ошибка загрузки бронирований' }
      })
    }
  }

  if (method === 'POST') {
    let body: Record<string, unknown>
    try {
      body = (await readBody(event)) as Record<string, unknown>
    } catch (e) {
      console.error('[api/bookings] Failed to read body:', e)
      throw createError({ statusCode: 400, message: 'Invalid request body' })
    }
    console.log('[api/bookings] POST to', url, 'body:', JSON.stringify(body, null, 2))
    try {
      const response = await $fetch<Booking>(url, {
        method: 'POST',
        headers: {
          Authorization: authHeader,
          'Content-Type': 'application/json'
        },
        body
      })
      return response
    } catch (error: any) {
      const status = error.statusCode || error.status || 500
      const errData = error.data || error.response?._data
      // Полный лог для отладки 500
      console.error('[api/bookings] Django error:', {
        status,
        url,
        message: error.message,
        data: errData,
        stack: error.stack?.slice(0, 500)
      })
      // Нормализуем data: если это объект с error/detail/message как boolean, заменяем на строку
      let safeData = errData
      if (errData && typeof errData === 'object') {
        safeData = { ...errData }
        if (typeof safeData.error === 'boolean') safeData.error = status === 500 ? 'Ошибка сервера' : 'Ошибка создания бронирования'
        if (typeof safeData.detail === 'boolean') safeData.detail = status === 500 ? 'Ошибка сервера' : 'Ошибка создания бронирования'
        if (typeof safeData.message === 'boolean') safeData.message = status === 500 ? 'Ошибка сервера' : 'Ошибка создания бронирования'
      }
      throw createError({
        statusCode: status,
        statusMessage: error.statusMessage || error.message,
        data: safeData || { error: status === 500 ? 'Ошибка сервера' : (error.message || 'Ошибка создания бронирования') }
      })
    }
  }

  throw createError({
    statusCode: 405,
    message: 'Method not allowed'
  })
})
