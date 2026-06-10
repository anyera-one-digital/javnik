<script setup lang="ts">
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isBefore, isSameDay, isSameMonth, startOfDay, getDay, addMonths, subMonths, addDays, parse, differenceInCalendarDays } from 'date-fns'
import { ru } from 'date-fns/locale'
import type { WorkSchedule, WorkBreak } from '~/types'
import {
  workScheduleTemplateList,
  resolveDayScheduleFromTemplate,
  type WorkScheduleTemplateId,
  type ShiftCycleId,
  type DayScheduleConfig
} from '~/utils/workScheduleTemplates'
import { validateWorkBreaksNoOverlap } from '~/utils/validateWorkBreaks'

const emit = defineEmits<{ saved: [] }>()

const toast = useToast()
const { getAuthHeaders, refreshAccessToken, fetchProfile, patchProfile, user: authUser } = useAuth()

// Состояние календаря
const currentMonth = ref(new Date())
const selectedDates = ref<Date[]>([])
const schedules = ref<Map<string, WorkSchedule>>(new Map())

// Состояние панели настроек
const scheduleType = ref<'workday' | 'nonworkday' | 'sickleave' | 'vacation'>('workday')
const startTime = ref('10:00')
const endTime = ref('22:00')
const breaks = ref<WorkBreak[]>([])

const selectedWorkTemplate = ref<WorkScheduleTemplateId>('standard-5')
const shiftCycle = ref<ShiftCycleId>('2-2')
const shiftAnchorInput = ref(format(new Date(), 'yyyy-MM-dd'))
const templateInitialized = ref(false)
const isSavingTemplate = ref(false)
const isSyncingTemplate = ref(false)

const templateSelectItems = workScheduleTemplateList.map(t => ({
  label: t.shortLabel,
  value: t.id
}))

const templateBlockHelp
  = 'Задаёт сегодняшний день и все будущие дни, пока для даты нет отдельной настройки ниже. Чтобы задать исключения, выберите дни в календаре и отредактируйте в форме настройки выбранных дней. Ручные настройки дня имеют приоритет над шаблоном.'

function templateResolveOptions() {
  return {
    shift: shiftCycle.value,
    anchor: selectedWorkTemplate.value === 'shift-cycle' ? getShiftAnchorDate() : undefined
  }
}

function findSampleWorkdayForTemplate(): Date {
  const from = startOfDay(new Date())
  for (let i = 0; i < 21; i++) {
    const day = addDays(from, i)
    const cfg = resolveDayScheduleFromTemplate(selectedWorkTemplate.value, day, templateResolveOptions())
    if (cfg.type === 'workday' && cfg.startTime && cfg.endTime) {
      return day
    }
  }
  return from
}

const templateWorkdayHoursLabel = computed(() => {
  const cfg = resolveDayScheduleFromTemplate(
    selectedWorkTemplate.value,
    findSampleWorkdayForTemplate(),
    templateResolveOptions()
  )
  if (cfg.type === 'workday' && cfg.startTime && cfg.endTime) {
    return `Рабочий день по шаблону: ${formatTime(cfg.startTime)}–${formatTime(cfg.endTime)}`
  }
  return 'По шаблону в выбранные дни — выходной (сменный график).'
})

function applyFormDefaultsFromTemplate() {
  const cfg = resolveDayScheduleFromTemplate(
    selectedWorkTemplate.value,
    findSampleWorkdayForTemplate(),
    templateResolveOptions()
  )
  if (cfg.type === 'workday' && cfg.startTime && cfg.endTime) {
    startTime.value = cfg.startTime
    endTime.value = cfg.endTime
  }
}

const detailBlockHelp
  = 'Помимо базового шаблона, вы можете выбрать любой день и настроить его время вручную, добавить нужное количество перерывов, чтобы показать клиентам действительно актуальные свободные окна во времени.'

