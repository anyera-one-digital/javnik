<script setup lang="ts">
import { Expand, Volume2, X } from '@lucide/vue'
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle
} from 'reka-ui'

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
const theaterRef = ref<HTMLVideoElement | null>(null)
const theaterOpen = ref(false)
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

watch(theaterOpen, async (open) => {
  if (open) {
    pausePreview()
    await nextTick()
    const el = theaterRef.value
    if (!el) return
    el.currentTime = previewRef.value?.currentTime ?? 0
    el.muted = false
    try {
      await el.play()
    } catch {
      // Пользователь может нажать play вручную
    }
  } else {
    const preview = previewRef.value
    if (preview && theaterRef.value) {
      preview.currentTime = theaterRef.value.currentTime
    }
    theaterRef.value?.pause()
    if (props.active) await playPreview()
  }
})

onMounted(() => {
  prefersReducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
})

onBeforeUnmount(() => {
  pausePreview()
  theaterRef.value?.pause()
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

        <!-- Титры внизу кадра -->
        <div class="showcase-demo__titles" aria-live="polite">
          <small>{{ screen.eyebrow }}</small>
          <strong>{{ captionText }}</strong>
        </div>

        <!-- Развернуть плеер со звуком -->
        <button
          v-if="hasVideo"
          type="button"
          class="showcase-demo__expand focus-ring"
          aria-label="Смотреть со звуком в полном размере"
          @click="theaterOpen = true"
        >
          <Expand :size="16" :stroke-width="1.8" />
          <span>Со звуком</span>
        </button>

        <div
          v-else
          class="showcase-demo__soon"
          title="Сюда подставится видео-превью экрана"
        >
          Видео скоро
        </div>
      </div>
    </div>

    <DialogRoot v-model:open="theaterOpen">
      <DialogPortal>
        <DialogOverlay class="showcase-theater__overlay" />
        <DialogContent class="showcase-theater focus-ring" aria-describedby="showcase-theater-desc">
          <div class="showcase-theater__head">
            <div>
              <DialogTitle class="showcase-theater__title">{{ screen.label }}</DialogTitle>
              <DialogDescription id="showcase-theater-desc" class="showcase-theater__desc">
                {{ screen.eyebrow }} · полный просмотр со звуком
              </DialogDescription>
            </div>
            <DialogClose class="showcase-theater__close focus-ring" aria-label="Закрыть">
              <X :size="18" :stroke-width="1.8" />
            </DialogClose>
          </div>

          <div class="showcase-theater__player">
            <video
              v-if="hasVideo"
              ref="theaterRef"
              class="showcase-theater__video"
              :poster="screen.image"
              :src="screen.video!"
              controls
              playsinline
              preload="metadata"
            />
          </div>

          <p class="showcase-theater__hint">
            <Volume2 :size="14" :stroke-width="1.8" />
            В превью звук выключен; здесь можно смотреть с озвучкой.
          </p>
        </DialogContent>
      </DialogPortal>
    </DialogRoot>
  </div>
</template>
