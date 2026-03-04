<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

defineProps<{
  collapsed?: boolean
}>()

const { user, logout, fetchProfile } = useAuth()

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
  label: 'Выйти',
  icon: 'i-lucide-log-out',
  onSelect: async () => {
    await logout()
  }
}]]))
</script>

<template>
  <UDropdownMenu
    :items="items"
    :content="{ align: 'center', collisionPadding: 12 }"
    :ui="{ content: collapsed ? 'w-48' : 'w-(--reka-dropdown-menu-trigger-width)' }"
  >
    <UButton
      :avatar="userAvatar ? { src: userAvatar, alt: userDisplayName } : undefined"
      :label="collapsed ? undefined : userDisplayName"
      :trailing-icon="collapsed ? undefined : 'i-lucide-chevrons-up-down'"
      color="neutral"
      variant="ghost"
      block
      :square="collapsed"
      class="data-[state=open]:bg-elevated"
      :ui="{
        trailingIcon: 'text-dimmed'
      }"
    />

    <template #chip-leading="{ item }">
      <div class="inline-flex items-center justify-center shrink-0 size-5">
        <span
          class="rounded-full ring ring-bg bg-(--chip-light) dark:bg-(--chip-dark) size-2"
          :style="{
            '--chip-light': `var(--color-${(item as any).chip}-500)`,
            '--chip-dark': `var(--color-${(item as any).chip}-400)`
          }"
        />
      </div>
    </template>
  </UDropdownMenu>
</template>
