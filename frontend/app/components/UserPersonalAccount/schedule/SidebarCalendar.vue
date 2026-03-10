<script setup lang="ts">
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isSameMonth, startOfWeek, endOfWeek, startOfDay } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { Booking } from '~/types'

const props = defineProps<{
  selectedDate?: Date
  bookings?: Booking[]
}>()

const emit = defineEmits<{
  'update:selectedDate': [date: Date]
}>()

const today = new Date()

// Инициализируем currentMonth с selectedDate, если он есть
const currentMonth = ref(props.selectedDate ? new Date(props.selectedDate.getFullYear(), props.selectedDate.getMonth(), 1) : new Date())

const monthStart = computed(() => startOfMonth(currentMonth.value))
const monthEnd = computed(() => endOfMonth(currentMonth.value))
const calendarStart = computed(() => startOfWeek(monthStart.value, { locale: ru }))
const calendarEnd = computed(() => endOfWeek(monthEnd.value, { locale: ru }))

const calendarDays = computed(() => {
  return eachDayOfInterval({ start: calendarStart.value, end: calendarEnd.value })
})

// Синхронизируем currentMonth с selectedDate при изменении
watch(() => props.selectedDate, (newDate) => {
  if (newDate && !isSameMonth(newDate, currentMonth.value)) {
    currentMonth.value = new Date(newDate.getFullYear(), newDate.getMonth(), 1)
  }
}, { immediate: true })

function getBookingsForDate(date: Date): Booking[] {
  if (!props.bookings) return []
  const dateStr = format(date, 'yyyy-MM-dd')
  return props.bookings.filter(b => b.date === dateStr)
}

function hasBookings(date: Date): boolean {
  return getBookingsForDate(date).length > 0
}

function isSelected(date: Date): boolean {
  if (!props.selectedDate) return false
  // Нормализуем обе даты для корректного сравнения
  return isSameDay(startOfDay(date), startOfDay(props.selectedDate))
}

function isToday(date: Date): boolean {
  return isSameDay(date, today)
}

function isCurrentMonth(date: Date): boolean {
  return isSameMonth(date, currentMonth.value)
}

function selectDate(date: Date) {
  // Нормализуем дату - убираем время, оставляем только дату
  const normalizedDate = startOfDay(date)
  // Обновляем текущий месяц, если выбранная дата из другого месяца
  if (!isSameMonth(normalizedDate, currentMonth.value)) {
    currentMonth.value = new Date(normalizedDate.getFullYear(), normalizedDate.getMonth(), 1)
  }
  emit('update:selectedDate', normalizedDate)
}

function previousMonth() {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() - 1, 1)
}

function nextMonth() {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1, 1)
}

function goToToday() {
  const today = new Date()
  currentMonth.value = today
  selectDate(today)
}
</script>

<template>
  <div class="px-4 py-2">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-xs font-semibold">
        {{ format(currentMonth, 'LLLL yyyy', { locale: ru }) }}
      </h3>
      <div class="flex items-center gap-1">
        <UButton
          icon="i-lucide-chevron-left"
          color="neutral"
          variant="ghost"
          size="xs"
          square
          @click="previousMonth"
        />
        <UButton
          icon="i-lucide-chevron-right"
          color="neutral"
          variant="ghost"
          size="xs"
          square
          @click="nextMonth"
        />
      </div>
    </div>

    <div class="grid grid-cols-7 gap-0.5 mb-1">
      <div
        v-for="day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']"
        :key="day"
        class="text-xs text-muted text-center font-medium py-1"
      >
        {{ day }}
      </div>
    </div>

    <div class="grid grid-cols-7 gap-0.5">
      <button
        v-for="day in calendarDays"
        :key="day.getTime()"
        type="button"
        class="aspect-square text-xs rounded-md transition-colors flex items-center justify-center cursor-pointer select-none"
        :class="[
          isCurrentMonth(day) ? 'text-highlighted' : 'text-dimmed',
          isSelected(day) ? 'bg-gray-900 text-white font-semibold dark:bg-white dark:text-gray-900' : 'hover:bg-elevated',
          isToday(day) && !isSelected(day) ? 'ring-2 ring-gray-900/50 dark:ring-white/50' : ''
        ]"
        @click="selectDate(day)"
      >
        {{ format(day, 'd') }}
      </button>
    </div>

    <UButton
      color="neutral"
      variant="ghost"
      size="xs"
      block
      class="mt-2"
      @click="goToToday"
    >
      Сегодня
    </UButton>
  </div>
</template>

