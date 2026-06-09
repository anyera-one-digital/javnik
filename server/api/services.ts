import type { Service } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)

  const headers = getHeaders(event)
  let authHeader = headers.authorization || headers.Authorization

  if (authHeader && !authHeader.startsWith('Bearer ')) {
    authHeader = `Bearer ${authHeader}`
  }

  if (!authHeader) {
    throw createError({
      statusCode: 401,
      message: 'Unauthorized'
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/services/`

  if (method === 'GET') {
    try {
      const response = await $fetch<Service[]>(url, {
        headers: {
          Authorization: authHeader,
          'Content-Type': 'application/json',
          Accept: 'application/json'
        }
      })

      if (Array.isArray(response)) {
        return response
      }
      if (response && typeof response === 'object' && 'results' in response) {
        return (response as { results?: Service[] }).results || []
      }
      return []
    } catch (error: any) {
      console.error('Django GET services error:', error.statusCode || error.status, error.data)

      let errorData: any = { detail: 'Ошибка при загрузке услуг' }
      let statusCode = error.statusCode || error.status || 400

      if (error.data) {
        errorData = error.data
      } else if (error.response?.data || error.response?._data) {
        errorData = error.response.data || error.response._data
        statusCode = error.response.status || error.response.statusCode || statusCode
      }

      if (errorData && typeof errorData === 'object') {
        const errorText = JSON.stringify(errorData).toLowerCase()
        if (errorText.includes('token') || errorText.includes('authentication') || errorText.includes('unauthorized')) {
          statusCode = 401
        }
      }

      throw createError({
        statusCode,
        statusMessage: error.statusMessage || 'Bad Request',
        data: errorData,
        message: error.message || JSON.stringify(errorData)
      })
    }
  }

  if (method === 'POST') {
    const contentType = headers['content-type'] || headers['Content-Type'] || ''
    const isMultipart = contentType.includes('multipart/form-data')

    if (isMultipart) {
      try {
        const rawBody = await readRawBody(event, false)
        return await $fetch<Service>(url, {
          method: 'POST',
          headers: {
            Authorization: authHeader,
            'Content-Type': contentType
          },
          body: rawBody
        })
      } catch (error: any) {
        console.error('Django POST service (multipart) error:', error.statusCode || error.status, error.data)
        throw createError({
          statusCode: error.statusCode || error.status || 400,
          statusMessage: error.statusMessage || 'Bad Request',
          data: error.data || error.response?.data || { detail: 'Ошибка при создании услуги' },
          message: error.message
        })
      }
    }

    const body = await readBody(event)
    try {
      return await $fetch<Service>(url, {
        method: 'POST',
        headers: {
          Authorization: authHeader,
          'Content-Type': 'application/json'
        },
        body
      })
    } catch (error: any) {
      console.error('Django POST service error:', error.statusCode || error.status, error.data)
      throw createError({
        statusCode: error.statusCode || error.status || 400,
        statusMessage: error.statusMessage || 'Bad Request',
        data: error.data || error.response?.data || { detail: 'Ошибка при создании услуги' },
        message: error.message
      })
    }
  }

  throw createError({
    statusCode: 405,
    message: 'Method not allowed'
  })
})
