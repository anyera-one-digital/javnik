<script setup lang="ts">
const columns = [{
  label: 'Ресурсы',
  children: [{
    label: 'Центр помощи'
  }, {
    label: 'Документация'
  }, {
    label: 'Дорожная карта'
  }, {
    label: 'Обновления'
  }]
}, {
  label: 'Возможности',
  children: [{
    label: 'Партнеры'
  }, {
    label: 'Портал'
  }, {
    label: 'Вакансии'
  }, {
    label: 'Спонсоры'
  }]
}, {
  label: 'Компания',
  children: [{
    label: 'О нас'
  }, {
    label: 'Цены'
  }, {
    label: 'Карьера'
  }, {
    label: 'Блог'
  }]
}]

const toast = useToast()

const email = ref('')
const loading = ref(false)

function onSubmit() {
  loading.value = true

  toast.add({
    title: 'Подписка оформлена!',
    description: 'Вы успешно подписались на нашу рассылку.'
  })
}
</script>

<template>
  <USeparator
    label="Я"
    class="h-px"
  />

  <UFooter :ui="{ top: 'border-b border-default' }">
    <template #top>
      <UContainer>
        <UFooterColumns :columns="columns">
          <template #right>
            <form @submit.prevent="onSubmit">
              <UFormField
                name="email"
                label="Подпишитесь на нашу рассылку"
                size="lg"
              >
                <UInput
                  v-model="email"
                  type="email"
                  class="w-full"
                  placeholder="Введите ваш email"
                >
                  <template #trailing>
                    <UButton
                      type="submit"
                      size="xs"
                      color="neutral"
                      label="Подписаться"
                    />
                  </template>
                </UInput>
              </UFormField>
            </form>
          </template>
        </UFooterColumns>
      </UContainer>
    </template>

    <template #left>
      <p class="text-muted text-sm">
        <ULink to="/terms" class="text-foreground hover:underline">Условия использования</ULink>
        <span class="mx-2">•</span>
        <ULink to="/privacy" class="text-foreground hover:underline">Политика конфиденциальности</ULink>
        <span class="mx-2">•</span>
        © {{ new Date().getFullYear() }}
      </p>
    </template>

    <template #right>
      <UButton
        to="https://go.nuxt.com/discord"
        target="_blank"
        icon="i-simple-icons-discord"
        aria-label="Nuxt on Discord"
        color="neutral"
        variant="ghost"
      />
      <UButton
        to="https://go.nuxt.com/x"
        target="_blank"
        icon="i-simple-icons-x"
        aria-label="Nuxt on X"
        color="neutral"
        variant="ghost"
      />
    </template>
  </UFooter>
</template>