// Подсказка через UPopover (mode click) — открытие по тапу/клику, не по ховеру
const scheduleHelpPopoverUi = {
  content: 'z-[300] w-[min(20rem,calc(100vw-2rem))] max-w-[min(20rem,calc(100vw-2rem))] p-3 text-left text-balance'
}

const compactSelectUi = {
  base: 'w-full min-w-0 max-w-full flex',
  value: 'min-w-0 flex-1 basis-0 shrink truncate text-start',
  itemLabel: 'whitespace-normal break-words',
  itemWrapper: 'min-w-0'
}

// Вычисляемые свойства
const monthStart = computed(() => startOfMonth(currentMonth.value))
const monthEnd = computed(() => endOfMonth(currentMonth.value))

// Сетка месяца: полные недели (пн–вс), с «хвостами» соседних месяцев
const monthGridStart = computed(() => startOfWeek(monthStart.value, { locale: ru, weekStartsOn: 1 }))
const monthGridEnd = computed(() => endOfWeek(monthEnd.value, { locale: ru, weekStartsOn: 1 }))
const calendarGridDays = computed(() =>
  eachDayOfInterval({ start: monthGridStart.value, end: monthGridEnd.value })
)

const daysToChange = computed(() => selectedDates.value.length)

function sortSelectedDays(dates: Date[]): Date[] {
  return dates.map(d => startOfDay(d)).sort((a, b) => a.getTime() - b.getTime())
}

function areSelectedDatesConsecutive(dates: Date[]): boolean {
  if (dates.length <= 1) return true
  const s = sortSelectedDays(dates)
  for (let i = 1; i < s.length; i++) {
    if (differenceInCalendarDays(s[i]!, s[i - 1]!) !== 1) {
      return false
    }
  }
  return true
}

/** Сокращённые даты под заголовком: 25.04.26; диапазон подряд; иначе список */
function formatSelectedDatesShortLine(dates: Date[]): string {
  if (dates.length === 0) return ''
  const shortFmt = 'dd.MM.yy'
  const sorted = sortSelectedDays(dates)
  if (sorted.length === 1) {
    return format(sorted[0]!, shortFmt)
  }
  if (areSelectedDatesConsecutive(dates)) {
    const a = sorted[0]!
    const b = sorted[sorted.length - 1]!
    return `${format(a, shortFmt)} – ${format(b, shortFmt)}`
  }
  return sorted.map(d => format(d, shortFmt)).join(', ')
}

const daySettingsHeading = computed(() => {
  const n = selectedDates.value.length
  if (n <= 1) {
    return 'Настройка дня'
  }
  return 'Настройка дней'
})

const daySettingsDatesLine = computed(() => {
  if (selectedDates.value.length === 0) {
    return ''
  }
  return formatSelectedDatesShortLine(selectedDates.value)
})

/** Подпись с корректным склонением: «Изменится 1 день» / «Изменятся N дня/дней» */
const changeApplyDaysLabel = computed(() => {
  const n = daysToChange.value
  if (n <= 0) return ''
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 14) {
    return `Изменятся ${n} дней`
  }
  if (mod10 === 1) {
    return `Изменится ${n} день`
  }
  if (mod10 >= 2 && mod10 <= 4) {
    return `Изменятся ${n} дня`
  }
  return `Изменятся ${n} дней`
})

/** Смена выбранных дат в календаре, без срабатывания при правке перерывов */
const selectedDateKeys = computed(() =>
  sortSelectedDays(selectedDates.value)
    .map(d => format(d, 'yyyy-MM-dd'))
    .join('|')
)

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
  if (!isScheduleDateEditable(date)) {
    return
  }
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

/** Сегодня и будущие — можно менять; вчера и раньше — нет */
function isScheduleDateEditable(date: Date): boolean {
  return !isBefore(startOfDay(date), startOfDay(new Date()))
}

/** Только явно сохранённые в API дни (переопределяют шаблон). */
function getStoredScheduleForDate(date: Date): WorkSchedule | undefined {
  const dateStr = format(date, 'yyyy-MM-dd')
  return schedules.value.get(dateStr)
}

