<script setup lang="ts">
import { eachDayOfInterval } from 'date-fns'
import type { Period, Range } from '~/types'

const model = defineModel<Period>({ required: true })

const props = defineProps<{
  range: Range
  disabled?: boolean
}>()

const days = computed(() => eachDayOfInterval(props.range))

const periodLabels: Record<Period, string> = {
  daily: 'По дням',
  weekly: 'По неделям',
  monthly: 'По месяцам'
}

const periods = computed<Period[]>(() => {
  if (days.value.length <= 8) {
    return [
      'daily'
    ]
  }

  if (days.value.length <= 31) {
    return [
      'daily',
      'weekly'
    ]
  }

  return [
    'weekly',
    'monthly'
  ]
})

// Ensure the model value is always a valid period
watch(periods, () => {
  if (!periods.value.includes(model.value)) {
    model.value = periods.value[0]!
  }
})

const periodItems = computed(() =>
  periods.value.map(value => ({
    label: periodLabels[value],
    value
  }))
)
</script>

<template>
  <USelect
    v-model="model"
    :items="periodItems"
    variant="ghost"
    class="data-[state=open]:bg-elevated"
    :disabled="props.disabled"
    :ui="{ trailingIcon: 'group-data-[state=open]:rotate-180 transition-transform duration-200' }"
  />
</template>
