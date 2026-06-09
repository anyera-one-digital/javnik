<template>
  <UPageHero
    v-if="title"
    :title="title"
    :description="description"
  >
    <template #footer>
      <div class="flex flex-col items-center gap-4 text-center">
        <UButton
          to="/signup"
          size="xl"
          color="neutral"
          class="!min-h-[52px] !h-auto !px-8 !py-3.5 !text-base sm:!text-lg rounded-full bg-gray-900 text-white hover:bg-gray-800 dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100"
        >
          Попробовать бесплатно
        </UButton>
        <p class="text-xs text-muted max-w-sm m-0">
          Тестируйте сервис 14 дней бесплатно и без привязки карты
        </p>
      </div>
    </template>

    <div class="relative">
      <UPageCard
        variant="subtle"
        class="rounded-2xl"
      >
        <video
          class="rounded-xl landing-hero-video"
          preload="none"
          poster="https://res.cloudinary.com/nuxt/video/upload/so_3.3/v1708511800/ui-pro/video-nuxt-ui-pro_kwfbdh.jpg"
          controls
          controlslist="nodownload noplaybackrate noremoteplayback"
          disablepictureinpicture
          disableremoteplayback
        >
          <source
            src="https://res.cloudinary.com/nuxt/video/upload/v1708511800/ui-pro/video-nuxt-ui-pro_kwfbdh.webm"
            type="video/webm"
          >
          <source
            src="https://res.cloudinary.com/nuxt/video/upload/v1708511800/ui-pro/video-nuxt-ui-pro_kwfbdh.mp4"
            type="video/mp4"
          >
          <source
            src="https://res.cloudinary.com/nuxt/video/upload/v1708511800/ui-pro/video-nuxt-ui-pro_kwfbdh.ogg"
            type="video/ogg"
          >
        </video>
      </UPageCard>
    </div>
  </UPageHero>
</template>

<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
}>()
</script>
