<script setup lang="ts">
definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const route = useRoute()

const orderId = computed(() => {
  const q = route.query.orderId
  return typeof q === 'string' ? q : Array.isArray(q) ? q[0] : undefined
})
</script>

<template>
  <UDashboardPanel id="payment-fail">
    <template #header>
      <UDashboardNavbar title="Оплата не завершена">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="max-w-lg mx-auto py-8 px-4 space-y-4">
        <UCard>
          <div class="flex flex-col items-center text-center gap-3 py-4">
            <UIcon name="i-lucide-circle-x" class="size-12 text-red-500" />
            <h1 class="text-xl font-semibold">
              Платёж отменён или не прошёл
            </h1>
            <p class="text-sm text-muted m-0">
              Средства не списаны. Вы можете попробовать снова на странице тарифов.
            </p>
            <p v-if="orderId" class="text-xs text-muted m-0">
              Номер заказа: {{ orderId }}
            </p>
          </div>
        </UCard>

        <UButton to="/payment" color="neutral" block>
          Вернуться к тарифам
        </UButton>
      </div>
    </template>
  </UDashboardPanel>
</template>
