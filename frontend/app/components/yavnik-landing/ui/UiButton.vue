<script setup lang="ts">
import { ArrowUpRight } from '@lucide/vue'

withDefaults(defineProps<{
  href?: string
  to?: string
  variant?: 'primary' | 'secondary' | 'ghost'
  size?: 'md' | 'lg'
  arrow?: boolean
}>(), {
  href: undefined,
  to: undefined,
  variant: 'primary',
  size: 'md',
  arrow: false
})
</script>

<template>
  <NuxtLink
    v-if="to"
    :to="to"
    class="yv-btn focus-ring"
    :class="[`yv-btn--${variant}`, `yv-btn--${size}`]"
  >
    <span><slot /></span>
    <ArrowUpRight
      v-if="arrow"
      :size="18"
      :stroke-width="1.8"
      aria-hidden="true"
    />
  </NuxtLink>
  <component
    :is="href ? 'a' : 'button'"
    v-else
    :href="href"
    class="yv-btn focus-ring"
    :class="[`yv-btn--${variant}`, `yv-btn--${size}`]"
  >
    <span><slot /></span>
    <ArrowUpRight
      v-if="arrow"
      :size="18"
      :stroke-width="1.8"
      aria-hidden="true"
    />
  </component>
</template>
