<script setup lang="ts">
import type { UserSubscription } from '~/types'
import { segmentControlTabsUi } from '~/utils/segmentControlTabs'
import { subscriptionStatusText } from '~/utils/subscription'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const { fetchProfile, getAuthHeaders } = useAuth()
const toast = useToast()
const config = useRuntimeConfig()

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
      `${config.public.apiBase}/api/auth/subscription/`,
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

const plans = [
  {
    id: 'free' as const,
    title: 'Free',
    description: 'Бесплатный план для начала работы.',
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
    description: 'Весь базовый функционал',
    price: { month: '500₽', year: '4800₽' },
    features: [
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

const selectedPlan = ref<'free' | 'pro'>('pro')

const selectedPlanData = computed(() => plans.find(p => p.id === selectedPlan.value))

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
    }>('/api/payments/subscription/init', {
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
      <div class="flex flex-col gap-4 max-w-3xl mx-auto py-4 px-4">
        <UCard v-if="loadingSubscription" :ui="{ body: 'py-4' }">
          <p class="text-sm text-muted m-0">
            Загрузка данных подписки...
          </p>
        </UCard>

        <UCard
          v-else-if="subscription"
          :ui="{ body: 'py-4' }"
          class="bg-elevated/40"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-sm text-muted">Сейчас активен:</span>
            <UBadge color="neutral" variant="subtle" size="sm">
              {{ subscription.planLabel }}
            </UBadge>
            <UBadge
              v-if="subscription.isTrial"
              color="primary"
              variant="subtle"
              size="sm"
            >
              Пробный период
            </UBadge>
          </div>
          <p v-if="subscriptionStatus" class="text-sm text-muted mt-2 mb-0">
            {{ subscriptionStatus }}
          </p>
        </UCard>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5 items-stretch">
          <UCard
            v-for="plan in plans"
            :key="plan.id"
            class="h-full flex flex-col transition-all"
            :class="{
              'opacity-75 pointer-events-none': isPlanDisabled(plan.id),
              'ring-2 ring-black dark:ring-white cursor-pointer': selectedPlan === plan.id && canSelectPlan(plan.id),
              'cursor-pointer': canSelectPlan(plan.id)
            }"
            :ui="{
              root: 'p-5 flex flex-col h-full',
              body: 'flex flex-col flex-1 gap-3 min-h-0'
            }"
            @click="selectPlan(plan.id)"
          >
            <div class="flex flex-wrap items-baseline gap-2">
              <UIcon
                v-if="selectedPlan === plan.id"
                name="i-lucide-check"
                class="size-4 shrink-0 text-highlighted"
              />
              <span class="text-base font-semibold text-highlighted">{{ plan.title }}</span>
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
              <span class="text-sm text-muted ml-auto">
                {{ isYearly === '1' ? plan.price.year : plan.price.month }}{{ isYearly === '1' ? '/год' : '/мес' }}
              </span>
            </div>
            <span
              v-if="plan.id === 'pro' && isYearly === '1'"
              class="text-xs text-green-600 dark:text-green-400 font-medium"
            >
              {{ yearlyMonthlyPrice(plan.price.year) }}₽/мес при оплате за год
            </span>

            <p class="text-sm text-muted leading-snug line-clamp-2 flex-1">
              <template v-if="isFreeLockedByPro(plan.id)">
                Тариф Free станет доступен автоматически после окончания подписки Pro.
              </template>
              <template v-else>
                {{ plan.description }}
              </template>
            </p>

            <ul class="space-y-1.5 text-sm text-muted">
              <li
                v-for="(feature, i) in plan.features"
                :key="i"
                class="flex items-center gap-2"
              >
                <UIcon name="i-lucide-check" class="size-4 shrink-0 text-muted" />
                <span>{{ feature }}</span>
              </li>
            </ul>
          </UCard>
        </div>

        <Transition
          enter-active-class="transition duration-300"
          enter-from-class="opacity-0 transform translate-y-4"
          enter-to-class="opacity-100 transform translate-y-0"
          leave-active-class="transition duration-200"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <UCard
            v-if="selectedPlan === 'pro' && selectedPlanData && currentPrice"
            class="bg-elevated/50"
            :ui="{ root: 'p-4' }"
          >
            <div class="space-y-2 mb-3">
              <div class="flex justify-between items-center">
                <span class="text-muted">Тариф:</span>
                <span class="font-medium">{{ selectedPlanData.title }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-muted">Тип подписки:</span>
                <span class="font-medium">{{ isYearly === '1' ? 'Ежегодная' : 'Ежемесячная' }}</span>
              </div>
              <div v-if="isYearly === '1'" class="flex justify-between items-center">
                <span class="text-muted">Цена в месяц:</span>
                <span class="font-medium">{{ currentPrice.monthly }}₽</span>
              </div>
              <div class="border-t border-default pt-3 mt-3">
                <div class="flex items-center gap-4">
                  <span
                    v-if="isYearly === '1' && currentPrice.yearlySavings > 0"
                    class="text-sm text-green-600 dark:text-green-400"
                  >
                    Экономия {{ currentPrice.yearlySavings }}₽ при годовой оплате
                  </span>
                  <div class="ml-auto flex items-baseline gap-2">
                    <span class="font-semibold">Итого к оплате:</span>
                    <span class="text-lg font-bold text-highlighted">
                      {{ currentPrice.total }}₽
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <UButton
              color="neutral"
              size="sm"
              block
              :loading="paying"
              :disabled="paying"
              @click="handlePayment"
            >
              Оплатить
            </UButton>
            <p class="text-xs text-muted text-center mt-2 mb-0">
              Оплата через Т‑Банк (Т‑Касса). После успешной оплаты откроется Pro.
            </p>
          </UCard>
        </Transition>
      </div>
    </template>
  </UDashboardPanel>
</template>
