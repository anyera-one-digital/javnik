<script setup lang="ts">
/**
 * Пароль с переключателем видимости: при скрытом пароле — «перечёркнутый глаз» (eye-off),
 * при открытом — обычный глаз (eye).
 */
const props = withDefaults(
  defineProps<{
    placeholder?: string
    disabled?: boolean
    autocomplete?: string
    name?: string
    id?: string
    size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xs'
    /** иконка слева (как у UInput) */
    icon?: string
  }>(),
  { size: 'md' }
)

const model = defineModel<string>({ default: '' })

const show = ref(false)

const inputType = computed(() => (show.value ? 'text' : 'password'))
const toggleIcon = computed(() => (show.value ? 'i-lucide-eye' : 'i-lucide-eye-off'))
const toggleLabel = computed(() => (show.value ? 'Скрыть пароль' : 'Показать пароль'))
</script>

<template>
  <UInput
    v-model="model"
    :type="inputType"
    :placeholder="props.placeholder"
    :disabled="props.disabled"
    :autocomplete="props.autocomplete"
    :name="props.name"
    :id="props.id"
    :size="props.size"
    :icon="props.icon"
    class="!w-full"
  >
    <template #trailing>
      <UButton
        type="button"
        color="neutral"
        variant="link"
        size="sm"
        :icon="toggleIcon"
        :aria-label="toggleLabel"
        :aria-pressed="show"
        @click="show = !show"
      />
    </template>
  </UInput>
</template>
