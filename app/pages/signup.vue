<script setup lang="ts">
import * as z from 'zod'
import type { FormSubmitEvent } from '@nuxt/ui'
import { zodPhoneRequired } from '~/utils/phone'
import { workScheduleTemplateList, type WorkScheduleTemplateId, type ShiftCycleId } from '~/utils/workScheduleTemplates'
import { format } from 'date-fns'

definePageMeta({
  layout: 'auth',
  middleware: 'guest'
})

useSeoMeta({
  title: 'Регистрация',
  description: 'Создайте аккаунт, чтобы начать'
})

const config = useRuntimeConfig()
const { register, registerCredentials, verifyEmail, resendVerificationCode, completeProfile, patchProfile } = useAuth()
const router = useRouter()
const step = ref(1)
const pendingEmail = ref('')

// Шаг 1 — email, имя, согласия
const step1Loading = ref(false)
const step1Schema = z.object({
  email: z.string().email('Неверный формат электронной почты'),
  first_name: z.string().min(1, 'Укажите имя'),
  offer_accepted: z.boolean().refine((v) => v === true, { message: 'Необходимо принять условия пользования' }),
  privacy_accepted: z.boolean().refine((v) => v === true, { message: 'Необходимо принять политику конфиденциальности' })
})
type Step1Schema = z.output<typeof step1Schema>
const step1Form = reactive<Partial<Step1Schema>>({
  email: '',
  first_name: '',
  offer_accepted: false,
  privacy_accepted: false
})

// Шаг 2 — код
const digits = ref<string[]>(['', '', '', '', '', ''])
const inputRefs = ref<(HTMLInputElement | null)[]>(Array(6).fill(null))
const isVerifying = ref(false)
const isResending = ref(false)
const code = computed(() => digits.value.join(''))

// Шаг 3 — пароль
const step3Loading = ref(false)
const step3Schema = z.object({
  password: z.string().min(8, 'Пароль должен содержать минимум 8 символов'),
  password_confirm: z.string().min(8, 'Подтверждение пароля обязательно')
}).refine((d) => d.password === d.password_confirm, {
  message: 'Пароли не совпадают',
  path: ['password_confirm']
})
type Step3Schema = z.output<typeof step3Schema>
const step3Form = reactive<Partial<Step3Schema>>({
  password: '',
  password_confirm: ''
})

// Шаг 4 — профиль
const step4Loading = ref(false)
const specialtyOptions = ref<{ label: string; value: number | null }[][]>([])
const specialtiesLoading = ref(false)
const step4Schema = z.object({
  phone: zodPhoneRequired(),
  username: z.string().min(3, 'Минимум 3 символа').max(30, 'Максимум 30 символов').regex(/^[a-zA-Z0-9_-]+$/, 'Только буквы, цифры, дефисы и подчёркивания'),
  specialty_id: z.number().nullable().optional()
})
type Step4Schema = z.output<typeof step4Schema>
const step4Form = reactive<Partial<Step4Schema>>({
  phone: '',
  username: '',
  specialty_id: null
})

// Шаг 5 — шаблон графика (после сохранения профиля)
const step5Loading = ref(false)
const step5Schema = z.object({
  work_schedule_template: z.string().min(1, 'Выберите шаблон'),
  shift_cycle: z.string().optional(),
  shift_anchor_date: z.string().optional()
})
type Step5Schema = z.output<typeof step5Schema>
const step5Form = reactive<Partial<Step5Schema>>({
  work_schedule_template: 'standard-5' as WorkScheduleTemplateId,
  shift_cycle: '2-2' as ShiftCycleId,
  shift_anchor_date: format(new Date(), 'yyyy-MM-dd')
})

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
      first_name: payload.data.first_name,
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

