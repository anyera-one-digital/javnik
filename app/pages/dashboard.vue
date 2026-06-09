<script setup lang="ts">
import { sub } from 'date-fns'
import type { Period, Range } from '~/types'
import DashboardAnalyticsLock from '~/components/UserPersonalAccount/dashboard/DashboardAnalyticsLock.vue'
import DashboardDateRangePicker from '~/components/UserPersonalAccount/dashboard/DashboardDateRangePicker.vue'
import DashboardPeriodSelect from '~/components/UserPersonalAccount/dashboard/DashboardPeriodSelect.vue'
import DashboardChart from '~/components/UserPersonalAccount/dashboard/DashboardChart.client.vue'
import DashboardPieCharts from '~/components/UserPersonalAccount/dashboard/DashboardPieCharts.client.vue'
import DashboardStats from '~/components/UserPersonalAccount/dashboard/DashboardStats.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const { hasProAccess, ensureSubscription } = useSubscription()

onMounted(() => {
  ensureSubscription()
})

const analyticsLocked = computed(() => !hasProAccess.value)

const range = shallowRef<Range>({
  start: sub(new Date(), { days: 14 }),
  end: new Date()
})
const period = ref<Period>('daily')
</script>

<template>
  <UDashboardPanel id="dashboard">
    <template #header>
      <UDashboardNavbar title="Аналитика" :ui="{ right: 'gap-3' }">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>

        <template #right>
          <DashboardDateRangePicker
            v-model="range"
            :disabled="analyticsLocked"
          />
          <DashboardPeriodSelect
            v-model="period"
            :range="range"
            :disabled="analyticsLocked"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <DashboardAnalyticsLock :locked="analyticsLocked">
        <DashboardStats
          :period="period"
          :range="range"
          :locked="analyticsLocked"
        />

        <ClientOnly>
          <DashboardChart
            :period="period"
            :range="range"
            :locked="analyticsLocked"
          />
          <template #fallback>
            <div class="h-96 w-full flex items-center justify-center text-muted">
              Загрузка графика...
            </div>
          </template>
        </ClientOnly>

        <ClientOnly>
          <DashboardPieCharts
            :period="period"
            :range="range"
            :locked="analyticsLocked"
          />
          <template #fallback>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
              <div class="h-64 w-full flex items-center justify-center text-muted rounded-lg border border-default">
                Загрузка диаграмм...
              </div>
              <div class="h-64 w-full flex items-center justify-center text-muted rounded-lg border border-default">
                Загрузка диаграмм...
              </div>
            </div>
          </template>
        </ClientOnly>
      </DashboardAnalyticsLock>
    </template>
  </UDashboardPanel>
</template>
