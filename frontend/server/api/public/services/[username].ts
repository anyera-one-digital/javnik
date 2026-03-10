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
    console.log('Fetching public services from Django:', url)
    const response = await $fetch<Service[]>(url)
    console.log('Django response type:', typeof response)
    console.log('Django response is array:', Array.isArray(response))
    console.log('Django response length:', Array.isArray(response) ? response.length : 'N/A')
    
    if (Array.isArray(response)) {
      console.log('Services received:', response.length)
      response.forEach((service, index) => {
        console.log(`  [${index}] ${service.name || 'Unknown'}: has_cover=${!!service.cover_image_url}, portfolio=${service.portfolio_images?.length || 0}`)
      })
    } else {
      console.log('Response is not an array:', response)
    }
    
    return response
  } catch (error: any) {
    console.error('Error fetching public services from Django:', error)
    console.error('Error status:', error.statusCode || error.status)
    console.error('Error data:', error.data)
    throw createError({
      statusCode: error.statusCode || 404,
      message: error.data?.error || 'Services not found'
    })
  }
})
