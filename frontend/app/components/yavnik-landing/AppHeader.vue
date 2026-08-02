<script setup lang="ts">
import { Menu, X } from '@lucide/vue'
import UserMenuHeader from '~/components/UserPersonalAccount/UserMenuHeader.vue'
import UserMenu from '~/components/UserPersonalAccount/UserMenu.vue'

const { isAuthenticated } = useAuth()

const open = ref(false)
const hidden = ref(false)
const mounted = ref(false)
const links = [
  { label: 'Возможности', href: '#showcase' },
  { label: 'Как работает', href: '#how' },
  { label: 'Для кого', href: '#audience' },
  { label: 'Стоимость', href: '#pricing' }
]

const showAuthMenu = computed(() => mounted.value && isAuthenticated.value)

const close = () => {
  open.value = false
}

let lastY = 0
let ticking = false

const onScroll = () => {
  if (ticking) return
  ticking = true
  requestAnimationFrame(() => {
    const y = window.scrollY
    const delta = y - lastY

    if (open.value || y < 24) {
      hidden.value = false
    }
    else if (delta > 8 && y > 80) {
      hidden.value = true
    }
    else if (delta < -4) {
      hidden.value = false
    }

    lastY = y
    ticking = false
  })
}

onMounted(() => {
  mounted.value = true
  lastY = window.scrollY
  window.addEventListener('scroll', onScroll, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})

watch(open, (isOpen) => {
  if (isOpen) hidden.value = false
})
</script>

<template>
  <header
    class="site-header"
    :class="{ 'is-hidden': hidden }"
  >
    <div class="container site-header__inner">
      <NuxtLink
        to="/"
        class="brand focus-ring"
        aria-label="Явьник — главная"
      >
        <span class="brand__mark">Я</span>
        <span>Явьник</span>
      </NuxtLink>

      <nav
        class="site-nav"
        aria-label="Основная навигация"
      >
        <a
          v-for="link in links"
          :key="link.href"
          :href="link.href"
        >{{ link.label }}</a>
      </nav>

      <div class="site-header__actions">
        <ThemeToggle />

        <UserMenuHeader
          v-if="showAuthMenu"
          class="site-header__user"
        />

        <template v-else>
          <NuxtLink
            class="login-link"
            to="/login"
          >
            Войти
          </NuxtLink>
          <UiButton
            to="/signup"
            size="md"
          >
            Создать страницу
          </UiButton>
        </template>

        <button
          class="menu-button focus-ring"
          type="button"
          :aria-expanded="open"
          aria-label="Открыть меню"
          @click="open = !open"
        >
          <X
            v-if="open"
            :size="20"
          />
          <Menu
            v-else
            :size="20"
          />
        </button>
      </div>
    </div>

    <Transition name="menu">
      <nav
        v-if="open"
        class="mobile-nav"
        aria-label="Мобильная навигация"
      >
        <a
          v-for="link in links"
          :key="link.href"
          :href="link.href"
          @click="close"
        >{{ link.label }}</a>

        <div
          v-if="showAuthMenu"
          class="mobile-nav__user"
        >
          <UserMenu :collapsed="false" />
        </div>
        <template v-else>
          <NuxtLink
            to="/login"
            @click="close"
          >
            Войти
          </NuxtLink>
          <UiButton
            to="/signup"
            size="lg"
            @click="close"
          >
            Создать страницу
          </UiButton>
        </template>
      </nav>
    </Transition>
  </header>
</template>
