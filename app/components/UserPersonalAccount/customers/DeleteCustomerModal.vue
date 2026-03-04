<script setup lang="ts">
import type { Customer } from '~/types'

const props = defineProps<{
  customer: Customer | null
}>()

const emit = defineEmits<{
  confirmed: []
  cancelled: []
}>()

const open = computed({
  get: () => props.customer !== null,
  set: (value) => {
    if (!value) {
      emit('cancelled')
    }
  }
})

function handleConfirm() {
  emit('confirmed')
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Удалить клиента"
    description="Вы точно хотите удалить этого клиента?"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <p v-if="customer" class="text-sm text-muted">
          Клиент "<strong>{{ customer.name }}</strong>" будет удалён без возможности восстановления.
        </p>

        <div class="flex justify-end gap-2">
          <UButton
            label="Нет"
            color="neutral"
            variant="subtle"
            @click="open = false"
          />
          <UButton
            label="Да"
            color="error"
            variant="solid"
            @click="handleConfirm"
          />
        </div>
      </div>
    </template>
  </UModal>
</template>
