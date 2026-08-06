<script setup lang="ts">
/**
 * Страница возврата с Т‑Банка после успешной оплаты.
 * Без auth middleware — должна рендериться всегда после редиректа банка.
 */
definePageMeta({
  layout: false
})

useSeoMeta({
  title: 'Оплата успешна'
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
          :class="isDark ? 'bg-emerald-500/15 text-emerald-400' : 'bg-emerald-50 text-emerald-600'"
        >
          <UIcon name="i-lucide-circle-check" class="size-8" />
        </div>
        <h1 class="text-xl font-semibold m-0">
          Спасибо за оплату!
        </h1>
        <p
          class="text-sm m-0"
          :class="isDark ? 'text-white/60' : 'text-gray-600'"
        >
          Подписка Pro активирована или будет активирована в течение минуты после подтверждения банком.
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
        К тарифам
      </UButton>
      <UButton to="/schedule" variant="outline" color="neutral" block class="!rounded-xl">
        В расписание
      </UButton>
    </div>
  </div>
</template>
