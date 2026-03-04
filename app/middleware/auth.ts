export default defineNuxtRouteMiddleware((to, from) => {
  const { isAuthenticated } = useAuth()

  // Если пользователь не авторизован и пытается зайти на защищенную страницу
  if (!isAuthenticated.value) {
    // Сохраняем путь, на который пользователь хотел зайти
    return navigateTo({
      path: '/login',
      query: {
        redirect: to.fullPath
      }
    })
  }
})
