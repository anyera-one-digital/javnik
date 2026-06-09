<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import type { Booking } from '~/types'
import { startOfDay } from 'date-fns'
import ScheduleSidebarCalendar from '~/components/UserPersonalAccount/schedule/SidebarCalendar.vue'
import SidebarProfile from '~/components/UserPersonalAccount/SidebarProfile.vue'

const toast = useToast()

const open = ref(false)

const isDashboardMobile = useMediaQuery('(max-width: 767px)')
const colorMode = useColorMode()

function toggleSidebarTheme() {
  colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'
}

const { selectedDate: selectedScheduleDate, pushScheduleDate } = useSchedulePageDate()

const { getAuthHeaders } = useAuth()
const { data: scheduleBookings } = await useFetch<Booking[]>('/api/bookings/', {
  default: () => [],
  headers: () => getAuthHeaders()
})

function handleDateSelect(date: Date) {
  void pushScheduleDate(startOfDay(date)).catch(() => {})
}

const links = [[{
  label: 'Расписание',
  icon: 'i-lucide-calendar',
  to: '/schedule',
  onSelect: () => { open.value = false }
}, {
  label: 'Аналитика',
  icon: 'i-lucide-layout-dashboard',
  to: '/dashboard',
  onSelect: () => { open.value = false }
}, {
  label: 'Клиенты',
  icon: 'i-lucide-users',
  to: '/customers',
  onSelect: () => { open.value = false }
}, {
  label: 'Услуги',
  icon: 'i-lucide-scissors',
  to: '/services',
  onSelect: () => { open.value = false }
}]] satisfies NavigationMenuItem[][]

const { user, logout } = useAuth()

const accountLinks = computed<NavigationMenuItem[][]>(() => [[{
  label: 'Тарифный план',
  icon: 'i-lucide-credit-card',
  to: '/payment',
  onSelect: () => { open.value = false }
}, {
  label: 'Настройки',
  icon: 'i-lucide-settings',
  to: '/settings',
  onSelect: () => { open.value = false }
}]])

const accountBottomLinks = computed<NavigationMenuItem[][]>(() => [[{
  label: 'Выйти',
  icon: 'i-lucide-log-out',
  onSelect: async () => {
    open.value = false
    await logout()
  }
}]])

onMounted(async () => {
  const cookie = useCookie('cookie-consent')
  if (cookie.value === 'accepted') {
    return
  }

  toast.add({
    title: 'Мы используем собственные cookies для улучшения вашего опыта на нашем сайте.',
    duration: 0,
    close: false,
    actions: [{
      label: 'Принять',
      color: 'neutral',
      variant: 'outline',
      onClick: () => {
        cookie.value = 'accepted'
      }
    }, {
      label: 'Отказаться',
      color: 'neutral',
      variant: 'ghost'
    }]
  })
})
</script>

<template>
  <UDashboardGroup
    unit="rem"
    storage-key="dashboard-v3"
    class="dashboard-page !items-stretch w-full min-h-0"
  >
    <UDashboardSidebar
      id="default"
      v-model:open="open"
      collapsible
      :default-size="23"
      :min-size="22.5"
      :max-size="24.5"
      class="bg-elevated/25 h-full min-h-0 self-stretch"
      :ui="{ header: 'max-md:flex max-md:items-center max-md:gap-2 max-md:px-4 max-md:py-3 max-md:border-b max-md:border-default' }"
    >
      <template v-if="isDashboardMobile" #header>
        <div class="flex flex-1 items-center gap-2 min-w-0">
          <NuxtLink
            to="/schedule"
            class="text-sm font-bold text-highlighted tracking-tight shrink-0"
            @click="open = false"
          >
            Явьник
          </NuxtLink>
          <UButton
            :icon="colorMode.value === 'dark' ? 'i-lucide-sun' : 'i-lucide-moon'"
            color="neutral"
            variant="ghost"
            square
            size="xs"
            class="ml-auto shrink-0"
            aria-label="Переключить тему"
            @click="toggleSidebarTheme"
          />
        </div>
      </template>

      <template #default="{ collapsed }">
        <div class="dashboard-sidebar-content flex h-full min-h-0 flex-col flex-1 overflow-y-auto px-[36px]">
          <SidebarProfile :collapsed="collapsed" />

          <ScheduleSidebarCalendar
            v-if="!collapsed"
            :selected-date="selectedScheduleDate"
            :bookings="scheduleBookings"
            class="mb-2"
            @update:selected-date="handleDateSelect"
          />

          <UNavigationMenu
            :collapsed="collapsed"
            :items="links[0]"
            orientation="vertical"
            color="neutral"
            tooltip
            popover
            class="px-4 mb-0"
            :ui="{ item: 'text-[10px] py-0', list: 'gap-0', linkLeadingIcon: 'shrink-0 size-[15px]' }"
          />

          <div class="border-t border-default my-[8px] mx-4" />

          <UNavigationMenu
            :collapsed="collapsed"
            :items="accountLinks[0]"
            orientation="vertical"
            color="neutral"
            tooltip
            popover
            class="px-4 mb-0"
            :ui="{ item: 'text-[10px] py-0', list: 'gap-0', linkLeadingIcon: 'shrink-0 size-[15px]' }"
          />

          <div class="border-t border-default my-[8px] mx-4" />

          <UNavigationMenu
            :collapsed="collapsed"
            :items="accountBottomLinks[0]"
            orientation="vertical"
            color="neutral"
            tooltip
            popover
            class="px-4 mb-0"
            :ui="{ item: 'text-[10px] py-0', list: 'gap-0', linkLeadingIcon: 'shrink-0 size-[15px]' }"
          />
        </div>
      </template>
    </UDashboardSidebar>

    <div class="h-full min-h-0 min-w-0 flex-1 self-stretch overflow-auto md:pr-[36px]">
      <slot />
    </div>
  </UDashboardGroup>
</template>
