<script setup lang="ts">
import { Moon, Sun } from '@lucide/vue'

const { theme, toggleTheme } = useYavnikTheme()
</script>

<template>
  <button
    class="theme-toggle focus-ring"
    type="button"
    :aria-label="theme === 'light' ? 'Включить темную тему' : 'Включить светлую тему'"
    @click="toggleTheme"
  >
    <Sun
      v-if="theme === 'dark'"
      :size="17"
      aria-hidden="true"
    />
    <Moon
      v-else
      :size="17"
      aria-hidden="true"
    />
  </button>
</template>
