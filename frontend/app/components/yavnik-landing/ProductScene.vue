<script setup lang="ts">
import { CalendarDays, Check, ChevronLeft, ChevronRight, Clock3, UserRound } from '@lucide/vue'

withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })
const { theme } = useYavnikTheme()
</script>

<template>
  <div
    class="product-scene"
    :class="{ 'product-scene--compact': compact }"
  >
    <div class="product-scene__glow" />
    <div class="browser-frame">
      <div class="browser-frame__bar">
        <div class="browser-frame__dots"><i /><i /><i /></div>
        <div class="browser-frame__address">
          app.yavnik.ru/schedule
        </div>
        <span class="browser-frame__secure">●</span>
      </div>
      <div class="browser-frame__body">
        <img
          :src="theme === 'dark' ? '/images/calendar-dark.png' : '/images/calendar-light.png'"
          alt="Расписание специалиста в сервисе Явьник"
          width="2160"
          height="1216"
        >
      </div>
    </div>

    <div class="booking-card">
      <div class="booking-card__top">
        <span class="avatar-mini"><UserRound :size="16" /></span>
        <div><strong>Владислав</strong><small>мастер татуировки</small></div>
        <span class="status-dot">онлайн</span>
      </div>
      <div class="booking-card__month">
        <button
          type="button"
          aria-label="Предыдущая неделя"
        >
          <ChevronLeft :size="15" />
        </button>
        <span>Август 2026</span>
        <button
          type="button"
          aria-label="Следующая неделя"
        >
          <ChevronRight :size="15" />
        </button>
      </div>
      <div class="booking-card__days">
        <span><small>Пн</small>3</span><span><small>Вт</small>4</span><span class="is-active"><small>Ср</small>5</span><span><small>Чт</small>6</span>
      </div>
      <div class="booking-card__slot">
        <Clock3 :size="15" /> <span>14:30–15:30</span><Check :size="16" />
      </div>
      <button
        class="booking-card__cta"
        type="button"
      >
        <CalendarDays :size="16" /> Записаться
      </button>
    </div>

    <div class="toast-card">
      <span><Check :size="15" /></span>
      <div><strong>Новая запись</strong><small>Сегодня в 14:30</small></div>
    </div>
  </div>
</template>