async function onStep3Submit(payload: FormSubmitEvent<Step3Schema>) {
  step3Loading.value = true
  try {
    const result = await registerCredentials({
      password: payload.data.password,
      password_confirm: payload.data.password_confirm
    })
    if (result.success) {
      step.value = 4
    }
  } finally {
    step3Loading.value = false
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
  for (let i = 0; i < pasted.length && i < 6; i++) {
    const ch = pasted[i]
    if (ch !== undefined) newDigits[i] = ch
  }
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

async function onStep4Submit(payload: FormSubmitEvent<Step4Schema>) {
  step4Loading.value = true
  try {
    const result = await completeProfile({
      phone: payload.data.phone,
      username: payload.data.username,
      specialty_id: payload.data.specialty_id ?? null
    })
    if (result.success) {
      step.value = 5
    }
  } finally {
    step4Loading.value = false
  }
}

async function onStep5Submit(payload: FormSubmitEvent<Step5Schema>) {
  step5Loading.value = true
  try {
    const t = payload.data.work_schedule_template
    const r = await patchProfile({
      work_schedule_template: t,
      shift_cycle: t === 'shift-cycle' ? (payload.data.shift_cycle ?? '2-2') : '2-2',
      shift_anchor_date: t === 'shift-cycle' ? (payload.data.shift_anchor_date ?? null) : null
    })
    if (r.success) {
      router.push('/schedule')
    }
  } finally {
    step5Loading.value = false
  }
}

const btnClass = '!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100'
</script>

<template>
  <div class="w-full space-y-6">
    <!-- Как у страницы входа: UAuthForm (иконка → заголовок → подпись со ссылкой) -->
    <div class="flex flex-col text-center">
      <div class="mb-2 flex justify-center">
        <UIcon name="i-lucide-lock" class="size-8 shrink-0" />
      </div>
      <h1 class="text-xl text-pretty font-semibold text-highlighted">
        Регистрация
      </h1>
      <p class="mt-1 text-base text-pretty text-muted">
        Уже есть аккаунт? <ULink to="/login" class="link-inline">Войти</ULink>
      </p>
    </div>

    <div class="min-h-[420px] flex flex-col">
      <!-- Шаг 1 -->
      <UForm
        v-if="step === 1"
        :schema="step1Schema"
        :state="step1Form"
        @submit="onStep1Submit"
        class="flex flex-col"
      >
        <div class="space-y-4">
          <UFormField name="first_name" label="Имя" required class="w-full">
            <div class="w-full min-w-0">
              <UInput
                v-model="step1Form.first_name"
                placeholder="Введите ваше имя"
                autocomplete="given-name"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="email" label="Электронная почта" required class="w-full">
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
          <UFormField name="offer_accepted" required>
            <label class="flex items-start gap-2 cursor-pointer">
              <UCheckbox v-model="step1Form.offer_accepted" />
              <span class="text-sm text-muted">Я принимаю <ULink to="/terms" class="link-inline">условия пользования</ULink> <span class="text-red-500">*</span></span>
            </label>
          </UFormField>
          <UFormField name="privacy_accepted" required>
            <label class="flex items-start gap-2 cursor-pointer">
              <UCheckbox v-model="step1Form.privacy_accepted" />
              <span class="text-sm text-muted">Я принимаю <ULink to="/privacy" class="link-inline">политику конфиденциальности</ULink> <span class="text-red-500">*</span></span>
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
          class="mt-4"
        >
          Продолжить
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
                class="size-11 text-center text-lg sm:text-xl font-semibold rounded-lg border-2 border-default bg-background text-foreground focus:border-foreground/50 focus:ring-2 focus:ring-default focus:outline-none transition-all"
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

      <!-- Шаг 3 — пароль -->
      <UForm
        v-else-if="step === 3"
        :schema="step3Schema"
        :state="step3Form"
        @submit="onStep3Submit"
        class="flex flex-col"
      >
        <div class="space-y-4">
          <UFormField name="password" label="Пароль" required class="w-full">
            <div class="w-full min-w-0">
              <PasswordInput
                v-model="step3Form.password"
                placeholder="Минимум 8 символов"
                autocomplete="new-password"
              />
            </div>
          </UFormField>
          <UFormField name="password_confirm" label="Подтвердить пароль" required class="w-full">
            <div class="w-full min-w-0">
              <PasswordInput
                v-model="step3Form.password_confirm"
                placeholder="Повторите пароль"
                autocomplete="new-password"
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
          class="mt-4"
        >
          Продолжить
        </UButton>
      </UForm>

      <!-- Шаг 4 — профиль -->
      <UForm
        v-else-if="step === 4"
        :schema="step4Schema"
        :state="step4Form"
        @submit="onStep4Submit"
        class="flex flex-col"
      >
        <div class="space-y-4">
          <UFormField name="phone" label="Номер телефона" required class="w-full">
            <div class="w-full min-w-0">
              <PhoneInputRu
                v-model="step4Form.phone"
                placeholder="+7 (999) 123-45-67"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="username" label="Имя пользователя (публичная ссылка)" required class="w-full">
            <template #description>
              Уникальный адрес вашего профиля для бронирования. Будет отображаться в URL, например: bookly.ru/booking/<strong>{{ step4Form.username || 'username' }}</strong>
            </template>
            <div class="w-full min-w-0">
              <UInput
                v-model="step4Form.username"
                placeholder="username"
                autocomplete="username"
                class="!w-full"
              />
            </div>
          </UFormField>
          <UFormField name="specialty_id" label="Специальность" class="w-full">
            <div class="w-full min-w-0">
              <USelect
                v-model="step4Form.specialty_id"
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
          :loading="step4Loading"
          color="neutral"
          variant="solid"
          :class="btnClass"
          class="mt-4"
        >
          Продолжить
        </UButton>
      </UForm>

      <!-- Шаг 5 — шаблон расписания -->
      <UForm
        v-else-if="step === 5"
        :schema="step5Schema"
        :state="step5Form"
        @submit="onStep5Submit"
        class="flex flex-col"
      >
        <p class="text-sm text-muted mb-4 text-left">
          Выберите типичный график — его можно в любой момент изменить в разделе «График работы».
        </p>
        <div class="space-y-4">
          <UFormField name="work_schedule_template" label="Шаблон расписания" required class="w-full">
            <div class="w-full min-w-0">
              <USelect
                v-model="step5Form.work_schedule_template"
                :items="workScheduleTemplateList.map(t => ({ label: `${t.title} — ${t.shortLabel}`, value: t.id }))"
                value-key="value"
                class="!w-full"
              />
            </div>
          </UFormField>
          <div
            v-if="step5Form.work_schedule_template === 'shift-cycle'"
            class="flex flex-col gap-3 sm:flex-row sm:items-end"
          >
            <UFormField name="shift_cycle" label="Цикл" class="w-full sm:flex-1">
              <USelect
                v-model="step5Form.shift_cycle"
                :items="[
                  { label: '2 / 2', value: '2-2' },
                  { label: '3 / 3', value: '3-3' },
                  { label: '4 / 4', value: '4-4' }
                ]"
                class="!w-full"
              />
            </UFormField>
            <UFormField name="shift_anchor_date" label="Начало цикла" class="w-full sm:flex-1">
              <UInput
                v-model="step5Form.shift_anchor_date"
                type="date"
                class="!w-full"
              />
            </UFormField>
          </div>
        </div>
        <div class="flex flex-col gap-2 mt-4">
          <UButton
            type="submit"
            block
            size="lg"
            :loading="step5Loading"
            color="neutral"
            variant="solid"
            :class="btnClass"
          >
            Начать работу
          </UButton>
          <button
            type="button"
            class="text-sm text-muted hover:text-foreground"
            :disabled="step5Loading"
            @click="step = 4"
          >
            Назад
          </button>
        </div>
      </UForm>
    </div>
  </div>
</template>
