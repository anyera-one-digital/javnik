<script setup lang="ts">
import { subscriptionStatusText } from '~/utils/subscription'
import type { UserSubscription } from '~/types'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const route = useRoute()
const { fetchProfile } = useAuth()

const subscription = ref<UserSubscription | null>(null)
const loading = ref(true)

const orderId = computed(() => {
  const q = route.query.orderId
  return typeof q === 'string' ? q : Array.isArray(q) ? q[0] : undefined
})

onMounted(async () => {
  loading.value = true
  try {
    const profile = await fetchProfile()
    if (profile?.subscription) {
      subscription.value = profile.subscription
    }
  } finally {
    loading.value = false
  }
})

const statusText = computed(() => subscriptionStatusText(subscription.value))
</script>

<template>
  <UDashboardPanel id="payment-success">
    <template #header>
      <UDashboardNavbar title="Оплата прошла успешно">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="max-w-lg mx-auto py-8 px-4 space-y-4">
        <UCard>
          <div class="flex flex-col items-center text-center gap-3 py-4">
            <UIcon name="i-lucide-circle-check" class="size-12 text-green-600" />
            <h1 class="text-xl font-semibold">
              Спасибо за оплату!
            </h1>
            <p class="text-sm text-muted m-0">
              Подписка Pro будет активирована в течение минуты после подтверждения банком.
            </p>
            <p v-if="orderId" class="text-xs text-muted m-0">
              Номер заказа: {{ orderId }}
            </p>
          </div>
        </UCard>

        <UCard v-if="!loading && subscription" :ui="{ body: 'py-4' }">
          <p class="text-sm text-muted m-0 mb-2">
            Текущий тариф:
          </p>
          <UBadge color="neutral" variant="subtle">
            {{ subscription.planLabel }}
          </UBadge>
          <p v-if="statusText" class="text-sm text-muted mt-2 mb-0">
            {{ statusText }}
          </p>
        </UCard>

        <UButton to="/payment" color="neutral" block>
          К тарифам
        </UButton>
        <UButton to="/schedule" variant="outline" color="neutral" block>
          В расписание
        </UButton>
      </div>
    </template>
  </UDashboardPanel>
</template>
