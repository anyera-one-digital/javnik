<script setup lang="ts">
export type ShowcaseScreen = {
  label: string
  eyebrow: string
  title: string
  image: string
  alt: string
  /** Путь к превью-ролику. Пока нет файла — показывается постер (image). */
  video?: string | null
  /** Доп. строка титров; по умолчанию = title */
  caption?: string
}

const props = defineProps<{
  screen: ShowcaseScreen
  active: boolean
}>()

const previewRef = ref<HTMLVideoElement | null>(null)
const prefersReducedMotion = ref(false)

const hasVideo = computed(() => Boolean(props.screen.video))
const captionText = computed(() => props.screen.caption || props.screen.title)

async function playPreview() {
  const el = previewRef.value
  if (!el || !hasVideo.value || !props.active) return
  if (prefersReducedMotion.value) {
    el.pause()
    return
  }
  el.muted = true
  el.defaultMuted = true
  try {
    await el.play()
  } catch {
    // Автоплей может быть заблокирован — оставляем постер
  }
}

function pausePreview() {
  previewRef.value?.pause()
}

watch(
  () => [props.active, props.screen.video] as const,
  async ([active]) => {
    await nextTick()
    if (active) await playPreview()
    else pausePreview()
  },
  { immediate: true }
)

onMounted(() => {
  prefersReducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
})

onBeforeUnmount(() => {
  pausePreview()
})
</script>

<template>
  <div class="showcase-demo">
    <div class="showcase-window">
      <div class="showcase-window__bar">
        <i /><i /><i />
        <span>yavnik.ru</span>
      </div>

      <div class="showcase-demo__stage">
        <Transition name="screen" mode="out-in">
          <div :key="screen.label" class="showcase-demo__media">
            <video
              v-if="hasVideo"
              ref="previewRef"
              class="showcase-demo__video"
              :poster="screen.image"
              :src="screen.video!"
              muted
              playsinline
              loop
              preload="metadata"
              aria-label="Превью интерфейса"
            />
            <img
              v-else
              class="showcase-demo__poster"
              :src="screen.image"
              :alt="screen.alt"
              width="2160"
              height="1216"
            >
          </div>
        </Transition>

        <div class="showcase-demo__titles" aria-live="polite">
          <small>{{ screen.eyebrow }}</small>
          <strong>{{ captionText }}</strong>
        </div>
      </div>
    </div>
  </div>
</template>
