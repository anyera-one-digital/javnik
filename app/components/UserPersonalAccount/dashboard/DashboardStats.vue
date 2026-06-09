<script setup lang="ts">
import { format } from 'date-fns'
import type { Period, Range, Stat, AnalyticsStatsResponse } from '~/types'
import { placeholderStats } from '~/utils/analyticsPlaceholders'

const props = defineProps<{
  period: Period
  range: Range
  locked?: boolean
}>()

const { getAuthHeaders } = useAuth()

function statFromMetric(
  title: string,
  icon: string,
  metric: { value: number, variation: number },
  to?: string
): Stat {
  return { title, icon, value: metric.value, variation: metric.variation, to }
}

const rangeKey = computed(() => {
  const start = format(props.range.start, 'yyyy-MM-dd')
  const end = format(props.range.end, 'yyyy-MM-dd')
  return `${start}_${end}`
})

const { data: stats, pending } = await useAsyncData<Stat[]>(
  () => `dashboard-stats-${rangeKey.value}`,
  async () => {
    if (props.locked) {
      return placeholderStats()
    }

    const empty: AnalyticsStatsResponse = {
      newClients: { value: 0, variation: 0 },
      regularClients: { value: 0, variation: 0 },
      bookings: { value: 0, variation: 0 },
      completedBookings: { value: 0, variation: 0 }
    }

    let analytics = empty

    try {
      const headers = getAuthHeaders()
      if (headers.Authorization) {
        analytics = await $fetch<AnalyticsStatsResponse>('/api/analytics/stats', {
          query: {
            start: format(props.range.start, 'yyyy-MM-dd'),
            end: format(props.range.end, 'yyyy-MM-dd')
          },
          headers
        })
      }
    } catch (e) {
      console.error('DashboardStats: failed to load analytics', e)
    }

    return [
      statFromMetric('Новые клиенты', 'i-lucide-user-plus', analytics.newClients),
      statFromMetric('Постоянные клиенты', 'i-lucide-users', analytics.regularClients),
      statFromMetric('Записи', 'i-lucide-calendar-check', analytics.bookings, '/schedule'),
      statFromMetric('Успешные записи', 'i-lucide-circle-check-big', analytics.completedBookings, '/schedule')
    ]
  },
  {
    watch: [rangeKey, () => props.locked],
    default: () => []
  }
)
</script>

<template>
  <UPageGrid class="lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-px">
    <UPageCard
      v-for="(stat, index) in stats"
      :key="`${stat.title}-${index}`"
      :icon="stat.icon"
      :title="stat.title"
      :to="stat.to ?? '/customers'"
      variant="subtle"
      :ui="{
        container: 'gap-y-1.5',
        wrapper: 'items-start',
        leading: 'p-2.5 rounded-full bg-gray-900/10 dark:bg-white/10 ring ring-inset ring-gray-900/25 dark:ring-white/25 flex-col',
        leadingIcon: 'size-5 shrink-0 text-highlighted',
        title: 'font-normal text-muted text-xs uppercase'
      }"
      class="lg:rounded-none first:rounded-l-lg last:rounded-r-lg hover:z-1"
    >
      <div class="flex items-center gap-2">
        <span class="text-2xl font-semibold text-highlighted">
          <template v-if="pending">—</template>
          <template v-else>{{ stat.value }}</template>
        </span>

        <UBadge
          v-if="!pending"
          color="neutral"
          variant="subtle"
          class="text-xs"
        >
          {{ stat.variation > 0 ? '+' : '' }}{{ stat.variation }}%
        </UBadge>
      </div>
    </UPageCard>
  </UPageGrid>
</template>
