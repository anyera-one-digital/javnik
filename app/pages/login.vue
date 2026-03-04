<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({
  layout: 'auth',
  middleware: 'guest'
})

useSeoMeta({
  title: 'Вход',
  description: 'Войдите в свой аккаунт, чтобы продолжить'
})

const { login, verifyEmail, resendVerificationCode } = useAuth()
const route = useRoute()
const router = useRouter()
const isLoading = ref(false)
const step = ref(1)
const pendingEmail = ref('')
const digits = ref<string[]>(['', '', '', '', '', ''])
const inputRefs = ref<(HTMLInputElement | null)[]>(Array(6).fill(null))
const isVerifying = ref(false)
const isResending = ref(false)

const code = computed(() => digits.value.join(''))

const fields = [{
  name: 'email',
  type: 'text' as const,
  label: 'Email',
  placeholder: 'Введите ваш email',
  required: true
}, {
  name: 'password',
  label: 'Пароль',
  type: 'password' as const,
  placeholder: 'Введите ваш пароль'
}, {
  name: 'remember',
  label: 'Запомнить меня',
  type: 'checkbox' as const
}]

const schema = z.object({
  email: z.string().email('Неверный формат email'),
  password: z.string().min(1, 'Пароль обязателен для заполнения')
})

type Schema = z.output<typeof schema>

async function onSubmit(payload: FormSubmitEvent<Schema>) {
  isLoading.value = true
  try {
    const result = await login(payload.data.email, payload.data.password)
    if (result.success) {
      const redirectTo = route.query.redirect as string || '/schedule'
      router.push(redirectTo)
    } else if (result.needsVerification && result.email) {
      pendingEmail.value = result.email
      step.value = 2
    }
  } finally {
    isLoading.value = false
  }
}

async function onVerify() {
  if (code.value.length !== 6) return
  isVerifying.value = true
  try {
    const result = await verifyEmail(pendingEmail.value, code.value)
    if (result.success) {
      const redirectTo = route.query.redirect as string || '/schedule'
      router.push(redirectTo)
    }
  } finally {
    isVerifying.value = false
  }
}

function onDigitInput(index: number, e: Event) {
  const target = e.target as HTMLInputElement
  const val = target.value.replace(/\D/g, '').slice(-1)
  const newDigits = [...digits.value]
  newDigits[index] = val
  digits.value = newDigits
  if (val && index < 5) {
    inputRefs.value[index + 1]?.focus()
  }
}

function onDigitKeydown(index: number, e: KeyboardEvent) {
  if (e.key === 'Backspace' && !digits.value[index] && index > 0) {
    inputRefs.value[index - 1]?.focus()
  } else if (e.key === 'ArrowLeft' && index > 0) {
    inputRefs.value[index - 1]?.focus()
  } else if (e.key === 'ArrowRight' && index < 5) {
    inputRefs.value[index + 1]?.focus()
  }
}

function onDigitPaste(e: ClipboardEvent) {
  e.preventDefault()
  const pasted = (e.clipboardData?.getData('text') || '').replace(/\D/g, '').slice(0, 6)
  const newDigits = [...digits.value]
  for (let i = 0; i < pasted.length && i < 6; i++) {
    newDigits[i] = pasted[i]
  }
  digits.value = newDigits
  const nextFocus = Math.min(pasted.length, 5)
  inputRefs.value[nextFocus]?.focus()
}

watch(step, (s) => {
  if (s === 2) {
    digits.value = ['', '', '', '', '', '']
    nextTick(() => inputRefs.value[0]?.focus())
  }
})

async function onResend() {
  isResending.value = true
  try {
    await resendVerificationCode(pendingEmail.value)
  } finally {
    isResending.value = false
  }
}

function goBack() {
  step.value = 1
  pendingEmail.value = ''
  digits.value = ['', '', '', '', '', '']
}
</script>

<template>
  <div v-if="step === 1">
    <UAuthForm
      :fields="fields"
      :schema="schema"
      :loading="isLoading"
      title="Добро пожаловать"
      icon="i-lucide-lock"
      :submit="{ label: 'Войти', color: 'neutral', variant: 'solid', class: '!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100' }"
      @submit="onSubmit"
    >
      <template #description>
        Нет аккаунта? <ULink
          to="/signup"
          class="text-foreground font-medium hover:underline"
        >Зарегистрируйтесь</ULink>.
      </template>

      <template #password-hint>
        <ULink
          to="/forgot-password"
          class="text-foreground font-medium hover:underline"
          tabindex="-1"
        >Забыли пароль?</ULink>
      </template>

      <template #footer>
        Входя в систему, вы соглашаетесь с нашими <ULink
          to="/terms"
          class="text-foreground font-medium hover:underline"
        >Условиями использования</ULink>.
      </template>
    </UAuthForm>
  </div>

  <div v-else class="space-y-4">
    <div class="text-center">
      <h1 class="text-xl font-semibold text-highlighted">
        Подтвердите email
      </h1>
      <p class="mt-1.5 text-muted text-sm">
        Мы отправили код на <strong>{{ pendingEmail }}</strong>
      </p>
    </div>

    <form
      @submit.prevent="onVerify"
      class="space-y-4"
    >
      <div>
        <label class="block text-sm font-medium text-foreground mb-2">
          Код из письма
        </label>
        <div class="flex justify-center gap-1.5 sm:gap-2" role="group" aria-label="Код подтверждения">
          <input
            v-for="(_, i) in 6"
            :key="i"
            :ref="(el) => { if (el && inputRefs.value) inputRefs.value[i] = el as HTMLInputElement }"
            :value="digits[i]"
            type="text"
            inputmode="numeric"
            maxlength="1"
            :autocomplete="i === 0 ? 'one-time-code' : 'off'"
            class="w-10 h-12 sm:w-12 sm:h-14 text-center text-lg sm:text-xl font-semibold rounded-lg border-2 border-default bg-background text-foreground focus:border-foreground/50 focus:ring-2 focus:ring-default focus:outline-none transition-all"
            @input="onDigitInput(i, $event)"
            @keydown="onDigitKeydown(i, $event)"
            @paste="onDigitPaste($event)"
          >
        </div>
      </div>

      <UButton
        type="submit"
        block
        size="lg"
        :loading="isVerifying"
        :disabled="code.length !== 6"
        color="neutral"
        variant="solid"
        class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
      >
        Подтвердить
      </UButton>
    </form>

    <div class="flex flex-col items-center gap-1.5 text-sm">
      <button
        type="button"
        class="text-foreground font-medium hover:underline"
        :disabled="isResending"
        @click="onResend"
      >
        {{ isResending ? 'Отправка...' : 'Отправить код повторно' }}
      </button>
      <button
        type="button"
        class="text-muted hover:text-foreground text-sm"
        @click="goBack"
      >
        Вернуться к входу
      </button>
    </div>

    <p class="text-center text-muted text-xs">
      Нет аккаунта? <ULink
        to="/signup"
        class="text-foreground font-medium hover:underline"
      >Зарегистрируйтесь</ULink>
    </p>
  </div>
</template>
