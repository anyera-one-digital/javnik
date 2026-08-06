<script setup lang="ts">
import type { UserSubscription } from '~/types'
import { segmentControlTabsUi } from '~/utils/segmentControlTabs'
import { subscriptionStatusText } from '~/utils/subscription'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

useSeoMeta({
  title: 'Тарифный план'
})

const { fetchProfile, getAuthHeaders } = useAuth()
const toast = useToast()

const subscription = ref<UserSubscription | null>(null)
const loadingSubscription = ref(true)

const effectivePlan = computed(() => subscription.value?.effectivePlan ?? 'free')

const subscriptionStatus = computed(() => subscriptionStatusText(subscription.value))

async function loadSubscription() {
  loadingSubscription.value = true
  try {
    const profile = await fetchProfile()
    if (profile?.subscription) {
      subscription.value = profile.subscription
      return
    }
    const data = await $fetch<UserSubscription>(
      '/api/auth/subscription/',
      { headers: getAuthHeaders() }
    )
    subscription.value = data
  } catch (e) {
    console.error('payment: failed to load subscription', e)
  } finally {
    loadingSubscription.value = false
  }
}

onMounted(() => {
  loadSubscription()
})

watch(effectivePlan, (plan) => {
  if (plan === 'pro') {
    selectedPlan.value = 'pro'
  } else if (plan === 'free' && selectedPlan.value === 'free') {
    selectedPlan.value = 'pro'
  }
})

const isYearly = ref('0')

const billingItems = [
  { label: 'Месяц', value: '0' },
  { label: 'Год', value: '1' }
]

const offers = computed(() => subscription.value?.offers)
const firstMonthBonus = computed(() => offers.value?.firstMonthBonusAvailable !== false)
const firstYearBonus = computed(() => offers.value?.firstYearBonusAvailable !== false)

const plans = computed(() => {
  const monthRub = offers.value?.monthPriceRub ?? 500
  const yearRub = offers.value?.yearPriceRub ?? 4800

  return [
    {
      id: 'free' as const,
      title: 'Free',
      chip: 'После пробного',
      description: 'После пробного месяца — базовый тариф без срока.',
      price: { month: '0₽', year: '0₽' },
      features: [
        'Базовые функции',
        'До 50 клиентов',
        'До 10 бронирований в месяц',
        'До 5 услуг',
        'Уведомления на почту'
      ],
      highlight: false
    },
    {
      id: 'pro' as const,
      title: 'Pro',
      chip: 'Все возможности',
      description: 'При регистрации — 1 месяц бесплатно, далее по подписке.',
      price: { month: `${monthRub}₽`, year: `${yearRub}₽` },
      features: [
        '1 месяц Pro при регистрации',
        'Базовый функционал',
        'Аналитика',
        'До 1500 клиентов',
        'До 150 бронирований в месяц',
        'До 15 услуг',
        'Уведомления на почту'
      ],
      highlight: true
    }
  ]
})

/** Фиолетовая плашка Pro: бонус первой оплаты под выбранный период */
const proBonusBadge = computed(() => {
  if (isYearly.value === '1') {
    return firstYearBonus.value ? 'Первый раз +3 месяца бесплатно' : null
  }
  return firstMonthBonus.value ? 'Первый раз +1 месяц бесплатно' : null
})

const selectedPlan = ref<'free' | 'pro'>('pro')

const selectedPlanData = computed(() => plans.value.find(p => p.id === selectedPlan.value))

const currentPrice = computed(() => {
  if (!selectedPlanData.value || selectedPlan.value === 'free') return null

  const priceStr = isYearly.value === '1'
    ? selectedPlanData.value.price.year
    : selectedPlanData.value.price.month

  const priceNum = Number.parseInt(priceStr.replace(/[^\d]/g, ''))
  const monthNum = Number.parseInt(selectedPlanData.value.price.month.replace(/[^\d]/g, ''))

  return {
    monthly: isYearly.value === '1' ? Math.round(priceNum / 12) : priceNum,
    total: priceNum,
    period: isYearly.value === '1' ? 'год' : 'месяц',
    yearlySavings: isYearly.value === '1' ? Math.max(0, monthNum * 12 - priceNum) : 0
  }
})

function formatPrice(raw: string) {
  const n = Number.parseInt(raw.replace(/[^\d]/g, ''), 10)
  if (Number.isNaN(n)) return raw
  return `${n.toLocaleString('ru-RU')} ₽`
}

function yearlyMonthlyPrice(yearPrice: string) {
  const yearNum = Number.parseInt(yearPrice.replace(/[^\d]/g, ''))
  return Math.round(yearNum / 12)
}

function isCurrentPlan(planId: 'free' | 'pro') {
  return effectivePlan.value === planId
}

/** Free нельзя выбрать при активном Pro — только после окончания подписки */
function isFreeLockedByPro(planId: 'free' | 'pro') {
  return planId === 'free' && effectivePlan.value === 'pro'
}

