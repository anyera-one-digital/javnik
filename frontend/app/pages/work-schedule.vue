<script setup lang="ts">
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, startOfDay, getDay, addMonths, subMonths } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { WorkSchedule, WorkBreak } from '~/types'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const toast = useToast()
const { getAuthHeaders, refreshAccessToken } = useAuth()

// Состояние календаря
const currentMonth = ref(new Date())
const selectedDates = ref<Date[]>([])
const schedules = ref<Map<string, WorkSchedule>>(new Map())

// Состояние панели настроек
const scheduleType = ref<'workday' | 'nonworkday' | 'sickleave' | 'vacation'>('workday')
const startTime = ref('10:00')
const endTime = ref('22:00')
const breaks = ref<WorkBreak[]>([])

// Вычисляемые свойства
const monthStart = computed(() => startOfMonth(currentMonth.value))
const monthEnd = computed(() => endOfMonth(currentMonth.value))

// Показываем только дни текущего месяца
const calendarDays = computed(() => {
  return eachDayOfInterval({ start: monthStart.value, end: monthEnd.value })
})

const daysToChange = computed(() => selectedDates.value.length)

// Функции календаря
function previousMonth() {
  currentMonth.value = subMonths(currentMonth.value, 1)
}

function nextMonth() {
  currentMonth.value = addMonths(currentMonth.value, 1)
}

function goToToday() {
  currentMonth.value = new Date()
  selectedDates.value = []
}

function toggleDate(date: Date) {
  const dateStr = format(date, 'yyyy-MM-dd')
  const index = selectedDates.value.findIndex(d => isSameDay(d, date))
  
  if (index >= 0) {
    selectedDates.value.splice(index, 1)
  } else {
    selectedDates.value.push(startOfDay(date))
  }
}

function isSelected(date: Date): boolean {
  return selectedDates.value.some(d => isSameDay(d, date))
}

function isToday(date: Date): boolean {
  return isSameDay(date, new Date())
}

function isCurrentMonth(date: Date): boolean {
  // Всегда true, так как теперь показываем только дни текущего месяца
  return true
}

function getScheduleForDate(date: Date): WorkSchedule | undefined {
  const dateStr = format(date, 'yyyy-MM-dd')
  return schedules.value.get(dateStr)
}

function isWeekend(date: Date): boolean {
  const day = getDay(date)
  return day === 0 || day === 6
}

function getDayAbbreviation(date: Date): string {
  const dayNames = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
  return dayNames[getDay(date)]
}

function formatTime(time: string | undefined): string {
  if (!time) return ''
  // Убираем секунды, если они есть (формат HH:MM:SS -> HH:MM)
  return time.split(':').slice(0, 2).join(':')
}

// Функции панели настроек
function addBreak() {
  breaks.value.push({ startTime: '12:00', endTime: '13:00' })
}

function removeBreak(index: number) {
  breaks.value.splice(index, 1)
}

function loadScheduleForDate(date: Date) {
  const schedule = getScheduleForDate(date)
  if (schedule) {
    scheduleType.value = schedule.type
    startTime.value = schedule.startTime || '10:00'
    endTime.value = schedule.endTime || '22:00'
    // Преобразуем breaks из формата API в формат компонента
    breaks.value = (schedule.breaks || []).map((b: any) => ({
      startTime: typeof b.startTime === 'string' ? b.startTime : b.start_time || '12:00',
      endTime: typeof b.endTime === 'string' ? b.endTime : b.end_time || '13:00'
    }))
  } else {
    // Значения по умолчанию
    scheduleType.value = 'workday'
    startTime.value = '10:00'
    endTime.value = '22:00'
    breaks.value = []
  }
}

