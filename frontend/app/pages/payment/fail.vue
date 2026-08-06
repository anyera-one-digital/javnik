<script setup lang="ts">
definePageMeta({
  layout: 'auth'
  // без middleware auth — редирект с Т‑Банка всегда показывает результат
})

useSeoMeta({
  title: 'Оплата не завершена'
})

const route = useRoute()
const { isAuthenticated } = useAuth()

const orderId = computed(() => {
  const q = route.query.orderId
  return typeof q === 'string' ? q : Array.isArray(q) ? q[0] : undefined
})
</script>

<template>
  <div class="w-full max-w-lg mx-auto space-y-4">
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

    <UButton :to="isAuthenticated ? '/payment' : '/login'" color="neutral" block>
      {{ isAuthenticated ? 'Вернуться к тарифам' : 'Войти в кабинет' }}
    </UButton>
  </div>
</template>