function isPlanDisabled(planId: 'free' | 'pro') {
  return isCurrentPlan(planId) || isFreeLockedByPro(planId)
}

function canSelectPlan(planId: 'free' | 'pro') {
  return !isPlanDisabled(planId)
}

function selectPlan(planId: 'free' | 'pro') {
  if (!canSelectPlan(planId)) return
  selectedPlan.value = planId
}

const paying = ref(false)

async function handlePayment() {
  if (!import.meta.client) return

  if (!selectedPlan.value || selectedPlan.value === 'free') {
    toast.add({
      title: 'Ошибка',
      description: 'Выберите тариф Pro для оплаты',
      color: 'error'
    })
    return
  }

  if (!currentPrice.value) return

  paying.value = true
  try {
    const billingPeriod = isYearly.value === '1' ? 'year' : 'month'
    const result = await $fetch<{
      paymentUrl: string
      orderId: string
    }>('/api/auth/payments/subscription/init/', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: { billing_period: billingPeriod }
    })

    if (!result.paymentUrl) {
      throw new Error('Платёжная ссылка не получена')
    }

    window.location.href = result.paymentUrl
  } catch (error: any) {
    const message
      = error?.data?.message
        || error?.message
        || 'Не удалось перейти к оплате. Проверьте настройки Т‑Банка или попробуйте позже.'
    toast.add({
      title: 'Ошибка оплаты',
      description: message,
      color: 'error'
    })
  } finally {
    paying.value = false
  }
}
</script>

