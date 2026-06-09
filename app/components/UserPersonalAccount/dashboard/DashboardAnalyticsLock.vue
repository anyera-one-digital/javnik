<script setup lang="ts">
defineProps<{
  locked: boolean
}>()
</script>

<template>
  <div class="relative">
    <div
      class="flex flex-col gap-4 sm:gap-6 transition-[filter]"
      :class="locked ? 'blur-md pointer-events-none select-none' : ''"
    >
      <slot />
    </div>

    <div
      v-if="locked"
      class="absolute inset-0 z-10 flex items-center justify-center p-4"
    >
      <div class="max-w-md w-full rounded-2xl border border-default bg-default/95 backdrop-blur-sm p-6 text-center shadow-lg">
        <div class="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-gray-900/10 dark:bg-white/10">
          <UIcon name="i-lucide-lock" class="size-6 text-highlighted" />
        </div>
        <h2 class="text-lg font-semibold text-highlighted mb-2">
          Аналитика доступна на Pro
        </h2>
        <p class="text-sm text-muted mb-5 m-0">
          Оформите или продлите подписку Pro, чтобы видеть статистику, доход и распределение записей.
        </p>
        <UButton
          to="/payment"
          color="neutral"
          size="lg"
          label="Перейти к тарифам"
          trailing-icon="i-lucide-arrow-right"
          class="justify-center"
        />
      </div>
    </div>
  </div>
</template>
