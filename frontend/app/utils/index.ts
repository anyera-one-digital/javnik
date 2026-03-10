export function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export function randomFrom<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)]!
}

/**
 * Форматирует день недели в строго двухбуквенный формат (пн, вт, ср, чт, пт, сб, вс)
 */
export function formatWeekdayShort(date: Date): string {
  const dayOfWeek = date.getDay() // 0 = воскресенье, 1 = понедельник, ..., 6 = суббота
  const shortNames = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб']
  return shortNames[dayOfWeek] || 'пн'
}
