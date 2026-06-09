/**
 * Единый вид для UTabs (pill): переключатели день/неделя, месяц/год.
 * Высота трека 44px, обводка как у остальных кнопок (border-default).
 */
export const segmentControlTabsUi = {
  list: 'relative flex w-full h-11 min-h-11 p-1 gap-0.5 box-border border border-default rounded-full bg-elevated',
  indicator: 'rounded-full',
  trigger:
    'flex min-w-0 flex-1 self-stretch items-center justify-center text-sm font-medium data-[state=inactive]:text-muted'
}
