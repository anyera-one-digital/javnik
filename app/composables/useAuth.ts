import type { User } from '~/types'

interface AuthTokens {
  access: string
  refresh: string
}

interface AuthResponse {
  user: User
  tokens: AuthTokens
  message?: string
}

export const useAuth = () => {
  const config = useRuntimeConfig()
  const router = useRouter()
  const toast = useToast()

  // Состояние аутентификации
  const user = useState<User | null>('auth.user', () => null)
  const accessToken = useState<string | null>('auth.accessToken', () => null)
  const refreshToken = useState<string | null>('auth.refreshToken', () => null)

  // Функция для загрузки данных из localStorage
  const loadFromStorage = () => {
    if (process.client) {
      try {
        const storedAccessToken = localStorage.getItem('auth.accessToken')
        const storedRefreshToken = localStorage.getItem('auth.refreshToken')
        const storedUser = localStorage.getItem('auth.user')

        // Загружаем токены, даже если они уже есть (для синхронизации)
        if (storedAccessToken) {
          accessToken.value = storedAccessToken
        }
        if (storedRefreshToken) {
          refreshToken.value = storedRefreshToken
        }
        if (storedUser) {
          try {
            user.value = JSON.parse(storedUser)
          } catch {
            // Игнорируем ошибки парсинга
          }
        }
      } catch (error) {
        console.error('Error loading auth from localStorage:', error)
      }
    }
  }

  // Инициализация при первом использовании на клиенте
  if (process.client) {
    loadFromStorage()
    
    // Слушаем изменения в других вкладках
    window.addEventListener('storage', (e) => {
      if (e.key === 'auth.accessToken') {
        accessToken.value = e.newValue
      }
      if (e.key === 'auth.refreshToken') {
        refreshToken.value = e.newValue
      }
      if (e.key === 'auth.user') {
        try {
          user.value = e.newValue ? JSON.parse(e.newValue) : null
        } catch {
          user.value = null
        }
      }
    })
  }

  // Проверка авторизации
  const isAuthenticated = computed(() => {
    // На сервере всегда false
    if (process.server) {
      return false
    }
    
    // На клиенте проверяем наличие токена и пользователя
    // Если токен есть, но пользователя нет, пытаемся загрузить
    if (accessToken.value && !user.value) {
      loadFromStorage()
    }
    
    // Если пользователь есть, но токена нет, пытаемся загрузить
    if (user.value && !accessToken.value) {
      loadFromStorage()
    }
    
    // Если ничего нет, но в localStorage есть данные, загружаем
    if (!user.value && !accessToken.value && process.client) {
      const storedToken = localStorage.getItem('auth.accessToken')
      const storedUser = localStorage.getItem('auth.user')
      if (storedToken && storedUser) {
        loadFromStorage()
      }
    }
    
    return !!(user.value && accessToken.value)
  })

  // Сохранение в localStorage
  const saveAuth = (authData: AuthResponse) => {
    user.value = authData.user
    accessToken.value = authData.tokens.access
    refreshToken.value = authData.tokens.refresh

    if (process.client) {
      localStorage.setItem('auth.accessToken', authData.tokens.access)
      localStorage.setItem('auth.refreshToken', authData.tokens.refresh)
      localStorage.setItem('auth.user', JSON.stringify(authData.user))
      
      // Триггерим событие storage для синхронизации между вкладками
      window.dispatchEvent(new StorageEvent('storage', {
        key: 'auth.accessToken',
        newValue: authData.tokens.access
      }))
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

  // Регистрация (шаг 1 — email, телефон, пароль)
  const register = async (data: {
    email: string
    phone: string
    password: string
    password_confirm: string
    offer_accepted: boolean
    privacy_accepted: boolean
  }) => {
    try {
      const apiUrl = config.public.apiBase || 'http://localhost:8000'
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

  // Подтверждение email (шаг 2 регистрации)
  const verifyEmail = async (email: string, code: string) => {
    try {
      const apiUrl = config.public.apiBase || 'http://localhost:8000'
      const response = await $fetch<AuthResponse>(`${apiUrl}/api/auth/verify-email/`, {
        method: 'POST',
        body: { email, code }
      })

      saveAuth(response)
      toast.add({
        title: 'Регистрация завершена',
        description: response.message || 'Добро пожаловать!',
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
      const apiUrl = config.public.apiBase || 'http://localhost:8000'
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
      const apiUrl = config.public.apiBase || 'http://localhost:8000'
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
        await $fetch(`${config.public.apiBase}/api/auth/logout/`, {
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
      const response = await $fetch<{ access: string }>(`${config.public.apiBase}/api/auth/token/refresh/`, {
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

  // Завершение профиля (шаг 3 регистрации — username, имя, специальность)
  const completeProfile = async (data: {
    username: string
    first_name: string
    specialty_id?: number | null
  }) => {
    try {
      const profile = await $fetch<{ user: User; message: string }>(
        `${config.public.apiBase}/api/auth/profile/update/`,
        {
          method: 'PATCH',
          headers: getAuthHeaders(),
          body: {
            username: data.username,
            first_name: data.first_name,
            specialty_id: data.specialty_id ?? null
          }
        }
      )
      user.value = profile.user
      if (process.client) {
        localStorage.setItem('auth.user', JSON.stringify(profile.user))
      }
      return { success: true, user: profile.user }
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
      const profile = await $fetch<User>(`${config.public.apiBase}/api/auth/profile/`, {
        headers: getAuthHeaders()
      })
      user.value = profile
      if (process.client) {
        localStorage.setItem('auth.user', JSON.stringify(profile))
      }
      return profile
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
      const apiUrl = config.public.apiBase || 'http://localhost:8000'
      const token = accessToken.value
      
      if (process.client) {
        console.log('Uploading avatar to:', `${apiUrl}/api/auth/avatar/`)
        console.log('Token exists:', !!token)
      }
      
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
          color: 'red'
        })
        return { success: false, error: errorMessage }
      }

      const data = await response.json() as { user: User; message: string }

      user.value = data.user
      if (process.client) {
        localStorage.setItem('auth.user', JSON.stringify(data.user))
      }

      toast.add({
        title: 'Аватар загружен',
        description: data.message || 'Аватар успешно обновлен',
        color: 'green'
      })

      return { success: true, data }
    } catch (error: any) {
      const errorMessage = error instanceof Error ? error.message : 'Ошибка при загрузке аватара'
      
      toast.add({
        title: 'Ошибка загрузки',
        description: errorMessage,
        color: 'red'
      })
      return { success: false, error: errorMessage }
    }
  }

  return {
    user: readonly(user),
    accessToken: readonly(accessToken),
    refreshToken: readonly(refreshToken),
    isAuthenticated,
    register,
    verifyEmail,
    resendVerificationCode,
    completeProfile,
    login,
    logout,
    refreshAccessToken,
    getAuthHeaders,
    fetchProfile,
    uploadAvatar
  }
}
