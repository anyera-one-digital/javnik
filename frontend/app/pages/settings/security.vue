<script setup lang="ts">
import * as z from 'zod'
import type { FormError } from '@nuxt/ui'
import DeleteAccountModal from '~/components/UserPersonalAccount/settings/DeleteAccountModal.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const { user, fetchProfile, deleteAccount, getAuthHeaders } = useAuth()
const toast = useToast()
const config = useRuntimeConfig()

const passwordSchema = z.object({
  current: z.string().min(8, 'Должно быть не менее 8 символов'),
  new: z.string().min(8, 'Должно быть не менее 8 символов')
})

type PasswordSchema = z.output<typeof passwordSchema>

const password = reactive<Partial<PasswordSchema>>({
  current: undefined,
  new: undefined
})

const validate = (state: Partial<PasswordSchema>): FormError[] => {
  const errors: FormError[] = []
  if (state.current && state.new && state.current === state.new) {
    errors.push({ name: 'new', message: 'Пароли должны отличаться' })
  }
  return errors
}

interface DeletionStatus {
  canDelete: boolean
  activeBookingsCount: number
  username: string
}

const deletionStatus = ref<DeletionStatus | null>(null)
const loadingDeletionStatus = ref(true)
const deleteModalOpen = ref(false)
const deletingAccount = ref(false)
const deleteError = ref<string | null>(null)

const canDeleteAccount = computed(() => deletionStatus.value?.canDelete ?? false)
const activeBookingsCount = computed(() => deletionStatus.value?.activeBookingsCount ?? 0)

const activeBookingsText = computed(() => {
  const n = activeBookingsCount.value
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return `${n} активная запись`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return `${n} активные записи`
  return `${n} активных записей`
})
const accountUsername = computed(
  () => deletionStatus.value?.username ?? user.value?.username ?? ''
)

async function loadDeletionStatus() {
  loadingDeletionStatus.value = true
  try {
    if (!user.value?.username) {
      await fetchProfile()
    }
    deletionStatus.value = await $fetch<DeletionStatus>(
      '/api/auth/account/deletion-status/',
      { headers: getAuthHeaders() }
    )
  } catch (e) {
    console.error('security: failed to load deletion status', e)
  } finally {
    loadingDeletionStatus.value = false
  }
}

function openDeleteModal() {
  if (!canDeleteAccount.value) return
  deleteError.value = null
  deleteModalOpen.value = true
}

async function handleDeleteConfirm(username: string) {
  deletingAccount.value = true
  deleteError.value = null
  try {
    const result = await deleteAccount(username)
    if (!result.success) {
      deleteError.value = result.error ?? 'Не удалось удалить аккаунт'
      return
    }
    deleteModalOpen.value = false
    toast.add({
      title: 'Аккаунт удалён',
      description: 'Все ваши данные удалены из системы',
      color: 'green'
    })
  } finally {
    deletingAccount.value = false
  }
}

onMounted(() => {
  loadDeletionStatus()
})
</script>

<template>
  <div class="flex flex-col gap-4 sm:gap-6">
    <UPageCard
      title="Пароль"
      description="Подтвердите текущий пароль перед установкой нового."
      variant="subtle"
    >
      <UForm
        :schema="passwordSchema"
        :state="password"
        :validate="validate"
        class="flex flex-col gap-4 max-w-xs"
      >
        <UFormField name="current" label="Текущий пароль" required>
          <PasswordInput
            v-model="password.current"
            placeholder="Введите текущий пароль"
            autocomplete="current-password"
          />
        </UFormField>

        <UFormField name="new" label="Новый пароль" required>
          <PasswordInput
            v-model="password.new"
            placeholder="Не менее 8 символов"
            autocomplete="new-password"
          />
        </UFormField>

        <UButton
          label="Обновить"
          color="neutral"
          variant="solid"
          class="w-fit"
          type="submit"
        />
      </UForm>
    </UPageCard>

    <UPageCard
      title="Удалить мой аккаунт"
      variant="subtle"
    >
      <div class="flex flex-col gap-4 max-w-2xl">
        <div class="space-y-3 text-sm text-muted">
          <p class="m-0">
            После удаления аккаунта мы полностью удаляем все данные, связанные с вами:
            профиль, клиентов, услуги, расписание, записи, отзывы и историю подписки.
            Мы не храним персональные данные после удаления.
          </p>
          <p class="m-0">
            Восстановить аккаунт будет невозможно. Удаление доступно только при отсутствии
            активных записей — ожидающих подтверждения или уже подтверждённых.
          </p>
        </div>

        <UAlert
          v-if="!loadingDeletionStatus && !canDeleteAccount"
          color="warning"
          variant="subtle"
          icon="i-lucide-calendar-clock"
          title="Есть активные записи"
          :description="`Сейчас у вас ${activeBookingsText}. Завершите или отмените их в расписании, затем вернитесь сюда.`"
        />

        <div class="flex flex-wrap items-center gap-3">
          <UButton
            label="Удалить"
            color="error"
            variant="solid"
            :disabled="loadingDeletionStatus || !canDeleteAccount"
            @click="openDeleteModal"
          />
          <UButton
            v-if="!loadingDeletionStatus && !canDeleteAccount"
            label="Перейти в расписание"
            color="neutral"
            variant="outline"
            to="/schedule"
          />
        </div>
      </div>
    </UPageCard>

    <DeleteAccountModal
      v-model:open="deleteModalOpen"
      :username="accountUsername"
      :loading="deletingAccount"
      :error="deleteError"
      @confirm="handleDeleteConfirm"
    />
  </div>
</template>
