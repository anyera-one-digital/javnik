<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'

definePageMeta({
  layout: 'auth',
  middleware: 'guest'
})

useSeoMeta({
  title: 'Регистрация',
  description: 'Создайте аккаунт, чтобы начать'
})

const config = useRuntimeConfig()
const { register, verifyEmail, resendVerificationCode, completeProfile } = useAuth()
const router = useRouter()
const step = ref(1)
const pendingEmail = ref('')

// Шаг 1
const step1Loading = ref(false)
const step1Schema = z.object({
  email: z.string().email('Неверный формат email'),
  phone: z.string().min(1, 'Укажите номер телефона'),
  password: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
  password_confirm: z.string().min(8, 'Подтверждение пароля обязательно'),
  offer_accepted: z.literal(true, { errorMap: () => ({ message: 'Необходимо принять условия пользования' }) }),
  privacy_accepted: z.literal(true, { errorMap: () => ({ message: 'Необходимо принять политику конфиденциальности' }) })
}).refine((d) => d.password === d.password_confirm, {
  message: 'Пароли не совпадают',
  path: ['password_confirm']
})
type Step1Schema = z.output<typeof step1Schema>
const step1Form = reactive<Partial<Step1Schema>>({
  email: '',
  phone: '',
  password: '',
  password_confirm: '',
  offer_accepted: undefined,
  privacy_accepted: undefined
})

// Шаг 2
const digits = ref<string[]>(['', '', '', '', '', ''])
const inputRefs = ref<(HTMLInputElement | null)[]>(Array(6).fill(null))
const isVerifying = ref(false)
const isResending = ref(false)
const code = computed(() => digits.value.join(''))

// Шаг 3
const step3Loading = ref(false)
const specialtyOptions = ref<{ label: string; value: number | null }[][]>([])
const specialtiesLoading = ref(false)
const step3Schema = z.object({
  username: z.string().min(3, 'Минимум 3 символа').max(30, 'Максимум 30 символов').regex(/^[a-zA-Z0-9_-]+$/, 'Только буквы, цифры, дефисы и подчёркивания'),
  first_name: z.string().min(1, 'Укажите имя'),
  specialty_id: z.number().nullable().optional()
})
type Step3Schema = z.output<typeof step3Schema>
const step3Form = reactive<Partial<Step3Schema>>({
  username: '',
  first_name: '',
  specialty_id: null
})

const stepNames = ['Регистрация', 'Подтверждение почты', 'Профиль']
const stepName = computed(() => stepNames[step.value - 1])

onMounted(async () => {
  specialtiesLoading.value = true
  try {
    const data = await $fetch<{ id: number; name: string; order: number; specialties: { id: number; name: string; order: number }[] }[]>(
      `${config.public.apiBase}/api/public/specialties/`
    )
    const groups = data.map(cat =>
      cat.specialties.map(s => ({ label: s.name, value: s.id }))
    )
    specialtyOptions.value = [[{ label: '— Не выбрано —', value: null }], ...groups]
  } finally {
    specialtiesLoading.value = false
  }
})

async function onStep1Submit(payload: FormSubmitEvent<Step1Schema>) {
  step1Loading.value = true
  try {
    const result = await register({
      email: payload.data.email,
      phone: payload.data.phone,
      password: payload.data.password,
      password_confirm: payload.data.password_confirm,
      offer_accepted: payload.data.offer_accepted,
      privacy_accepted: payload.data.privacy_accepted
    })
    if (result.success && result.needsVerification && result.email) {
      pendingEmail.value = result.email
      step.value = 2
      nextTick(() => {
        digits.value = ['', '', '', '', '', '']
        inputRefs.value[0]?.focus()
      })
    }
  } finally {
    step1Loading.value = false
  }
}

