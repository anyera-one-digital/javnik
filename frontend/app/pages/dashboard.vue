<script setup lang="ts">
import { eachDayOfInterval, sub } from 'date-fns'
import type { Period, Range } from '~/types'
import DashboardAnalyticsLock from '~/components/UserPersonalAccount/dashboard/DashboardAnalyticsLock.vue'
import DashboardDateRangePicker from '~/components/UserPersonalAccount/dashboard/DashboardDateRangePicker.vue'
import DashboardOverview from '~/components/UserPersonalAccount/dashboard/DashboardOverview.vue'
import DashboardLoadSection from '~/components/UserPersonalAccount/dashboard/DashboardLoadSection.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

useSeoMeta({
  title: 'Аналитика'
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

const daysInRange = computed(() => {
  try {
    return eachDayOfInterval(range.value).length
  } catch {
    return 14
  }
})

watch(daysInRange, (len) => {
  if (len <= 31) period.value = 'daily'
  else if (len <= 90) period.value = 'weekly'
  else period.value = 'monthly'
}, { immediate: true })
</script>

<template>
  <UDashboardPanel id="dashboard">
    <template #header>
      <UDashboardNavbar title="Аналитика" :ui="{ right: 'gap-2 sm:gap-3 flex-wrap' }">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>

        <template #right>
          <DashboardDateRangePicker
            v-model="range"
            :disabled="analyticsLocked"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <DashboardAnalyticsLock :locked="analyticsLocked">
        <div class="analytics-page space-y-8 pb-6">
          <DashboardOverview
            :period="period"
            :range="range"
            :locked="analyticsLocked"
          />

          <section class="space-y-3">
            <div class="flex items-end justify-between gap-3 px-0.5">
              <div>
                <h2 class="text-lg font-semibold text-highlighted">
                  Загрузка и спрос
                </h2>
                <p class="text-xs text-muted mt-1">
                  Когда записываются клиенты и как распределена нагрузка
                </p>
              </div>
            </div>

            <DashboardLoadSection
              :range="range"
              :locked="analyticsLocked"
            />
          </section>
        </div>
      </DashboardAnalyticsLock>
    </template>
  </UDashboardPanel>
</template>

<style>
.analytics-page {
  --analytics-accent: #8b5cf6; /* violet-500 — как «Новая запись» */
  --analytics-card-bg: color-mix(in oklab, var(--ui-bg-elevated) 45%, var(--ui-bg));
  --analytics-card-border: color-mix(in oklab, var(--ui-border) 55%, transparent);
  --analytics-track: color-mix(in oklab, var(--ui-bg-elevated) 70%, var(--ui-bg));
}

.dark .analytics-page {
  /* Лёгкий подъём над фоном — как на макетах, без «графитовых» плашек */
  --analytics-card-bg: color-mix(in oklab, white 3.5%, var(--ui-bg));
  --analytics-card-border: color-mix(in oklab, white 5.5%, transparent);
  --analytics-track: color-mix(in oklab, white 5%, var(--ui-bg));
}

.analytics-page .analytics-card {
  border-radius: 14px;
  border: 1px solid var(--analytics-card-border);
  background: var(--analytics-card-bg);
  box-shadow: none;
}

.analytics-page .analytics-track {
  background: var(--analytics-track);
}
</style>
