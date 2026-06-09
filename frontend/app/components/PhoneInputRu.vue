<script setup lang="ts">
import { applyRuPhoneMask } from '~/utils/phone'

const model = defineModel<string>({ default: '' })

withDefaults(
  defineProps<{
    placeholder?: string
  }>(),
  { placeholder: '+7 (999) 123-45-67' }
)

function onUpdate(v: string | number) {
  model.value = applyRuPhoneMask(String(v ?? ''))
}

function onKeydown(e: KeyboardEvent) {
  if (e.ctrlKey || e.metaKey || e.altKey) return
  const k = e.key
  if (k === 'Backspace' || k === 'Delete' || k === 'Tab' || k === 'Escape' || k === 'Enter') return
  if (k === 'ArrowLeft' || k === 'ArrowRight' || k === 'ArrowUp' || k === 'ArrowDown' || k === 'Home' || k === 'End') return
  if (k.length === 1 && !/\d/.test(k)) {
    e.preventDefault()
  }
}
</script>

<template>
  <UInput
    :model-value="model"
    type="tel"
    inputmode="numeric"
    :placeholder="placeholder"
    autocomplete="tel"
    class="w-full"
    v-bind="$attrs"
    @update:model-value="onUpdate"
    @keydown="onKeydown"
  />
</template>
