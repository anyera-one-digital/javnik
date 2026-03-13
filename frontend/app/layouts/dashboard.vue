<script setup lang="ts">
import type { NavigationMenuItem } from '@nuxt/ui'
import type { Booking } from '~/types'
import { isSameDay, format, startOfDay, parse } from 'date-fns'
import ScheduleSidebarCalendar from '~/components/UserPersonalAccount/schedule/SidebarCalendar.vue'
import SidebarProfile from '~/components/UserPersonalAccount/SidebarProfile.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()

const open = ref(false)

// Нормализуем дату из query параметра
function parseDateFromQuery(dateStr: string | undefined): Date {
  if (!dateStr) return startOfDay(new Date())
  // Используем parse для правильной интерпретации даты в формате yyyy-MM-dd
  try {
    return startOfDay(parse(dateStr, 'yyyy-MM-dd', new Date()))
  } catch {
    return startOfDay(new Date())
  }
}

const selectedScheduleDate = ref<Date>(route.path === '/schedule' && route.query.date ? parseDateFromQuery(route.query.date as string) : startOfDay(new Date()))

const { getAuthHeaders } = useAuth()
const { data: scheduleBookings } = await useFetch<Booking[]>('/api/bookings/', {
  default: () => [],
  headers: () => getAuthHeaders()
})

function handleDateSelect(date: Date) {
  // Нормализуем дату перед сохранением
  const normalizedDate = startOfDay(date)
  selectedScheduleDate.value = normalizedDate
  // Используем format вместо toISOString для правильной работы с локальным временем
  const dateStr = format(normalizedDate, 'yyyy-MM-dd')
  if (route.path !== '/schedule') {
    router.push({
      path: '/schedule',
      query: {
        date: dateStr
      }
    })
  } else {
    router.push({
      query: {
        ...route.query,
        date: dateStr
      }
    })
  }
}

// Синхронизируем selectedScheduleDate с route.query.date
watch(() => route.query.date, (dateStr) => {
  if (dateStr && typeof dateStr === 'string' && route.path === '/schedule') {
    const newDate = parseDateFromQuery(dateStr)
    if (!isSameDay(newDate, selectedScheduleDate.value)) {
      selectedScheduleDate.value = newDate
    }
  }
}, { immediate: true })

const links = [[{
  label: 'Аналитика',
  icon: 'i-lucide-layout-dashboard',
  to: '/dashboard',
  onSelect: () => { open.value = false }
}, {
  label: 'Расписание',
  icon: 'i-lucide-calendar',
  to: '/schedule',
  onSelect: () => { open.value = false }
}, {
  label: 'Клиенты',
  icon: 'i-lucide-users',
  to: '/customers',
  onSelect: () => { open.value = false }
}]] satisfies NavigationMenuItem[][]

const { user, logout } = useAuth()

const middleLinks = computed<NavigationMenuItem[][]>(() => [[{
  label: 'Услуги',
  icon: 'i-lucide-scissors',
  to: '/services',
  onSelect: () => { open.value = false }
}, {
  label: 'График',
  icon: 'i-lucide-calendar-clock',
  to: '/work-schedule',
  onSelect: () => { open.value = false }
}]])

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
  <UDashboardGroup unit="rem" storage-key="dashboard-v3" class="dashboard-page">
    <UDashboardSidebar
      id="default"
      v-model:open="open"
      collapsible
      :default-size="23"
      :min-size="22.5"
      :max-size="24.5"
      class="bg-elevated/25"
    >
      <template #default="{ collapsed }">
        <div class="dashboard-sidebar-content flex flex-col flex-1 min-h-0 px-[36px]">
          <SidebarProfile :collapsed="collapsed" />

          <ScheduleSidebarCalendar
          v-if="!collapsed"
          :selected-date="selectedScheduleDate"
          :bookings="scheduleBookings"
          @update:selected-date="handleDateSelect"
          class="mb-2"
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
          :items="middleLinks[0]"
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

    <div class="flex-1 min-w-0 overflow-auto md:pr-[36px]">
      <slot />
    </div>
  </UDashboardGroup>
</template>
