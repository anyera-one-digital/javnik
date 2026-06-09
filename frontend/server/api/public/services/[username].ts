import type { Service } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const username = getRouterParam(event, 'username')

  if (!username) {
    throw createError({
      statusCode: 400,
      message: 'Username is required'
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/public/services/${username}/`

  try {
    return await $fetch<Service[]>(url)
  } catch (error: any) {
    console.error('Error fetching public services:', error.statusCode || error.status, error.data)
    throw createError({
      statusCode: error.statusCode || 404,
      message: error.data?.error || 'Services not found'
    })
  }
})
