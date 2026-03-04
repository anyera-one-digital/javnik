export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const method = getMethod(event)
  const username = getRouterParam(event, 'username')
  const query = getQuery(event)

  if (!username) {
    throw createError({
      statusCode: 400,
      message: 'Username is required'
    })
  }

  const apiBase = config.apiBase || config.public.apiBase || 'http://localhost:8000'
  let url = `${apiBase}/api/public/schedule/${username}/`

  // Добавляем query параметры
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
      const response = await $fetch<any>(url)
      
      // Обрабатываем разные форматы ответа
      let schedules: any[] = []
      
      if (Array.isArray(response)) {
        schedules = response
      } else if (response && typeof response === 'object') {
        if (Array.isArray(response.results)) {
          schedules = response.results
        } else if (Array.isArray(response.data)) {
          schedules = response.data
        } else if (Array.isArray(response.schedules)) {
          schedules = response.schedules
        } else if (response.id) {
          schedules = [response]
        }
      }
      
      return schedules
    } catch (error: any) {
      throw createError({
        statusCode: error.statusCode || error.status || 400,
        statusMessage: error.statusMessage || error.message,
        data: error.data || error.response?._data || { error: error.message || 'Ошибка загрузки графика работы' }
      })
    }
  }

  throw createError({
    statusCode: 405,
    message: 'Method not allowed'
  })
})
