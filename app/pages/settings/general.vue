<script setup lang="ts">
definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const { user, patchProfile, fetchProfile } = useAuth()

const showPublicSchedule = ref(true)
const showPublicReviews = ref(true)
const showPublicPortfolio = ref(true)
const saving = ref(false)

function syncFromUser() {
  const u = user.value
  if (!u) return
  showPublicSchedule.value = u.show_public_schedule !== false
  showPublicReviews.value = u.show_public_reviews !== false
  showPublicPortfolio.value = u.show_public_portfolio !== false
}

onMounted(async () => {
  const profile = await fetchProfile()
  if (profile) {
    showPublicSchedule.value = profile.show_public_schedule !== false
    showPublicReviews.value = profile.show_public_reviews !== false
    showPublicPortfolio.value = profile.show_public_portfolio !== false
  } else {
    syncFromUser()
  }
})

watch(user, syncFromUser)

async function patchPublicSetting(
  field: 'show_public_schedule' | 'show_public_reviews' | 'show_public_portfolio',
  value: boolean,
  rollback: () => void
) {
  if (saving.value) return
  saving.value = true
  const result = await patchProfile({ [field]: value })
  saving.value = false
  if (!result.success) {
    rollback()
  }
}

function onShowPublicScheduleChange(value: boolean) {
  const previous = showPublicSchedule.value
  showPublicSchedule.value = value
  patchPublicSetting('show_public_schedule', value, () => {
    showPublicSchedule.value = previous
  })
}

function onShowPublicReviewsChange(value: boolean) {
  const previous = showPublicReviews.value
  showPublicReviews.value = value
  patchPublicSetting('show_public_reviews', value, () => {
    showPublicReviews.value = previous
  })
}

function onShowPublicPortfolioChange(value: boolean) {
  const previous = showPublicPortfolio.value
  showPublicPortfolio.value = value
  patchPublicSetting('show_public_portfolio', value, () => {
    showPublicPortfolio.value = previous
  })
}
</script>

<template>
  <div>
    <UPageCard
      title="Общие"
      description="Настройки публичной страницы записи."
      variant="naked"
      class="mb-4"
    />

    <UPageCard variant="subtle" :ui="{ container: 'divide-y divide-default' }">
      <UFormField
        name="show_public_schedule"
        label="Расписание на публичной странице"
        description="Если выключено, клиенты видят только кнопку «Записаться» без перехода в общее расписание."
        class="flex items-center justify-between gap-4"
      >
        <USwitch
          :model-value="showPublicSchedule"
          color="neutral"
          :disabled="saving"
          @update:model-value="onShowPublicScheduleChange"
        />
      </UFormField>

      <UFormField
        name="show_public_reviews"
        label="Отзывы на публичной странице"
        description="Если выключено, скрываются звёзды рейтинга и вкладка «Отзывы»."
        class="flex items-center justify-between gap-4"
      >
        <USwitch
          :model-value="showPublicReviews"
          color="neutral"
          :disabled="saving"
          @update:model-value="onShowPublicReviewsChange"
        />
      </UFormField>

      <UFormField
        name="show_public_portfolio"
        label="Портфолио на публичной странице"
        description="Если выключено, скрывается вкладка «Портфолио» с примерами работ."
        class="flex items-center justify-between gap-4"
      >
        <USwitch
          :model-value="showPublicPortfolio"
          color="neutral"
          :disabled="saving"
          @update:model-value="onShowPublicPortfolioChange"
        />
      </UFormField>
    </UPageCard>
  </div>
</template>
