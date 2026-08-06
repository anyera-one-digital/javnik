<script setup lang="ts">
/**
 * Страница возврата с Т‑Банка после неуспешной оплаты.
 * Без auth middleware и без зависимостей от профиля — должна рендериться всегда.
 */
definePageMeta({
  layout: false
})

useSeoMeta({
  title: 'Оплата не завершена'
})

const route = useRoute()
const colorMode = useColorMode()

const orderId = computed(() => {
  const q = route.query.orderId
  return typeof q === 'string' ? q : Array.isArray(q) ? q[0] : undefined
})

const isDark = computed(() => colorMode.value === 'dark')
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center px-4 py-10"
    :class="isDark ? 'bg-[#1b1718] text-white' : 'bg-white text-gray-900'"
  >
    <div class="w-full max-w-md space-y-5">
      <div
        class="rounded-2xl border p-6 text-center space-y-3"
        :class="isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'"
      >
        <div
          class="mx-auto flex size-14 items-center justify-center rounded-full"
          :class="isDark ? 'bg-red-500/15 text-red-400' : 'bg-red-50 text-red-600'"
        >
          <UIcon name="i-lucide-circle-x" class="size-8" />
        </div>
        <h1 class="text-xl font-semibold m-0">
          Платёж отменён или не прошёл
        </h1>
        <p
          class="text-sm m-0"
          :class="isDark ? 'text-white/60' : 'text-gray-600'"
        >
          Средства не списаны. Вы можете попробовать снова на странице тарифов.
        </p>
        <p
          v-if="orderId"
          class="text-xs m-0 break-all"
          :class="isDark ? 'text-white/40' : 'text-gray-400'"
        >
          Номер заказа: {{ orderId }}
        </p>
      </div>

      <UButton to="/payment" color="neutral" size="lg" block class="!rounded-xl">
        Вернуться к тарифам
      </UButton>
      <UButton to="/" variant="ghost" color="neutral" block>
        На главную
      </UButton>
    </div>
  </div>
</template>
