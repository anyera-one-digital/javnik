<script setup lang="ts">
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { Customer, CustomerHistoryItem } from '~/types'
import {
  CUSTOMER_STATUS_SELECT_ITEMS,
  autoCustomerStatus,
  customerStatusIcon,
  customerStatusLabel,
  resolveCustomerStatus,
  type CustomerStatus
} from '~/utils/customerStatus'

const HISTORY_INITIAL = 3

const props = defineProps<{
  customer: Customer | null
  history: CustomerHistoryItem[]
  loadingHistory?: boolean
  saving?: boolean
}>()

const emit = defineEmits<{
  save: [payload: Partial<Customer>]
  remove: []
  book: []
}>()

const toast = useToast()

const draft = reactive({
  name: '',
  email: '',
  phone: '',
  notes: '',
  status: 'regular' as CustomerStatus,
  statusManual: false
})

const editingField = ref<string | null>(null)
const historyExpanded = ref(false)

watch(
  () => props.customer,
  (c) => {
    editingField.value = null
    historyExpanded.value = false
    if (!c) return
    draft.name = c.name || ''
    draft.email = c.email || ''
    draft.phone = c.phone || ''
    draft.notes = c.notes || ''
    draft.statusManual = Boolean(c.status_manual)
    draft.status = resolveCustomerStatus(c)
  },
  { immediate: true }
)

