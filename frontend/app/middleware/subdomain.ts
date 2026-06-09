export default defineNuxtRouteMiddleware((to, from) => {
  // Работает только на клиенте
  if (process.server) {
    return
  }

  // Получаем хост из window.location
  const host = window.location.hostname
  
  // Проверяем, является ли это поддоменом
  // Примеры: username.localhost, username.bookly.local
  const parts = host.split('.')
  
  // Определяем username из поддомена
  // Для localhost: username.localhost (3 части, первая - username)
  // Для других: username.domain.com (3+ части, первая - username)
  let username: string | null = null
  
  if (parts.length >= 2) {
    // Проверяем, не является ли первая часть localhost или 127
    if (parts[0] !== 'localhost' && parts[0] !== '127' && parts[0] !== 'www') {
      username = parts[0]
    }
  }
  
  // Если это поддомен и мы на странице публичного календаря
  if (username && to.path.startsWith('/booking/')) {
    // Если username в URL не совпадает с поддоменом, обновляем URL
    if (to.params.username !== username) {
      const query = to.query
      const newPath = `/booking/${username}`
      return navigateTo({
        path: newPath,
        query
      })
    }
  }
  
  // Если это поддомен и мы НЕ на странице публичного календаря, перенаправляем
  if (username && !to.path.startsWith('/booking/')) {
    return navigateTo({
      path: `/booking/${username}`,
      query: to.query
    })
  }
})
