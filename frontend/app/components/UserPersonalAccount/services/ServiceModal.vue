<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import type { Service } from '~/types'

const props = defineProps<{
  service?: Service
  modelValue?: boolean
}>()

const emit = defineEmits<{
  saved: []
  close: []
  'update:modelValue': [value: boolean]
}>()

const schema = z.object({
  name: z.string().min(2, 'Слишком короткое'),
  description: z.string().optional().or(z.literal('')),
  duration: z.number().min(1, 'Минимум 1 минута'),
  price: z.number().min(0, 'Цена не может быть отрицательной')
})

type Schema = z.output<typeof schema>

const open = computed({
  get: () => {
    // Если modelValue передан, используем его, иначе используем внутреннее состояние
    if (props.modelValue !== undefined) {
      return props.modelValue
    }
    return internalOpen.value
  },
  set: (value) => {
    if (props.modelValue !== undefined) {
      emit('update:modelValue', value)
    } else {
      internalOpen.value = value
    }
  }
})

const internalOpen = ref(false)

watch(() => props.service, (service) => {
  if (service) {
    if (props.modelValue !== undefined) {
      emit('update:modelValue', true)
    } else {
      internalOpen.value = true
    }
  }
})

watch(() => props.modelValue, (value) => {
  // modelValue управляется извне через computed open
  // Здесь ничего не делаем, так как computed уже обрабатывает это
})

watch(open, (isOpen) => {
  if (!isOpen) {
    if (props.modelValue !== undefined) {
      emit('update:modelValue', false)
    } else {
      internalOpen.value = false
    }
    if (!props.service) {
      // Сбрасываем форму при закрытии для новой услуги
      state.name = undefined
      state.description = undefined
      state.duration = undefined
      state.price = undefined
      // Сбрасываем изображения
      portfolioImageFiles.value.forEach(file => {
        const index = portfolioImageFiles.value.indexOf(file)
        if (portfolioImagePreviews.value[index] && portfolioImagePreviews.value[index].startsWith('blob:')) {
          URL.revokeObjectURL(portfolioImagePreviews.value[index])
        }
      })
      portfolioImageFiles.value = []
      portfolioImagePreviews.value = []
    }
  } else {
    // Когда модал открывается, синхронизируем состояние
    if (props.modelValue !== undefined && !props.modelValue) {
      emit('update:modelValue', true)
    }
  }
})

const state = reactive<Partial<Schema>>({
  name: undefined,
  description: undefined,
  duration: undefined,
  price: undefined
})

// Состояния для изображений
const portfolioImageFiles = ref<File[]>([])
const portfolioImagePreviews = ref<string[]>([])
const existingPortfolioImages = ref<any[]>([]) // Существующие изображения из БД
const removedPortfolioImageIds = ref<number[]>([]) // ID удаленных изображений

// Refs для input элементов
const portfolioImagesInput = ref<HTMLInputElement | null>(null)

// Загрузка существующих изображений при редактировании
watch(() => props.service, (service) => {
  if (service) {
    state.name = service.name
    state.description = service.description || ''
    state.duration = service.duration
    state.price = service.price
    // Загружаем превью существующих изображений
    if (service.portfolio_images && service.portfolio_images.length > 0) {
      existingPortfolioImages.value = service.portfolio_images
      portfolioImagePreviews.value = service.portfolio_images
        .map(img => img.image_url || '')
        .filter(url => url)
    } else {
      existingPortfolioImages.value = []
      portfolioImagePreviews.value = []
    }
    // Сбрасываем выбранные файлы при редактировании (чтобы не перезаписывать существующие, если не выбраны новые)
    portfolioImageFiles.value = []
    removedPortfolioImageIds.value = []
  } else {
    // Сброс формы для новой услуги
    state.name = undefined
    state.description = undefined
    state.duration = undefined
    state.price = undefined
    portfolioImageFiles.value.forEach((_, index) => {
      if (portfolioImagePreviews.value[index] && portfolioImagePreviews.value[index].startsWith('blob:')) {
        URL.revokeObjectURL(portfolioImagePreviews.value[index])
      }
    })
    portfolioImageFiles.value = []
    portfolioImagePreviews.value = []
  }
}, { immediate: true })

// Обработчики загрузки файлов
function onPortfolioImagesChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    const files = Array.from(input.files)
    portfolioImageFiles.value = [...portfolioImageFiles.value, ...files]
    files.forEach(file => {
      portfolioImagePreviews.value.push(URL.createObjectURL(file))
    })
  }
  // Сбрасываем значение input, чтобы можно было выбрать те же файлы снова
  input.value = ''
}

