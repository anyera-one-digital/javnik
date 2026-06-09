import * as z from 'zod'

export const PHONE_ERROR_MESSAGE = 'Введите корректный номер телефона'

export function digitsOnly(value: string): string {
  return value.replace(/\D/g, '')
}

/** Корректный номер РФ: 10 цифр (9…) или 11 (7/8…). */
export function isValidPhoneNumber(value: string): boolean {
  const trimmed = value.trim()
  if (!trimmed) return false
  const d = digitsOnly(trimmed)
  if (d.length < 10 || d.length > 11) return false
  if (d.length === 11) {
    return d[0] === '7' || d[0] === '8'
  }
  return d[0] === '9'
}

/**
 * Маска +7 (XXX) XXX-XX-XX; ввод только из цифр (остальное отбрасывается).
 */
export function formatPhoneRuInput(value: string): string {
  let d = digitsOnly(value)
  if (!d.length) return ''

  if (d[0] === '8') {
    d = '7' + d.slice(1)
  }
  if (d.length <= 10 && d[0] === '9') {
    d = '7' + d
  }

  d = d.slice(0, 11)
  if (!d.startsWith('7')) {
    return d.length ? `+${d}` : ''
  }

  const rest = d.slice(1)
  let out = '+7'
  if (rest.length === 0) return out

  out += ' (' + rest.slice(0, 3)
  if (rest.length >= 3) {
    out += ')'
  } else {
    return out
  }

  if (rest.length > 3) {
    out += ' ' + rest.slice(3, 6)
  }
  if (rest.length > 6) {
    out += '-' + rest.slice(6, 8)
  }
  if (rest.length > 8) {
    out += '-' + rest.slice(8, 10)
  }
  return out
}

export function applyRuPhoneMask(raw: string): string {
  return formatPhoneRuInput(digitsOnly(raw))
}

export const zodPhoneRequired = () =>
  z.string().min(1, 'Укажите номер телефона').refine(isValidPhoneNumber, {
    message: PHONE_ERROR_MESSAGE
  })
