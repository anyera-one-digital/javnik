import type { Service } from '~/types'

/** Услуги, доступные для онлайн-записи (active !== false). */
export function onlyActiveServices(services: Service[] | null | undefined): Service[] {
  if (!services?.length) return []
  return services.filter(service => service.active !== false)
}
