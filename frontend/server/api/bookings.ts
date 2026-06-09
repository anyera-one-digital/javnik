import type { Booking } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)
  const query = getQuery(event)

  const headers = getHeaders(event)
  const authHeader = headers.authorization || headers.Authorization

  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  let url = `${apiBase}/api/bookings/`

  const params = new URLSearchParams()
  if (query.date) {
    params.append('date', query.date as string)
  }
  if (query.start_date) {
    params.append('start_date', query.start_date as string)
  }
  if (query.end_date) {
    params.append('end_date', query.end_date as string)
  }
  if (params.toString()) {
    url += `?${params.toString()}`
  }

  if (method === 'GET') {
    try {
      const response = await $fetch<any>(url, {
        headers: {
          Authorization: authHeader
        }
      })

      let bookings: Booking[] = []

      if (Array.isArray(response)) {
        bookings = response
      } else if (response && typeof response === 'object') {
        if (Array.isArray(response.results)) {
          bookings = response.results
        } else if (Array.isArray(response.data)) {
          bookings = response.data
        } else if (Array.isArray(response.bookings)) {
          bookings = response.bookings
        } else if (response.id) {
          bookings = [response]
        }
      }

      return bookings
    } catch (error: any) {
      console.error('Bookings API GET error:', error.statusCode || error.status, error.data)
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
      console.error('[api/bookings] Django POST error:', status, errData)
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
