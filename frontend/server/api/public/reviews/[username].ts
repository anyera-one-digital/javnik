import type { Review } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const username = getRouterParam(event, 'username')

  if (!username) {
    throw createError({
      statusCode: 400,
      message: 'Username is required',
      fatal: false
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/public/reviews/${username}/`

  try {
    const response = await $fetch<Review[]>(url)
    return response
  } catch (error: any) {
    throw createError({
      statusCode: error.statusCode || 404,
      statusMessage: error.data?.error || 'Reviews not found',
      fatal: false
    })
  }
})
