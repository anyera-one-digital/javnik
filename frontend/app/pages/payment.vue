<script setup lang="ts">
import type { Subscription } from '~/types'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const { user, getAuthHeaders } = useAuth()
const toast = useToast()

// Моковые данные текущей подписки (в будущем загружать из API)
const currentSubscription = ref<Subscription>({
  plan: 'free',
  planLabel: 'Free',
  isActive: true,
  endDate: null // Бесконечный для Free
})

// Загрузка текущей подписки (заглушка)
onMounted(async () => {
  // TODO: Загрузить реальные данные из API
  // const subscription = await $fetch('/api/subscription', { headers: getAuthHeaders() })
  // currentSubscription.value = subscription
  selectedPlan.value = currentSubscription.value.plan === 'free' ? 'pro' : 'pro'
})

// Переключатель Месяц/Год
const isYearly = ref('0')

const billingItems = [
  {
    label: 'Месяц',
    value: '0'
  },
  {
    label: 'Год',
    value: '1'
  }
]

// Тарифы: Free, Pro, Pro+
const plans = [
  {
    id: 'free',
    title: 'Free',
    description: 'Бесплатный план для начала работы.',
    price: {
      month: '0₽',
      year: '0₽'
    },
    button: {
      label: 'Текущий',
      color: 'neutral',
      variant: 'subtle',
      disabled: true
    },
    features: [
      'Базовые функции',
      'До 50 клиентов',
      'До 30 бронирований в месяц',
      'До 7 услуг',
      'Уведомления на email'
    ],
    highlight: false
  },
  {
    id: 'pro',
    title: 'Pro',
    description: 'Профессиональный план для растущего бизнеса.',
    price: {
      month: '750₽',
      year: '7200₽' // 750 * 12 * 0.8 (скидка 20%)
    },
    button: {
      label: 'Выбрать',
      color: 'neutral'
    },
    features: [
      'Все функции Free',
      'Расширенная аналитика',
      '∞ клиентов',
      '∞ броней',
      '∞ услуг',
      'Уведомления в ТГ бота'
    ],
    highlight: true
  },
  {
    id: 'pro-plus',
    title: 'Pro+',
    description: 'Максимальный план для крупных команд.',
    price: {
      month: '1500₽',
      year: '14400₽' // 1500 * 12 * 0.8 (скидка 20%)
    },
    button: {
      label: 'Выбрать',
      color: 'neutral',
      variant: 'subtle'
    },
    features: [
      'Все функции Pro',
      'Командная работа',
      'Множественные календари',
      'Интеграции с внешними сервисами',
      'API доступ'
    ],
    highlight: false
  }
]

// Выбор по умолчанию: Free → Pro. Pro+ пока недоступен («Скоро»)
const selectedPlan = ref<string | null>('pro')

// Вычисляем цену выбранного тарифа
const selectedPlanData = computed(() => {
  if (!selectedPlan.value) return null
  return plans.find(p => p.id === selectedPlan.value)
})

const currentPrice = computed(() => {
  if (!selectedPlanData.value) return null
  
  const priceStr = isYearly.value === '1' 
    ? selectedPlanData.value.price.year 
    : selectedPlanData.value.price.month
  
  // Извлекаем число из строки (убираем ₽ и пробелы)
  const priceNum = Number.parseInt(priceStr.replace(/[^\d]/g, ''))
  const monthNum = Number.parseInt(selectedPlanData.value.price.month.replace(/[^\d]/g, ''))
  
  return {
    monthly: isYearly.value === '1' ? Math.round(priceNum / 12) : priceNum,
    total: priceNum,
    period: isYearly.value === '1' ? 'год' : 'месяц',
    // Реальная экономия 20% при годовой оплате (Pro, Pro+)
    yearlySavings: isYearly.value === '1' ? Math.max(0, monthNum * 12 - priceNum) : 0
  }
})

function handlePayment() {
  if (!selectedPlan.value) {
    toast.add({
      title: 'Ошибка',
      description: 'Выберите тариф для оплаты',
      color: 'error'
    })
    return
  }
  
  const plan = selectedPlanData.value
  const price = currentPrice.value
  
  // Здесь будет логика оплаты
  toast.add({
    title: 'Переход к оплате',
    description: `Выбран тариф ${plan?.title}. Сумма: ${price?.total}₽ за ${price?.period}`,
    color: 'success'
  })
}

