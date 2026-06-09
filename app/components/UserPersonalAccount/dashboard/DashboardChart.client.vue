<script setup lang="ts">
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { VisXYContainer, VisLine, VisAxis, VisArea, VisCrosshair, VisTooltip } from '@unovis/vue'
import type { Period, Range, AnalyticsRevenueMode, AnalyticsRevenueResponse } from '~/types'
import { segmentControlTabsUi } from '~/utils/segmentControlTabs'
import { placeholderRevenuePoints } from '~/utils/analyticsPlaceholders'

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
</script>

<template>
  <UCard ref="cardRef" :ui="{ root: 'overflow-visible', body: '!px-0 !pt-0 !pb-3' }">
    <template #header>
      <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div class="min-w-0">
          <p class="text-xs text-muted uppercase mb-1.5">
            {{ chartTitle }}
          </p>
          <p class="text-3xl text-highlighted font-semibold">
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
          size="md"
          color="neutral"
          variant="pill"
          :content="false"
          class="w-full shrink-0 sm:w-[280px]"
          :ui="segmentControlTabsUi"
        />
      </div>
    </template>

    <div v-if="loading" class="h-96 w-full flex items-center justify-center text-muted">
      Загрузка графика...
    </div>

    <VisXYContainer
      v-else-if="data.length > 0"
      :data="data"
      :padding="{ top: 40 }"
      class="h-96"
      :width="width"
    >
      <VisLine
        :x="x"
        :y="y"
        color="var(--ui-chart-line)"
      />
      <VisArea
        :x="x"
        :y="y"
        color="var(--ui-chart-line)"
        :opacity="0.15"
      />

      <VisAxis
        type="x"
        :x="x"
        :tick-format="xTicks"
      />

      <VisCrosshair
        color="var(--ui-chart-line)"
        :template="template"
      />

      <VisTooltip />
    </VisXYContainer>

    <div v-else class="h-96 w-full flex items-center justify-center text-muted text-sm text-center px-4">
      {{ emptyHint }}
    </div>
  </UCard>
</template>

<style scoped>
.unovis-xy-container {
  --ui-chart-line: var(--ui-text-highlighted);
  --vis-crosshair-line-stroke-color: var(--ui-chart-line);
  --vis-crosshair-circle-stroke-color: var(--ui-bg);

  --vis-axis-grid-color: var(--ui-border);
  --vis-axis-tick-color: var(--ui-border);
  --vis-axis-tick-label-color: var(--ui-text-dimmed);

  --vis-tooltip-background-color: var(--ui-bg);
  --vis-tooltip-border-color: var(--ui-border);
  --vis-tooltip-text-color: var(--ui-text-highlighted);
}
</style>
