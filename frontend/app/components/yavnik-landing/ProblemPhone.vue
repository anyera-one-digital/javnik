<script setup lang="ts">
import {
  ArrowLeftRight,
  Bell,
  CalendarDays,
  ChevronLeft,
  MapPin,
  Phone,
  Video,
} from '@lucide/vue';

const messages = [
  { from: 'client', text: 'А завтра после шести можно?', time: '18:02' },
  { from: 'you', text: 'Сейчас гляну…', time: '18:03' },
  { from: 'client', text: 'А какие окна остались?', time: '18:04' },
  { from: 'client', text: 'Напомните, пожалуйста, адрес', time: '18:05' },
  { from: 'client', text: 'Перенесем на пятницу?', time: '18:07' },
  {
    from: 'you',
    text: 'Мое расписание можно посмотреть вот по этой ссылке и там же вся информация:',
    link: 'javnik.ru/username',
    time: '18:09',
  },
] as const;

const calloutsLeft = [
  { id: 'slots', label: 'Свободные окна', icon: CalendarDays },
  { id: 'address', label: 'Адрес в записи', icon: MapPin },
] as const;

const calloutsRight = [
  { id: 'reschedule', label: 'Перенос без звонка', icon: ArrowLeftRight },
  { id: 'reminder', label: 'Напоминание клиенту', icon: Bell },
] as const;

const visibleCount = ref(0);
const reduceMotion = ref(false);
const rootRef = ref<HTMLElement | null>(null);
const threadRef = ref<HTMLElement | null>(null);
const cycleKey = ref(0);
const hasStarted = ref(false);

const visibleMessages = computed(() => messages.slice(0, visibleCount.value));

const STEP_MS = 700;
const HOLD_MS = 20000;
let timers: ReturnType<typeof setTimeout>[] = [];
let observer: IntersectionObserver | undefined;

const clearTimers = () => {
  timers.forEach(clearTimeout);
  timers = [];
};

const scrollThread = () => {
  const el = threadRef.value;
  if (!el) return;
  el.scrollTo({ top: el.scrollHeight, behavior: reduceMotion.value ? 'auto' : 'smooth' });
};

const runCycle = () => {
  clearTimers();
  visibleCount.value = 0;
  cycleKey.value += 1;

  if (reduceMotion.value) {
    visibleCount.value = messages.length;
    timers.push(setTimeout(runCycle, HOLD_MS));
    return;
  }

  messages.forEach((_, index) => {
    timers.push(setTimeout(() => {
      visibleCount.value = index + 1;
      nextTick(scrollThread);
    }, STEP_MS * (index + 1)));
  });

  timers.push(setTimeout(runCycle, STEP_MS * (messages.length + 1) + HOLD_MS));
};

const startAnimation = () => {
  if (hasStarted.value) return;
  hasStarted.value = true;
  runCycle();
};

onMounted(() => {
  reduceMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const target = rootRef.value;
  if (!target) return;

  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry?.isIntersecting) {
        startAnimation();
        observer?.disconnect();
        observer = undefined;
      }
    },
    { threshold: 0.35, rootMargin: '0px 0px -8% 0px' },
  );

  observer.observe(target);
});

onBeforeUnmount(() => {
  clearTimers();
  observer?.disconnect();
});
</script>

