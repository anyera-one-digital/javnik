/**
 * Прокси POST для публичного создания бронирования.
 * POST /api/public/bookings/:username/create/
 */
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const username = getRouterParam(event, 'username')

  if (!username) {
    throw createError({ statusCode: 400, message: 'Username is required' })
  }

  const apiBase = config.apiBase || 'http://backend:8000'
  const url = `${apiBase}/api/public/bookings/${username}/create/`
  const body = await readBody(event)

  try {
    return await $fetch(url, {
      method: 'POST',
      body
    })
  } catch (error: any) {
    throw createError({
      statusCode: error.statusCode || error.status || 400,
      statusMessage: error.statusMessage || error.message,
      data: error.data || error.response?._data || { error: error.message || 'Ошибка создания бронирования' }
    })
  }
})
