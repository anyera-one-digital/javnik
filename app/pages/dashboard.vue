<script setup lang="ts">
import { sub } from 'date-fns'
import type { Period, Range } from '~/types'
import DashboardDateRangePicker from '~/components/UserPersonalAccount/dashboard/DashboardDateRangePicker.vue'
import DashboardPeriodSelect from '~/components/UserPersonalAccount/dashboard/DashboardPeriodSelect.vue'
import DashboardChart from '~/components/UserPersonalAccount/dashboard/DashboardChart.client.vue'
import DashboardPieCharts from '~/components/UserPersonalAccount/dashboard/DashboardPieCharts.client.vue'
import DashboardSales from '~/components/UserPersonalAccount/dashboard/DashboardSales.vue'
import DashboardStats from '~/components/UserPersonalAccount/dashboard/DashboardStats.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const range = shallowRef<Range>({
  start: sub(new Date(), { days: 14 }),
  end: new Date()
})
const period = ref<Period>('daily')
</script>

<template>
  <UDashboardPanel id="dashboard">
    <template #header>
      <UDashboardNavbar title="Главная" :ui="{ right: 'gap-3' }">
        <template #leading>
          <div class="hidden">
            <UDashboardSidebarCollapse />
          </div>
        </template>

        <template #right>
          <DashboardDateRangePicker v-model="range" />

          <DashboardPeriodSelect v-model="period" :range="range" />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <DashboardStats :period="period" :range="range" />
      <ClientOnly>
        <DashboardChart :period="period" :range="range" />
        <template #fallback>
          <div class="h-96 w-full flex items-center justify-center text-muted">
            Загрузка графика...
          </div>
        </template>
      </ClientOnly>
      <ClientOnly>
        <DashboardPieCharts :period="period" :range="range" />
        <template #fallback>
          <div class="h-64 w-full flex items-center justify-center text-muted">
            Загрузка диаграмм...
          </div>
        </template>
      </ClientOnly>
      <DashboardSales :period="period" :range="range" />
    </template>
  </UDashboardPanel>
</template>
