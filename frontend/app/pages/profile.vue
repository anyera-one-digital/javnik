<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import type { User } from '~/types'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const { user, fetchProfile, uploadAvatar, getAuthHeaders } = useAuth()
const toast = useToast()
const fileRef = ref<HTMLInputElement>()
const addressSuggestRef = ref<HTMLElement>()
const addressInputFocused = ref(false)
type AddressSuggestion = {
  address: string
  title: string
  uri?: string
}

const { suggestions: addressSuggestions, loading: addressSuggestLoading, isOpen: addressSuggestOpen, search: addressSuggestSearch, select: addressSuggestSelect, close: addressSuggestClose } = useAddressSuggest()

const addressSearchQuery = ref('')
const specialtiesLoading = ref(false)
const specialtyOptions = ref<{ label: string; value: number | null }[][]>([])

onClickOutside(addressSuggestRef, () => addressSuggestClose())

interface SpecialtyCategoryItem {
  id: number
  name: string
  order: number
  specialties: { id: number; name: string; order: number }[]
}

const isLoading = ref(false)
const isUploadingAvatar = ref(false)
const isSyncingProfile = ref(false)
const isProfileHydrated = ref(false)
const profileDirty = ref(false)

onMounted(async () => {
  await fetchProfile()
  specialtiesLoading.value = true
  try {
    const data = await $fetch<SpecialtyCategoryItem[]>('/api/public/specialties/')
    const groups = data.map(cat =>
      cat.specialties.map(s => ({ label: s.name, value: s.id }))
    )
    specialtyOptions.value = [[{ label: '— Не выбрано —', value: null }], ...groups]
  } finally {
    specialtiesLoading.value = false
  }
})

const profileSchema = z.object({
  username: z.string().min(3, 'Минимум 3 символа').max(30, 'Максимум 30 символов').regex(/^[a-zA-Z0-9_-]+$/, 'Только буквы, цифры, дефисы и подчеркивания'),
  first_name: z.string().min(1, 'Имя обязательно').optional().or(z.literal('')),
  last_name: z.string().optional(),
  phone: z.string().optional(),
  email: z.string().email('Неверный формат электронной почты').optional(),
  specialty_id: z.number().nullable().optional(),
  bio: z.string().optional(),
  city: z.string().optional(),
  service_address: z.string().optional()
})

type ProfileSchema = z.output<typeof profileSchema>

const profile = reactive<Partial<ProfileSchema & { avatar_url?: string }>>({
  username: user.value?.username || '',
  first_name: user.value?.first_name || '',
  last_name: user.value?.last_name || '',
  phone: user.value?.phone || '',
  email: user.value?.email || '',
  specialty_id: user.value?.specialty_id ?? null,
  bio: user.value?.bio || '',
  city: user.value?.city || '',
  service_address: user.value?.service_address || '',
  avatar_url: user.value?.avatar_url || undefined
})

function syncProfileFromUser(newUser: User | null) {
  if (!newUser) return

  isSyncingProfile.value = true
  profile.username = newUser.username || ''
  profile.first_name = newUser.first_name || ''
  profile.last_name = newUser.last_name || ''
  profile.phone = newUser.phone || ''
  profile.email = newUser.email || ''
  profile.specialty_id = newUser.specialty_id ?? null
  profile.bio = newUser.bio || ''
  profile.city = newUser.city || ''
  profile.service_address = newUser.service_address || ''
  profile.avatar_url = newUser.avatar_url || undefined
  addressSearchQuery.value = newUser.service_address || ''
  profileDirty.value = false
  isProfileHydrated.value = true
  nextTick(() => {
    isSyncingProfile.value = false
  })
}

watch(() => user.value, (newUser) => {
  if (!newUser) return
  if (!isProfileHydrated.value || !profileDirty.value) {
    syncProfileFromUser(newUser)
  }
}, { immediate: true })

watch(profile, () => {
  if (!isSyncingProfile.value && isProfileHydrated.value) {
    profileDirty.value = true
  }
}, { deep: true })

watch(() => profile.service_address, (val) => {
  if (!addressInputFocused.value) {
    addressSearchQuery.value = val ?? ''
  }
}, { immediate: true })

watch(() => addressSearchQuery.value, (val) => {
  if (addressInputFocused.value && profile.service_address !== val) {
    profile.service_address = val ?? ''
  }
  if (addressInputFocused.value) {
    addressSuggestSearch(val ?? '')
  } else {
    addressSuggestClose()
  }
})

function onAddressSelect(item: AddressSuggestion) {
  profile.service_address = addressSuggestSelect(item)
  addressSearchQuery.value = profile.service_address
}

