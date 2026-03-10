<script setup lang="ts">
import AppLogo from '~/components/LandingPage/AppLogo.vue'
import UserMenuHeader from '~/components/UserPersonalAccount/UserMenuHeader.vue'

const route = useRoute()
const router = useRouter()
const { isAuthenticated, user, accessToken } = useAuth()

// Состояние аутентификации с правильной инициализацией
const isAuth = ref(false)

// Инициализация и отслеживание изменений
onMounted(() => {
  // Функция для проверки и обновления состояния
  const updateAuthState = () => {
    if (process.client) {
      // Используем isAuthenticated из composable, который уже проверяет все правильно
      isAuth.value = isAuthenticated.value
    }
  }
  
  // Проверяем при монтировании
  updateAuthState()
  
  // Отслеживаем изменения isAuthenticated
  watch(isAuthenticated, (val) => {
    if (process.client) {
      isAuth.value = val
    }
  }, { immediate: true })
  
  // Также слушаем изменения в localStorage (для синхронизации между вкладками)
  if (process.client) {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key?.startsWith('auth.')) {
        // Небольшая задержка, чтобы дать composable обновиться
        setTimeout(() => {
          updateAuthState()
        }, 100)
      }
    }
    
    window.addEventListener('storage', handleStorageChange)
    
    // Очистка при размонтировании
    onUnmounted(() => {
      window.removeEventListener('storage', handleStorageChange)
    })
  }
  
})

