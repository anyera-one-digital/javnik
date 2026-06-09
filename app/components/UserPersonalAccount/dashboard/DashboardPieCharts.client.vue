<script setup lang="ts">
import { format } from 'date-fns'
import { VisSingleContainer, VisDonut } from '@unovis/vue'
import type { Period, Range, AnalyticsServicesBreakdownResponse } from '~/types'
import { placeholderServicesBreakdown } from '~/utils/analyticsPlaceholders'

const props = defineProps<{
  period: Period
  range: Range
  locked?: boolean
}>()

const { getAuthHeaders } = useAuth()

type ChartItem = { label: string, value: number }

const bookingsByService = ref<ChartItem[]>([])
const revenueByService = ref<ChartItem[]>([])
const bookingsTotal = ref(0)
const revenueTotal = ref(0)
const loading = ref(true)

const chartColors = [
  'var(--ui-text-highlighted)',
  'var(--ui-text-muted)',
  'var(--ui-text-dimmed)',
  'var(--ui-border)',
  'var(--ui-bg-elevated)'
]

function getColor(_: ChartItem, i: number) {
  return chartColors[i % chartColors.length]
}

const itemValue = (d: ChartItem) => d.value

const formatRuble = (value: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(value)

function pluralBookings(n: number) {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'запись'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'записи'
  return 'записей'
}

async function loadBreakdown() {
  loading.value = true
  try {
    if (props.locked) {
      const placeholder = placeholderServicesBreakdown()
      bookingsByService.value = placeholder.bookingsByService
      revenueByService.value = placeholder.revenueByService
      bookingsTotal.value = placeholder.bookingsTotal
      revenueTotal.value = placeholder.revenueTotal
      return
    }

    const headers = getAuthHeaders()
    if (!headers.Authorization) {
      bookingsByService.value = []
      revenueByService.value = []
      bookingsTotal.value = 0
      revenueTotal.value = 0
      return
    }

    const response = await $fetch<AnalyticsServicesBreakdownResponse>(
      '/api/analytics/services-breakdown',
      {
        query: {
          start: format(props.range.start, 'yyyy-MM-dd'),
          end: format(props.range.end, 'yyyy-MM-dd')
        },
        headers
      }
    )

    bookingsByService.value = response.bookingsByService.items
    revenueByService.value = response.revenueByService.items
    bookingsTotal.value = response.bookingsByService.total
    revenueTotal.value = response.revenueByService.total
  } catch (e) {
    console.error('DashboardPieCharts: failed to load breakdown', e)
    bookingsByService.value = []
    revenueByService.value = []
    bookingsTotal.value = 0
    revenueTotal.value = 0
  } finally {
    loading.value = false
  }
}

watch(
  [() => props.period, () => props.range.start, () => props.range.end, () => props.locked],
  () => loadBreakdown(),
  { immediate: true }
)
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
    <UCard :ui="{ root: 'overflow-visible', body: '!px-0 !pt-6 !pb-4' }">
      <template #header>
        <div>
          <p class="text-xs text-muted uppercase mb-1.5">
            Виды записей
          </p>
          <p class="text-2xl text-highlighted font-semibold">
            <template v-if="loading">—</template>
            <template v-else>{{ bookingsTotal }} {{ pluralBookings(bookingsTotal) }}</template>
          </p>
        </div>
      </template>

      <div v-if="loading" class="h-64 flex items-center justify-center text-muted text-sm">
        Загрузка...
      </div>
      <div v-else-if="bookingsByService.length === 0" class="h-64 flex items-center justify-center text-muted text-sm text-center px-4">
        Нет записей за выбранный период
      </div>
      <div v-else class="flex flex-col items-center gap-4">
        <VisSingleContainer :data="bookingsByService" class="h-64 w-full">
          <VisDonut
            :value="itemValue"
            :color="getColor"
            arc-width="24"
            pad-angle="0.02"
          />
        </VisSingleContainer>
        <div class="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-muted px-2">
          <span v-for="(item, i) in bookingsByService" :key="`b-${i}`">
            {{ item.label }}: {{ item.value }}
          </span>
        </div>
      </div>
    </UCard>

    <UCard :ui="{ root: 'overflow-visible', body: '!px-0 !pt-6 !pb-4' }">
      <template #header>
        <div>
          <p class="text-xs text-muted uppercase mb-1.5">
            Доход по видам услуг
          </p>
          <p class="text-2xl text-highlighted font-semibold">
            <template v-if="loading">—</template>
            <template v-else>{{ formatRuble(revenueTotal) }}</template>
          </p>
        </div>
      </template>

      <div v-if="loading" class="h-64 flex items-center justify-center text-muted text-sm">
        Загрузка...
      </div>
      <div v-else-if="revenueByService.length === 0" class="h-64 flex items-center justify-center text-muted text-sm text-center px-4">
        Нет завершённых записей за период
      </div>
      <div v-else class="flex flex-col items-center gap-4">
        <VisSingleContainer :data="revenueByService" class="h-64 w-full">
          <VisDonut
            :value="itemValue"
            :color="getColor"
            arc-width="24"
            pad-angle="0.02"
          />
        </VisSingleContainer>
        <div class="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-muted px-2">
          <span v-for="(item, i) in revenueByService" :key="`r-${i}`">
            {{ item.label }}: {{ formatRuble(item.value) }}
          </span>
        </div>
      </div>
    </UCard>
  </div>
</template>

<style scoped>
:deep(.vis-single-container) {
  --vis-donut-central-label-text-color: var(--ui-text-highlighted);
  --vis-donut-central-sub-label-text-color: var(--ui-text-muted);
  --vis-dark-donut-central-label-text-color: var(--ui-text-highlighted);
  --vis-dark-donut-central-sub-label-text-color: var(--ui-text-muted);
  --vis-donut-background-color: var(--ui-bg-elevated);
  --vis-dark-donut-background-color: var(--ui-bg-elevated);
}
</style>