<template>
  <div ref="rootRef" class="problem-phone reveal" aria-label="Чаты с клиентами в телефоне">
    <div class="problem-phone__glow" aria-hidden="true" />

    <ul class="problem-callouts problem-callouts--left" aria-label="Возможности слева">
      <li
        v-for="(item, index) in calloutsLeft"
        :key="item.id"
        class="problem-callout problem-callout--left"
        :style="{ '--i': index }"
      >
        <span class="problem-callout__icon">
          <component :is="item.icon" :size="15" :stroke-width="1.8" />
        </span>
        <span>{{ item.label }}</span>
        <i class="problem-callout__line" aria-hidden="true" />
      </li>
    </ul>

    <div class="phone">
      <div class="phone__bezel">
        <div class="phone__side phone__side--left" aria-hidden="true">
          <i class="phone__btn phone__btn--silent" /><i class="phone__btn phone__btn--vol" /><i class="phone__btn phone__btn--vol" />
        </div>
        <div class="phone__side phone__side--right" aria-hidden="true">
          <i class="phone__btn phone__btn--power" />
        </div>

        <div class="phone__screen">
          <div class="phone__chrome">
            <div class="phone__status">
              <span class="phone__time">9:41</span>
              <div class="phone__island" aria-hidden="true">
                <i class="phone__island-camera" />
              </div>
              <div class="phone__status-icons" aria-hidden="true">
                <svg class="phone__icon-signal" viewBox="0 0 18 12" fill="currentColor">
                  <rect x="0" y="8" width="3" height="4" rx="0.7" />
                  <rect x="5" y="5.5" width="3" height="6.5" rx="0.7" />
                  <rect x="10" y="2.5" width="3" height="9.5" rx="0.7" />
                  <rect x="15" y="0" width="3" height="12" rx="0.7" />
                </svg>
                <svg class="phone__icon-wifi" viewBox="0 0 16 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
                  <path d="M1.2 4.2a9.2 9.2 0 0 1 13.6 0" />
                  <path d="M3.5 6.6a6 6 0 0 1 9 0" />
                  <path d="M5.8 9a2.8 2.8 0 0 1 4.4 0" />
                  <circle cx="8" cy="11.1" r="1" fill="currentColor" stroke="none" />
                </svg>
                <span class="phone__battery">
                  <span class="phone__battery-level" />
                </span>
              </div>
            </div>

            <header class="chat-header">
              <button type="button" class="chat-header__back" aria-hidden="true" tabindex="-1">
                <ChevronLeft :size="16" :stroke-width="2.4" />
              </button>
              <div class="chat-header__avatar" aria-hidden="true">К</div>
              <div class="chat-header__meta">
                <strong>Клиент</strong>
                <small>онлайн</small>
              </div>
              <div class="chat-header__actions" aria-hidden="true">
                <Video :size="14" :stroke-width="1.8" />
                <Phone :size="13" :stroke-width="1.8" />
              </div>
            </header>
          </div>

          <div ref="threadRef" class="chat-thread">
            <div v-if="visibleCount > 0" class="chat-day is-visible">Сегодня</div>
            <TransitionGroup name="chat-msg" tag="div" class="chat-thread__list">
              <div
                v-for="(message, index) in visibleMessages"
                :key="`${cycleKey}-${index}`"
                class="chat-bubble"
                :class="message.from === 'client' ? 'chat-bubble--in' : 'chat-bubble--out'"
              >
                <p>
                  {{ message.text }}
                  <template v-if="'link' in message && message.link">
                    <br>
                    <span class="chat-bubble__link">{{ message.link }}</span>
                  </template>
                </p>
                <time>{{ message.time }}</time>
              </div>
            </TransitionGroup>
          </div>

          <div class="chat-composer" aria-hidden="true">
            <span class="chat-composer__field">Сообщение</span>
            <span class="chat-composer__send">↑</span>
          </div>

          <div class="phone__home" aria-hidden="true" />
        </div>
      </div>
    </div>

    <ul class="problem-callouts problem-callouts--right" aria-label="Возможности справа">
      <li
        v-for="(item, index) in calloutsRight"
        :key="item.id"
        class="problem-callout problem-callout--right"
        :style="{ '--i': index + 2 }"
      >
        <i class="problem-callout__line" aria-hidden="true" />
        <span class="problem-callout__icon">
          <component :is="item.icon" :size="15" :stroke-width="1.8" />
        </span>
        <span>{{ item.label }}</span>
      </li>
    </ul>
  </div>
</template>
