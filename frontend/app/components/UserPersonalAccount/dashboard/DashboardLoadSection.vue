<script setup lang="ts">
import { format } from 'date-fns'
import type { AnalyticsLoadResponse, Range } from '~/types'
import { placeholderLoad } from '~/utils/analyticsPlaceholders'

const props = defineProps<{
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

function pluralBookings(n: number) {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'запись'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'записи'
  return 'записей'
}

function pluralWindows(n: number) {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'свободное окно'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return 'свободных окна'
  return 'свободных окон'
}

const insightIcon: Record<string, string> = {
  'trending-up': 'i-lucide-trending-up',
  clock: 'i-lucide-clock',
  moon: 'i-lucide-moon',
  calendar: 'i-lucide-calendar',
  activity: 'i-lucide-activity'
}

const rangeKey = computed(() => {
  const start = format(props.range.start, 'yyyy-MM-dd')
  const end = format(props.range.end, 'yyyy-MM-dd')
  return `${start}_${end}`
})

const { data, pending } = await useAsyncData<AnalyticsLoadResponse>(
  () => `analytics-load-${rangeKey.value}`,
  async () => {
    if (props.locked) return placeholderLoad()
    const headers = getAuthHeaders()
    if (!headers.Authorization) return placeholderLoad()
    return await $fetch<AnalyticsLoadResponse>('/api/analytics/load', {
      query: {
        start: format(props.range.start, 'yyyy-MM-dd'),
        end: format(props.range.end, 'yyyy-MM-dd')
      },
      headers
    })
  },
  {
    watch: [rangeKey, () => props.locked],
    default: () => placeholderLoad()
  }
)

function heatStyle(value: number, max: number) {
  if (!value || !max) {
    return { backgroundColor: 'var(--analytics-track, color-mix(in oklab, white 5%, var(--ui-bg)))' }
  }
  const t = Math.min(1, value / max)
  const alpha = 0.18 + t * 0.82
  return {
    backgroundColor: `color-mix(in oklab, #8b5cf6 ${Math.round(alpha * 100)}%, transparent)`
  }
}
</script>

<template>
  <div class="space-y-3">
    <!-- Load KPIs -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div class="analytics-card p-4 sm:p-5">
        <div class="flex items-start justify-between gap-2 mb-3">
          <p class="text-xs text-muted">Загрузка</p>
          <UIcon name="i-lucide-gauge" class="size-4 text-muted" />
        </div>
        <p class="text-2xl sm:text-3xl font-semibold text-highlighted tracking-tight">
          <template v-if="pending">—</template>
          <template v-else>{{ data.load.value }}%</template>
        </p>
      </div>

      <div class="analytics-card p-4 sm:p-5">
        <div class="flex items-start justify-between gap-2 mb-3">
          <p class="text-xs text-muted">Свободные окна</p>
          <UIcon name="i-lucide-clock" class="size-4 text-muted" />
        </div>
        <p class="text-2xl sm:text-3xl font-semibold text-highlighted tracking-tight">
          <template v-if="pending">—</template>
          <template v-else>{{ data.freeSlots.value }} {{ pluralWindows(data.freeSlots.value) }}</template>
        </p>
      </div>
    </div>

    <!-- Heatmap + Insights -->
    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1.7fr)_minmax(260px,1fr)] gap-3">
      <div class="analytics-card p-4 sm:p-5 overflow-x-auto">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h3 class="text-base font-semibold text-highlighted">
            Когда записываются
          </h3>
          <div class="flex items-center gap-2 text-[11px] text-muted">
            <span>меньше</span>
            <div class="flex gap-0.5">
              <span
                v-for="n in 5"
                :key="n"
                class="size-2.5 rounded-sm"
                :style="heatStyle(n, 5)"
              />
            </div>
            <span>больше</span>
          </div>
        </div>

        <div v-if="pending" class="h-64 flex items-center justify-center text-muted text-sm">
          Загрузка...
        </div>
        <div v-else class="min-w-[420px]">
          <div
            class="grid gap-1 mb-1"
            :style="{ gridTemplateColumns: `48px repeat(${data.heatmap.days.length}, minmax(0, 1fr))` }"
          >
            <div />
            <div
              v-for="day in data.heatmap.days"
              :key="day"
              class="text-center text-[11px] text-muted py-1"
            >
              {{ day }}
            </div>
          </div>
          <div
            v-for="(hour, hi) in data.heatmap.hours"
            :key="hour"
            class="grid gap-1 mb-1"
            :style="{ gridTemplateColumns: `48px repeat(${data.heatmap.days.length}, minmax(0, 1fr))` }"
          >
            <div class="text-[11px] text-muted self-center">
              {{ hour }}
            </div>
            <div
              v-for="(cell, di) in data.heatmap.cells[hi]"
              :key="`${hour}-${di}`"
              class="h-7 rounded-md transition-colors"
              :style="heatStyle(cell, data.heatmap.max)"
              :title="`${data.heatmap.days[di]} ${hour}: ${cell}`"
            />
          </div>
        </div>
      </div>

      <div class="analytics-card p-4 sm:p-5">
        <h3 class="text-base font-semibold text-highlighted">
          Выводы
        </h3>
        <p class="text-xs text-muted mt-1 mb-5">
          <template v-if="pending">—</template>
          <template v-else>На основе {{ data.bookings.value }} {{ pluralBookings(data.bookings.value) }}</template>
        </p>

        <div v-if="pending" class="h-40 flex items-center justify-center text-muted text-sm">
          Загрузка...
        </div>
        <ul v-else class="space-y-4">
          <li
            v-for="(insight, i) in data.insights"
            :key="i"
            class="flex items-start gap-3 text-sm text-highlighted"
          >
            <span class="size-8 rounded-full analytics-track flex items-center justify-center shrink-0">
              <UIcon :name="insightIcon[insight.icon] || 'i-lucide-sparkles'" class="size-4 text-violet-500" />
            </span>
            <span class="pt-1.5 leading-snug">{{ insight.text }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Load by day + Popular services -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
      <div class="analytics-card p-4 sm:p-5">
        <h3 class="text-base font-semibold text-highlighted mb-5">
          Загрузка по дням
        </h3>
        <div v-if="pending" class="h-48 flex items-center justify-center text-muted text-sm">
          Загрузка...
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="day in data.loadByDay"
            :key="day.day"
            class="grid grid-cols-[28px_1fr_40px] items-center gap-2"
          >
            <span class="text-xs text-muted">{{ day.day }}</span>
            <div class="h-2 rounded-full analytics-track overflow-hidden">
              <div
                class="h-full rounded-full bg-violet-500 transition-[width] duration-500"
                :style="{ width: `${Math.max(day.loadPercent > 0 ? 4 : 0, day.loadPercent)}%` }"
              />
            </div>
            <span class="text-xs font-medium text-highlighted text-right">{{ day.loadPercent }}%</span>
          </div>
        </div>
      </div>

      <div class="analytics-card p-4 sm:p-5">
        <h3 class="text-base font-semibold text-highlighted mb-5">
          Популярные услуги
        </h3>
        <div v-if="pending" class="h-48 flex items-center justify-center text-muted text-sm">
          Загрузка...
        </div>
        <div
          v-else-if="!data.popularServices.length"
          class="h-48 flex items-center justify-center text-muted text-sm text-center"
        >
          Нет данных по услугам
        </div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-xs text-muted border-b border-default/40">
                <th class="text-left font-medium py-2 pr-2 w-8">#</th>
                <th class="text-left font-medium py-2 pr-2">Услуга</th>
                <th class="text-right font-medium py-2 pr-2">Записей</th>
                <th class="text-right font-medium py-2">Доход</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(service, i) in data.popularServices"
                :key="service.name"
                class="border-b border-default/30 last:border-0"
              >
                <td class="py-3 pr-2 text-muted">{{ i + 1 }}</td>
                <td class="py-3 pr-2 text-highlighted">{{ service.name }}</td>
                <td class="py-3 pr-2 text-right text-highlighted tabular-nums">{{ service.bookings }}</td>
                <td class="py-3 text-right text-highlighted tabular-nums">{{ formatMoney(service.revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
