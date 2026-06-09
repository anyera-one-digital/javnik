<script setup lang="ts">
definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

// Редирект на первую вкладку настроек (профиль вынесен на отдельную страницу /profile)
await navigateTo('/settings/general', { replace: true })
</script>

<template>
  <div />
</template>
