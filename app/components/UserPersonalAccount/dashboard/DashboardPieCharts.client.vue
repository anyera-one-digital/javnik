<script setup lang="ts">
import { VisSingleContainer, VisDonut } from '@unovis/vue'
import type { Period, Range } from '~/types'

const props = defineProps<{
  period: Period
  range: Range
}>()

// Диаграмма 1: Распределение по статусам заказов
type StatusItem = { label: string; value: number }
const statusData = ref<StatusItem[]>([])

// Диаграмма 2: Распределение дохода по категориям услуг
type CategoryItem = { label: string; value: number }
const categoryData = ref<CategoryItem[]>([])

const chartColors = [
  'var(--ui-text-highlighted)',
  'var(--ui-text-muted)',
  'var(--ui-text-dimmed)',
  'var(--ui-border)',
  'var(--ui-bg-elevated)'
]

function getStatusColor(_: StatusItem, i: number) {
  return chartColors[i % chartColors.length]
}

function getCategoryColor(_: CategoryItem, i: number) {
  return chartColors[i % chartColors.length]
}

const statusValue = (d: StatusItem) => d.value
const categoryValue = (d: CategoryItem) => d.value

watch([() => props.period, () => props.range], () => {
  statusData.value = [
    { label: 'Оплачено', value: randomInt(60, 85) },
    { label: 'Ожидает', value: randomInt(10, 25) },
    { label: 'Отменено', value: randomInt(2, 10) }
  ]
  categoryData.value = [
    { label: 'Маникюр', value: randomInt(15000, 35000) },
    { label: 'Стрижки', value: randomInt(20000, 45000) },
    { label: 'Наращивание', value: randomInt(25000, 55000) },
    { label: 'Другое', value: randomInt(5000, 20000) }
  ]
}, { immediate: true })

const formatRuble = (value: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(value)

const statusTotal = computed(() => statusData.value.reduce((s, d) => s + d.value, 0))
const categoryTotal = computed(() => categoryData.value.reduce((s, d) => s + d.value, 0))
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
    <UCard :ui="{ root: 'overflow-visible', body: '!px-0 !pt-0 !pb-4' }">
      <template #header>
        <div>
          <p class="text-xs text-muted uppercase mb-1.5">
            Статусы заказов
          </p>
          <p class="text-2xl text-highlighted font-semibold">
            {{ statusTotal }} заказов
          </p>
        </div>
      </template>

      <div class="flex flex-col items-center gap-4">
        <VisSingleContainer :data="statusData" class="h-64 w-full">
          <VisDonut
            :value="statusValue"
            :color="getStatusColor"
            arc-width="24"
            pad-angle="0.02"
          />
        </VisSingleContainer>
        <div class="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-muted">
          <span v-for="(item, i) in statusData" :key="i">
            {{ item.label }}: {{ item.value }}
          </span>
        </div>
      </div>
    </UCard>

    <UCard :ui="{ root: 'overflow-visible', body: '!px-0 !pt-0 !pb-4' }">
      <template #header>
        <div>
          <p class="text-xs text-muted uppercase mb-1.5">
            Доход по категориям
          </p>
          <p class="text-2xl text-highlighted font-semibold">
            {{ formatRuble(categoryTotal) }}
          </p>
        </div>
      </template>

      <div class="flex flex-col items-center gap-4">
        <VisSingleContainer :data="categoryData" class="h-64 w-full">
          <VisDonut
            :value="categoryValue"
            :color="getCategoryColor"
            arc-width="24"
            pad-angle="0.02"
          />
        </VisSingleContainer>
        <div class="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-muted">
          <span v-for="(item, i) in categoryData" :key="i">
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
