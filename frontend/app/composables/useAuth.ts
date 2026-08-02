import type { User } from '~/types'
import { getClientApiBase, normalizeMediaUrl } from '~/utils/apiBase'

interface AuthTokens {
  access: string
  refresh: string
}

interface AuthResponse {
  user: User
  tokens: AuthTokens
  message?: string
}

function normalizeAuthUser(user: User): User {
  return {
    ...user,
    avatar_url: normalizeMediaUrl(user.avatar_url) ?? user.avatar_url
  }
}

function withCacheBuster(url: string, version: string | number = Date.now()): string {
  if (!import.meta.client || typeof window === 'undefined') {
    return url
  }

  try {
    const parsedUrl = new URL(url, window.location.origin)
    parsedUrl.searchParams.set('v', String(version))
    return parsedUrl.toString()
  } catch {
    const separator = url.includes('?') ? '&' : '?'
    return `${url}${separator}v=${encodeURIComponent(String(version))}`
  }
}

function waitForImageLoad(url: string): Promise<void> {
  if (!import.meta.client) {
    return Promise.resolve()
  }

  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve()
    image.onerror = () => reject(new Error('Файл аватара загружен, но не открывается по ссылке.'))
    image.src = url
  })
}

export const useAuth = () => {
  const config = useRuntimeConfig()
  const router = useRouter()
  const toast = useToast()

  const getApiUrl = () => {
    if (process.server) {
      return config.apiBase || 'http://backend:8000'
    }
    return getClientApiBase()
  }
  const accessToken = useState<string | null>('auth.accessToken', () => null)
  const refreshToken = useState<string | null>('auth.refreshToken', () => null)
  const user = useState<User | null>('auth.user', () => null)
  const storageListenerBound = useState<boolean>('auth.storageListenerBound', () => false)

  // Функция для загрузки данных из localStorage
  const loadFromStorage = () => {
    if (process.client) {
      try {
        const storedAccessToken = localStorage.getItem('auth.accessToken')
        const storedRefreshToken = localStorage.getItem('auth.refreshToken')
        const storedUser = localStorage.getItem('auth.user')

        // Не перезаписывать теми же значениями — иначе новый объект user → лишний re-render
        if (storedAccessToken && storedAccessToken !== accessToken.value) {
          accessToken.value = storedAccessToken
        }
        if (storedRefreshToken && storedRefreshToken !== refreshToken.value) {
          refreshToken.value = storedRefreshToken
        }
        if (storedUser) {
          try {
            const parsed = normalizeAuthUser(JSON.parse(storedUser))
            const prev = user.value
            const same =
              prev &&
              prev.id === parsed.id &&
              prev.email === parsed.email &&
              prev.username === parsed.username &&
              prev.avatar_url === parsed.avatar_url &&
              prev.phone === parsed.phone &&
              prev.first_name === parsed.first_name
            if (!same) {
              user.value = parsed
            }
          } catch {
            // Игнорируем ошибки парсинга
          }
        }
      } catch (error) {
        console.error('Error loading auth from localStorage:', error)
      }
    }
  }

  // Инициализация один раз на клиенте (не вешать storage на каждый вызов useAuth)
  if (process.client) {
    loadFromStorage()

    if (!storageListenerBound.value) {
      storageListenerBound.value = true
      window.addEventListener('storage', (e) => {
        if (e.key === 'auth.accessToken') {
          accessToken.value = e.newValue
        }
        if (e.key === 'auth.refreshToken') {
          refreshToken.value = e.newValue
        }
        if (e.key === 'auth.user') {
          try {
            user.value = e.newValue ? normalizeAuthUser(JSON.parse(e.newValue)) : null
          } catch {
            user.value = null
          }
        }
      })
    }
  }

  // Проверка авторизации (без side-effects в computed — только чтение)
  const isAuthenticated = computed(() => {
    if (process.server) {
      return false
    }
    return !!(user.value && accessToken.value)
  })

  // Сохранение в localStorage
  const saveAuth = (authData: AuthResponse) => {
    const normalizedUser = normalizeAuthUser(authData.user)
    user.value = normalizedUser
    accessToken.value = authData.tokens.access
    refreshToken.value = authData.tokens.refresh

    if (process.client) {
      localStorage.setItem('auth.accessToken', authData.tokens.access)
      localStorage.setItem('auth.refreshToken', authData.tokens.refresh)
      localStorage.setItem('auth.user', JSON.stringify(normalizedUser))
      // Не диспатчить StorageEvent в этом же окне — storage и так для других вкладок;
      // ручной dispatch давал лишние обновления refs в текущей вкладке.
    }
  }

  // Очистка данных аутентификации
  const clearAuth = () => {
    user.value = null
    accessToken.value = null
    refreshToken.value = null

    if (process.client) {
      localStorage.removeItem('auth.accessToken')
      localStorage.removeItem('auth.refreshToken')
      localStorage.removeItem('auth.user')
    }
  }

  // Регистрация (шаг 1 — email, имя, согласия; код → пароль → завершение профиля)
  const register = async (data: {
    email: string
    first_name: string
    offer_accepted: boolean
    privacy_accepted: boolean
  }) => {
    try {
      const apiUrl = getApiUrl()
      const response = await $fetch<AuthResponse & { needs_verification?: boolean; email?: string }>(`${apiUrl}/api/auth/register/`, {
        method: 'POST',
        body: data
      })

      if (response.needs_verification && response.email) {
        toast.add({
          title: 'Проверьте почту',
          description: response.message || 'Введите код из письма',
          color: 'green'
        })
        return { success: true, needsVerification: true, email: response.email, data: response }
      }

      saveAuth(response)
      toast.add({
        title: 'Успешная регистрация',
        description: response.message || 'Добро пожаловать!',
        color: 'green'
      })
      return { success: true, data: response }
    } catch (error: any) {
      const data = error.data
      let errorMessage = data?.detail || data?.message || 'Ошибка при регистрации'
      if (typeof data === 'object' && !Array.isArray(data) && typeof data?.detail !== 'string') {
        const messages = Object.values(data).flat().filter(Boolean)
        if (messages.length > 0) {
          errorMessage = messages.join('. ')
        }
      }
      toast.add({
        title: 'Ошибка регистрации',
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        color: 'red'
      })
      return { success: false, error: errorMessage }
    }
  }

  const registerCredentials = async (data: { password: string; password_confirm: string }) => {
    try {
      const response = await $fetch<{ user: User; message?: string }>(`${getApiUrl()}/api/auth/register/credentials/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: data
      })
      const normalizedUser = normalizeAuthUser(response.user)
      user.value = normalizedUser
      if (process.client) {
        localStorage.setItem('auth.user', JSON.stringify(normalizedUser))
      }
      toast.add({
        title: 'Пароль сохранён',
        description: response.message || 'Продолжите заполнение профиля',
        color: 'green'
      })
      return { success: true, data: response }
    } catch (error: any) {
      const dataErr = error.data
      let errorMessage = dataErr?.detail || dataErr?.message || 'Ошибка'
      if (typeof dataErr === 'object' && !Array.isArray(dataErr) && typeof dataErr?.detail !== 'string') {
        const messages = Object.values(dataErr).flat().filter(Boolean)
        if (messages.length > 0) errorMessage = messages.join('. ')
      }
      toast.add({
        title: 'Ошибка',
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        color: 'red'
      })
      return { success: false, error: errorMessage }
    }
  }

  // Подтверждение email (шаг 2 регистрации)
  const verifyEmail = async (email: string, code: string) => {
    try {
      const apiUrl = getApiUrl()
      const response = await $fetch<AuthResponse>(`${apiUrl}/api/auth/verify-email/`, {
        method: 'POST',
        body: { email, code }
      })

      saveAuth(response)
      toast.add({
        title: 'Email подтверждён',
        description: response.message || 'Установите пароль',
        color: 'green'
      })
      return { success: true, data: response }
    } catch (error: any) {
      const errorMessage = error.data?.detail || error.data?.error || 'Неверный код'
      toast.add({
        title: 'Ошибка',
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        color: 'red'
      })
      return { success: false, error: errorMessage }
    }
  }

  // Повторная отправка кода подтверждения
  const resendVerificationCode = async (email: string) => {
    try {
      const apiUrl = getApiUrl()
      await $fetch<{ message: string }>(`${apiUrl}/api/auth/resend-verification/`, {
        method: 'POST',
        body: { email }
      })
      toast.add({
        title: 'Код отправлен',
        description: 'Проверьте почту',
        color: 'green'
      })
      return { success: true }
    } catch (error: any) {
      const errorMessage = error.data?.detail || error.data?.error || 'Ошибка'
      toast.add({
        title: 'Ошибка',
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        color: 'red'
      })
      return { success: false, error: errorMessage }
    }
  }

  // Вход
  const login = async (email: string, password: string) => {
    try {
      const apiUrl = getApiUrl()
      const response = await $fetch<AuthResponse & { needs_verification?: boolean; email?: string }>(`${apiUrl}/api/auth/login/`, {
        method: 'POST',
        body: { email, password }
      })

      if (response.needs_verification && response.email) {
        toast.add({
          title: 'Подтвердите email',
          description: response.message || 'Введите код из письма',
          color: 'green'
        })
        return { success: false, needsVerification: true, email: response.email, data: response }
      }

      saveAuth(response)
      toast.add({
        title: 'Успешный вход',
        description: response.message || 'Добро пожаловать!',
        color: 'green'
      })
      return { success: true, data: response }
    } catch (error: any) {
      const errorMessage = error.data?.detail || error.data?.message || 'Неверный email или пароль'
      toast.add({
        title: 'Ошибка входа',
        description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
        color: 'red'
      })
      return { success: false, error: errorMessage }
    }
  }

  // Выход
  const logout = async () => {
    try {
      if (refreshToken.value) {
        await $fetch(`${getApiUrl()}/api/auth/logout/`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${accessToken.value}`
          },
          body: {
            refresh_token: refreshToken.value
          }
        })
      }
    } catch (error) {
      // Игнорируем ошибки при выходе
      console.error('Logout error:', error)
    } finally {
      clearAuth()
      toast.add({
        title: 'Выход выполнен',
        description: 'Вы успешно вышли из системы',
        color: 'green'
      })
      router.push('/login')
    }
  }

  // Обновление токена
  const refreshAccessToken = async () => {
    if (!refreshToken.value) {
      return false
    }

    try {
      const response = await $fetch<{ access: string }>(`${getApiUrl()}/api/auth/token/refresh/`, {
        method: 'POST',
        body: {
          refresh: refreshToken.value
        }
      })

      accessToken.value = response.access
      if (process.client) {
        localStorage.setItem('auth.accessToken', response.access)
      }
      return true
    } catch (error) {
      clearAuth()
      router.push('/login')
      return false
    }
  }

  // Получение заголовков для API запросов
  const getAuthHeaders = () => {
    // На сервере токен не нужен, так как запросы идут через Nuxt server API
    if (process.server) {
      return {}
    }
    
    // На клиенте загружаем токен из localStorage, если его нет в состоянии
    if (process.client && !accessToken.value) {
      loadFromStorage()
    }
    
    // Проверяем наличие токена
    if (!accessToken.value) {
      return {}
    }
    
    // Нормализуем токен (убираем "Bearer " если есть)
    const token = accessToken.value.startsWith('Bearer ') 
      ? accessToken.value.slice(7) 
      : accessToken.value
    
    return {
      Authorization: `Bearer ${token}`
    }
  }

  // Частичное обновление профиля (шаблон графика и т.д.)
  const patchProfile = async (body: Record<string, unknown>) => {
    try {
      const profile = await $fetch<{ user: User; message: string }>(
        `${getApiUrl()}/api/auth/profile/update/`,
        {
          method: 'PATCH',
          headers: getAuthHeaders(),
          body
        }
      )
      const normalizedUser = normalizeAuthUser(profile.user)
      user.value = normalizedUser
      if (process.client) {
        localStorage.setItem('auth.user', JSON.stringify(normalizedUser))
      }
      return { success: true, user: normalizedUser }
    } catch (error: any) {
      const dataErr = error.data
      let errorMessage = dataErr?.detail || dataErr?.message || 'Ошибка при сохранении'
      if (typeof dataErr === 'object' && !Array.isArray(dataErr) && typeof dataErr?.detail !== 'string') {
        const messages = Object.values(dataErr).flat().filter(Boolean)
        if (messages.length > 0) errorMessage = messages.join('. ')
      }
      toast.add({ title: 'Ошибка', description: errorMessage, color: 'red' })
      return { success: false, error: errorMessage }
    }
  }

  // Завершение профиля (после пароля — телефон, username, специальность; имя задано на шаге 1)
  const completeProfile = async (data: {
    phone: string
    username: string
    specialty_id?: number | null
    work_schedule_template?: string
    shift_cycle?: string
    shift_anchor_date?: string | null
  }) => {
    try {
      const body: Record<string, unknown> = {
        phone: data.phone,
        username: data.username,
        specialty_id: data.specialty_id ?? null
      }
      if (data.work_schedule_template !== undefined) {
        body.work_schedule_template = data.work_schedule_template
      }
      if (data.shift_cycle !== undefined) {
        body.shift_cycle = data.shift_cycle
      }
      if (data.shift_anchor_date !== undefined) {
        body.shift_anchor_date = data.shift_anchor_date
      }
      const profile = await $fetch<{ user: User; message: string }>(
        `${getApiUrl()}/api/auth/profile/update/`,
        {
          method: 'PATCH',
          headers: getAuthHeaders(),
          body
        }
      )
      const normalizedUser = normalizeAuthUser(profile.user)
      user.value = normalizedUser
      if (process.client) {
        localStorage.setItem('auth.user', JSON.stringify(normalizedUser))
      }
      return { success: true, user: normalizedUser }
    } catch (error: any) {
      const dataErr = error.data
      let errorMessage = dataErr?.detail || dataErr?.message || 'Ошибка при сохранении'
      if (typeof dataErr === 'object' && !Array.isArray(dataErr) && typeof dataErr?.detail !== 'string') {
        const messages = Object.values(dataErr).flat().filter(Boolean)
        if (messages.length > 0) errorMessage = messages.join('. ')
      }
      toast.add({ title: 'Ошибка', description: errorMessage, color: 'red' })
      return { success: false, error: errorMessage }
    }
  }

  // Загрузка профиля пользователя
  const fetchProfile = async () => {
    if (!accessToken.value) {
      return null
    }

    try {
      const profile = await $fetch<User>(`${getApiUrl()}/api/auth/profile/`, {
        headers: getAuthHeaders()
      })
      const normalizedProfile = normalizeAuthUser(profile)
      user.value = normalizedProfile
      if (process.client) {
        localStorage.setItem('auth.user', JSON.stringify(normalizedProfile))
      }
      return normalizedProfile
    } catch (error) {
      // Если токен невалидный, пытаемся обновить
      if (await refreshAccessToken()) {
        return fetchProfile()
      }
      return null
    }
  }

  // Загрузка аватара
  const uploadAvatar = async (file: File) => {
    if (!accessToken.value) {
      // Пытаемся обновить токен перед загрузкой
      const refreshed = await refreshAccessToken()
      if (!refreshed) {
        return { success: false, error: 'Не авторизован. Пожалуйста, войдите снова.' }
      }
    }

    try {
      const formData = new FormData()
      formData.append('avatar', file)

      // Используем fetch напрямую для FormData, так как $fetch может некорректно обрабатывать заголовки
      const apiUrl = getApiUrl()
      const token = accessToken.value
      
      const response = await fetch(`${apiUrl}/api/auth/avatar/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
          // Не устанавливаем Content-Type - браузер сам установит с boundary для FormData
        },
        body: formData
      })

      if (!response.ok) {
        let errorMessage = 'Ошибка загрузки аватара'
        try {
          const errorData = await response.json()
          errorMessage = errorData.error || errorData.detail || errorMessage
        } catch {
          errorMessage = `Ошибка ${response.status}: ${response.statusText}`
        }
        
        toast.add({
          title: 'Ошибка загрузки',
          description: errorMessage,
          color: 'error'
        })
        return { success: false, error: errorMessage }
      }

      const data = await response.json() as { user: User; message: string }

      const normalizedAvatarUrl = normalizeMediaUrl(data.user?.avatar_url) ?? data.user?.avatar_url
      if (!normalizedAvatarUrl) {
        throw new Error('Сервер не вернул ссылку на загруженный аватар.')
      }

      const displayAvatarUrl = withCacheBuster(normalizedAvatarUrl, data.user.updated_at || Date.now())
      await waitForImageLoad(displayAvatarUrl)

      const updatedUser = user.value
        ? {
            ...user.value,
            avatar: data.user.avatar,
            avatar_url: displayAvatarUrl,
            updated_at: data.user.updated_at
          }
        : normalizeAuthUser({ ...data.user, avatar_url: displayAvatarUrl })

      user.value = updatedUser
      if (process.client) {
        localStorage.setItem('auth.user', JSON.stringify(updatedUser))
      }

      toast.add({
        title: 'Аватар загружен',
        description: data.message || 'Аватар успешно обновлен',
        color: 'success'
      })

      return { success: true, data, user: updatedUser }
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Ошибка при загрузке аватара'
      
      toast.add({
        title: 'Ошибка загрузки',
        description: errorMessage,
        color: 'error'
      })
      return { success: false, error: errorMessage }
    }
  }

  const deleteAccount = async (username: string) => {
    try {
      await $fetch(`${getApiUrl()}/api/auth/account/delete/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: { username }
      })
      clearAuth()
      await router.push('/')
      return { success: true as const }
    } catch (error: unknown) {
      const err = error as {
        data?: Record<string, unknown>
        statusMessage?: string
      }
      const data = err.data
      const apiError = typeof data?.error === 'string' ? data.error : undefined
      const detail = typeof data?.detail === 'string' ? data.detail : undefined
      const usernameErrors = data?.username
      const errorMessage = apiError
        ?? detail
        ?? (Array.isArray(usernameErrors) ? String(usernameErrors[0]) : undefined)
        ?? err.statusMessage
        ?? 'Не удалось удалить аккаунт'
      return { success: false as const, error: errorMessage }
    }
  }

  return {
    user: readonly(user),
    accessToken: readonly(accessToken),
    refreshToken: readonly(refreshToken),
    isAuthenticated,
    register,
    registerCredentials,
    verifyEmail,
    resendVerificationCode,
    completeProfile,
    patchProfile,
    login,
    logout,
    deleteAccount,
    refreshAccessToken,
    getAuthHeaders,
    fetchProfile,
    uploadAvatar
  }
}
