<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const links = [[{
  label: 'Уведомления',
  icon: 'i-lucide-bell',
  to: '/settings/notifications'
}, {
  label: 'Безопасность',
  icon: 'i-lucide-shield',
  to: '/settings/security'
}]] satisfies NavigationMenuItem[][]
</script>

<template>
  <UDashboardPanel id="settings" :ui="{ body: 'lg:py-12' }">
    <template #header>
      <UDashboardNavbar title="Настройки">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>
      </UDashboardNavbar>

      <UDashboardToolbar>
        <!-- NOTE: The `-mx-1` class is used to align with the `DashboardSidebarCollapse` button here. -->
        <UNavigationMenu :items="links" highlight class="-mx-1 flex-1" />
      </UDashboardToolbar>
    </template>

    <template #body>
      <div class="flex flex-col gap-4 sm:gap-6 lg:gap-12 w-full mx-auto" :class="$route.path === '/settings/schedule' ? 'max-w-full' : 'lg:max-w-5xl'">
        <NuxtPage />
      </div>
    </template>
  </UDashboardPanel>
</template>
