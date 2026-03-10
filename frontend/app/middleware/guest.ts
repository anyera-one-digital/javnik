export default defineNuxtRouteMiddleware((to, from) => {
  // Middleware работает только на клиенте
  if (process.server) {
    return
  }
  
  const { isAuthenticated, accessToken, user } = useAuth()
  
  // Проверяем наличие данных в localStorage, если состояние еще не инициализировано
  if (!isAuthenticated.value && process.client) {
    const storedToken = localStorage.getItem('auth.accessToken')
    const storedUser = localStorage.getItem('auth.user')
    
    if (storedToken && storedUser) {
      // Если данные есть в localStorage, но состояние не инициализировано,
      // значит пользователь авторизован, перенаправляем
      return navigateTo('/schedule')
    }
  }

  // Если пользователь уже авторизован, перенаправляем на dashboard
  if (isAuthenticated.value) {
    return navigateTo('/schedule')
  }
})