const formatMoney = (v: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(v)

/** Select value: 'auto' or an explicit status */
const statusSelectValue = computed({
  get(): 'auto' | CustomerStatus {
    return draft.statusManual ? draft.status : 'auto'
  },
  set(value: 'auto' | CustomerStatus) {
    if (value === 'auto') {
      draft.statusManual = false
      draft.status = autoCustomerStatus(props.customer?.visits_count ?? 0)
      return
    }
    draft.statusManual = true
    draft.status = value
  }
})

const statusSelectItems = computed(() => {
  const autoResolved = autoCustomerStatus(props.customer?.visits_count ?? 0)
  const autoLabel = customerStatusLabel(autoResolved)
  return CUSTOMER_STATUS_SELECT_ITEMS.map((item) =>
    item.value === 'auto'
      ? {
          ...item,
          label: `Автоматически · ${autoLabel}`,
          icon: customerStatusIcon(autoResolved)
        }
      : item
  )
})

/** Icon for closed select trigger (item.icon only shows in dropdown) */
const statusLeadingIcon = computed(() => {
  const selected = statusSelectItems.value.find(item => item.value === statusSelectValue.value)
  return selected?.icon ?? customerStatusIcon(draft.status)
})

function formatDateLong(dateStr?: string | null) {
  if (!dateStr) return '—'
  try {
    return format(parseISO(dateStr), 'd MMMM yyyy', { locale: ru })
  } catch {
    return '—'
  }
}

function formatNext(c: Customer) {
  if (!c.next_booking_date) return '—'
  try {
    const d = format(parseISO(c.next_booking_date), 'd MMMM', { locale: ru })
    return c.next_booking_time ? `${d}, ${c.next_booking_time}` : d
  } catch {
    return '—'
  }
}

function formatHistoryDate(dateStr: string) {
  try {
    return format(parseISO(dateStr), 'd MMMM yyyy', { locale: ru })
  } catch {
    return dateStr
  }
}

const pastHistory = computed(() =>
  props.history
    .filter(h => h.status === 'completed' || !h.isUpcoming)
    .slice()
    .sort((a, b) => {
      const byDate = b.date.localeCompare(a.date)
      if (byDate !== 0) return byDate
      return (b.startTime || '').localeCompare(a.startTime || '')
    })
)

const visibleHistory = computed(() =>
  historyExpanded.value
    ? pastHistory.value
    : pastHistory.value.slice(0, HISTORY_INITIAL)
)

const hasMoreHistory = computed(() =>
  !historyExpanded.value && pastHistory.value.length > HISTORY_INITIAL
)

watch(
  () => pastHistory.value.length,
  () => {
    historyExpanded.value = false
  }
)

function showMoreHistory() {
  historyExpanded.value = true
}

function startEdit(field: string) {
  editingField.value = field
}

function commitField() {
  editingField.value = null
}

function saveAll() {
  if (!props.customer) return
  const name = draft.name.trim()
  const email = draft.email.trim()
  if (name.length < 2) {
    toast.add({ title: 'Ошибка', description: 'Укажите имя клиента', color: 'error' })
    return
  }
  if (!email || !email.includes('@')) {
    toast.add({ title: 'Ошибка', description: 'Укажите корректный email', color: 'error' })
    return
  }
  const visits = props.customer.visits_count ?? 0
  const status = draft.statusManual ? draft.status : autoCustomerStatus(visits)
  emit('save', {
    name,
    email,
    phone: draft.phone.trim() || undefined,
    notes: draft.notes.trim() || undefined,
    status,
    status_manual: draft.statusManual
  })
}
</script>

<template>
  <div class="catalog-panel rounded-[14px] h-full min-h-0 flex flex-col overflow-hidden">
    <div
      v-if="!customer"
      class="flex-1 flex items-center justify-center text-sm text-muted px-6 text-center"
    >
      Выберите клиента в списке
    </div>

    <template v-else>
      <div class="px-5 pt-4 pb-3 border-b border-default/40 shrink-0 space-y-2">
        <div class="flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <input
              v-if="editingField === 'name'"
              v-model="draft.name"
              class="w-full bg-transparent text-lg font-semibold text-highlighted outline-none border-b border-violet-500"
              @blur="commitField"
              @keydown.enter="commitField"
            >
            <h3
              v-else
              class="text-lg font-semibold text-highlighted truncate cursor-pointer hover:text-violet-400"
              @click="startEdit('name')"
            >
              {{ draft.name || customer.name }}
            </h3>
          </div>
          <UButton
            icon="i-lucide-pencil"
            color="neutral"
            variant="ghost"
            size="xs"
            class="shrink-0"
            @click="startEdit('name')"
          />
        </div>

        <div class="flex items-center">
          <USelect
            v-model="statusSelectValue"
            :items="statusSelectItems"
            :leading-icon="statusLeadingIcon"
            color="neutral"
            size="xs"
            variant="outline"
            class="min-w-[12rem]"
            :ui="{
              base: 'ps-9 pe-9 focus:ring-violet-500',
              leading: 'ps-3.5',
              trailing: 'pe-3.5',
              trailingIcon: 'group-data-[state=open]:rotate-180 transition-transform duration-200'
            }"
          />
        </div>

        <div class="space-y-1 text-sm">
          <div class="flex items-baseline justify-between gap-3">
            <span class="text-muted">Следующая запись</span>
            <span
              class="font-medium"
              :class="customer.next_booking_date ? 'text-violet-400' : 'text-highlighted'"
            >
              {{ formatNext(customer) }}
            </span>
          </div>
          <div class="flex items-baseline justify-between gap-3">
            <span class="text-muted">Последний визит</span>
            <span class="text-highlighted">{{ formatDateLong(customer.last_visit_date) }}</span>
          </div>
        </div>
      </div>

      <div class="flex-1 min-h-0 overflow-hidden flex flex-col px-5 pt-2 pb-3">
        <div class="shrink-0">
          <!-- Phone -->
          <div class="flex items-center gap-3 py-1 border-b border-default/30">
            <UIcon name="i-lucide-phone" class="size-4 text-muted shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="text-[11px] text-muted leading-tight">Телефон</p>
              <input
                v-if="editingField === 'phone'"
                v-model="draft.phone"
                type="tel"
                class="w-full bg-transparent text-sm text-highlighted outline-none"
                placeholder="+7 …"
                @blur="commitField"
                @keydown.enter="commitField"
              >
              <p
                v-else
                class="text-sm text-highlighted cursor-pointer hover:text-violet-400 leading-snug"
                @click="startEdit('phone')"
              >
                {{ draft.phone || 'Добавить телефон' }}
              </p>
            </div>
            <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" size="xs" @click="startEdit('phone')" />
          </div>

          <!-- Email -->
          <div class="flex items-center gap-3 py-1 border-b border-default/30">
            <UIcon name="i-lucide-mail" class="size-4 text-muted shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="text-[11px] text-muted leading-tight">Email</p>
              <input
                v-if="editingField === 'email'"
                v-model="draft.email"
                type="email"
                class="w-full bg-transparent text-sm text-highlighted outline-none"
                placeholder="email@example.com"
                @blur="commitField"
                @keydown.enter="commitField"
              >
              <p
                v-else
                class="text-sm text-highlighted truncate cursor-pointer hover:text-violet-400 leading-snug"
                @click="startEdit('email')"
              >
                {{ draft.email || 'Добавить email' }}
              </p>
            </div>
            <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" size="xs" @click="startEdit('email')" />
          </div>

          <!-- Notes -->
          <div class="flex items-start gap-3 py-1 border-b border-default/30">
            <UIcon name="i-lucide-align-left" class="size-4 text-muted shrink-0 mt-0.5" />
            <div class="flex-1 min-w-0">
              <p class="text-[11px] text-muted leading-tight">Заметки</p>
              <textarea
                v-if="editingField === 'notes'"
                v-model="draft.notes"
                rows="2"
                class="w-full bg-transparent text-sm text-highlighted outline-none resize-none"
                placeholder="Заметки о клиенте"
                @blur="commitField"
              />
              <p
                v-else
                class="text-sm text-highlighted whitespace-pre-wrap cursor-pointer hover:text-violet-400 leading-snug line-clamp-2"
                @click="startEdit('notes')"
              >
                {{ draft.notes || 'Добавить заметку' }}
              </p>
            </div>
            <UButton icon="i-lucide-pencil" color="neutral" variant="ghost" size="xs" @click="startEdit('notes')" />
          </div>
        </div>

        <div
          class="min-h-0 flex flex-col pt-2"
          :class="historyExpanded ? 'flex-1' : 'shrink-0'"
        >
          <h4 class="text-sm font-semibold text-highlighted mb-1.5 shrink-0">
            Визиты
            <span class="tabular-nums text-violet-400 font-semibold">{{ customer.visits_count ?? 0 }}</span>
          </h4>
          <div
            class="min-h-0"
            :class="historyExpanded ? 'flex-1 overflow-y-auto' : 'overflow-visible'"
          >
            <div v-if="loadingHistory" class="text-sm text-muted py-3 text-center">
              Загрузка...
            </div>
            <div v-else-if="!pastHistory.length" class="text-sm text-muted py-3 text-center">
              Пока нет завершённых визитов
            </div>
            <ul v-else class="space-y-2">
              <li
                v-for="item in visibleHistory"
                :key="item.id"
                class="flex items-start justify-between gap-3 text-sm"
              >
                <div class="min-w-0">
                  <p class="text-xs text-muted mb-0.5">{{ formatHistoryDate(item.date) }}</p>
                  <p class="text-highlighted truncate">{{ item.serviceName }}</p>
                </div>
                <span class="shrink-0 tabular-nums text-muted">{{ formatMoney(item.price) }}</span>
              </li>
            </ul>
          </div>

          <div v-if="hasMoreHistory" class="shrink-0 pt-1.5 flex justify-center">
            <UButton
              label="Показать ещё"
              color="neutral"
              variant="ghost"
              size="sm"
              class="text-violet-500 hover:text-violet-400"
              @click="showMoreHistory"
            />
          </div>
        </div>
      </div>

      <div class="p-4 border-t border-default/40 flex items-center gap-2 shrink-0">
        <UButton
          label="Сохранить"
          class="min-w-0 flex-1 !bg-violet-500 !text-white hover:!bg-violet-400 justify-center"
          :loading="saving"
          @click="saveAll"
        />
        <UButton
          label="Записать"
          icon="i-lucide-calendar-plus"
          color="neutral"
          variant="outline"
          class="shrink-0"
          :disabled="saving"
          @click="emit('book')"
        />
        <UButton
          icon="i-lucide-trash"
          color="error"
          variant="outline"
          square
          class="icon-btn-round shrink-0"
          :disabled="saving"
          @click="emit('remove')"
        />
      </div>
    </template>
  </div>
</template>