const scrollToSection = (id: string) => {
  if (process.client) {
    if (route.path !== '/') {
      router.push(`/#${id}`)
      // Ждем перехода на главную страницу
      nextTick(() => {
        setTimeout(() => {
          const element = document.getElementById(id)
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        }, 300)
      })
    } else {
      const element = document.getElementById(id)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }
}

const items = computed(() => {
  const menuItems = [{
    label: 'Возможности',
    to: '/',
    exact: false,
    onSelect: (e: Event) => {
      e.preventDefault()
      scrollToSection('features')
    }
  }, {
    label: 'Преимущества',
    to: '/',
    exact: false,
    onSelect: (e: Event) => {
      e.preventDefault()
      scrollToSection('advantages')
    }
  }, {
    label: 'Отзывы',
    to: '/',
    exact: false,
    onSelect: (e: Event) => {
      e.preventDefault()
      scrollToSection('testimonials')
    }
  }, {
    label: 'Тарифы',
    to: '/',
    exact: false,
    onSelect: (e: Event) => {
      e.preventDefault()
      scrollToSection('pricing')
    }
  }, {
    label: 'FAQ',
    to: '/',
    exact: false,
    onSelect: (e: Event) => {
      e.preventDefault()
      scrollToSection('faq')
    }
  }]
  
  return menuItems
})
</script>

<template>
  <UHeader>
    <template #left>
      <NuxtLink to="/">
        <AppLogo class="w-auto h-6 shrink-0" />
      </NuxtLink>
    </template>

    <UNavigationMenu
      :items="items"
      variant="link"
      class="header-nav"
    />

    <template #right>
      <UColorModeButton />

      <ClientOnly>
        <!-- Для авторизованных пользователей показываем меню профиля -->
        <template v-if="isAuth">
          <UserMenuHeader />
        </template>

        <!-- Для неавторизованных пользователей показываем кнопки входа/регистрации -->
        <template v-else>
          <UButton
            icon="i-lucide-log-in"
            color="neutral"
            variant="ghost"
            to="/login"
            class="lg:hidden"
          />

          <UButton
            label="Войти"
            color="neutral"
            variant="outline"
            to="/login"
            class="hidden lg:inline-flex"
          />

          <UButton
            label="Регистрация"
            color="neutral"
            trailing-icon="i-lucide-arrow-right"
            class="hidden lg:inline-flex"
            to="/signup"
          />
        </template>

        <template #fallback>
          <!-- Показываем кнопки входа/регистрации во время загрузки -->
          <UButton
            icon="i-lucide-log-in"
            color="neutral"
            variant="ghost"
            to="/login"
            class="lg:hidden"
          />

          <UButton
            label="Войти"
            color="neutral"
            variant="outline"
            to="/login"
            class="hidden lg:inline-flex"
          />

          <UButton
            label="Регистрация"
            color="neutral"
            trailing-icon="i-lucide-arrow-right"
            class="hidden lg:inline-flex"
            to="/signup"
          />
        </template>
      </ClientOnly>
    </template>

    <template #body>
      <UNavigationMenu
        :items="items"
        orientation="vertical"
        class="-mx-2.5 header-nav"
      />

      <USeparator class="my-6" />

      <ClientOnly>
        <!-- Для авторизованных пользователей показываем меню профиля в мобильной версии -->
        <template v-if="isAuth">
          <div class="px-2.5">
            <UserMenu :collapsed="false" />
          </div>
        </template>

        <!-- Для неавторизованных пользователей показываем кнопки входа/регистрации -->
        <template v-else>
          <UButton
            label="Войти"
            color="neutral"
            variant="subtle"
            to="/login"
            block
            class="mb-3"
          />
          <UButton
            label="Регистрация"
            color="neutral"
            to="/signup"
            block
          />
        </template>

        <template #fallback>
          <!-- Показываем кнопки входа/регистрации во время загрузки -->
          <UButton
            label="Войти"
            color="neutral"
            variant="subtle"
            to="/login"
            block
            class="mb-3"
          />
          <UButton
            label="Регистрация"
            color="neutral"
            to="/signup"
            block
          />
        </template>
      </ClientOnly>
    </template>
  </UHeader>
</template>

<style scoped>
/* Жесткое переопределение стилей для навигации в хедере - темная тема (белый текст) */
:deep(.header-nav) a,
:deep(.header-nav) button,
:deep(.header-nav) [role="link"],
:deep(.header-nav) nav a,
:deep(.header-nav) ul a,
:deep(.header-nav) li a,
:deep(.header-nav) span,
:deep(.header-nav) [class*="text-primary"],
:deep(.header-nav) [class*="text-green"],
:deep(.header-nav) [class*="text-lime"],
:deep(.header-nav) [class*="ui-navigation-menu"] a,
:deep(.header-nav) [class*="ui-navigation-menu"] button,
:deep(.header-nav) [class*="ui-navigation-menu"] span {
  color: white !important;
  text-decoration: none !important;
  text-decoration-color: white !important;
  transition: text-decoration 0.2s ease !important;
  font-size: 0.8125rem !important; /* 13px - еще меньше */
}

:deep(.header-nav) a:hover,
:deep(.header-nav) button:hover,
:deep(.header-nav) [role="link"]:hover,
:deep(.header-nav) nav a:hover,
:deep(.header-nav) ul a:hover,
:deep(.header-nav) li a:hover,
:deep(.header-nav) [class*="ui-navigation-menu"] a:hover {
  color: white !important;
  text-decoration: underline !important;
  text-decoration-color: white !important;
  text-underline-offset: 4px !important;
}

:deep(.header-nav) a[aria-current="page"],
:deep(.header-nav) a.active,
:deep(.header-nav) [data-headlessui-state="active"],
:deep(.header-nav) [class*="active"] a {
  color: white !important;
  text-decoration: none !important;
  text-decoration-color: white !important;
}

/* Светлая тема - темный текст на светлом фоне */
:deep(.light .header-nav) a,
:deep(.light .header-nav) button,
:deep(.light .header-nav) [role="link"],
:deep(.light .header-nav) nav a,
:deep(.light .header-nav) ul a,
:deep(.light .header-nav) li a,
:deep(.light .header-nav) span,
:deep(.light .header-nav) [class*="text-primary"],
:deep(.light .header-nav) [class*="text-green"],
:deep(.light .header-nav) [class*="text-lime"],
:deep(.light .header-nav) [class*="ui-navigation-menu"] a,
:deep(.light .header-nav) [class*="ui-navigation-menu"] button,
:deep(.light .header-nav) [class*="ui-navigation-menu"] span {
  color: #1f2937 !important; /* dark gray для светлой темы */
  text-decoration: none !important;
  text-decoration-color: #1f2937 !important;
  transition: text-decoration 0.2s ease !important;
  font-size: 0.8125rem !important;
}

:deep(.light .header-nav) a:hover,
:deep(.light .header-nav) button:hover,
:deep(.light .header-nav) [role="link"]:hover,
:deep(.light .header-nav) nav a:hover,
:deep(.light .header-nav) ul a:hover,
:deep(.light .header-nav) li a:hover,
:deep(.light .header-nav) [class*="ui-navigation-menu"] a:hover {
  color: #1f2937 !important;
  text-decoration: underline !important;
  text-decoration-color: #1f2937 !important;
  text-underline-offset: 4px !important;
}

:deep(.light .header-nav) a[aria-current="page"],
:deep(.light .header-nav) a.active,
:deep(.light .header-nav) [data-headlessui-state="active"],
:deep(.light .header-nav) [class*="active"] a {
  color: #1f2937 !important;
  text-decoration: none !important;
  text-decoration-color: #1f2937 !important;
}
</style>
