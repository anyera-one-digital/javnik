import type { User } from '~/types'

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const username = getRouterParam(event, 'username')

  if (!username) {
    throw createError({
      statusCode: 400,
      message: 'Username is required',
      fatal: false // Не вызываем редирект
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  const url = `${apiBase}/api/public/profile/${username}/`

  try {
    const response = await $fetch<User>(url)
    return response
  } catch (error: any) {
    // Возвращаем ошибку без fatal флага, чтобы не вызывать редирект
    throw createError({
      statusCode: error.statusCode || 404,
      statusMessage: error.data?.error || 'User not found',
      fatal: false // Важно: не вызываем редирект на страницу ошибки
    })
  }
})
