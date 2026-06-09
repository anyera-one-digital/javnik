/**
 * Управление темой на публичных страницах (/booking/*).
 * Тема по умолчанию — системная (устройства клиента).
 * Переключение сохраняется отдельно от ЛК исполнителя (bookly-public-color-mode).
 */
const PUBLIC_STORAGE_KEY = 'bookly-public-color-mode'
const RESTORE_STORAGE_KEY = 'bookly-color-mode-restore'

export function usePublicPageColorMode() {
  const colorMode = useColorMode()

  /** Переключить тему (светлая ↔ тёмная) и сохранить для публичной страницы */
  function toggle() {
    const next = colorMode.value === 'dark' ? 'light' : 'dark'
    colorMode.preference = next
    if (import.meta.client) {
      localStorage.setItem(PUBLIC_STORAGE_KEY, next)
    }
  }

  return { toggle }
}

/** Применить тему публичной страницы при входе на /booking/* */
export function applyPublicPageColorMode() {
  if (!import.meta.client) return

  const colorMode = useColorMode()
  const saved = localStorage.getItem(PUBLIC_STORAGE_KEY)
  colorMode.preference = saved === 'light' || saved === 'dark' ? saved : 'system'
}

/** Сохранить текущую тему для восстановления при выходе с публичной страницы */
export function saveColorModeForRestore() {
  if (!import.meta.client) return

  const colorMode = useColorMode()
  sessionStorage.setItem(RESTORE_STORAGE_KEY, colorMode.preference || 'system')
}

/** Восстановить тему при выходе с публичной страницы */
export function restoreColorMode() {
  if (!import.meta.client) return

  const colorMode = useColorMode()
  const saved = sessionStorage.getItem(RESTORE_STORAGE_KEY)
  if (saved) {
    colorMode.preference = saved
    sessionStorage.removeItem(RESTORE_STORAGE_KEY)
  }
}
