import { startOfDay, getDay } from 'date-fns'
import type { WorkBreak } from '~/types'

export type WorkScheduleTemplateId
  = 'standard-5'
  | 'peak-wed-sun'
  | 'shift-cycle'
  | 'flex-evening'
  | 'intensive-6'

export type ShiftCycleId = '2-2' | '3-3' | '4-4'

export interface WorkScheduleTemplateItem {
  id: WorkScheduleTemplateId
  title: string
  shortLabel: string
  description: string
  example: string
}

export const workScheduleTemplateList: WorkScheduleTemplateItem[] = [
  {
    id: 'standard-5',
    title: 'Стандартная пятидневка',
    shortLabel: 'Пн–Пт, 10:00–20:00',
    description: 'Классический офисный ритм. Подходит мастерам, работающим в салонах с устоявшимся графиком, или тем, кто хочет сохранить выходные для семьи.',
    example: 'Будни, с 10 до 20, обед плавающий'
  },
  {
    id: 'peak-wed-sun',
    title: 'Работа в пиковые дни',
    shortLabel: 'Ср–Вс, 11:00–21:00',
    description: 'Популярно у частных специалистов: вечер будней и выходные. Понедельник и вторник — выходные.',
    example: 'Среда–воскресенье, с 11 до 21, пн–вт — выходные'
  },
  {
    id: 'shift-cycle',
    title: 'Посменный плавающий график',
    shortLabel: '2/2, 3/3, 4/4',
    description: 'Смены и аренда кресла: график циклами «день через день» или «три через три» без жёсткой привязки к дням недели (от выбранной даты-опоры).',
    example: '2 дня работаю (10:00–22:00), 2 дня отдыхаю'
  },
  {
    id: 'flex-evening',
    title: 'Гибкий / частично занятый',
    shortLabel: 'вечер будней + сб',
    description: 'Совмещение с учёбой, другой работой или декрет: сокращённые смены.',
    example: 'Пн–Пт 17:00–21:00, сб полный день 10:00–20:00, вс — выходной'
  },
  {
    id: 'intensive-6',
    title: 'Интенсивный график',
    shortLabel: 'Пн–Сб, 9:00–21:00',
    description: 'Сезон или набор базы: шесть дней подряд, один фиксированный выходной (воскресенье).',
    example: 'Пн–Сб с 9:00 до 21:00, Вс — выходной'
  }
]

export interface DayScheduleConfig {
  type: 'workday' | 'nonworkday' | 'sickleave' | 'vacation'
  startTime?: string
  endTime?: string
  breaks: WorkBreak[]
}

function d(date: Date): number {
  return getDay(date)
}

/** getDay: 0=вс ... 1=пн ... 6=сб */
function isInCycleWorkSlot(date: Date, anchor: Date, workDays: number, offDays: number): boolean {
  const a = startOfDay(anchor).getTime()
  const t = startOfDay(date).getTime()
  const diff = Math.round((t - a) / 86400000)
  const cycle = workDays + offDays
  if (cycle === 0) return false
  const m = ((diff % cycle) + cycle) % cycle
  return m < workDays
}

/**
 * Правило для даты по шаблону. Для shift-cycle нужны anchor и shift (нап. 2+2).
 */
export function resolveDayScheduleFromTemplate(
  templateId: WorkScheduleTemplateId,
  date: Date,
  options?: { shift?: ShiftCycleId, anchor?: Date }
): DayScheduleConfig {
  const noBreak: WorkBreak[] = []

  switch (templateId) {
    case 'standard-5': {
      const day = d(date)
      if (day >= 1 && day <= 5) {
        return { type: 'workday', startTime: '10:00', endTime: '20:00', breaks: noBreak }
      }
      return { type: 'nonworkday', breaks: noBreak }
    }
    case 'peak-wed-sun': {
      const day = d(date)
      if (day === 0 || day === 3 || day === 4 || day === 5 || day === 6) {
        return { type: 'workday', startTime: '11:00', endTime: '21:00', breaks: noBreak }
      }
      return { type: 'nonworkday', breaks: noBreak }
    }
    case 'shift-cycle': {
      const shift: ShiftCycleId = options?.shift ?? '2-2'
      const [w, o] = shift.split('-').map(Number) as [number, number]
      const anchor = options?.anchor ? startOfDay(options.anchor) : startOfDay(new Date())
      const work = isInCycleWorkSlot(date, anchor, w, o)
      if (work) {
        return { type: 'workday', startTime: '10:00', endTime: '22:00', breaks: noBreak }
      }
      return { type: 'nonworkday', breaks: noBreak }
    }
    case 'flex-evening': {
      const day = d(date)
      if (day >= 1 && day <= 5) {
        return { type: 'workday', startTime: '17:00', endTime: '21:00', breaks: noBreak }
      }
      if (day === 6) {
        return { type: 'workday', startTime: '10:00', endTime: '20:00', breaks: noBreak }
      }
      return { type: 'nonworkday', breaks: noBreak }
    }
    case 'intensive-6': {
      const day = d(date)
      if (day >= 1 && day <= 6) {
        return { type: 'workday', startTime: '09:00', endTime: '21:00', breaks: noBreak }
      }
      return { type: 'nonworkday', breaks: noBreak }
    }
    default: {
      return { type: 'nonworkday', breaks: noBreak }
    }
  }
}

export function toApiBody(dateStr: string, cfg: DayScheduleConfig): Record<string, unknown> {
  const o: Record<string, unknown> = {
    date: dateStr,
    type: cfg.type
  }
  if (cfg.type === 'workday' && cfg.startTime && cfg.endTime) {
    o.startTime = cfg.startTime
    o.endTime = cfg.endTime
    if (cfg.breaks.length > 0) {
      o.breaks = cfg.breaks.map(b => ({ startTime: b.startTime, endTime: b.endTime }))
    }
  }
  return o
}
