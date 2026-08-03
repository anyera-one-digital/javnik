<script setup lang="ts">
import { format, parseISO, differenceInDays } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { Customer } from '~/types'
import {
  customerStatusIcon,
  customerStatusLabel,
  resolveCustomerStatus,
  type CustomerStatus
} from '~/utils/customerStatus'

export type CustomerListFilter = 'all' | CustomerStatus | 'stale'

const PAGE_SIZE = 10
const STALE_DAYS = 45

const props = defineProps<{
  customers: Customer[]
  selectedId: number | null
  search: string
  filter: CustomerListFilter
}>()

const emit = defineEmits<{
  select: [customer: Customer]
  'update:search': [value: string]
  'update:filter': [value: CustomerListFilter]
}>()

const page = ref(1)

function isStale(c: Customer) {
  const today = new Date()
  if (c.last_visit_date) {
    try {
      return differenceInDays(today, parseISO(c.last_visit_date)) > STALE_DAYS
    } catch {
      return false
    }
  }
  if (c.created_at) {
    try {
      return differenceInDays(today, parseISO(c.created_at)) > STALE_DAYS
    } catch {
      return false
    }
  }
  return false
}

function matchesFilter(c: Customer, filter: CustomerListFilter) {
  if (filter === 'all') return true
  if (filter === 'stale') return isStale(c)
  return resolveCustomerStatus(c) === filter
}

const filterSelectValue = computed({
  get: () => props.filter,
  set: (value: CustomerListFilter) => emit('update:filter', value)
})

const filterItems = [
  { label: 'Все', value: 'all' as const, icon: 'i-lucide-users' },
  { label: customerStatusLabel('first-time'), value: 'first-time' as const, icon: customerStatusIcon('first-time') },
  { label: customerStatusLabel('regular'), value: 'regular' as const, icon: customerStatusIcon('regular') },
  { label: customerStatusLabel('loyal'), value: 'loyal' as const, icon: customerStatusIcon('loyal') },
  { label: customerStatusLabel('vip'), value: 'vip' as const, icon: customerStatusIcon('vip') },
  { label: 'Давно не были', value: 'stale' as const, icon: 'i-lucide-clock' }
]

const filterLeadingIcon = computed(() => {
  const selected = filterItems.find(item => item.value === props.filter)
  return selected?.icon ?? 'i-lucide-users'
})

const filtered = computed(() => {
  const q = props.search.trim().toLowerCase()
  return props.customers.filter((c) => {
    if (!matchesFilter(c, props.filter)) return false
    if (!q) return true
    return (
      c.name.toLowerCase().includes(q)
      || (c.email || '').toLowerCase().includes(q)
      || (c.phone || '').includes(q)
    )
  })
})

const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))

const paged = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filtered.value.slice(start, start + PAGE_SIZE)
})

watch(
  () => [props.search, props.filter, filtered.value.length] as const,
  () => {
    page.value = 1
  }
)

watch(pageCount, (count) => {
  if (page.value > count) page.value = count
})

function formatLastVisit(dateStr?: string | null) {
  if (!dateStr) return '—'
  try {
    return format(parseISO(dateStr), 'd MMM yyyy', { locale: ru })
  } catch {
    return '—'
  }
}
</script>

<template>
  <div class="flex flex-col gap-3 min-h-0 h-full overflow-hidden">
    <div class="flex items-center gap-2 shrink-0">
      <UInput
        :model-value="search"
        icon="i-lucide-search"
        placeholder="Найти клиента"
        size="md"
        class="min-w-0 flex-[3]"
        :ui="{ base: 'bg-transparent' }"
        @update:model-value="emit('update:search', String($event ?? ''))"
      />
      <USelect
        v-model="filterSelectValue"
        :items="filterItems"
        :leading-icon="filterLeadingIcon"
        color="neutral"
        size="md"
        variant="outline"
        class="min-w-0 flex-[2]"
        :ui="{
          base: 'ps-9 pe-9 focus:ring-violet-500',
          leading: 'ps-3.5',
          trailing: 'pe-3.5',
          trailingIcon: 'group-data-[state=open]:rotate-180 transition-transform duration-200'
        }"
      />
    </div>

    <div class="flex-1 min-h-0 overflow-hidden flex flex-col">
      <div class="hidden sm:grid grid-cols-[minmax(0,1fr)_7.5rem_4.5rem] gap-2 py-2.5 px-3 text-[11px] text-muted border-b border-default/40 shrink-0">
        <span>Клиент</span>
        <span>Последний визит</span>
        <span class="text-center">Визитов</span>
      </div>

      <div class="flex-1 min-h-0 overflow-hidden">
        <div v-if="!filtered.length" class="py-12 text-center text-sm text-muted">
          Клиенты не найдены
        </div>

        <div
          v-for="c in paged"
          :key="c.id"
          class="catalog-list-row w-full text-left grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_7.5rem_4.5rem] gap-2 items-center py-3 px-3 border-b border-default/30 last:border-0 cursor-pointer transition-colors"
          :class="selectedId === c.id
            ? 'bg-black/[0.04] dark:bg-white/[0.06]'
            : 'hover:bg-black/[0.03] dark:hover:bg-white/[0.03]'"
          @click="emit('select', c)"
        >
          <div class="min-w-0">
            <span class="font-medium text-highlighted truncate block">{{ c.name }}</span>
          </div>
          <span class="text-sm text-muted tabular-nums">{{ formatLastVisit(c.last_visit_date) }}</span>
          <span class="text-sm text-highlighted tabular-nums text-center">{{ c.visits_count ?? 0 }}</span>
        </div>
      </div>
    </div>

    <div
      v-if="filtered.length > PAGE_SIZE"
      class="catalog-pagination shrink-0 flex justify-center pt-1"
    >
      <UPagination
        v-model:page="page"
        :total="filtered.length"
        :items-per-page="PAGE_SIZE"
        :sibling-count="1"
        show-edges
        size="xs"
        color="neutral"
        variant="outline"
      >
        <template #item="{ page: current, item }">
          <UButton
            :label="String(item.value)"
            square
            size="xs"
            color="neutral"
            :variant="current === item.value ? 'solid' : 'outline'"
            :class="current === item.value ? 'catalog-pagination-active' : ''"
          />
        </template>
      </UPagination>
    </div>
  </div>
</template>
