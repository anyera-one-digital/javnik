<script setup lang="ts">
const isYearly = ref('0')

const items = ref([
  { label: 'Месяц', value: '0' },
  { label: 'Год', value: '1' }
])

defineProps<{
  pricing?: {
    title?: string
    description?: string
    plans?: Array<{
      title: string
      description: string
      price?: { month?: string; year?: string }
      button?: { label: string; color?: string; variant?: string }
      highlight?: boolean
      scale?: boolean
      features?: string[]
    }>
  }
}>()
</script>

<template>
  <UPageSection
    v-if="pricing"
    id="pricing"
    :title="pricing.title"
    :description="pricing.description"
  >
    <template #links>
      <UTabs
        v-model="isYearly"
        :items="items"
        color="neutral"
        size="xs"
        class="w-48"
        :ui="{
          list: 'ring ring-default rounded-full',
          indicator: 'rounded-full',
          trigger: 'w-1/2'
        }"
      />
    </template>
    <UContainer>
      <UPricingPlans scale>
        <UPricingPlan
          v-for="(plan, index) in pricing?.plans || []"
          :key="index"
          v-bind="plan"
          :price="isYearly === '1' ? plan.price?.year : plan.price?.month"
          :billing-cycle="isYearly === '1' ? '/год' : '/месяц'"
        />
      </UPricingPlans>
    </UContainer>
  </UPageSection>
</template>
