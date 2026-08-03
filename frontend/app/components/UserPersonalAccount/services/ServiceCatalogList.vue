<script setup lang="ts">
import type { Service } from '~/types'
import { formatDurationMinutes } from '~/utils/formatDuration'

export type ServiceFilter = 'all' | 'published' | 'hidden'

const PAGE_SIZE = 10

const props = defineProps<{
  services: Service[]
  selectedId: number | null
  filter: ServiceFilter
}>()

const emit = defineEmits<{
  select: [service: Service]
  reorder: [ids: number[]]
  'update:filter': [value: ServiceFilter]
}>()

const page = ref(1)

const formatMoney = (v: number) =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(v)

const publishedCount = computed(() => props.services.filter(s => s.active !== false).length)
const hiddenCount = computed(() => props.services.filter(s => s.active === false).length)

const filters = computed(() => [
  { id: 'all' as const, label: `Все ${props.services.length}` },
  { id: 'published' as const, label: `Опубликованы ${publishedCount.value}` },
  { id: 'hidden' as const, label: `Скрытые ${hiddenCount.value}` }
])

const filtered = computed(() => {
  if (props.filter === 'published') return props.services.filter(s => s.active !== false)
  if (props.filter === 'hidden') return props.services.filter(s => s.active === false)
  return props.services
})

const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE_SIZE)))

const pageOffset = computed(() => (page.value - 1) * PAGE_SIZE)

const paged = computed(() => {
  const start = pageOffset.value
  return filtered.value.slice(start, start + PAGE_SIZE)
})

watch(
  () => [props.filter, filtered.value.length] as const,
  () => {
    page.value = 1
  }
)

watch(pageCount, (count) => {
  if (page.value > count) page.value = count
})

const dragFrom = ref<number | null>(null)

function onDragStart(index: number, e: DragEvent) {
  dragFrom.value = index
  e.dataTransfer?.setData('text/plain', String(index))
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

function onDragOver(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
}

function onDrop(toIndex: number, e: DragEvent) {
  e.preventDefault()
  const from = dragFrom.value
  dragFrom.value = null
  if (from == null || from === toIndex) return

  const offset = pageOffset.value
  const fromAbs = offset + from
  const toAbs = offset + toIndex

  const visible = filtered.value
  const fromId = visible[fromAbs]?.id
  const toId = visible[toAbs]?.id
  if (fromId == null || toId == null) return

  const next = [...props.services]
  const fromFull = next.findIndex(s => s.id === fromId)
  const toFull = next.findIndex(s => s.id === toId)
  if (fromFull < 0 || toFull < 0) return

  const [moved] = next.splice(fromFull, 1)
  if (!moved) return
  next.splice(toFull, 0, moved)
  emit('reorder', next.map(s => s.id))
}
</script>

<template>
  <div class="flex flex-col gap-3 min-h-0 h-full overflow-hidden">
    <div class="flex flex-wrap gap-2 shrink-0">
      <button
        v-for="f in filters"
        :key="f.id"
        type="button"
        class="px-3 py-1.5 text-xs font-medium rounded-full border transition-colors"
        :class="filter === f.id
          ? 'border-violet-500 text-highlighted bg-violet-500/10'
          : 'border-default text-muted hover:text-highlighted'"
        @click="emit('update:filter', f.id)"
      >
        {{ f.label }}
      </button>
    </div>

    <div class="flex-1 min-h-0 overflow-hidden">
      <div v-if="!filtered.length" class="py-12 text-center text-sm text-muted">
        Нет услуг в этом фильтре
      </div>

      <div
        v-for="(s, index) in paged"
        :key="s.id"
        draggable="true"
        class="grid grid-cols-[1.5rem_minmax(0,1fr)_auto] sm:grid-cols-[1.5rem_minmax(0,1.5fr)_5.5rem_5.5rem_7rem] gap-2 sm:gap-3 items-center py-3 pr-3 border-b border-default/30 last:border-0 cursor-pointer transition-colors"
        :class="selectedId === s.id
          ? 'bg-black/[0.04] dark:bg-white/[0.06]'
          : 'hover:bg-black/[0.03] dark:hover:bg-white/[0.03]'"
        @click="emit('select', s)"
        @dragstart="onDragStart(index, $event)"
        @dragover="onDragOver"
        @drop="onDrop(index, $event)"
      >
        <span
          class="text-muted cursor-grab active:cursor-grabbing flex items-center justify-center"
          title="Перетащить"
          @click.stop
        >
          <UIcon name="i-lucide-grip-vertical" class="size-4" />
        </span>

        <div class="min-w-0">
          <p class="font-medium text-highlighted truncate">{{ s.name }}</p>
          <p v-if="s.description" class="text-xs text-muted truncate mt-0.5">
            {{ s.description }}
          </p>
        </div>

        <span class="hidden sm:block text-sm text-muted tabular-nums">
          {{ formatDurationMinutes(s.duration) }}
        </span>
        <span class="hidden sm:block text-sm text-highlighted tabular-nums text-right">
          {{ formatMoney(Number(s.price) || 0) }}
        </span>
        <span
          class="text-[11px] font-medium px-2 py-0.5 rounded-full text-center"
          :class="s.active !== false
            ? 'text-emerald-500 bg-emerald-500/10'
            : 'text-muted bg-elevated'"
        >
          {{ s.active !== false ? 'Опубликована' : 'Скрыта' }}
        </span>
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
