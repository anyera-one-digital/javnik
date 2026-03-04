<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

const { user, logout, fetchProfile } = useAuth()
const colorMode = useColorMode()
const router = useRouter()

// Загружаем профиль при монтировании, если его нет
onMounted(async () => {
  if (!user.value) {
    await fetchProfile()
  }
})

const userDisplayName = computed(() => {
  if (!user.value) return 'Пользователь'
  return user.value.display_name || user.value.first_name || user.value.username || user.value.email
})

const userAvatar = computed(() => {
  if (!user.value) return undefined
  return user.value.avatar_url || undefined
})

const items = computed<DropdownMenuItem[][]>(() => ([[{
  type: 'label',
  label: userDisplayName.value,
  avatar: userAvatar.value ? { src: userAvatar.value, alt: userDisplayName.value } : undefined
}], [{
  label: 'Моя страница',
  icon: 'i-lucide-user',
  onSelect: () => {
    if (user.value?.username) {
      window.open(`/booking/${user.value.username}`, '_blank')
    }
  }
}, {
  label: 'Оплата',
  icon: 'i-lucide-credit-card',
  to: '/payment'
}, {
  label: 'Настройки',
  icon: 'i-lucide-settings',
  to: '/settings'
}], [{
  label: 'Внешний вид',
  icon: 'i-lucide-sun-moon',
  children: [{
    label: 'Светлая',
    icon: 'i-lucide-sun',
    type: 'checkbox',
    checked: colorMode.value === 'light',
    onSelect(e: Event) {
      e.preventDefault()
      colorMode.preference = 'light'
    }
  }, {
    label: 'Тёмная',
    icon: 'i-lucide-moon',
    type: 'checkbox',
    checked: colorMode.value === 'dark',
    onUpdateChecked(checked: boolean) {
      if (checked) {
        colorMode.preference = 'dark'
      }
    },
    onSelect(e: Event) {
      e.preventDefault()
    }
  }]
}], [{
  label: 'Выйти',
  icon: 'i-lucide-log-out',
  onSelect: async () => {
    await logout()
    router.push('/')
  }
}]]))
</script>

<template>
  <UDropdownMenu
    :items="items"
    :content="{ align: 'end', collisionPadding: 12 }"
    :ui="{ content: 'w-56' }"
  >
    <UButton
      :avatar="userAvatar ? { src: userAvatar, alt: userDisplayName } : undefined"
      :label="userDisplayName"
      trailing-icon="i-lucide-chevron-down"
      color="neutral"
      variant="ghost"
      class="hidden lg:inline-flex"
      :ui="{
        trailingIcon: 'text-dimmed'
      }"
    />

    <!-- Мобильная версия - только аватар -->
    <UButton
      :avatar="userAvatar ? { src: userAvatar, alt: userDisplayName } : undefined"
      color="neutral"
      variant="ghost"
      square
      class="lg:hidden"
    />
  </UDropdownMenu>
</template>
