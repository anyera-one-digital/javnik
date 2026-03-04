<script setup lang="ts">
definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const state = reactive<{ [key: string]: boolean }>({
  email: true,
  desktop: false
})

const sections = [{
  title: 'Каналы уведомлений',
  description: 'Где мы можем уведомлять вас?',
  fields: [{
    name: 'email',
    label: 'Email',
    description: 'Получать ежедневную сводку по email.'
  }, {
    name: 'desktop',
    label: 'Рабочий стол',
    description: 'Получать уведомления на рабочем столе.'
  }]
}]

async function onChange() {
  // Do something with data
  console.log(state)
}
</script>

<template>
  <div v-for="(section, index) in sections" :key="index">
    <UPageCard
      :title="section.title"
      :description="section.description"
      variant="naked"
      class="mb-4"
    />

    <UPageCard variant="subtle" :ui="{ container: 'divide-y divide-default' }">
      <UFormField
        v-for="field in section.fields"
        :key="field.name"
        :name="field.name"
        :label="field.label"
        :description="field.description"
        class="flex items-center justify-between not-last:pb-4 gap-2"
      >
        <USwitch
          v-model="state[field.name]"
          @update:model-value="onChange"
        />
      </UFormField>
    </UPageCard>
  </div>
</template>
