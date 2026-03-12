<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import type { Customer } from '~/types'

const props = defineProps<{
  modelValue?: boolean
  customer?: Customer | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const schema = z.object({
  name: z.string().min(2, 'Слишком короткое'),
  email: z.string().email('Неверный email'),
  phone: z.string().optional()
})

const isOpen = computed({
  get: () => props.modelValue ?? false,
  set: (value) => emit('update:modelValue', value)
})

type Schema = z.output<typeof schema>

const state = reactive<Partial<Schema>>({
  name: undefined,
  email: undefined,
  phone: undefined
})

const toast = useToast()
const { getAuthHeaders } = useAuth()

watch(() => props.customer, (customer) => {
  if (customer) {
    state.name = customer.name
    state.email = customer.email
    state.phone = customer.phone || undefined
  } else {
    state.name = undefined
    state.email = undefined
    state.phone = undefined
  }
}, { immediate: true })

async function onSubmit(event: FormSubmitEvent<Schema>) {
  try {
    if (props.customer) {
      await $fetch(`/api/customers/${props.customer.id}/`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: {
          name: event.data.name,
          email: event.data.email,
          phone: event.data.phone || undefined
        }
      })
      toast.add({
        title: 'Успешно',
        description: `Клиент ${event.data.name} обновлён`,
        color: 'success'
      })
    } else {
      await $fetch('/api/customers/', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: {
          name: event.data.name,
          email: event.data.email,
          phone: event.data.phone || undefined
        }
      })
      toast.add({
        title: 'Успешно',
        description: `Новый клиент ${event.data.name} добавлен`,
        color: 'success'
      })
    }

    emit('saved')
    isOpen.value = false
    state.name = undefined
    state.email = undefined
    state.phone = undefined
  } catch (error: any) {
    const errorMessage = error.data?.error || error.data?.message || error.message || 'Не удалось сохранить клиента'
    toast.add({
      title: 'Ошибка',
      description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
      color: 'error'
    })
  }
}
</script>

<template>
  <UModal v-model:open="isOpen" :title="props.customer ? 'Редактировать клиента' : 'Новый клиент'" :description="props.customer ? 'Изменить данные клиента' : 'Добавить нового клиента в базу данных'">
    <template v-if="modelValue === undefined && !customer" #trigger>
      <slot>
        <UButton 
          label="Новый клиент" 
          icon="i-lucide-plus" 
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
        <UFormField label="Имя" placeholder="Иван Иванов" name="name">
          <UInput v-model="state.name" class="w-full" />
        </UFormField>
        <UFormField label="Email" placeholder="ivan.ivanov@example.com" name="email">
          <UInput v-model="state.email" class="w-full" />
        </UFormField>
        <UFormField label="Телефон (необязательно)" placeholder="+7 (999) 999-99-99" name="phone">
          <UInput v-model="state.phone" type="tel" class="w-full" />
        </UFormField>
        <div class="flex justify-end gap-2">
          <UButton
            label="Отмена"
            color="neutral"
            variant="subtle"
            @click="isOpen = false"
          />
          <UButton
            :label="props.customer ? 'Сохранить' : 'Создать'"
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