async function loadSchedules() {
  if (!process.client) return
  
  try {
    let headers = getAuthHeaders()
    
    if (!headers.Authorization) {
      console.warn('Work Schedule: No auth token, trying to refresh...')
      const refreshed = await refreshAccessToken()
      if (refreshed) {
        headers = getAuthHeaders()
      } else {
        console.error('Work Schedule: No auth token available, skipping schedules load')
        return
      }
    }
    
    // Загружаем график для текущего месяца
    const startDate = format(monthStart.value, 'yyyy-MM-dd')
    const endDate = format(monthEnd.value, 'yyyy-MM-dd')

    const response = await $fetch<WorkSchedule[]>('/api/schedule/', {
      headers,
      query: {
        start_date: startDate,
        end_date: endDate
      }
    })
    
    // Преобразуем массив в Map для быстрого доступа
    const schedulesMap = new Map<string, WorkSchedule>()
    response.forEach(schedule => {
      schedulesMap.set(schedule.date, schedule)
    })
    schedules.value = schedulesMap
  } catch (error: any) {
    console.error('Error loading schedules:', error)
    if (error.statusCode === 401 || error.status === 401) {
      // Пытаемся обновить токен и повторить запрос
      const refreshed = await refreshAccessToken()
      if (refreshed) {
        // Повторяем запрос после обновления токена
        try {
          const headers = getAuthHeaders()
          const startDate = format(monthStart.value, 'yyyy-MM-dd')
          const endDate = format(monthEnd.value, 'yyyy-MM-dd')
          const response = await $fetch<WorkSchedule[]>('/api/schedule/', {
            headers,
            query: {
              start_date: startDate,
              end_date: endDate
            }
          })
          const schedulesMap = new Map<string, WorkSchedule>()
          response.forEach(schedule => {
            schedulesMap.set(schedule.date, schedule)
          })
          schedules.value = schedulesMap
          return
        } catch (retryError) {
          console.error('Error loading schedules after token refresh:', retryError)
        }
      }
    }
    if (error.statusCode !== 401 && error.status !== 401) {
      toast.add({
        title: 'Ошибка',
        description: 'Не удалось загрузить график работы',
        color: 'error'
      })
    }
  }
}

function cancelChanges() {
  selectedDates.value = []
  scheduleType.value = 'workday'
  startTime.value = '10:00'
  endTime.value = '22:00'
  breaks.value = []
}

async function saveSchedule() {
  if (selectedDates.value.length === 0) {
    toast.add({
      title: 'Ошибка',
      description: 'Выберите хотя бы один день',
      color: 'error'
    })
    return
  }

  if (scheduleType.value === 'workday' && (!startTime.value || !endTime.value)) {
    toast.add({
      title: 'Ошибка',
      description: 'Укажите рабочее время',
      color: 'error'
    })
    return
  }

  if (!process.client) return

  try {
    let headers = getAuthHeaders()
    
    if (!headers.Authorization) {
      console.warn('Work Schedule: No auth token, trying to refresh...')
      const refreshed = await refreshAccessToken()
      if (refreshed) {
        headers = getAuthHeaders()
      } else {
        toast.add({
          title: 'Ошибка',
          description: 'Не удалось авторизоваться. Пожалуйста, войдите снова.',
          color: 'error'
        })
        return
      }
    }

    // Подготавливаем данные для сохранения
    const schedulesToSave = selectedDates.value.map(date => {
      const dateStr = format(date, 'yyyy-MM-dd')
      const scheduleData: any = {
        date: dateStr,
        type: scheduleType.value
      }
      
      if (scheduleType.value === 'workday') {
        scheduleData.startTime = startTime.value
        scheduleData.endTime = endTime.value
        if (breaks.value.length > 0) {
          scheduleData.breaks = breaks.value.map(b => ({
            startTime: b.startTime,
            endTime: b.endTime
          }))
        }
      }
      
      return scheduleData
    })

    // Сохраняем график для каждого выбранного дня
    const savedSchedules: WorkSchedule[] = []
    const errors: string[] = []
    
    for (const scheduleData of schedulesToSave) {
      const dateStr = scheduleData.date
      
      try {
        // Проверяем, существует ли уже график для этой даты
        const existingSchedule = schedules.value.get(dateStr)
        
        if (existingSchedule && existingSchedule.id) {
          // Обновляем существующий график
          const updated = await $fetch<WorkSchedule>(`/api/schedule/${existingSchedule.id}/`, {
            method: 'PUT',
            headers,
            body: scheduleData
          })
          schedules.value.set(dateStr, updated)
          savedSchedules.push(updated)
        } else {
          // Создаем новый график
          console.log('Creating schedule for', dateStr)
          console.log('Schedule data:', JSON.stringify(scheduleData, null, 2))
          try {
            const created = await $fetch<WorkSchedule>('/api/schedule/', {
              method: 'POST',
              headers,
              body: scheduleData
            })
            console.log('Created schedule:', created)
            schedules.value.set(dateStr, created)
            savedSchedules.push(created)
          } catch (fetchError: any) {
            // Если получили 401, пытаемся обновить токен и повторить
            if (fetchError.statusCode === 401 || fetchError.status === 401) {
              const refreshed = await refreshAccessToken()
              if (refreshed) {
                headers = getAuthHeaders()
                // Повторяем запрос
                const created = await $fetch<WorkSchedule>('/api/schedule/', {
                  method: 'POST',
                  headers,
                  body: scheduleData
                })
                schedules.value.set(dateStr, created)
                savedSchedules.push(created)
                continue
              }
            }
            console.error('Full error object:', fetchError)
            console.error('Error response:', fetchError.response)
            console.error('Error data:', fetchError.data)
            throw fetchError
          }
        }
      } catch (error: any) {
        console.error(`Error saving schedule for ${dateStr}:`, error)
        const errorMsg = error.data?.message || error.data?.detail || error.message || 'Неизвестная ошибка'
        errors.push(`${dateStr}: ${errorMsg}`)
      }
    }
    
    // Если были ошибки, показываем их
    if (errors.length > 0) {
      toast.add({
        title: 'Частичная ошибка',
        description: `Не удалось сохранить ${errors.length} из ${schedulesToSave.length} дней. Ошибки: ${errors.join('; ')}`,
        color: 'error',
        timeout: 10000
      })
      return
    }

    // Обновляем локальное состояние с сохраненными графиками
    savedSchedules.forEach(schedule => {
      schedules.value.set(schedule.date, schedule)
    })
    
    // Перезагружаем графики для обновления данных
    await loadSchedules()

    toast.add({
      title: 'Успешно',
      description: `График сохранен для ${savedSchedules.length} ${savedSchedules.length === 1 ? 'дня' : 'дней'}`,
      color: 'success'
    })

    selectedDates.value = []
    scheduleType.value = 'workday'
    startTime.value = '10:00'
    endTime.value = '22:00'
    breaks.value = []
  } catch (error: any) {
    console.error('Error saving schedule:', error)
    console.error('Error data:', error.data)
    console.error('Error response:', error.response)
    
    let errorMessage = 'Не удалось сохранить график'
    
    if (error.data) {
      if (typeof error.data === 'string') {
        errorMessage = error.data
      } else if (error.data.detail) {
        errorMessage = error.data.detail
      } else if (error.data.message) {
        errorMessage = error.data.message
      } else if (typeof error.data === 'object') {
        // Пытаемся извлечь детали ошибки валидации
        const validationErrors = Object.entries(error.data)
          .map(([field, errors]: [string, any]) => {
            const fieldName = field === 'date' ? 'Дата' : 
                             field === 'type' ? 'Тип' : 
                             field === 'start_time' || field === 'startTime' ? 'Время начала' :
                             field === 'end_time' || field === 'endTime' ? 'Время окончания' :
                             field === 'breaks' ? 'Перерывы' : field
            const errorList = Array.isArray(errors) ? errors.join(', ') : String(errors)
            return `${fieldName}: ${errorList}`
          })
        if (validationErrors.length > 0) {
          errorMessage = validationErrors.join('\n')
        }
      }
    }
    
    toast.add({
      title: 'Ошибка',
      description: errorMessage,
      color: 'error',
      timeout: 10000
    })
  }
}

