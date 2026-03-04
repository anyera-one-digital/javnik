import type { Booking } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({ statusCode: 400, message: 'Booking ID is required' })
  }

  const authHeader = getHeader(event, 'authorization') || getHeader(event, 'Authorization')
  if (!authHeader) {
    throw createError({ statusCode: 401, message: 'Unauthorized' })
  }
  const normalizedAuth = authHeader.startsWith('Bearer ') ? authHeader : `Bearer ${authHeader}`

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/bookings/${id}/`

  try {
    if (method === 'GET') {
      const response = await $fetch<Booking>(url, {
        headers: { Authorization: normalizedAuth, Accept: 'application/json' }
      })
      return response
    }

    if (method === 'PATCH' || method === 'PUT') {
      const body = await readBody(event)
      const response = await $fetch<Booking>(url, {
        method: method as 'PATCH' | 'PUT',
        headers: {
          Authorization: normalizedAuth,
          'Content-Type': 'application/json',
          Accept: 'application/json'
        },
        body
      })
      return response
    }

    if (method === 'DELETE') {
      await $fetch(url, {
        method: 'DELETE',
        headers: { Authorization: normalizedAuth, Accept: 'application/json' }
      })
      return { success: true }
    }

    throw createError({ statusCode: 405, message: 'Method not allowed' })
  } catch (error: any) {
    throw createError({
      statusCode: error.statusCode || error.status || 500,
      statusMessage: error.statusMessage || error.message,
      data: error.data || error.response?._data
    })
  }
})
