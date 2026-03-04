<script setup lang="ts">
import type { Service } from '~/types'

const props = defineProps<{
  service: Service | null
}>()

const emit = defineEmits<{
  confirmed: []
  cancelled: []
}>()

const open = computed({
  get: () => props.service !== null,
  set: (value) => {
    if (!value) {
      emit('cancelled')
    }
  }
})

function handleConfirm() {
  emit('confirmed')
  // Модальное окно закроется автоматически через v-model
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="Удалить услугу"
    description="Вы точно хотите удалить эту услугу?"
  >
    <template #body>
      <div class="flex flex-col gap-4">
        <p v-if="service" class="text-sm text-muted">
          Услуга "<strong>{{ service.name }}</strong>" будет удалена без возможности восстановления.
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