// Загружаем график при выборе даты
watch(selectedDates, (dates) => {
  if (dates.length === 1) {
    loadScheduleForDate(dates[0])
  } else if (dates.length > 1) {
    // Если выбрано несколько дней, используем значения по умолчанию
    scheduleType.value = 'workday'
    startTime.value = '10:00'
    endTime.value = '22:00'
    breaks.value = []
  }
}, { deep: true })

// Загружаем график при изменении месяца
watch(currentMonth, () => {
  if (process.client) {
    loadSchedules()
  }
}, { immediate: false })

// Загружаем данные при монтировании
onMounted(async () => {
  if (process.client) {
    await nextTick()
    // Небольшая задержка для загрузки токена
    setTimeout(async () => {
      await loadSchedules()
    }, 300)
  }
})
</script>

<template>
  <UDashboardPanel id="work-schedule" :ui="{ body: 'lg:py-12' }">
    <template #header>
      <UDashboardNavbar title="График работы">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="flex flex-col gap-6">
        <!-- Заголовок с навигацией -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <UButton
              icon="i-lucide-chevron-left"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              @click="previousMonth"
            />
            <h2 class="text-lg font-semibold">
              {{ format(currentMonth, 'LLLL yyyy', { locale: ru }) }}
            </h2>
            <UButton
              icon="i-lucide-chevron-right"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              @click="nextMonth"
            />
          </div>
          <UButton
            label="Сегодня"
            color="neutral"
            variant="ghost"
            size="sm"
            @click="goToToday"
          />
        </div>

        <!-- Полоска дней месяца -->
        <div class="border border-default rounded-lg bg-elevated/50 overflow-x-auto">
          <div class="flex min-w-max">
            <div
              v-for="day in calendarDays"
              :key="day.getTime()"
              class="flex flex-col w-16 min-w-[64px] border-r border-default last:border-r-0 p-1"
            >
                <!-- Заголовок дня недели -->
                <div class="text-xs text-muted text-center font-medium py-2 px-1 border-b border-default">
                  {{ getDayAbbreviation(day) }}
                </div>
                <!-- Вся область дня (кликабельная) -->
                <button
                  type="button"
                  class="relative transition-colors flex flex-col flex-1 cursor-pointer min-h-[60px]"
                  @click="toggleDate(day)"
                >
                  <!-- Номер дня -->
                  <div 
                    class="flex items-center justify-center p-2 transition-colors rounded"
                    :class="[
                      isSelected(day) ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900' : 'hover:bg-elevated',
                      isToday(day) && !isSelected(day) ? 'border-2 border-gray-900 dark:border-white' : '',
                      isWeekend(day) && !isSelected(day) ? 'text-error' : ''
                    ]"
                  >
                    <span class="text-sm font-medium">{{ format(day, 'd') }}</span>
                  </div>
                
                  <!-- Индикатор графика -->
                  <div class="flex-1 p-1 flex items-center justify-center" :class="isSelected(day) ? '' : ''">
                    <div
                      v-if="getScheduleForDate(day)"
                      class="w-full rounded border border-gray-900 dark:border-white p-1 flex flex-col items-center justify-center gap-0.5 min-h-[32px]"
                    >
                      <template v-if="getScheduleForDate(day)?.type === 'workday'">
