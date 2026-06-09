<script setup lang="ts">
import AppLogo from '~/components/LandingPage/AppLogo.vue'
import UserMenuHeader from '~/components/UserPersonalAccount/UserMenuHeader.vue'
import UserMenu from '~/components/UserPersonalAccount/UserMenu.vue'

const { isAuthenticated } = useAuth()

const mounted = ref(false)

onMounted(() => {
  mounted.value = true
})

const showAuthMenu = computed(() => mounted.value && isAuthenticated.value)

const items = computed(() => [])
</script>

<template>
  <UHeader>
    <template #left>
      <ULink
        to="/"
        class="inline-flex text-inherit no-underline hover:opacity-80"
      >
        <AppLogo class="w-auto h-6 shrink-0" />
      </ULink>
    </template>

    <UNavigationMenu
      v-if="items.length"
      :items="items"
      variant="link"
      class="header-nav"
    />

    <template #right>
      <UColorModeButton />

      <UserMenuHeader v-if="showAuthMenu" />

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
    </template>

    <template #body>
      <UNavigationMenu
        v-if="items.length"
        :items="items"
        orientation="vertical"
        class="-mx-2.5 header-nav"
      />

      <USeparator
        v-if="items.length"
        class="my-6"
      />

      <div
        v-if="showAuthMenu"
        class="px-2.5"
      >
        <UserMenu :collapsed="false" />
      </div>

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
    </template>
  </UHeader>
</template>
