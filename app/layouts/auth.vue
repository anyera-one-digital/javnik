<template>
  <div class="auth-page auth-forms-neutral min-h-screen flex items-center justify-center px-4 py-4 sm:py-6">
    <UButton
      icon="i-lucide-chevron-left"
      to="/"
      size="lg"
      color="neutral"
      variant="subtle"
      class="absolute left-4 top-4 sm:left-6 sm:top-6 rounded-full z-10 bg-gray-200 text-gray-900 hover:bg-gray-300 dark:bg-white/10 dark:text-white dark:hover:bg-white/20"
    />

    <UPageCard
      variant="subtle"
      class="max-w-sm w-full my-auto max-h-[calc(100vh-3rem)] overflow-hidden flex flex-col"
    >
      <div class="overflow-y-auto flex-1 min-h-0 py-4 px-4 sm:py-5 sm:px-5">
        <slot />
      </div>
    </UPageCard>
  </div>
</template>