function onAddressBlur() {
  addressInputFocused.value = false
  profile.service_address = addressSearchQuery.value.trim()
  addressSearchQuery.value = profile.service_address
}

function clearAddress() {
  profile.service_address = ''
  addressSearchQuery.value = ''
  addressSuggestClose()
}

async function onSubmit(event: FormSubmitEvent<ProfileSchema>) {
  isLoading.value = true
  try {
    const response = await $fetch<{ user: any; message: string }>('/api/auth/profile/update/', {
      method: 'PATCH',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      } as HeadersInit,
      body: {
        username: event.data.username,
        first_name: event.data.first_name || '',
        last_name: event.data.last_name || '',
        phone: event.data.phone || '',
        specialty_id: profile.specialty_id ?? null,
        bio: event.data.bio || '',
        city: event.data.city || '',
        service_address: profile.service_address || ''
      }
    })

    await fetchProfile()
    syncProfileFromUser(user.value ?? response.user)

    toast.add({
      title: 'Успешно',
      description: response.message || 'Ваши настройки были обновлены.',
      icon: 'i-lucide-check',
      color: 'success'
    })
  } catch (error: any) {
    const errorMessage = error.data?.detail || error.data?.message || 'Ошибка при обновлении профиля'
    toast.add({
      title: 'Ошибка',
      description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
      color: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement

  if (!input.files?.length) {
    return
  }

  const file = input.files[0]
  if (!file) {
    return
  }

  if (file.size > 1024 * 1024) {
    toast.add({
      title: 'Ошибка',
      description: 'Размер файла превышает 1 МБ.',
      color: 'error'
    })
    return
  }

  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
  if (!allowedTypes.includes(file.type)) {
    toast.add({
      title: 'Ошибка',
      description: 'Недопустимый тип файла. Разрешены только JPG, PNG и GIF.',
      color: 'error'
    })
    return
  }

  isUploadingAvatar.value = true
  const previewUrl = URL.createObjectURL(file)
  const previousAvatarUrl = profile.avatar_url
  profile.avatar_url = previewUrl

  try {
    const result = await uploadAvatar(file)
    if (!result.success) {
      profile.avatar_url = previousAvatarUrl
      return
    }
    profile.avatar_url = result.user?.avatar_url || previousAvatarUrl
  } catch {
    profile.avatar_url = previousAvatarUrl
  } finally {
    URL.revokeObjectURL(previewUrl)
    isUploadingAvatar.value = false
    if (input) {
      input.value = ''
    }
  }
}

function onFileClick() {
  fileRef.value?.click()
}

function openPublicProfilePreview() {
  if (!user.value?.username) {
    toast.add({
      title: 'Ошибка',
      description: 'Не удалось получить имя пользователя',
      color: 'error'
    })
    return
  }
  const publicProfileUrl = `/booking/${user.value.username}`
  window.open(publicProfileUrl, '_blank')
}
</script>

<template>
  <UDashboardPanel id="profile">
    <template #header>
      <UDashboardNavbar title="Редактирование профиля">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>
        <template #right>
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-external-link"
              color="neutral"
              variant="ghost"
              size="sm"
              label="Как это выглядит"
              :disabled="!user?.username"
              @click="openPublicProfilePreview"
            />
            <UButton
              form="profile-form"
              label="Сохранить изменения"
              color="neutral"
              type="submit"
              :loading="isLoading"
            />
          </div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex flex-col gap-4 sm:gap-6 lg:gap-12 w-full mx-auto lg:max-w-5xl">
        <UForm
          id="profile-form"
          :schema="profileSchema"
          :state="profile"
          @submit="onSubmit"
        >
          <UPageCard
            title="Профиль"
            description="Эта информация будет отображаться публично и в вашем публичном календаре."
            variant="naked"
            orientation="horizontal"
            class="mb-4"
          />

          <UPageCard variant="subtle">
            <UFormField
              name="username"
              label="Имя пользователя"
              description="Ваше уникальное имя пользователя для входа и URL вашего публичного календаря. Может содержать только буквы, цифры, дефисы и подчеркивания."
              required
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div class="w-full min-w-0">
                <UInput
                  v-model="profile.username"
                  class="!w-full"
                  type="text"
                  autocomplete="username"
                  placeholder="username"
                />
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="first_name"
              label="Имя"
              description="Ваше имя, которое будет отображаться в профиле и в публичном календаре."
              required
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div class="w-full min-w-0">
                <UInput
                  v-model="profile.first_name"
                  class="!w-full"
                  autocomplete="given-name"
                  placeholder="Введите ваше имя"
                />
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="last_name"
              label="Фамилия"
              description="Ваша фамилия (необязательно)."
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div class="w-full min-w-0">
                <UInput
                  v-model="profile.last_name"
                  class="!w-full"
                  autocomplete="family-name"
                  placeholder="Введите вашу фамилию"
                />
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="email"
              label="Электронная почта"
              description="Используется для входа. Нельзя изменить."
              required
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div class="w-full min-w-0">
                <UInput
                  v-model="profile.email"
                  class="!w-full"
                  type="email"
                  autocomplete="email"
                  disabled
                />
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="phone"
              label="Телефон"
              description="Ваш номер телефона для связи."
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div class="w-full min-w-0">
                <UInput
                  v-model="profile.phone"
                  class="!w-full"
                  type="tel"
                  autocomplete="tel"
                  placeholder="+7 (999) 123-45-67"
                />
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="specialty_id"
              label="Специальность"
              description="Выберите вашу специальность из списка."
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div class="w-full min-w-0">
                <USelect
                  v-model="profile.specialty_id"
                  :items="specialtyOptions"
                  placeholder="Выберите специальность"
                  :loading="specialtiesLoading"
                  value-key="value"
                  class="!w-full"
                />
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="bio"
              label="О себе"
              description="Краткое описание о вас и вашем опыте работы. Будет отображаться в публичном профиле."
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div class="w-full min-w-0">
                <UTextarea
                  v-model="profile.bio"
                  class="!w-full"
                  placeholder="Расскажите о себе..."
                  :rows="4"
                />
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="city"
              label="Город"
              description="Город, в котором вы находитесь. Будет отображаться в публичном профиле рядом с вашим именем."
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div class="w-full min-w-0">
                <UInput
                  v-model="profile.city"
                  class="!w-full"
                  placeholder="Например: Самара"
                />
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="service_address"
              label="Адрес оказания услуг"
              description="Полный адрес, по которому вы оказываете услуги. Будет отображаться в публичном профиле."
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start"
            >
              <div ref="addressSuggestRef" class="w-full min-w-0 relative">
                <div class="flex gap-2">
                  <UInput
                    v-model="addressSearchQuery"
                    class="!w-full"
                    placeholder="Введите адрес и выберите из списка"
                    :loading="addressSuggestLoading"
                    autocomplete="off"
                    @focus="addressInputFocused = true"
                    @blur="onAddressBlur"
                  />
                  <UButton
                    v-if="profile.service_address"
                    color="neutral"
                    variant="ghost"
                    icon="i-lucide-x"
                    aria-label="Очистить адрес"
                    @click="clearAddress"
                  />
                </div>
                <div
                  v-if="addressSuggestOpen"
                  class="absolute z-50 mt-1 w-full rounded-lg border border-default bg-background shadow-lg overflow-hidden"
                >
                  <template v-if="addressSuggestions.length > 0">
                    <button
                      v-for="(item, i) in addressSuggestions"
                      :key="i"
                      type="button"
                      class="w-full px-4 py-2.5 text-left text-sm hover:bg-muted transition-colors truncate"
                      @mousedown.prevent
                      @click="onAddressSelect(item)"
                    >
                      {{ item.address }}
                    </button>
                  </template>
                  <div v-else-if="addressSearchQuery.trim().length >= 2 && !addressSuggestLoading" class="px-4 py-3 text-sm text-muted">
                    Адрес не найден. Введите другой запрос.
                  </div>
                </div>
              </div>
            </UFormField>
            <USeparator />
            <UFormField
              name="avatar"
              label="Аватар"
              description="JPG, GIF или PNG. Максимум 1 МБ. Будет отображаться в профиле и в публичном календаре."
              class="grid grid-cols-[1fr_1fr] max-sm:grid-cols-1 gap-4 items-start sm:items-center"
            >
              <div class="flex flex-wrap items-center gap-3 w-full min-w-0">
                <UAvatar
                  :src="profile.avatar_url"
                  :alt="profile.first_name || profile.username"
                  size="lg"
                />
                <UButton
                  label="Выбрать"
                  color="neutral"
                  :loading="isUploadingAvatar"
                  @click="onFileClick"
                />
                <input
                  ref="fileRef"
                  type="file"
                  class="hidden"
                  accept=".jpg,.jpeg,.png,.gif,image/jpeg,image/png,image/gif"
                  @change="onFileChange"
                >
              </div>
            </UFormField>
          </UPageCard>
        </UForm>
      </div>
    </template>
  </UDashboardPanel>
</template>
