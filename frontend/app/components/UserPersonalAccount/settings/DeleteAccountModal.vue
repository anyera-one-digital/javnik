<script setup lang="ts">
const props = defineProps<{
  open: boolean
  username: string
  loading?: boolean
  error?: string | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: [username: string]
}>()

const confirmUsername = ref('')

watch(() => props.open, (isOpen) => {
  if (!isOpen) {
    confirmUsername.value = ''
  }
})

const canConfirm = computed(
  () => confirmUsername.value === props.username && !props.loading
)

function handleCancel() {
  emit('update:open', false)
}

function handleConfirm() {
  if (!canConfirm.value) return
  emit('confirm', confirmUsername.value)
}
</script>

<template>
  <UModal
    :open="open"
    title="Удалить аккаунт"
    description="Это действие необратимо. Все ваши данные будут удалены без возможности восстановления."
    @update:open="emit('update:open', $event)"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-muted m-0">
          Чтобы подтвердить удаление, введите ваше имя пользователя:
          <strong class="text-highlighted">{{ username }}</strong>
        </p>

        <UFormField label="Имя пользователя" required>
          <UInput
            v-model="confirmUsername"
            placeholder="Введите имя пользователя"
            autocomplete="off"
            :disabled="loading"
          />
        </UFormField>

        <p
          v-if="error"
          class="text-sm text-error m-0"
        >
          {{ error }}
        </p>

        <div class="flex justify-end gap-2">
          <UButton
            label="Отмена"
            color="neutral"
            variant="subtle"
            :disabled="loading"
            @click="handleCancel"
          />
          <UButton
            label="Подтвердить"
            color="error"
            variant="solid"
            :loading="loading"
            :disabled="!canConfirm"
            @click="handleConfirm"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
