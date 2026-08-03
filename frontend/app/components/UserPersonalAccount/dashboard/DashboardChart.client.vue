<script setup lang="ts">
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { VisXYContainer, VisLine, VisAxis, VisArea, VisCrosshair, VisTooltip } from '@unovis/vue'
import type { Period, Range, AnalyticsRevenueMode, AnalyticsRevenueResponse } from '~/types'
import { placeholderRevenuePoints } from '~/utils/analyticsPlaceholders'

const ACCENT = '#8b5cf6'

const props = defineProps<{
  period: Period
  range: Range
  locked?: boolean
}>()

const cardRef = useTemplateRef<HTMLElement | null>('cardRef')
const { getAuthHeaders } = useAuth()

const revenueMode = ref<AnalyticsRevenueMode>('actual')

type DataRecord = {
  date: Date
  amount: number
}

const { width } = useElementSize(cardRef)

const data = ref<DataRecord[]>([])
const total = ref(0)
const loading = ref(true)

const chartTitle = computed(() =>
  revenueMode.value === 'actual' ? 'Доход' : 'Потенциальный доход'
)

const emptyHint = computed(() =>
  revenueMode.value === 'actual'
    ? 'Нет завершённых записей за выбранный период'
    : 'Нет записей за выбранный период'
)

const formatNumber = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0
}).format

const formatDate = (date: Date): string => {
  return ({
    daily: format(date, 'd MMM', { locale: ru }),
    weekly: format(date, 'd MMM', { locale: ru }),
    monthly: format(date, 'MMM yyyy', { locale: ru })
  })[props.period]
}

async function loadRevenue() {
  loading.value = true
  try {
    if (props.locked) {
      const placeholder = placeholderRevenuePoints(props.range)
      data.value = placeholder.points
      total.value = placeholder.total
      return
    }

    const headers = getAuthHeaders()
    if (!headers.Authorization) {
      data.value = []
      total.value = 0
      return
    }

    const response = await $fetch<AnalyticsRevenueResponse>('/api/analytics/revenue', {
      query: {
        start: format(props.range.start, 'yyyy-MM-dd'),
        end: format(props.range.end, 'yyyy-MM-dd'),
        period: props.period,
        mode: revenueMode.value
      },
      headers
    })

    data.value = response.points.map(point => ({
      date: parseISO(point.date),
      amount: point.amount
    }))
    total.value = response.total
  } catch (e) {
    console.error('DashboardChart: failed to load revenue', e)
    data.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

watch(
  [() => props.period, () => props.range.start, () => props.range.end, revenueMode, () => props.locked],
  () => loadRevenue(),
  { immediate: true }
)

const x = (_: DataRecord, i: number) => i
const y = (d: DataRecord) => d.amount

const xTicks = (i: number) => {
  if (i === 0 || i === data.value.length - 1 || !data.value[i]) {
    return ''
  }
  return formatDate(data.value[i].date)
}

const template = (d: DataRecord) => `${formatDate(d.date)}: ${formatNumber(d.amount)}`

const chartTabsUi = {
  list: 'relative flex w-full h-9 min-h-9 p-0.5 gap-0.5 box-border rounded-full analytics-track',
  indicator: 'rounded-full bg-violet-500/20',
  trigger:
    'flex min-w-0 flex-1 self-stretch items-center justify-center text-xs font-medium data-[state=inactive]:text-muted data-[state=active]:text-violet-400'
}
</script>

<template>
  <div ref="cardRef" class="analytics-card p-4 sm:p-5 min-w-0 overflow-hidden">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-4">
      <div class="min-w-0">
        <p class="text-base font-semibold text-highlighted mb-1">
          {{ chartTitle }}
        </p>
        <p class="text-2xl sm:text-3xl font-semibold text-highlighted tracking-tight">
          <template v-if="loading">—</template>
          <template v-else>{{ formatNumber(total) }}</template>
        </p>
      </div>

      <UTabs
        v-model="revenueMode"
        :items="[
          { label: 'Реальный', value: 'actual' },
          { label: 'Потенциальный', value: 'potential' }
        ]"
        size="sm"
        color="neutral"
        variant="pill"
        :content="false"
        class="w-full shrink-0 sm:w-[260px]"
        :ui="chartTabsUi"
      />
    </div>

    <div v-if="loading" class="h-96 w-full flex items-center justify-center text-muted text-sm">
      Загрузка графика...
    </div>

    <VisXYContainer
      v-else-if="data.length > 0"
      :data="data"
      :padding="{ top: 40 }"
      class="h-96 analytics-unovis"
      :width="width"
    >
      <VisLine
        :x="x"
        :y="y"
        :color="ACCENT"
      />
      <VisArea
        :x="x"
        :y="y"
        :color="ACCENT"
        :opacity="0.18"
      />

      <VisAxis
        type="x"
        :x="x"
        :tick-format="xTicks"
      />

      <VisCrosshair
        :color="ACCENT"
        :template="template"
      />

      <VisTooltip />
    </VisXYContainer>

    <div v-else class="h-96 w-full flex items-center justify-center text-muted text-sm text-center px-4">
      {{ emptyHint }}
    </div>
  </div>
</template>

<style scoped>
.analytics-unovis :deep(.unovis-xy-container),
:deep(.unovis-xy-container) {
  --ui-chart-line: #8b5cf6;
  --vis-crosshair-line-stroke-color: #8b5cf6;
  --vis-crosshair-circle-stroke-color: var(--ui-bg);

  --vis-axis-grid-color: color-mix(in oklab, var(--ui-border) 55%, transparent);
  --vis-axis-tick-color: transparent;
  --vis-axis-tick-label-color: var(--ui-text-dimmed);

  --vis-tooltip-background-color: var(--analytics-card-bg, var(--ui-bg));
  --vis-tooltip-border-color: var(--analytics-card-border, var(--ui-border));
  --vis-tooltip-text-color: var(--ui-text-highlighted);
}
</style>
