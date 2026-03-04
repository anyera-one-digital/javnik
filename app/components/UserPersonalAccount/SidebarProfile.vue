<script setup lang="ts">
defineProps<{
  collapsed?: boolean
}>()

const { user, fetchProfile } = useAuth()
const colorMode = useColorMode()

function toggleTheme() {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}

// План подписки (пока заглушка, в будущем из API)
const subscriptionLabel = ref('Free')

onMounted(async () => {
  if (!user.value) await fetchProfile()
})

const displayName = computed(() => {
  if (!user.value) return 'Пользователь'
  return user.value.display_name || user.value.first_name || user.value.username || ''
})

const email = computed(() => user.value?.email || '')

const avatarUrl = computed(() => user.value?.avatar_url || undefined)

</script>

<template>
  <div v-if="!collapsed" class="pt-4 pb-2 pl-4 text-left">
    <div class="flex items-center justify-between gap-2 mb-[48px] pr-1">
      <NuxtLink :to="'/dashboard'" class="text-sm font-bold text-highlighted tracking-tight shrink-0">
        Явьник
      </NuxtLink>
      <UButton
        :icon="colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon'"
        color="neutral"
        variant="ghost"
        square
        size="xs"
        aria-label="Переключить тему"
        @click="toggleTheme"
      />
    </div>
    <NuxtLink
      to="/profile"
      class="flex items-center gap-2 min-w-0 cursor-pointer hover:opacity-80 transition-opacity rounded-lg -m-1 p-1"
    >
      <UAvatar
        :src="avatarUrl"
        :alt="displayName"
        size="sm"
        class="shrink-0"
      >
        <template v-if="displayName && !avatarUrl" #fallback>
          <span class="text-xs font-medium">
            {{ displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) }}
          </span>
        </template>
      </UAvatar>
      <div class="min-w-0 flex-1">
        <div class="flex items-center justify-between gap-1">
          <p class="text-xs font-medium text-highlighted truncate m-0">
            {{ displayName }}
          </p>
          <UIcon name="i-lucide-pencil" class="shrink-0 size-3 text-muted" aria-label="Редактировать профиль" />
        </div>
        <p class="text-xs text-muted truncate mt-0.5 m-0">
          {{ subscriptionLabel }}
          <span v-if="email" class="text-dimmed">·</span>
          {{ email }}
        </p>
      </div>
    </NuxtLink>
  </div>
</template>
