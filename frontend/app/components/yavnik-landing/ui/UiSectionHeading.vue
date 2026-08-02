<script setup lang="ts">
withDefaults(defineProps<{
  label: string;
  title: string;
  text?: string;
  align?: 'left' | 'center';
  inverse?: boolean;
}>(), { text: '', align: 'left', inverse: false });
</script>

<template>
  <div class="section-heading" :class="[`section-heading--${align}`, { 'is-inverse': inverse }]">
    <span class="eyebrow section-heading__label"><i />{{ label }}</span>
    <h2>{{ title }}</h2>
    <p v-if="text">{{ text }}</p>
  </div>
</template>