async function onVerify() {
  if (code.value.length !== 6) return
  isVerifying.value = true
  try {
    const result = await verifyEmail(pendingEmail.value, code.value)
    if (result.success) {
      step.value = 3
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
  if (val && index < 5) inputRefs.value[index + 1]?.focus()
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
  for (let i = 0; i < pasted.length && i < 6; i++) newDigits[i] = pasted[i]
  digits.value = newDigits
  inputRefs.value[Math.min(pasted.length, 5)]?.focus()
}

async function onResend() {
  isResending.value = true
  try {
    await resendVerificationCode(pendingEmail.value)
  } finally {
    isResending.value = false
  }
}

function goBackToStep1() {
  step.value = 1
  pendingEmail.value = ''
  digits.value = ['', '', '', '', '', '']
}

async function onStep3Submit(payload: FormSubmitEvent<Step3Schema>) {
  step3Loading.value = true
  try {
    const result = await completeProfile({
      username: payload.data.username,
      first_name: payload.data.first_name,
      specialty_id: payload.data.specialty_id ?? null
    })
    if (result.success) {
      router.push('/schedule')
    }
  } finally {
    step3Loading.value = false
  }
}

const btnClass = '!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100'
</script>

<template>
  <div class="w-full">
    <!-- Прогресс -->
    <div class="flex items-center justify-between gap-2 mb-6">
      <div class="flex gap-1 flex-1">
        <div
          v-for="i in 3"
          :key="i"
          class="h-1.5 flex-1 rounded-full transition-colors"
          :class="step >= i ? 'bg-foreground/80' : 'bg-default'"
        />
      </div>
      <span class="text-sm font-medium text-muted shrink-0">
        Шаг {{ step }} из 3
      </span>
    </div>
    <h2 class="text-lg font-semibold text-highlighted mb-6">
      {{ stepName }}
    </h2>

    <!-- Контейнер фиксированной высоты -->
    <div class="min-h-[420px] flex flex-col">
      <!-- Шаг 1 -->
      <UForm
        v-if="step === 1"
        :schema="step1Schema"
        :state="step1Form"
        @submit="onStep1Submit"
        class="flex flex-col flex-1"
      >
        <div class="space-y-4 flex-1">
          <UFormField name="email" label="Email" required class="w-full">
            <div class="w-full min-w-0">
              <UInput
                v-model="step1Form.email"
                type="email"
                placeholder="example@mail.ru"
                autocomplete="email"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="phone" label="Номер телефона" required class="w-full">
            <div class="w-full min-w-0">
              <UInput
                v-model="step1Form.phone"
                type="tel"
                placeholder="+7 (999) 123-45-67"
                autocomplete="tel"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="password" label="Пароль" required class="w-full">
            <div class="w-full min-w-0">
              <UInput
                v-model="step1Form.password"
                type="password"
                placeholder="Минимум 8 символов"
                autocomplete="new-password"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="password_confirm" label="Подтвердить пароль" required class="w-full">
            <div class="w-full min-w-0">
              <UInput
                v-model="step1Form.password_confirm"
                type="password"
                placeholder="Повторите пароль"
                autocomplete="new-password"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="offer_accepted" required>
            <label class="flex items-start gap-2 cursor-pointer">
              <UCheckbox v-model="step1Form.offer_accepted" />
              <span class="text-sm">Я принимаю <ULink to="/terms" class="underline hover:no-underline">условия пользования</ULink> <span class="text-red-500">*</span></span>
            </label>
          </UFormField>
          <UFormField name="privacy_accepted" required>
            <label class="flex items-start gap-2 cursor-pointer">
              <UCheckbox v-model="step1Form.privacy_accepted" />
              <span class="text-sm">Я принимаю <ULink to="/privacy" class="underline hover:no-underline">политику конфиденциальности</ULink> <span class="text-red-500">*</span></span>
            </label>
          </UFormField>
        </div>
        <UButton
          type="submit"
          block
          size="lg"
          :loading="step1Loading"
          color="neutral"
          variant="solid"
          :class="btnClass"
          class="mt-6"
        >
          Зарегистрироваться
        </UButton>
      </UForm>

      <!-- Шаг 2 -->
      <div v-else-if="step === 2" class="flex flex-col flex-1">
        <p class="text-muted text-sm mb-4">
          Мы отправили код на <strong class="text-foreground">{{ pendingEmail }}</strong>
        </p>
        <form @submit.prevent="onVerify" class="flex flex-col flex-1">
          <div class="mb-4">
            <label class="block text-sm font-medium text-foreground mb-2">Код из письма</label>
            <div class="flex justify-center gap-1.5 sm:gap-2" role="group" aria-label="Код подтверждения">
              <input
                v-for="(_, i) in 6"
                :key="i"
                :ref="(el) => { if (el) inputRefs[i] = el as HTMLInputElement }"
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
            :class="btnClass"
            class="mt-auto"
          >
            Подтвердить
          </UButton>
        </form>
        <div class="flex flex-col items-center gap-1.5 mt-4 text-sm">
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
            class="text-muted hover:text-foreground"
            @click="goBackToStep1"
          >
            Изменить email
          </button>
        </div>
      </div>

      <!-- Шаг 3 -->
      <UForm
        v-else-if="step === 3"
        :schema="step3Schema"
        :state="step3Form"
        @submit="onStep3Submit"
        class="flex flex-col flex-1"
      >
        <div class="space-y-4 flex-1">
          <UFormField name="username" label="Имя пользователя (публичная ссылка)" required class="w-full">
            <template #description>
              Уникальный адрес вашего профиля для бронирования. Будет отображаться в URL, например: bookly.ru/booking/<strong>{{ step3Form.username || 'username' }}</strong>
            </template>
            <div class="w-full min-w-0">
              <UInput
                v-model="step3Form.username"
                placeholder="username"
                autocomplete="username"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="first_name" label="Имя" required class="w-full">
            <template #description>
              Имя, которое будет отображаться в вашем профиле
            </template>
            <div class="w-full min-w-0">
              <UInput
                v-model="step3Form.first_name"
                placeholder="Введите ваше имя"
                autocomplete="given-name"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="specialty_id" label="Специальность" class="w-full">
            <div class="w-full min-w-0">
              <USelect
                v-model="step3Form.specialty_id"
                :items="specialtyOptions"
                placeholder="Выберите специальность"
                :loading="specialtiesLoading"
                value-key="value"
                class="!w-full"
              />
            </div>
          </UFormField>
        </div>
        <UButton
          type="submit"
          block
          size="lg"
          :loading="step3Loading"
          color="neutral"
          variant="solid"
          :class="btnClass"
          class="mt-6"
        >
          Завершить
        </UButton>
      </UForm>
    </div>

    <p class="mt-6 text-center text-muted text-sm">
      Уже есть аккаунт? <ULink to="/login" class="text-foreground font-medium hover:underline">Войти</ULink>
    </p>
  </div>
</template>
