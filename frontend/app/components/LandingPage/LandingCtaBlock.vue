<script setup lang="ts">
defineProps<{
  cta?: {
    title?: string
    description?: string
    links?: Array<{ label: string; to?: string; trailingIcon?: string }>
  }
}>()
</script>

<template>
  <div
    v-if="cta"
    class="py-16 sm:py-24"
  >
    <UContainer>
      <div class="flex flex-col items-center text-center gap-8">
        <!-- Крупный заголовок как на первом скрине -->
        <h2 class="text-4xl sm:text-5xl md:text-6xl font-bold text-highlighted tracking-tight max-w-4xl">
          {{ cta.title }}
        </h2>

        <!-- Кнопка в стиле pill: белая/светлая в тёмной теме, тёмная в светлой -->
        <div
          v-if="cta.links?.length"
          class="flex flex-wrap justify-center gap-4"
        >
          <UButton
            v-for="(link, i) in cta.links"
            :key="i"
            :to="link.to"
            :trailing-icon="link.trailingIcon"
            size="xl"
            color="neutral"
            :variant="'solid'"
            class="rounded-full bg-gray-900 text-white hover:bg-gray-800 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100"
          >
            {{ link.label }}
          </UButton>
        </div>
      </div>
    </UContainer>
  </div>
</template>
