import type { Customer } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)
  const id = getRouterParam(event, 'id')

  if (!id) {
    throw createError({
      statusCode: 400,
      message: 'Customer ID is required'
    })
  }

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
  const url = `${apiBase}/api/customers/${id}/`

  if (method === 'PUT' || method === 'PATCH') {
    const body = await readBody(event)
    const response = await $fetch<Customer>(url, {
      method: method,
      headers: {
        Authorization: authHeader,
        'Content-Type': 'application/json'
      },
      body
    })
    return response
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
