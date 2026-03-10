import type { Event } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const username = getRouterParam(event, 'username')
  const query = getQuery(event)

  if (!username) {
    throw createError({
      statusCode: 400,
      message: 'Username is required'
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  let url = `${apiBase}/api/public/events/${username}/`

  // Добавляем query параметры
  const params = new URLSearchParams()
  if (query.date) {
    params.append('date', query.date as string)
  }
  if (params.toString()) {
    url += `?${params.toString()}`
  }

  try {
    const response = await $fetch<Event[]>(url)
    return response
  } catch (error: any) {
    throw createError({
      statusCode: error.statusCode || 404,
      message: error.data?.error || 'Events not found'
    })
  }
})