function selectPlan(planId: string) {
  // Нельзя выбрать Free, если он уже активен
  if (planId === 'free' && currentSubscription.value.plan === 'free') {
    return
  }
  // Pro+ пока недоступен
  if (planId === 'pro-plus') {
    return
  }
  selectedPlan.value = planId
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
            size="sm"
            :content="false"
            class="w-40"
            :ui="{
                list: 'bg-elevated rounded-full p-0.5',
                indicator: 'rounded-full',
                trigger: 'flex-1 justify-center'
              }"
            />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex flex-col gap-4 max-w-5xl mx-auto py-4 px-4">
        <!-- Тарифы: компактная сетка одинакового размера -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 items-stretch">
          <UCard
            v-for="plan in plans"
            :key="plan.id"
            class="cursor-pointer h-full flex flex-col transition-all"
            :class="{
              'opacity-75': plan.id === currentSubscription.plan || plan.id === 'pro-plus',
              'pointer-events-none': plan.id === currentSubscription.plan || plan.id === 'pro-plus',
              'ring-2 ring-black dark:ring-white': selectedPlan === plan.id && plan.id !== 'pro-plus'
            }"
            :ui="{
              root: 'p-5 flex flex-col h-full',
              body: 'flex flex-col flex-1 gap-3 min-h-0'
            }"
            @click="selectPlan(plan.id)"
          >
            <!-- Заголовок: галочка при выборе + название + бейдж + цена -->
            <div class="flex flex-wrap items-baseline gap-2">
              <UIcon
                v-if="selectedPlan === plan.id"
                name="i-lucide-check"
                class="size-4 shrink-0 text-highlighted"
              />
              <span class="text-base font-semibold text-highlighted">{{ plan.title }}</span>
              <UBadge
                v-if="plan.id === currentSubscription.plan"
                color="neutral"
                variant="subtle"
                size="xs"
              >
                Текущий
              </UBadge>
              <UBadge
                v-if="plan.id === 'pro-plus'"
                color="neutral"
                variant="subtle"
                size="xs"
              >
                Скоро
              </UBadge>
              <span class="text-sm text-muted ml-auto">
                {{ isYearly === '1' ? plan.price.year : plan.price.month }}{{ isYearly === '1' ? '/год' : '/мес' }}
              </span>
            </div>
            <span
              v-if="(plan.id === 'pro' || plan.id === 'pro-plus') && isYearly === '1'"
              class="text-xs text-green-600 dark:text-green-400 font-medium"
            >
              Скидка 20%
            </span>

            <p class="text-sm text-muted leading-snug line-clamp-2 flex-1">
              {{ plan.description }}
            </p>

            <!-- Список возможностей (до 6) -->
            <ul class="space-y-1.5 text-sm text-muted">
              <li
                v-for="(feature, i) in plan.features.slice(0, 6)"
                :key="i"
                class="flex items-center gap-2"
              >
                <UIcon name="i-lucide-check" class="size-4 shrink-0 text-muted" />
                <span v-if="feature.startsWith('∞ ')">
                  <span class="text-base align-middle">∞</span>
                  {{ feature.slice(2) }}
                </span>
                <span v-else>{{ feature }}</span>
              </li>
            </ul>
          </UCard>
        </div>

        <!-- Детали оплаты (показывается только после выбора тарифа) -->
        <Transition
          enter-active-class="transition duration-300"
          enter-from-class="opacity-0 transform translate-y-4"
          enter-to-class="opacity-100 transform translate-y-0"
          leave-active-class="transition duration-200"
          leave-from-class="opacity-100"
          leave-to-class="opacity-0"
        >
          <UCard 
            v-if="selectedPlan && selectedPlanData && currentPrice"
            class="bg-elevated/50"
            :ui="{ root: 'p-4' }"
          >
            <div>
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
                @click="handlePayment"
              >
                Оплатить
              </UButton>
            </div>
          </UCard>
        </Transition>
      </div>
    </template>
  </UDashboardPanel>
</template>