// Функции для открытия диалога выбора файлов
function openPortfolioImagesDialog() {
  if (process.client && portfolioImagesInput.value) {
    portfolioImagesInput.value.click()
  }
}

function removePortfolioImage(index: number) {
  // Проверяем, это новое изображение или существующее
  const existingCount = existingPortfolioImages.value.length
  if (index < existingCount) {
    // Удаляем существующее изображение
    const imageId = existingPortfolioImages.value[index].id
    if (imageId) {
      removedPortfolioImageIds.value.push(imageId)
    }
    existingPortfolioImages.value.splice(index, 1)
  } else {
    // Удаляем новое изображение (файл)
    const fileIndex = index - existingCount
    portfolioImageFiles.value.splice(fileIndex, 1)
    if (portfolioImagePreviews.value[index] && portfolioImagePreviews.value[index].startsWith('blob:')) {
      URL.revokeObjectURL(portfolioImagePreviews.value[index])
    }
  }
  portfolioImagePreviews.value.splice(index, 1)
}

const toast = useToast()
const { accessToken } = useAuth()

async function onSubmit(event: FormSubmitEvent<Schema>) {
  try {
    // Проверяем наличие токена
    let token = accessToken.value
    
    // Если токена нет, пытаемся загрузить из localStorage
    if (!token && process.client) {
      token = localStorage.getItem('auth.accessToken')
      if (token) {
        // Обновляем токен в composable
        accessToken.value = token
      }
    }
    
    if (!token) {
      toast.add({
        title: 'Ошибка',
        description: 'Необходима авторизация. Пожалуйста, войдите в систему.',
        color: 'error'
      })
      return
    }
    
    // Убеждаемся, что токен в правильном формате
    const authToken = token.startsWith('Bearer ') ? token : `Bearer ${token}`

    // Убеждаемся, что все обязательные поля заполнены
    if (!event.data.duration || event.data.duration <= 0) {
      toast.add({
        title: 'Ошибка валидации',
        description: 'Длительность должна быть больше 0',
        color: 'error'
      })
      return
    }

    if (event.data.price === undefined || event.data.price < 0) {
      toast.add({
        title: 'Ошибка валидации',
        description: 'Цена должна быть указана и не может быть отрицательной',
        color: 'error'
      })
      return
    }

    // Создаем FormData для отправки файлов
    const formData = new FormData()
    formData.append('name', event.data.name.trim())
    formData.append('duration', String(Number(event.data.duration)))
    formData.append('price', String(Number(event.data.price)))
    
    // Описание передаем только если оно не пустое
    if (event.data.description && event.data.description.trim()) {
      formData.append('description', event.data.description.trim())
    }
    
    // Добавляем изображения портфолио
    portfolioImageFiles.value.forEach((file) => {
      formData.append('portfolio_images', file)
    })
    
    // Добавляем информацию об удаленных изображениях (для обновления)
    if (props.service && removedPortfolioImageIds.value.length > 0) {
      formData.append('removed_portfolio_image_ids', JSON.stringify(removedPortfolioImageIds.value))
    }
    
    console.log('Sending form data to server')

    if (props.service) {
      // Обновление существующей услуги
      await $fetch(`/api/services/${props.service.id}/`, {
        method: 'PUT',
        headers: {
          Authorization: authToken
        },
        body: formData
      })

      toast.add({
        title: 'Успешно',
        description: `Услуга "${event.data.name}" обновлена`,
        color: 'success'
      })
    } else {
      // Создание новой услуги
      const createdService = await $fetch<Service>('/api/services/', {
        method: 'POST',
        headers: {
          Authorization: authToken
        },
        body: formData
      })
      
      console.log('Service created successfully:', createdService)
      
      toast.add({
        title: 'Успешно',
        description: `Новая услуга "${event.data.name}" создана`,
        color: 'success'
      })
    }

    open.value = false
    // Сброс формы
    state.name = undefined
    state.description = undefined
    state.duration = undefined
    state.price = undefined
    coverImageFile.value = null
    coverImagePreview.value = null
    portfolioImageFiles.value = []
    portfolioImagePreviews.value = []
    
    // Эмитим событие saved для обновления списка
    emit('saved')
  } catch (error: any) {
    console.error('Error saving service:', error)
    console.error('Error status:', error.statusCode || error.status)
    console.error('Error data:', error.data)
    console.error('Error response:', error.response)
    
    let errorMessage = 'Произошла ошибка при сохранении услуги'
    
    // Проверяем разные форматы ошибок от $fetch
    const errorData = error.data || error.response?.data || error
    
    if (errorData) {
      // Django REST Framework возвращает ошибки валидации в формате { field: ['error'] }
      if (typeof errorData === 'object' && !Array.isArray(errorData)) {
        const validationErrors = Object.entries(errorData)
          .filter(([key]) => key !== 'detail' && key !== 'message')
          .map(([field, errors]: [string, any]) => {
            const fieldName = field === 'duration' ? 'Длительность' : 
                             field === 'price' ? 'Цена' : 
                             field === 'name' ? 'Название' : 
                             field === 'description' ? 'Описание' : field
            const errorList = Array.isArray(errors) ? errors.join(', ') : String(errors)
            return `${fieldName}: ${errorList}`
          })
        
        if (validationErrors.length > 0) {
          errorMessage = validationErrors.join('\n')
        } else if (errorData.detail) {
          errorMessage = String(errorData.detail)
        } else if (errorData.message) {
          errorMessage = String(errorData.message)
        } else {
          // Показываем весь объект ошибки для отладки
          errorMessage = JSON.stringify(errorData, null, 2)
        }
      } else if (typeof errorData === 'string') {
        errorMessage = errorData
      } else if (errorData.detail) {
        errorMessage = String(errorData.detail)
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    toast.add({
      title: 'Ошибка',
      description: errorMessage,
      color: 'error',
      timeout: 10000 // Увеличиваем время показа для длинных сообщений
    })
  }
}
</script>

<template>
  <UModal
    v-model:open="open"
    :title="service ? 'Редактировать услугу' : 'Новая услуга'"
    :description="service ? 'Изменить информацию об услуге' : 'Создать новую услугу'"
  >
    <template #trigger>
      <slot>
        <UButton
          v-if="!modelValue"
          :label="service ? 'Редактировать' : 'Новая услуга'"
          icon="i-lucide-plus"
          class="service-modal-trigger"
          data-service-modal
          @click="open = true"
        />
      </slot>
    </template>

    <template #body>
      <UForm
        :schema="schema"
        :state="state"
        class="space-y-4"
        @submit="onSubmit"
      >
        <UFormField label="Название" placeholder="Название услуги" name="name" required>
          <UInput v-model="state.name" class="w-full" />
        </UFormField>

        <UFormField label="Описание" placeholder="Описание услуги" name="description">
          <UTextarea v-model="state.description" class="w-full" :rows="3" />
        </UFormField>

        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Длительность (мин)" placeholder="30" name="duration" required>
            <UInput v-model.number="state.duration" type="number" class="w-full" />
          </UFormField>

          <UFormField label="Цена (₽)" placeholder="1000" name="price" required>
            <UInput v-model.number="state.price" type="number" class="w-full" />
          </UFormField>
        </div>

        <!-- Галерея портфолио -->
        <UFormField label="Примеры работ" description="Загрузите несколько фотографий для портфолио услуги">
          <div class="space-y-3">
            <div v-if="portfolioImagePreviews.length > 0" class="grid grid-cols-3 gap-3">
              <div
                v-for="(preview, index) in portfolioImagePreviews"
                :key="index"
                class="relative aspect-square"
              >
                <img
                  :src="preview"
                  alt="Превью изображения портфолио"
                  class="w-full h-full object-cover rounded-lg border border-default"
                />
                <UButton
                  icon="i-lucide-x"
                  color="red"
                  variant="solid"
                  size="sm"
                  square
                  class="absolute top-1 right-1"
                  @click="removePortfolioImage(index)"
                />
              </div>
            </div>
            <UButton
              label="Добавить фото"
              color="neutral"
              variant="outline"
              icon="i-lucide-upload"
              @click="openPortfolioImagesDialog"
            />
            <input
              ref="portfolioImagesInput"
              type="file"
              accept="image/*"
              multiple
              class="hidden"
              @change="onPortfolioImagesChange"
            />
          </div>
        </UFormField>

        <div class="flex justify-end gap-2">
          <UButton
            label="Отмена"
            color="neutral"
            variant="subtle"
            @click="open = false"
          />
          <UButton
            :label="service ? 'Сохранить' : 'Создать'"
            color="neutral"
            variant="solid"
            class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
            type="submit"
          />
        </div>
      </UForm>
    </template>
  </UModal>
</template>

