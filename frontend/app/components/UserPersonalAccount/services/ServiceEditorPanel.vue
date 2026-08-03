<script setup lang="ts">
import type { Service, ServiceImage } from '~/types'
import { formatDurationMinutes } from '~/utils/formatDuration'

export type ServiceSavePayload = {
  data: Partial<Service>
  portfolioFiles: File[]
  removedPortfolioImageIds: number[]
}

const props = defineProps<{
  service: Service | null
  saving?: boolean
}>()

const emit = defineEmits<{
  save: [payload: ServiceSavePayload]
  remove: []
}>()

const draft = reactive({
  name: '',
  description: '',
  duration: 60,
  price: 0,
  prepayment: 0,
  active: true
})

const editingField = ref<string | null>(null)

const existingPortfolioImages = ref<ServiceImage[]>([])
const portfolioImageFiles = ref<File[]>([])
const portfolioImagePreviews = ref<string[]>([])
const removedPortfolioImageIds = ref<number[]>([])
const portfolioImagesInput = ref<HTMLInputElement | null>(null)

function resetPortfolio(s: Service | null) {
  portfolioImageFiles.value.forEach((_, index) => {
    const url = portfolioImagePreviews.value[existingPortfolioImages.value.length + index]
    if (url?.startsWith('blob:')) URL.revokeObjectURL(url)
  })
  removedPortfolioImageIds.value = []
  portfolioImageFiles.value = []
  if (s?.portfolio_images?.length) {
    existingPortfolioImages.value = [...s.portfolio_images]
    portfolioImagePreviews.value = s.portfolio_images
      .map(img => img.image_url || '')
      .filter(Boolean)
  } else {
    existingPortfolioImages.value = []
    portfolioImagePreviews.value = []
  }
}

watch(
  () => props.service,
  (s) => {
    editingField.value = null
    if (!s) {
      resetPortfolio(null)
      return
    }
    draft.name = s.name || ''
    draft.description = s.description || ''
    draft.duration = Number(s.duration) || 60
    draft.price = Number(s.price) || 0
    draft.prepayment = Number(s.prepayment) || 0
    draft.active = s.active !== false
    resetPortfolio(s)
  },
  { immediate: true }
)