function configToWorkSchedule(dateStr: string, cfg: DayScheduleConfig): WorkSchedule {
  return {
    date: dateStr,
    type: cfg.type,
    startTime: cfg.startTime,
    endTime: cfg.endTime,
    breaks: cfg.breaks || []
  }
}

/**
 * День в календаре: сначала запись из API, иначе для сегодня и будущего — расчёт по шаблону профиля.
 * Прошлые даты без явной записи — пусто (—).
 */
function getEffectiveScheduleForDate(date: Date): WorkSchedule | undefined {
  const stored = getStoredScheduleForDate(date)
  if (stored) {
    return stored
  }
  if (isBefore(startOfDay(date), startOfDay(new Date()))) {
    return undefined
  }
  const dateStr = format(date, 'yyyy-MM-dd')
  const cfg = resolveDayScheduleFromTemplate(selectedWorkTemplate.value, date, {
    shift: shiftCycle.value,
    anchor: selectedWorkTemplate.value === 'shift-cycle' ? getShiftAnchorDate() : undefined
  })
  return configToWorkSchedule(dateStr, cfg)
}

function isWeekend(date: Date): boolean {
  const day = getDay(date)
  return day === 0 || day === 6
}

function getDayAbbreviation(date: Date): string {
  const dayNames = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'] as const
  return dayNames[getDay(date)] ?? '—'
}

function formatTime(time: string | undefined): string {
  if (!time) return ''
  // Убираем секунды, если они есть (формат HH:MM:SS -> HH:MM)
  return time.split(':').slice(0, 2).join(':')
}

/** Короткая подпись для ячейки календаря */
function getScheduleTimeLabel(date: Date): string {
  const schedule = getEffectiveScheduleForDate(date)
  if (!schedule) return '—'
  if (schedule.type === 'workday' && schedule.startTime && schedule.endTime) {
    return `${formatTime(schedule.startTime)}–${formatTime(schedule.endTime)}`
  }
  if (schedule.type === 'nonworkday') return 'Вых.'
  if (schedule.type === 'sickleave') return 'Бол.'
  if (schedule.type === 'vacation') return 'Отп.'
  return '—'
}

function cellClasses(day: Date): string {
  if (!isScheduleDateEditable(day)) {
    return 'border border-default/40 bg-elevated/20 opacity-55'
  }
  if (isSelected(day)) {
    return 'border border-gray-900 dark:border-white !bg-gray-900 !text-white dark:!bg-white dark:!text-gray-900 shadow-sm'
  }
  const extra: string[] = []
  if (!isSameMonth(day, currentMonth.value)) {
    extra.push('opacity-45')
  }
  if (isToday(day)) {
    extra.push('ring-2 ring-inset ring-gray-900/70 dark:ring-white/70')
  }
  const schedule = getEffectiveScheduleForDate(day)
  if (schedule?.type === 'workday') {
    return [
      'border border-emerald-600/30 bg-emerald-500/[0.12] dark:bg-emerald-500/18 hover:bg-emerald-500/20',
      ...extra
    ].join(' ')
  }
  if (schedule) {
    return [
      'border border-amber-500/25 bg-amber-500/10 dark:bg-amber-500/15 hover:bg-amber-500/15',
      ...extra
    ].join(' ')
  }
  return [
    'border border-default bg-background/80 hover:bg-elevated/90 dark:bg-elevated/25',
    ...extra
  ].join(' ')
}

function weekendLabelClass(day: Date): string {
  if (!isScheduleDateEditable(day)) {
    return 'text-dimmed'
  }
  if (isSelected(day)) {
    return 'text-inherit opacity-90'
  }
  return isWeekend(day) ? 'text-error' : 'text-muted'
}

function timeLabelClass(day: Date): string {
  if (!isScheduleDateEditable(day)) {
    return 'text-dimmed'
  }
  if (isSelected(day)) {
    return 'text-inherit/95'
  }
  const schedule = getEffectiveScheduleForDate(day)
  if (schedule?.type === 'workday') {
    return 'text-emerald-900/90 dark:text-emerald-100/95'
  }
  if (schedule) {
    return 'text-amber-900/85 dark:text-amber-100/90'
  }
  return 'text-muted'
}