<template>
  <UDashboardPanel id="payment">
    <template #header>
      <UDashboardNavbar title="Тарифный план">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>
        <template #right>
          <UTabs
            v-model="isYearly"
            :items="billingItems"
            color="neutral"
            variant="pill"
            size="md"
            :content="false"
            class="w-40"
            :ui="segmentControlTabsUi"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex flex-col gap-6 max-w-4xl mx-auto py-6 px-4 sm:px-6">
        <div
          v-if="loadingSubscription"
          class="rounded-[28px] border border-default bg-elevated/30 px-5 py-4"
        >
          <p class="text-sm text-muted m-0">
            Загрузка данных подписки...
          </p>
        </div>

        <div
          v-else-if="subscription"
          class="rounded-[28px] border border-default bg-elevated/30 px-5 py-4"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-sm text-muted">Сейчас активен:</span>
            <UBadge color="neutral" variant="subtle" size="sm">
              {{ subscription.planLabel }}
            </UBadge>
            <UBadge
              v-if="subscription.isTrial"
              color="neutral"
              variant="subtle"
              size="sm"
              class="!bg-violet-500/15 !text-violet-600 dark:!text-violet-300 !ring-violet-500/30"
            >
              Пробный период
            </UBadge>
          </div>
          <p v-if="subscriptionStatus" class="text-sm text-muted mt-2 mb-0">
            {{ subscriptionStatus }}
          </p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 items-stretch">
          <article
            v-for="plan in plans"
            :key="plan.id"
            class="lk-price-card relative flex flex-col rounded-[36px] border bg-default p-7 md:p-8 min-h-[440px] transition-all duration-200"
            :class="{
              'opacity-70 pointer-events-none': isPlanDisabled(plan.id),
              'border-default': !(selectedPlan === plan.id && canSelectPlan(plan.id)) && !plan.highlight,
              'border-2 border-gray-900 dark:border-white bg-elevated/50 shadow-sm': plan.highlight && !(selectedPlan === plan.id && canSelectPlan(plan.id)),
              'border-2 border-gray-900 dark:border-white ring-2 ring-gray-900/20 dark:ring-white/20 cursor-pointer': selectedPlan === plan.id && canSelectPlan(plan.id),
              'cursor-pointer hover:border-gray-400 dark:hover:border-white/40': canSelectPlan(plan.id) && selectedPlan !== plan.id
            }"
            @click="selectPlan(plan.id)"
          >
            <div
              v-if="plan.highlight && proBonusBadge"
              class="absolute -top-3.5 right-6 inline-flex items-center gap-1.5 rounded-full bg-violet-500 px-3 py-1.5 text-[10px] font-bold uppercase tracking-wide text-white shadow-md"
            >
              <UIcon name="i-lucide-sparkles" class="size-3.5" />
              {{ proBonusBadge }}
            </div>

            <div class="flex items-start justify-between gap-4">
              <div class="min-w-0">
                <span class="inline-flex items-center rounded-full border border-default bg-elevated/60 px-2.5 py-1 text-[11px] font-semibold text-muted">
                  {{ plan.chip }}
                </span>
                <h3 class="mt-4 text-[32px] md:text-[38px] font-medium tracking-tight text-highlighted leading-none">
                  {{ plan.title }}
                </h3>
                <div class="mt-3 flex flex-wrap items-center gap-2">
                  <UBadge
                    v-if="isCurrentPlan(plan.id)"
                    color="neutral"
                    variant="subtle"
                    size="xs"
                  >
                    Текущий
                  </UBadge>
                  <UBadge
                    v-else-if="isFreeLockedByPro(plan.id)"
                    color="neutral"
                    variant="outline"
                    size="xs"
                  >
                    После Pro
                  </UBadge>
                  <span
                    v-else-if="selectedPlan === plan.id"
                    class="inline-flex items-center gap-1 text-xs font-semibold text-highlighted"
                  >
                    <UIcon name="i-lucide-check" class="size-3.5" />
                    Выбрано
                  </span>
                </div>
              </div>
              <div class="text-right shrink-0 pt-1">
                <strong class="block text-[28px] md:text-[32px] font-medium tracking-tight text-highlighted whitespace-nowrap leading-none">
                  {{ formatPrice(isYearly === '1' ? plan.price.year : plan.price.month) }}
                  <small class="ml-0.5 text-xs font-medium tracking-normal text-muted">
                    /{{ isYearly === '1' ? 'год' : 'мес' }}
                  </small>
                </strong>
                <p
                  v-if="plan.id === 'pro' && isYearly === '1'"
                  class="mt-2 text-xs font-medium text-emerald-600 dark:text-emerald-400"
                >
                  {{ yearlyMonthlyPrice(plan.price.year) }} ₽/мес
                </p>
              </div>
            </div>

            <p class="mt-8 text-[15px] text-muted leading-relaxed max-w-md">
              <template v-if="isFreeLockedByPro(plan.id)">
                Тариф Free станет доступен автоматически после окончания подписки Pro.
              </template>
              <template v-else>
                {{ plan.description }}
              </template>
            </p>

            <ul class="mt-10 mb-8 flex flex-col gap-3.5 flex-1 list-none p-0 m-0">
              <li
                v-for="(feature, i) in plan.features"
                :key="i"
                class="flex items-center gap-2.5 text-[13px] text-muted"
              >
                <UIcon name="i-lucide-check" class="size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                <span>{{ feature }}</span>
              </li>
            </ul>

            <div
              class="mt-auto w-full rounded-[30px] px-4 py-3 text-center text-sm font-semibold transition-colors"
              :class="selectedPlan === plan.id
                ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
                : 'bg-elevated text-highlighted border border-default'"
            >
              <template v-if="isCurrentPlan(plan.id)">Текущий тариф</template>
              <template v-else-if="isFreeLockedByPro(plan.id)">Недоступен сейчас</template>
              <template v-else-if="selectedPlan === plan.id">Выбрано</template>
              <template v-else>Выбрать {{ plan.title }}</template>
            </div>
          </article>
        </div>

        <Transition
          enter-active-class="transition duration-300"
          enter-from-class="opacity-0 transform translate-y-4"
          enter-to-class="opacity-100 transform translate-y-0"
          leave-active-class="transition duration-200"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <div
            v-if="selectedPlan === 'pro' && selectedPlanData && currentPrice"
            class="rounded-[28px] border border-default bg-elevated/40 p-5 md:p-6"
          >
            <div class="space-y-2 mb-4">
              <div class="flex justify-between items-center text-sm">
                <span class="text-muted">Тариф:</span>
                <span class="font-medium text-highlighted">{{ selectedPlanData.title }}</span>
              </div>
              <div class="flex justify-between items-center text-sm">
                <span class="text-muted">Тип подписки:</span>
                <span class="font-medium text-highlighted">{{ isYearly === '1' ? 'Ежегодная' : 'Ежемесячная' }}</span>
              </div>
              <div v-if="isYearly === '1'" class="flex justify-between items-center text-sm">
                <span class="text-muted">Цена в месяц:</span>
                <span class="font-medium text-highlighted">{{ currentPrice.monthly }} ₽</span>
              </div>
              <div class="border-t border-default pt-3 mt-3">
                <div class="flex flex-wrap items-center gap-3">
                  <span
                    v-if="isYearly === '1' && currentPrice.yearlySavings > 0"
                    class="text-sm text-emerald-600 dark:text-emerald-400"
                  >
                    Экономия {{ currentPrice.yearlySavings }} ₽ при годовой оплате
                  </span>
                  <div class="ml-auto flex items-baseline gap-2">
                    <span class="font-semibold text-highlighted">Итого к оплате:</span>
                    <span class="text-xl font-bold tracking-tight text-highlighted">
                      {{ currentPrice.total.toLocaleString('ru-RU') }} ₽
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <UButton
              color="neutral"
              size="lg"
              block
              class="!rounded-[30px]"
              :loading="paying"
              :disabled="paying"
              @click="handlePayment"
            >
              Оплатить
            </UButton>
            <p class="text-xs text-muted text-center mt-3 mb-0">
              Оплата через Т‑Банк (Т‑Касса). После успешной оплаты откроется Pro.
            </p>
          </div>
        </Transition>
      </div>
    </template>
  </UDashboardPanel>
</template>