const formatMoney = (v: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(v)

const descriptionInput = ref<HTMLTextAreaElement | null>(null)

const descriptionLineCount = computed(() => {
  const text = draft.description || ''
  return Math.max(1, text.split('\n').length)
})

function resizeDescription() {
  const el = descriptionInput.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${el.scrollHeight}px`
}

function startEdit(field: string) {
  editingField.value = field
  if (field === 'description') {
    nextTick(() => {
      resizeDescription()
      descriptionInput.value?.focus()
    })
  }
}

function commitField() {
  editingField.value = null
}

function onPortfolioImagesChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files) return
  const files = Array.from(input.files)
  portfolioImageFiles.value = [...portfolioImageFiles.value, ...files]
  files.forEach((file) => {
    portfolioImagePreviews.value.push(URL.createObjectURL(file))
  })
  input.value = ''
}

function openPortfolioImagesDialog() {
  portfolioImagesInput.value?.click()
}

function removePortfolioImage(index: number) {
  const existingCount = existingPortfolioImages.value.length
  if (index < existingCount) {
    const imageId = existingPortfolioImages.value[index]?.id
    if (imageId) removedPortfolioImageIds.value.push(imageId)
    existingPortfolioImages.value.splice(index, 1)
  } else {
    const fileIndex = index - existingCount
    portfolioImageFiles.value.splice(fileIndex, 1)
    const url = portfolioImagePreviews.value[index]
    if (url?.startsWith('blob:')) URL.revokeObjectURL(url)
  }
  portfolioImagePreviews.value.splice(index, 1)
}

function saveAll() {
  if (!props.service) return
  emit('save', {
    data: {
      name: draft.name.trim() || props.service.name,
      description: draft.description,
      duration: Number(draft.duration) || 1,
      price: Number(draft.price) || 0,
      prepayment: Number(draft.prepayment) || 0,
      active: draft.active
    },
    portfolioFiles: [...portfolioImageFiles.value],
    removedPortfolioImageIds: [...removedPortfolioImageIds.value]
  })
}
</script>

<template>
  <div class="catalog-panel rounded-[14px] h-full min-h-0 flex flex-col overflow-hidden">
    <div
      v-if="!service"
      class="flex-1 flex items-center justify-center text-sm text-muted px-6 text-center"
    >
      Выберите услугу в каталоге
    </div>

    <template v-else>
      <div class="px-5 pt-4 pb-2 border-b border-default/40 shrink-0">
        <div class="flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <input
              v-if="editingField === 'name'"
              v-model="draft.name"
              class="w-full bg-transparent text-lg font-semibold text-highlighted outline-none border-b border-violet-500"
              @blur="commitField"
              @keydown.enter="commitField"
            >
            <h3
              v-else
              class="text-lg font-semibold text-highlighted truncate cursor-pointer hover:text-violet-400"
              @click="startEdit('name')"
            >
              {{ draft.name || service.name }}
            </h3>
          </div>
          <UButton
            icon="i-lucide-pencil"
            color="neutral"
            variant="ghost"
            size="xs"
            class="shrink-0"
            @click="startEdit('name')"
          />
        </div>
      </div>

      <div class="flex-1 min-h-0 overflow-auto px-5 pt-1 pb-5 space-y-1">
        <!-- Description: one line by default, grows only with extra lines -->
        <div class="flex items-start gap-3 py-2 border-b border-default/30">
          <div class="min-w-0 flex-1">
            <textarea
              v-if="editingField === 'description'"
              ref="descriptionInput"
              v-model="draft.description"
              rows="1"
              placeholder="Описание услуги"
              class="w-full bg-transparent text-sm text-muted outline-none resize-none border-b border-violet-500 leading-snug overflow-hidden"
              @input="resizeDescription"
              @blur="commitField"
            />
            <p
              v-else
              class="text-sm text-muted cursor-pointer hover:text-highlighted leading-snug"
              :class="descriptionLineCount > 1 ? 'whitespace-pre-wrap' : 'truncate'"
              @click="startEdit('description')"
            >
              {{ draft.description || 'Добавить описание' }}
            </p>
          </div>
          <UButton
            icon="i-lucide-pencil"
            color="neutral"
            variant="ghost"
            size="xs"
            class="shrink-0"
            @click="startEdit('description')"
          />
        </div>

        <!-- Duration -->
        <div class="flex items-center gap-3 py-3 border-b border-default/30">
          <UIcon name="i-lucide-clock" class="size-4 text-muted shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="text-[11px] text-muted mb-0.5">Длительность</p>
            <input
              v-if="editingField === 'duration'"
              v-model.number="draft.duration"
              type="number"
              min="1"
              class="w-full bg-transparent text-sm text-highlighted outline-none"
              @blur="commitField"
              @keydown.enter="commitField"
            >
            <p v-else class="text-sm text-highlighted">{{ formatDurationMinutes(draft.duration) }}</p>
          </div>
          <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" size="xs" @click="startEdit('duration')" />
        </div>

        <!-- Price -->
        <div class="flex items-center gap-3 py-3 border-b border-default/30">
          <UIcon name="i-lucide-banknote" class="size-4 text-muted shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="text-[11px] text-muted mb-0.5">Цена</p>
            <input
              v-if="editingField === 'price'"
              v-model.number="draft.price"
              type="number"
              min="0"
              class="w-full bg-transparent text-sm text-highlighted outline-none"
              @blur="commitField"
              @keydown.enter="commitField"
            >
            <p v-else class="text-sm text-highlighted">{{ formatMoney(draft.price) }}</p>
          </div>
          <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" size="xs" @click="startEdit('price')" />
        </div>

        <!-- Publication = online booking availability -->
        <div class="flex items-center gap-3 py-3 border-b border-default/30">
          <UIcon name="i-lucide-globe" class="size-4 text-muted shrink-0" />
          <div class="flex-1 min-w-0">
            <p class="text-[11px] text-muted mb-0.5">Статус</p>
            <p class="text-sm text-highlighted">
              {{ draft.active ? 'Опубликована' : 'Скрыта' }}
            </p>
            <p class="text-[11px] text-muted mt-0.5">
              {{ draft.active ? 'Доступна для онлайн-записи' : 'Скрыта со страницы записи' }}
            </p>
          </div>
          <USwitch v-model="draft.active" color="primary" :ui="{ base: 'data-[state=checked]:bg-violet-500' }" />
        </div>

        <!-- Portfolio / examples -->
        <div class="pt-4">
          <div class="flex items-center justify-between gap-2 mb-3">
            <div>
              <p class="text-sm font-medium text-highlighted">Примеры работ</p>
              <p class="text-[11px] text-muted mt-0.5">Фото для портфолио услуги</p>
            </div>
            <UButton
              label="Добавить"
              icon="i-lucide-upload"
              color="neutral"
              variant="outline"
              size="xs"
              @click="openPortfolioImagesDialog"
            />
          </div>

          <div v-if="portfolioImagePreviews.length" class="grid grid-cols-3 gap-2">
            <div
              v-for="(preview, index) in portfolioImagePreviews"
              :key="`${preview}-${index}`"
              class="relative aspect-square rounded-lg overflow-hidden border border-default/40"
            >
              <img :src="preview" alt="" class="w-full h-full object-cover">
              <UButton
                icon="i-lucide-x"
                color="error"
                variant="solid"
                size="xs"
                square
                class="icon-btn-round-sm absolute top-1 right-1"
                @click="removePortfolioImage(index)"
              />
            </div>
          </div>
          <p v-else class="text-sm text-muted py-4 text-center border border-dashed border-default/40 rounded-xl">
            Пока нет фото — добавьте примеры работ
          </p>

          <input
            ref="portfolioImagesInput"
            type="file"
            accept="image/*"
            multiple
            class="hidden"
            @change="onPortfolioImagesChange"
          >
        </div>
      </div>

      <div class="p-4 border-t border-default/40 flex items-center gap-2 shrink-0">
        <UButton
          label="Сохранить"
          class="min-w-0 flex-1 !bg-violet-500 !text-white hover:!bg-violet-400 justify-center"
          :loading="saving"
          @click="saveAll"
        />
        <UButton
          icon="i-lucide-trash"
          color="error"
          variant="outline"
          square
          class="icon-btn-round shrink-0"
          :disabled="saving"
          @click="emit('remove')"
        />
      </div>
    </template>
  </div>
</template>
