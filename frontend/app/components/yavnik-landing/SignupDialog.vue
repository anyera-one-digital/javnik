<script setup lang="ts">
import { Check, X } from '@lucide/vue'
import {
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
  DialogTrigger
} from 'reka-ui'

withDefaults(defineProps<{
  label?: string
  variant?: 'primary' | 'secondary'
  large?: boolean
}>(), {
  label: 'Получить месяц Pro бесплатно',
  variant: 'primary',
  large: false
})

const sent = ref(false)
const name = ref('')
const email = ref('')

const submit = async () => {
  await navigateTo({
    path: '/signup',
    query: {
      ...(name.value ? { name: name.value } : {}),
      ...(email.value ? { email: email.value } : {})
    }
  })
}
</script>

<template>
  <DialogRoot
    @update:open="(open) => { if (!open) sent = false }"
  >
    <DialogTrigger
      class="yv-btn focus-ring"
      :class="[`yv-btn--${variant}`, large ? 'yv-btn--lg' : 'yv-btn--md']"
    >
      {{ label }}
    </DialogTrigger>
    <DialogPortal>
      <DialogOverlay class="dialog-overlay" />
      <DialogContent
        class="dialog-content"
        @escape-key-down="sent = false"
      >
        <DialogClose
          class="dialog-close focus-ring"
          aria-label="Закрыть окно"
        >
          <X :size="20" />
        </DialogClose>
        <template v-if="!sent">
          <span class="eyebrow"><i /> Бесплатный старт</span>
          <DialogTitle>Ваша страница — через 5 минут</DialogTitle>
          <DialogDescription>
            Оставьте почту. Мы создадим аккаунт и покажем короткую настройку без звонков и обязательств.
          </DialogDescription>
          <form
            class="signup-form"
            @submit.prevent="submit"
          >
            <label>
              <span>Ваше имя</span>
              <input
                v-model="name"
                required
                name="name"
                placeholder="Например, Анна"
                autocomplete="name"
              >
            </label>
            <label>
              <span>Электронная почта</span>
              <input
                v-model="email"
                required
                type="email"
                name="email"
                placeholder="anna@example.ru"
                autocomplete="email"
              >
            </label>
            <button
              class="yv-btn yv-btn--primary yv-btn--lg"
              type="submit"
            >
              Начать — месяц Pro бесплатно
            </button>
          </form>
          <small>Нажимая кнопку, вы соглашаетесь с политикой конфиденциальности.</small>
        </template>
        <template v-else>
          <div class="success-state">
            <span><Check :size="28" /></span>
            <DialogTitle>Все готово</DialogTitle>
            <DialogDescription>Это демонстрационная форма лендинга. В рабочем проекте сюда подключается ваш API регистрации.</DialogDescription>
            <DialogClose class="yv-btn yv-btn--primary yv-btn--lg">
              Понятно
            </DialogClose>
          </div>
        </template>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