<div class="text-xs text-gray-900 dark:text-white font-medium leading-tight">
                        {{ formatTime(getScheduleForDate(day)?.startTime) }}
                        </div>
                        <div class="text-xs text-gray-900 dark:text-white font-medium leading-tight">
                          {{ formatTime(getScheduleForDate(day)?.endTime) }}
                        </div>
                      </template>
                      <div v-else class="w-1 h-1 rounded-full bg-gray-900/50 dark:bg-white/50"></div>
                    </div>
                  </div>
                </button>
            </div>
          </div>
        </div>

        <!-- Панель настроек под полоской дней -->
        <UPageCard variant="subtle">
          <template #header>
            <h3 class="text-lg font-semibold">Настройка графика</h3>
          </template>

          <div class="space-y-6">
            <!-- Тип и рабочее время в одной строке -->
            <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-end">
              <!-- Тип -->
              <div class="flex-1 min-w-0">
                <label class="text-sm font-medium mb-2 block">Тип</label>
                <USelect
                  v-model="scheduleType"
                  :items="[
                    { label: 'Рабочий день', value: 'workday', icon: 'i-lucide-briefcase' },
                    { label: 'Нерабочий день', value: 'nonworkday', icon: 'i-lucide-trash-2' },
                    { label: 'Больничный', value: 'sickleave', icon: 'i-lucide-stethoscope' },
                    { label: 'Отпуск', value: 'vacation', icon: 'i-lucide-umbrella' }
                  ]"
                />
              </div>

              <!-- Рабочее время (только для рабочего дня) -->
              <div v-if="scheduleType === 'workday'" class="flex-1 min-w-0">
                <label class="text-sm font-medium mb-2 block">Рабочее время</label>
                <div class="flex items-center gap-2">
                  <UInput
                    v-model="startTime"
                    type="time"
                    class="flex-1"
                  />
                  <span class="text-muted">—</span>
                  <UInput
                    v-model="endTime"
                    type="time"
                    class="flex-1"
                  />
                </div>
              </div>
            </div>

            <!-- Перерывы (только для рабочего дня) -->
            <div v-if="scheduleType === 'workday'">
              <label class="text-sm font-medium mb-2 block">Перерывы</label>
              <div class="space-y-2">
                <div
                  v-for="(breakItem, index) in breaks"
                  :key="index"
                  class="flex items-center gap-2"
                >
                  <UInput
                    v-model="breakItem.startTime"
                    type="time"
                    class="flex-1"
                  />
                  <span class="text-muted">—</span>
                  <UInput
                    v-model="breakItem.endTime"
                    type="time"
                    class="flex-1"
                  />
                  <UButton
                    icon="i-lucide-trash"
                    color="error"
                    variant="ghost"
                    size="sm"
                    square
                    @click="removeBreak(index)"
                  />
                </div>
                <UButton
                  v-if="scheduleType === 'workday'"
                  label="+ Добавить перерыв"
                  color="neutral"
                  variant="ghost"
                  size="sm"
                  icon="i-lucide-plus"
                  @click="addBreak"
                />
              </div>
            </div>

            <!-- Информация о количестве дней -->
            <div v-if="daysToChange > 0" class="text-sm text-muted">
              Изменится дней: {{ daysToChange }}
            </div>

            <!-- Кнопки действий -->
            <div class="flex justify-end gap-2 pt-4 border-t border-default">
              <UButton
                label="Отменить"
                color="neutral"
                variant="outline"
                @click="cancelChanges"
              />
              <UButton
                label="Сохранить"
                color="neutral"
                variant="solid"
                class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
                @click="saveSchedule"
              />
            </div>
          </div>
        </UPageCard>
      </div>
    </template>
  </UDashboardPanel>
</template>
