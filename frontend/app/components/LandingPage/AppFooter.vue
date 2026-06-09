<script setup lang="ts">
/** Временно: только нижняя полоска (условия, политика, ©) */
const showFooterTop = false

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
    :label="showFooterTop ? 'Я' : undefined"
    class="h-px"
  />

  <UFooter :ui="{ top: showFooterTop ? 'border-b border-default' : '' }">
    <template v-if="showFooterTop" #top>
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
                  placeholder="Введите электронную почту"
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
      <div class="space-y-1">
        <p class="text-muted text-sm m-0">
          © {{ new Date().getFullYear() }} ООО «ЭНИЕРА». Все права защищены.
        </p>
        <p class="text-muted text-sm m-0 flex flex-wrap gap-x-3 gap-y-0.5">
          <span>ОГРН 1236300014807</span>
          <span>ИНН 6319260879</span>
        </p>
      </div>
    </template>

    <template #right>
      <p class="text-muted text-sm m-0 flex flex-wrap items-center justify-end gap-x-2 gap-y-1">
        <ULink to="/terms" class="text-foreground hover:underline">Условия использования</ULink>
        <span aria-hidden="true">•</span>
        <ULink to="/privacy" class="text-foreground hover:underline">Политика конфиденциальности</ULink>
      </p>
    </template>
  </UFooter>
</template>
