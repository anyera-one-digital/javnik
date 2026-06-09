function isSignupTempUsername(username: string | undefined): boolean {
  return !!username && /^u_[a-f0-9]{12}$/.test(username)
}

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
      if (to.path === '/signup') {
        try {
          const u = JSON.parse(storedUser) as { username?: string }
          if (isSignupTempUsername(u.username)) {
            // Регистрация: после кода пользователь с временным username остаётся на /signup
          } else {
            return navigateTo('/schedule')
          }
        } catch {
          return navigateTo('/schedule')
        }
      } else {
        return navigateTo('/schedule')
      }
    }
  }

  // Если пользователь уже авторизован, перенаправляем на dashboard (кроме незавершённой регистрации)
  if (isAuthenticated.value) {
    if (to.path === '/signup' && isSignupTempUsername(user.value?.username)) {
      return
    }
    return navigateTo('/schedule')
  }
})
