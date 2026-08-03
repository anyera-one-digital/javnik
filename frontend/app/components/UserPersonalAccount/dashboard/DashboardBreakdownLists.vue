<script setup lang="ts">
import type {
  AnalyticsBreakdownItem,
  AnalyticsClientsBreakdown,
  AnalyticsPeriodSummary,
  AnalyticsServiceBreakdownSection
} from '~/types'

const props = defineProps<{
  revenueByService: AnalyticsServiceBreakdownSection
  periodSummary: AnalyticsPeriodSummary
  clientsBreakdown: AnalyticsClientsBreakdown
  loading?: boolean
}>()

const formatMoney = (value: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(value)

function barWidth(value: number, total: number) {
  if (!total || value <= 0) return '0%'
  return `${Math.max(4, Math.round((100 * value) / total))}%`
}

function withShare(items: AnalyticsBreakdownItem[], total: number) {
  return items.map(item => ({
    ...item,
    share: total > 0 ? Math.round((100 * item.value) / total) : 0
  }))
}

const revenueItems = computed(() =>
  withShare(props.revenueByService?.items || [], props.revenueByService?.total || 0)
)

const clientItems = computed(() =>
  withShare(props.clientsBreakdown?.items || [], props.clientsBreakdown?.total || 0)
)

const summary = computed(() => props.periodSummary)
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:items-stretch">
    <!-- Слева: доход по услугам -->
    <div class="analytics-card p-4 sm:p-5 flex flex-col min-h-0">
      <h3 class="text-base font-semibold text-highlighted mb-5">
        Доход по услугам
      </h3>

      <div v-if="loading" class="flex-1 flex items-center justify-center text-muted text-sm min-h-48">
        Загрузка...
      </div>
      <div
        v-else-if="!revenueItems.length"
        class="flex-1 flex items-center justify-center text-muted text-sm text-center min-h-48"
      >
        Нет завершённых записей за период
      </div>
      <template v-else>
        <div class="space-y-4 flex-1">
          <div v-for="(item, i) in revenueItems" :key="`rev-${i}`" class="space-y-1.5">
            <div class="flex items-baseline justify-between gap-3 text-sm">
              <span class="text-highlighted truncate">{{ item.label }}</span>
              <span class="shrink-0 font-medium text-highlighted">{{ formatMoney(item.value) }}</span>
            </div>
            <div class="h-1.5 rounded-full analytics-track overflow-hidden">
              <div
                class="h-full rounded-full bg-violet-500 transition-[width] duration-500"
                :style="{ width: barWidth(item.value, revenueByService.total) }"
              />
            </div>
          </div>
        </div>

        <div class="mt-5 pt-4 border-t border-default/40 flex items-center justify-between text-sm">
          <span class="text-muted">Всего</span>
          <span class="font-semibold text-highlighted">
            {{ formatMoney(revenueByService?.total || 0) }}
          </span>
        </div>
      </template>
    </div>

    <!-- Справа: клиенты + коротко о периоде — вместе по высоте как левая плашка -->
    <div class="flex flex-col gap-3 min-h-0 lg:h-full">
      <div class="analytics-card p-4 sm:p-5 flex flex-col flex-1 min-h-0">
        <h3 class="text-base font-semibold text-highlighted mb-4">
          Клиенты за период
        </h3>

        <div v-if="loading" class="flex-1 flex items-center justify-center text-muted text-sm">
          Загрузка...
        </div>
        <div
          v-else-if="!(clientsBreakdown?.total)"
          class="flex-1 flex items-center justify-center text-muted text-sm text-center"
        >
          Нет клиентов за выбранный период
        </div>
        <template v-else>
          <div class="space-y-3 flex-1">
            <div v-for="(item, i) in clientItems" :key="`cli-${i}`" class="space-y-1.5">
              <div class="flex items-baseline justify-between gap-3 text-sm">
                <span class="text-highlighted">{{ item.label }}</span>
                <span class="shrink-0 font-medium text-highlighted">
                  {{ item.value }}
                  <span class="text-muted font-normal">({{ item.share }}%)</span>
                </span>
              </div>
              <div class="h-1.5 rounded-full analytics-track overflow-hidden">
                <div
                  class="h-full rounded-full bg-violet-500 transition-[width] duration-500"
                  :style="{ width: barWidth(item.value, clientsBreakdown.total) }"
                />
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-default/40 flex items-center justify-between text-sm">
            <span class="text-muted">Всего</span>
            <span class="font-semibold text-highlighted">
              {{ clientsBreakdown?.total || 0 }}
            </span>
          </div>
        </template>
      </div>

      <div class="analytics-card p-4 sm:p-5 flex flex-col flex-1 min-h-0">
        <h3 class="text-base font-semibold text-highlighted mb-4">
          Коротко о периоде
        </h3>

        <div v-if="loading" class="flex-1 flex items-center justify-center text-muted text-sm">
          Загрузка...
        </div>
        <template v-else-if="summary">
          <dl class="space-y-3 flex-1">
            <div class="flex items-baseline justify-between gap-3">
              <dt class="text-sm text-muted">Средний чек</dt>
              <dd class="text-sm font-semibold text-highlighted">
                {{ formatMoney(summary.averageCheck) }}
              </dd>
            </div>
            <div class="flex items-baseline justify-between gap-3">
              <dt class="text-sm text-muted">Отмены</dt>
              <dd class="text-sm font-semibold text-highlighted">
                {{ summary.cancellations }}
              </dd>
            </div>
            <div class="flex items-baseline justify-between gap-3">
              <dt class="text-sm text-muted">Повторные клиенты</dt>
              <dd class="text-sm font-semibold text-highlighted">
                {{ summary.returningClients }}
              </dd>
            </div>
          </dl>

          <div class="mt-4 pt-3 border-t border-default/40 flex items-start gap-2.5 text-xs text-muted">
            <UIcon name="i-lucide-activity" class="size-4 shrink-0 mt-0.5" />
            <span>
              <template v-if="summary.trendReady">
                Тренд строится по {{ summary.bookingsCount }} записям периода
              </template>
              <template v-else>
                {{ summary.trendHint || 'Тренд появится после 5 записей' }}
              </template>
            </span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
