<script setup lang="ts">
import { format } from 'date-fns'
import type { AnalyticsOverviewResponse, Period, Range } from '~/types'
import { placeholderOverview } from '~/utils/analyticsPlaceholders'
import DashboardBreakdownLists from '~/components/UserPersonalAccount/dashboard/DashboardBreakdownLists.vue'
import DashboardChart from '~/components/UserPersonalAccount/dashboard/DashboardChart.client.vue'

const props = defineProps<{
  period: Period
  range: Range
  locked?: boolean
}>()

const { getAuthHeaders } = useAuth()

const formatMoney = (value: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(value)

const rangeKey = computed(() => {
  const start = format(props.range.start, 'yyyy-MM-dd')
  const end = format(props.range.end, 'yyyy-MM-dd')
  return `${start}_${end}_${props.period}`
})

const { data, pending } = await useAsyncData<AnalyticsOverviewResponse>(
  () => `analytics-overview-${rangeKey.value}`,
  async () => {
    if (props.locked) return placeholderOverview(props.range)
    const headers = getAuthHeaders()
    if (!headers.Authorization) return placeholderOverview(props.range)
    return await $fetch<AnalyticsOverviewResponse>('/api/analytics/overview', {
      query: {
        start: format(props.range.start, 'yyyy-MM-dd'),
        end: format(props.range.end, 'yyyy-MM-dd'),
        period: props.period
      },
      headers
    })
  },
  {
    watch: [rangeKey, () => props.locked],
    default: () => placeholderOverview(props.range)
  }
)

const overview = computed(() => data.value)
</script>

<template>
  <div class="space-y-3">
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">
      <div class="analytics-card p-4 sm:p-5">
        <p class="text-xs text-muted mb-2">Доход</p>
        <p class="text-2xl sm:text-3xl font-semibold text-highlighted tracking-tight">
          <template v-if="pending">—</template>
          <template v-else>{{ formatMoney(overview.revenue.value) }}</template>
        </p>
      </div>

      <div class="analytics-card p-4 sm:p-5">
        <p class="text-xs text-muted mb-2">Записи</p>
        <p class="text-2xl sm:text-3xl font-semibold text-highlighted tracking-tight">
          <template v-if="pending">—</template>
          <template v-else>{{ overview.bookings.value }}</template>
        </p>
      </div>

      <div class="analytics-card p-4 sm:p-5">
        <p class="text-xs text-muted mb-2">Новые клиенты</p>
        <p class="text-2xl sm:text-3xl font-semibold text-highlighted tracking-tight">
          <template v-if="pending">—</template>
          <template v-else>{{ overview.newClients.value }}</template>
        </p>
      </div>

      <div class="analytics-card p-4 sm:p-5">
        <p class="text-xs text-muted mb-2">Успешно</p>
        <div class="flex items-end justify-between gap-3">
          <p class="text-2xl sm:text-3xl font-semibold text-highlighted tracking-tight">
            <template v-if="pending">—</template>
            <template v-else>
              {{ overview.completedBookings.value }}
              <span class="text-lg text-muted font-medium">из {{ overview.bookings.value }}</span>
            </template>
          </p>
          <div
            v-if="!pending"
            class="flex items-center gap-1.5 text-sm font-medium text-emerald-500"
          >
            <span class="size-1.5 rounded-full bg-emerald-500" />
            {{ overview.successRate }}%
          </div>
        </div>
      </div>
    </div>

    <ClientOnly>
      <DashboardChart
        :period="period"
        :range="range"
        :locked="locked"
      />
      <template #fallback>
        <div class="analytics-card h-96 flex items-center justify-center text-muted text-sm">
          Загрузка графика...
        </div>
      </template>
    </ClientOnly>

    <DashboardBreakdownLists
      :revenue-by-service="overview.revenueByService"
      :period-summary="overview.periodSummary"
      :clients-breakdown="overview.clientsBreakdown"
      :loading="pending"
    />
  </div>
</template>
