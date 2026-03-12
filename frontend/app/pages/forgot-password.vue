<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({
  layout: 'auth',
  middleware: 'guest'
})

useSeoMeta({
  title: 'Восстановление пароля',
  description: 'Восстановите доступ к своему аккаунту'
})

const router = useRouter()
const toast = useToast()

const step = ref<'email' | 'code'>('email')
const isLoading = ref(false)
const email = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// Схема для шага 1: ввод email
const emailSchema = z.object({
  email: z.string().email('Неверный формат email')
})

type EmailSchema = z.output<typeof emailSchema>

// Схема для шага 2: ввод кода
const codeSchema = z.object({
  code: z.string().min(4, 'Код должен содержать минимум 4 символа'),
  newPassword: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
  confirmPassword: z.string().min(8, 'Подтверждение пароля обязательно')
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: 'Пароли не совпадают',
  path: ['confirmPassword']
})

type CodeSchema = z.output<typeof codeSchema>

// Шаг 1: Отправка email для получения кода
async function onEmailSubmit(payload: FormSubmitEvent<EmailSchema>) {
  isLoading.value = true
  try {
    const response = await $fetch('/api/auth/password-reset/', {
      method: 'POST',
      body: {
        email: payload.data.email
      }
    })

    email.value = payload.data.email
    step.value = 'code'
    
    // В режиме разработки может быть debug_code
    if (response && 'debug_code' in response) {
      toast.add({
        title: 'Код отправлен (режим разработки)',
        description: `Код: ${response.debug_code}. Проверьте настройки email для продакшена.`,
        color: 'green',
        timeout: 10000
      })
    } else {
      toast.add({
        title: 'Код отправлен',
        description: 'Проверьте вашу почту. Код подтверждения отправлен на указанный email.',
        color: 'green'
      })
    }
  } catch (error: any) {
    const errorMessage = error.data?.error || error.data?.detail || error.data?.message || 'Ошибка при отправке кода'
    toast.add({
      title: 'Ошибка',
      description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
      color: 'red'
    })
  } finally {
    isLoading.value = false
  }
}

// Шаг 2: Подтверждение кода и установка нового пароля
async function onCodeSubmit(payload: FormSubmitEvent<CodeSchema>) {
  isLoading.value = true
  try {
    await $fetch('/api/auth/password-reset/confirm/', {
      method: 'POST',
      body: {
        email: email.value,
        code: payload.data.code,
        new_password: payload.data.newPassword
      }
    })

    toast.add({
      title: 'Пароль успешно изменен',
      description: 'Теперь вы можете войти с новым паролем.',
      color: 'green'
    })

    // Перенаправляем на страницу входа
    setTimeout(() => {
      router.push('/login')
    }, 1500)
  } catch (error: any) {
    const errorMessage = error.data?.error || error.data?.detail || error.data?.message || 'Ошибка при сбросе пароля'
    toast.add({
      title: 'Ошибка',
      description: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
      color: 'red'
    })
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  if (step.value === 'code') {
    step.value = 'email'
    code.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } else {
    router.push('/login')
  }
}
</script>

<template>
  <div class="w-full">
    <!-- Шаг 1: Ввод email -->
    <UForm
      v-if="step === 'email'"
      :schema="emailSchema"
      :state="{ email }"
      @submit="onEmailSubmit"
      class="space-y-3"
    >
      <div class="text-center mb-4">
        <div class="flex justify-center mb-3">
          <div class="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
            <Icon name="i-lucide-mail" class="w-5 h-5 text-muted" />
          </div>
        </div>
        <h1 class="text-xl font-semibold mb-1.5">Восстановление пароля</h1>
        <p class="text-muted text-sm">
          Введите ваш email, и мы отправим код подтверждения для восстановления пароля
        </p>
      </div>

      <UFormField name="email" label="Email" required>
        <UInput
          v-model="email"
          type="email"
          placeholder="Введите ваш email"
          icon="i-lucide-mail"
          size="lg"
          :disabled="isLoading"
          class="w-full"
        />
      </UFormField>

      <UButton
        type="submit"
        label="Отправить код"
        color="neutral"
        variant="solid"
        size="lg"
        block
        :loading="isLoading"
        :disabled="isLoading"
        class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
      />

      <div class="text-center">
        <UButton
          variant="ghost"
          color="neutral"
          label="Вернуться к входу"
          @click="goBack"
          :disabled="isLoading"
        />
      </div>
    </UForm>

    <!-- Шаг 2: Ввод кода и нового пароля -->
    <UForm
      v-else
      :schema="codeSchema"
      :state="{ code, newPassword, confirmPassword }"
      @submit="onCodeSubmit"
      class="space-y-3"
    >
      <div class="text-center mb-4">
        <div class="flex justify-center mb-3">
          <div class="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
            <Icon name="i-lucide-key" class="w-5 h-5 text-muted" />
          </div>
        </div>
        <h1 class="text-xl font-semibold mb-1.5">Введите код подтверждения</h1>
        <p class="text-muted text-sm mb-2">
          Код отправлен на <span class="font-medium">{{ email }}</span>
        </p>
        <p class="text-xs text-muted">
          Проверьте папку "Спам", если письмо не пришло
        </p>
      </div>

      <UFormField name="code" label="Код подтверждения" required>
        <UInput
          v-model="code"
          type="text"
          placeholder="Введите код из письма"
          icon="i-lucide-key"
          size="lg"
          :disabled="isLoading"
          maxlength="6"
          autocomplete="one-time-code"
          inputmode="numeric"
          pattern="[0-9]*"
          class="w-full"
        />
      </UFormField>

      <UFormField name="newPassword" label="Новый пароль" required>
        <UInput
          v-model="newPassword"
          type="password"
          placeholder="Введите новый пароль (минимум 8 символов)"
          icon="i-lucide-lock"
          size="lg"
          :disabled="isLoading"
          class="w-full"
        />
      </UFormField>

      <UFormField name="confirmPassword" label="Подтвердите пароль" required>
        <UInput
          v-model="confirmPassword"
          type="password"
          placeholder="Повторите новый пароль"
          icon="i-lucide-lock"
          size="lg"
          :disabled="isLoading"
          class="w-full"
        />
      </UFormField>

      <UButton
        type="submit"
        label="Изменить пароль"
        color="neutral"
        variant="solid"
        size="lg"
        block
        :loading="isLoading"
        :disabled="isLoading"
        class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
      />

      <div class="text-center">
        <UButton
          variant="ghost"
          color="neutral"
          label="Назад"
          @click="goBack"
          :disabled="isLoading"
        />
      </div>
    </UForm>
  </div>
</template>

<style scoped>
:deep([data-slot="label"]) {
  white-space: nowrap;
}
:deep(.text-sm.font-medium) {
  white-space: nowrap;
}
</style>