function dateNumberClass(day: Date): string {
  if (!isScheduleDateEditable(day)) {
    return 'text-dimmed'
  }
  if (isSelected(day)) {
    return 'text-white dark:text-gray-900'
  }
  return isSameMonth(day, currentMonth.value) ? 'text-highlighted' : 'text-dimmed'
}

// Функции панели настроек
function addBreak() {
  breaks.value.push({ startTime: '12:00', endTime: '13:00' })
}

function removeBreak(index: number) {
  breaks.value = breaks.value.filter((_, i) => i !== index)
}

function loadScheduleForDate(date: Date) {
  const schedule = getEffectiveScheduleForDate(date)
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

function syncFormFromSchedulesIfSingleSelection() {
  const dates = sortSelectedDays(selectedDates.value)
  if (dates.length === 1 && dates[0]) {
    loadScheduleForDate(dates[0])
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
    
    const response = await $fetch<WorkSchedule[]>('/api/schedule', {
      headers,
      query: {
        start_date: startDate,
        end_date: endDate,
        explicit_only: '1'
      }
    })

    // Только явные переопределения в БД; дни без записи — из шаблона профиля
    const schedulesMap = new Map<string, WorkSchedule>()
    response.forEach((schedule) => {
      if (schedule?.id != null) {
        schedulesMap.set(schedule.date, schedule)
      }
    })
    schedules.value = schedulesMap
    syncFormFromSchedulesIfSingleSelection()
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
          const response = await $fetch<WorkSchedule[]>('/api/schedule', {
            headers,
            query: {
              start_date: startDate,
              end_date: endDate,
              explicit_only: '1'
            }
          })
          const schedulesMap = new Map<string, WorkSchedule>()
          response.forEach((schedule) => {
            if (schedule?.id != null) {
              schedulesMap.set(schedule.date, schedule)
            }
          })
          schedules.value = schedulesMap
          syncFormFromSchedulesIfSingleSelection()
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

function getShiftAnchorDate(): Date {
  try {
    return startOfDay(parse(shiftAnchorInput.value, 'yyyy-MM-dd', new Date()))
  } catch {
    return startOfDay(new Date())
  }
}

/**
 * Сохранение набора дней (ручные правки — перекрывают шаблон для выбранных дат).
 */
async function persistSchedulesData(schedulesToSave: Record<string, any>[]) {
  const savedSchedules: WorkSchedule[] = []
  const errors: string[] = []

  let headers = getAuthHeaders()
  if (!headers.Authorization) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      headers = getAuthHeaders()
    } else {
      return { ok: false as const, authFailed: true, saved: savedSchedules, errors }
    }
  }

  for (const scheduleData of schedulesToSave) {
    const dateStr = scheduleData.date

    try {
      const existingSchedule = schedules.value.get(dateStr as string)

      if (existingSchedule && existingSchedule.id) {
        const updated = await $fetch<WorkSchedule>(`/api/schedule/${existingSchedule.id}`, {
          method: 'PUT',
          headers,
          body: scheduleData
        })
        schedules.value.set(dateStr as string, updated)
        savedSchedules.push(updated)
      } else {
        try {
          const created = await $fetch<WorkSchedule>('/api/schedule', {
            method: 'POST',
            headers,
            body: scheduleData
          })
          schedules.value.set(dateStr as string, created)
          savedSchedules.push(created)
        } catch (fetchError: any) {
          if (fetchError.statusCode === 401 || fetchError.status === 401) {
            const refreshed = await refreshAccessToken()
            if (refreshed) {
              headers = getAuthHeaders()
              const created = await $fetch<WorkSchedule>('/api/schedule', {
                method: 'POST',
                headers,
                body: scheduleData
              })
              schedules.value.set(dateStr as string, created)
              savedSchedules.push(created)
              continue
            }
          }
          throw fetchError
        }
      }
    } catch (error: any) {
      const errorMsg = error.data?.message || error.data?.detail || error.message || 'Неизвестная ошибка'
      errors.push(`${dateStr}: ${errorMsg}`)
    }
  }

  return { ok: true as const, authFailed: false, saved: savedSchedules, errors }
}

function syncTemplateFieldsFromUser() {
  const u = authUser.value
  if (!u) return
  if (u.work_schedule_template) {
    selectedWorkTemplate.value = u.work_schedule_template as WorkScheduleTemplateId
  }
  if (u.shift_cycle) {
    shiftCycle.value = u.shift_cycle as ShiftCycleId
  }
  if (u.shift_anchor_date) {
    shiftAnchorInput.value = u.shift_anchor_date.slice(0, 10)
  }
}

let templateSaveTimer: ReturnType<typeof setTimeout> | null = null
async function onUserChangedWorkTemplate() {
  if (isSyncingTemplate.value || !templateInitialized.value || !import.meta.client) {
    return
  }
  if (templateSaveTimer) {
    clearTimeout(templateSaveTimer)
  }
  templateSaveTimer = setTimeout(async () => {
    isSavingTemplate.value = true
    try {
      const r = await patchProfile({
        work_schedule_template: selectedWorkTemplate.value,
        shift_cycle: shiftCycle.value,
        shift_anchor_date: selectedWorkTemplate.value === 'shift-cycle' ? shiftAnchorInput.value : null
      })
      if (r.success) {
        applyFormDefaultsFromTemplate()
        emit('saved')
        toast.add({
          title: 'Шаблон сохранён',
          description: 'Для дней без отдельных настроек используется выбранный шаблон. Ранее сохранённые вручную дни не меняются.',
          color: 'success'
        })
      }
    } finally {
      isSavingTemplate.value = false
    }
  }, 400)
}

function cancelChanges() {
  selectedDates.value = []
  scheduleType.value = 'workday'
  startTime.value = '10:00'
  endTime.value = '22:00'
  breaks.value = []
}

async function saveSchedule() {
  const editableOnly = selectedDates.value.filter(d => isScheduleDateEditable(d))
  if (editableOnly.length === 0) {
    toast.add({
      title: 'Ошибка',
      description: selectedDates.value.length > 0
        ? 'Нельзя сохранить график для прошедших дней. Выберите сегодняшний день или даты в будущем.'
        : 'Выберите хотя бы один день',
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

  if (scheduleType.value === 'workday' && breaks.value.length > 0) {
    const breakErr = validateWorkBreaksNoOverlap(breaks.value)
    if (breakErr) {
      toast.add({
        title: 'Перерывы',
        description: breakErr,
        color: 'error',
        timeout: 8000
      })
      return
    }
  }

  if (!import.meta.client) {
    return
  }

  try {
    // Подготавливаем данные для сохранения (только сегодня и будущие)
    const schedulesToSave = editableOnly.map((date) => {
      const dateStr = format(date, 'yyyy-MM-dd')
      const scheduleData: Record<string, any> = {
        date: dateStr,
        type: scheduleType.value
      }

      if (scheduleType.value === 'workday') {
        scheduleData.startTime = startTime.value
        scheduleData.endTime = endTime.value
        // Пустой массив — чтобы бэкенд удалил старые перерывы (иначе поле не шлётся)
        scheduleData.breaks = breaks.value.map(b => ({
          startTime: b.startTime,
          endTime: b.endTime
        }))
      }

      return scheduleData
    })

    const result = await persistSchedulesData(schedulesToSave)

    if (result.authFailed) {
      toast.add({
        title: 'Ошибка',
        description: 'Не удалось авторизоваться. Пожалуйста, войдите снова.',
        color: 'error'
      })
      return
    }

    if (result.errors.length > 0) {
      toast.add({
        title: 'Частичная ошибка',
        description: `Не удалось сохранить ${result.errors.length} из ${schedulesToSave.length} дней. Ошибки: ${result.errors.join('; ')}`,
        color: 'error',
        timeout: 10000
      })
      return
    }

    await loadSchedules()

    toast.add({
      title: 'Успешно',
      description: `График сохранен для ${result.saved.length} ${result.saved.length === 1 ? 'дня' : 'дней'}`,
      color: 'success'
    })

    emit('saved')

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

// Только смена набора дат — иначе deep-watch ловит шум и снова вызывает loadScheduleForDate, затирая перерывы
watch(selectedDateKeys, () => {
  const dates = sortSelectedDays(selectedDates.value)
  if (dates.length === 1 && dates[0]) {
    loadScheduleForDate(dates[0])
  } else if (dates.length > 1) {
    scheduleType.value = 'workday'
    startTime.value = '10:00'
    endTime.value = '22:00'
    breaks.value = []
  }
})

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
      await fetchProfile()
      isSyncingTemplate.value = true
      syncTemplateFieldsFromUser()
      await nextTick()
      isSyncingTemplate.value = false
      templateInitialized.value = true
      await loadSchedules()
    }, 300)
  }
})
</script>

<template>
  <div class="flex w-full min-w-0 max-w-full flex-col gap-6">
        <!-- Шаблон: первый блок настроек -->
        <div class="w-full min-w-0 max-w-full flex flex-col gap-3 sm:gap-4">
          <div class="flex min-w-0 items-center gap-1.5">
            <h3 class="min-w-0 text-lg font-semibold">
              Основной шаблон графика
            </h3>
            <UPopover
              mode="click"
              :ui="scheduleHelpPopoverUi"
              :content="{ side: 'bottom', sideOffset: 6, collisionPadding: 12 }"
            >
              <UButton
                type="button"
                icon="i-lucide-circle-help"
                color="neutral"
                variant="ghost"
                square
                class="!size-7 shrink-0 rounded-full p-0 !text-muted"
                aria-label="Справка: основной шаблон графика"
                aria-haspopup="dialog"
              />
              <template #content>
                <p class="m-0 text-xs leading-relaxed text-highlighted sm:text-sm whitespace-normal break-words text-pretty">
                  {{ templateBlockHelp }}
                </p>
              </template>
            </UPopover>
          </div>
          <div class="w-full min-w-0 max-w-full sm:max-w-2xl">
            <USelect
              v-model="selectedWorkTemplate"
              :items="templateSelectItems"
              value-key="value"
              :ui="compactSelectUi"
              class="w-full min-w-0 max-w-full"
              :disabled="isSavingTemplate"
              portal
              @update:model-value="onUserChangedWorkTemplate"
            />
          </div>
          <p class="text-xs text-muted">
            {{ templateWorkdayHoursLabel }}
          </p>
          <div
            v-if="selectedWorkTemplate === 'shift-cycle'"
            class="flex w-full min-w-0 max-w-full flex-col gap-3 sm:flex-row sm:items-end sm:gap-4"
          >
            <div class="w-full min-w-0 sm:flex-1 sm:max-w-xs">
              <label class="text-sm font-medium mb-1.5 block">Цикл</label>
              <USelect
                v-model="shiftCycle"
                :ui="compactSelectUi"
                class="w-full min-w-0 max-w-full"
                :items="[
                  { label: '2 рабочих / 2 выходных', value: '2-2' },
                  { label: '3 рабочих / 3 выходных', value: '3-3' },
                  { label: '4 рабочих / 4 выходных', value: '4-4' }
                ]"
                :disabled="isSavingTemplate"
                portal
                @update:model-value="onUserChangedWorkTemplate"
              />
            </div>
            <div class="w-full min-w-0 sm:flex-1 sm:max-w-xs">
              <label class="text-sm font-medium mb-1.5 block">Дата начала цикла</label>
              <UInput
                v-model="shiftAnchorInput"
                type="date"
                class="w-full min-w-0 max-w-full"
                :disabled="isSavingTemplate"
                @change="onUserChangedWorkTemplate"
              />
            </div>
          </div>
          <p
            v-if="isSavingTemplate"
            class="text-xs text-muted"
          >
            Сохранение…
          </p>
        </div>

        <div class="flex w-full min-w-0 max-w-full items-center gap-1.5">
          <h3 class="min-w-0 text-lg font-semibold">
            Детальная настройка
          </h3>
          <UPopover
            mode="click"
            :ui="scheduleHelpPopoverUi"
            :content="{ side: 'bottom', sideOffset: 6, collisionPadding: 12 }"
          >
            <UButton
              type="button"
              icon="i-lucide-circle-help"
              color="neutral"
              variant="ghost"
              square
              class="!size-7 shrink-0 rounded-full p-0 !text-muted"
              aria-label="Справка: детальная настройка"
              aria-haspopup="dialog"
            />
            <template #content>
              <p class="m-0 text-xs leading-relaxed text-highlighted sm:text-sm whitespace-normal break-words text-pretty">
                {{ detailBlockHelp }}
              </p>
            </template>
          </UPopover>
        </div>

        <!-- Месяц и «Сегодня» — сразу над календарём -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex min-w-0 items-center gap-2">
            <UButton
              icon="i-lucide-chevron-left"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              @click="previousMonth"
            />
            <h2 class="min-w-0 text-lg font-semibold truncate">
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
            class="shrink-0"
            @click="goToToday"
          />
        </div>

        <!-- Календарная сетка месяца: компактные ячейки -->
        <div class="w-full min-w-0 max-w-full border border-default/80 rounded-lg bg-elevated/20 p-2 sm:p-3">
          <!-- Заголовки дней недели -->
          <div
            class="grid grid-cols-7 gap-1 mb-1"
            role="row"
            aria-hidden="true"
          >
            <div
              v-for="w in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']"
              :key="w"
              class="text-center text-[9px] font-medium text-muted tabular-nums py-0.5"
            >
              {{ w }}
            </div>
          </div>

          <div
            class="grid grid-cols-7 gap-1"
            role="grid"
            :aria-label="`Календарь ${format(currentMonth, 'LLLL yyyy', { locale: ru })}`"
          >
            <button
              v-for="day in calendarGridDays"
              :key="day.getTime()"
              type="button"
              class="group relative flex w-full min-w-0 flex-col items-center justify-center text-center
                rounded-md border px-1.5 py-1.5
                max-md:min-h-[5.25rem] max-md:px-1.5 max-md:py-2.5
                md:min-h-[3.25rem] md:px-1.5 md:py-1.5
                transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-primary
                disabled:cursor-not-allowed disabled:opacity-100"
              :class="cellClasses(day)"
              :disabled="!isScheduleDateEditable(day)"
              :aria-pressed="isSelected(day) ? 'true' : 'false'"
              :aria-label="isScheduleDateEditable(day)
                ? `${format(day, 'd MMMM', { locale: ru })}, ${getScheduleTimeLabel(day)}`
                : `${format(day, 'd MMMM', { locale: ru })}, прошедший день, не редактируется`"
              :title="!isScheduleDateEditable(day) ? 'Прошедшие дни нельзя редактировать' : undefined"
              @click="toggleDate(day)"
            >
              <div
                class="flex w-full max-w-full flex-col items-center justify-center gap-0.5"
              >
                <div
                  class="text-[8px] font-medium leading-tight max-md:opacity-85"
                  :class="weekendLabelClass(day)"
                >
                  {{ getDayAbbreviation(day) }}
                </div>
                <div
                  class="text-xs font-semibold tabular-nums leading-none"
                  :class="dateNumberClass(day)"
                >
                  {{ format(day, 'd') }}
                </div>
                <div
                  class="w-full max-w-full px-0.5 text-center text-[7px] font-medium leading-snug max-md:text-[8px] sm:text-[9px] break-words hyphens-auto"
                  :class="timeLabelClass(day)"
                >
                  {{ getScheduleTimeLabel(day) }}
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- Панель настроек: только при выборе одного или нескольких дней -->
        <UPageCard
          v-if="selectedDates.length > 0"
          variant="subtle"
          class="w-full min-w-0 max-w-full"
          :ui="{
            root: 'w-full min-w-0 overflow-visible',
            container: 'min-w-0 p-4 sm:p-6',
            body: 'min-w-0 w-full',
            header: 'min-w-0 w-full'
          }"
        >
          <template #header>
            <div class="min-w-0">
              <h3 class="text-pretty text-lg font-semibold leading-snug">
                {{ daySettingsHeading }}
              </h3>
              <p
                v-if="daySettingsDatesLine"
                class="mt-1 text-pretty text-sm text-muted"
              >
                {{ daySettingsDatesLine }}
              </p>
            </div>
          </template>

          <div class="w-full min-w-0 max-w-full space-y-6">
            <!-- Тип + рабочее время: та же схема, что у строки перерыва (2×flex-1 + место под кнопку) -->
            <div
              class="flex w-full min-w-0 flex-col gap-4 sm:flex-row sm:items-end sm:gap-2"
            >
              <div class="min-w-0 w-full sm:flex-1">
                <label class="text-sm font-medium mb-2 block">Тип</label>
                <USelect
                  v-model="scheduleType"
                  :ui="compactSelectUi"
                  class="w-full min-w-0 max-w-full"
                  portal
                  :items="[
                    { label: 'Рабочий день', value: 'workday', icon: 'i-lucide-briefcase' },
                    { label: 'Нерабочий день', value: 'nonworkday', icon: 'i-lucide-trash-2' },
                    { label: 'Больничный', value: 'sickleave', icon: 'i-lucide-stethoscope' },
                    { label: 'Отпуск', value: 'vacation', icon: 'i-lucide-umbrella' }
                  ]"
                />
              </div>

              <div
                v-if="scheduleType === 'workday'"
                class="min-w-0 w-full sm:flex-1"
              >
                <label class="text-sm font-medium mb-2 block">Рабочее время</label>
                <div class="flex items-center gap-2">
                  <UInput
                    v-model="startTime"
                    type="time"
                    class="min-w-0 flex-1"
                  />
                  <span class="shrink-0 text-muted" aria-hidden="true">—</span>
                  <UInput
                    v-model="endTime"
                    type="time"
                    class="min-w-0 flex-1"
                  />
                </div>
              </div>

              <!-- невидимый столбец под square size="sm" у удаления перерыва -->
              <div
                v-if="scheduleType === 'workday'"
                class="hidden h-8 w-8 shrink-0 self-end sm:block"
                aria-hidden="true"
              />
            </div>

            <!-- Перерывы (только для рабочего дня) -->
            <div v-if="scheduleType === 'workday'">
              <label class="text-sm font-medium mb-2 block">Перерывы</label>
              <div class="space-y-2">
                <div
                  v-for="(breakItem, index) in breaks"
                  :key="`${index}-${breakItem.startTime}-${breakItem.endTime}`"
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
                    type="button"
                    icon="i-lucide-trash"
                    color="error"
                    variant="ghost"
                    size="sm"
                    square
                    @click.stop="removeBreak(index)"
                  />
                </div>
                <UButton
                  v-if="scheduleType === 'workday'"
                  label="Добавить перерыв"
                  color="neutral"
                  variant="ghost"
                  size="sm"
                  icon="i-lucide-plus"
                  @click="addBreak"
                />
              </div>
            </div>

            <!-- Кнопки и подпись об охвате дней — одна линия (текст слева, кнопки справа) -->
            <div
              class="flex min-w-0 items-start justify-between gap-3 border-t border-default pt-4"
            >
              <p class="min-w-0 flex-1 text-sm text-muted">
                {{ changeApplyDaysLabel }}
              </p>
              <div class="flex shrink-0 justify-end gap-2">
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
          </div>
        </UPageCard>
  </div>
</template>
