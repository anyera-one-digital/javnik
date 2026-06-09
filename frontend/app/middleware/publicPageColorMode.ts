/**
 * Middleware для темы на публичных страницах /booking/*.
 * - При входе: сохраняем текущую тему, применяем тему публичной страницы (системная по умолчанию)
 * - При выходе: восстанавливаем сохранённую тему (для исполнителя, вернувшегося в ЛК)
 */
export default defineNuxtRouteMiddleware((to, from) => {
  if (import.meta.server) return

  const isBookingRoute = (path: string) => path.startsWith('/booking/')

  const toBooking = isBookingRoute(to.path)
  const fromBooking = from.path ? isBookingRoute(from.path) : false

  if (toBooking) {
    if (!fromBooking) {
    // Вход на публичную страницу — сохраняем текущую тему и применяем публичную
      saveColorModeForRestore()
    }
    applyPublicPageColorMode()
  } else if (fromBooking) {
    // Выход с публичной страницы — восстанавливаем тему
    restoreColorMode()
  }
})
