<script setup lang="ts">
definePageMeta({
  layout: 'landing',
  ssr: true
})

import {
  ArrowRight,
  Brain,
  CalendarCheck2,
  Camera,
  Check,
  Clock3,
  Dumbbell,
  GraduationCap,
  Music2,
  Palette,
  PawPrint,
  Play,
  Scissors,
  Sparkles,
  UserRound,
} from '@lucide/vue';
import { ToggleGroupItem, ToggleGroupRoot } from 'reka-ui';

const page = ref<HTMLElement | null>(null);
const showcase = ref<HTMLElement | null>(null);
const activeScreen = ref(0);
const billing = ref<'month' | 'year'>('month');
const { theme } = useYavnikTheme();

useHead({
  link: [
    {
      rel: 'preload',
      as: 'video',
      href: '/videos/showcase-profile.mp4',
      type: 'video/mp4',
    },
  ],
})

const screens = computed(() => [
  {
    label: 'Профиль',
    eyebrow: 'Ваша витрина',
    title: 'Страница, которая знакомит и записывает',
    image: '/images/specialist-page.png',
    alt: 'Публичная страница специалиста в Явьнике',
    video: '/videos/showcase-profile.mp4' as string | null,
    caption: 'Клиент сразу видит услуги, отзывы и кнопку записи'
  },
  {
    label: 'Расписание',
    eyebrow: 'Ваше время',
    title: 'Свободные слоты видны без переписки',
    image: theme.value === 'dark' ? '/images/calendar-dark.png' : '/images/calendar-light.png',
    alt: 'Недельное расписание в Явьнике',
    video: '/videos/showcase-schedule.mp4' as string | null,
    caption: 'Неделя, день и свободные окна — на одном экране'
  },
  {
    label: 'Аналитика',
    eyebrow: 'Динамика практики',
    title: 'Видно, сколько записей и как растет поток',
    image: theme.value === 'dark' ? '/images/calendar-dark.png' : '/images/calendar-light.png',
    alt: 'Аналитика в кабинете Явьник',
    video: '/videos/showcase-analytics.mp4' as string | null,
    caption: 'Записи, выручка и загрузка без сложных отчётов'
  },
  {
    label: 'Клиенты',
    eyebrow: 'База рядом',
    title: 'Все клиенты и история визитов в одном месте',
    image: theme.value === 'dark' ? '/images/calendar-dark.png' : '/images/calendar-light.png',
    alt: 'Список клиентов в Явьнике',
    video: '/videos/showcase-clients.mp4' as string | null,
    caption: 'Контакты и история визитов всегда под рукой'
  },
  {
    label: 'Услуги',
    eyebrow: 'Ваш прайс',
    title: 'Услуги и длительность настраиваются один раз',
    image: '/images/pricing.png',
    alt: 'Услуги и тарифы в Явьнике',
    video: '/videos/showcase-services.mp4' as string | null,
    caption: 'Название, длительность и цена — один раз настроили'
  }
]);

const audiences = [
  { icon: Scissors, title: 'Бьюти' }, { icon: Brain, title: 'Психологи' },
  { icon: GraduationCap, title: 'Репетиторы' }, { icon: Dumbbell, title: 'Тренеры' },
  { icon: Palette, title: 'Художники' }, { icon: Camera, title: 'Фотографы' },
  { icon: Music2, title: 'Преподаватели' }, { icon: PawPrint, title: 'Грумеры' },
];

let demoTimer: ReturnType<typeof setInterval> | undefined;
const playDemo = () => {
  showcase.value?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  activeScreen.value = 0;
  clearInterval(demoTimer);
  let step = 0;
  demoTimer = setInterval(() => {
    step += 1;
    activeScreen.value = step % screens.value.length;
    if (step >= screens.value.length) clearInterval(demoTimer);
  }, 1500);
};

onMounted(() => {
  const { $gsap, $ScrollTrigger } = useNuxtApp();
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion) return;

  const context = $gsap.context(() => {
    $gsap.from('.hero-copy > *', { opacity: 0, y: 26, duration: 0.8, stagger: 0.1, ease: 'power3.out' });
    $gsap.from('.hero-visual', { opacity: 0, y: 36, scale: 0.97, duration: 1, delay: 0.25, ease: 'power3.out' });

    $gsap.utils.toArray<HTMLElement>('.reveal').forEach((el) => {
      $gsap.from(el, {
        opacity: 0, y: 42, duration: 0.9, ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      });
    });

    $gsap.utils.toArray<HTMLElement>('[data-parallax]').forEach((el) => {
      $gsap.to(el, { yPercent: -4, ease: 'none', scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: 0.8 } });
    });
  }, page.value ?? undefined);

  onBeforeUnmount(() => { context.revert(); $ScrollTrigger.getAll().forEach((trigger) => trigger.kill()); });
});

onBeforeUnmount(() => clearInterval(demoTimer));
</script>

<template>
  <div ref="page" class="landing-page">
    <AppHeader />

    <main>
      <section class="hero-section">
        <div class="hero-orb hero-orb--one" data-parallax />
        <div class="hero-orb hero-orb--two" data-parallax />
        <div class="container hero-grid">
          <div class="hero-copy">
            <UiChip><Sparkles :size="13" /> Запись клиентов — без переписки</UiChip>
            <h1>Ваши клиенты<br><em>записываются сами.</em></h1>
            <p>Личная страница, свободные слоты, напоминания и клиентская база — в одном спокойном сервисе.</p>
            <div class="hero-actions">
              <SignupDialog />
              <UiButton
                variant="secondary"
                size="md"
                @click="playDemo"
              >
                <Play
                  :size="16"
                  fill="currentColor"
                />
                Посмотреть демо
              </UiButton>
            </div>
            <ul class="hero-proof" aria-label="Преимущества">
              <li><Check :size="14" /> 1 месяц Pro бесплатно</li>
              <li><Check :size="14" /> Без банковской карты</li>
              <li><Check :size="14" /> Работает с телефона</li>
            </ul>
          </div>
          <div class="hero-visual" data-parallax>
            <ProductScene />
          </div>
        </div>
        <div class="container hero-footnote">
          <span>Меньше рутины</span><i /><span>Больше подтвержденных записей</span><i /><span>Больше времени на работу</span>
        </div>
      </section>

      <section class="problem-section section-pad">
        <div class="container problem-grid">
          <div class="problem-lead reveal">
            <span class="eyebrow"><i /> Знакомая ситуация?</span>
            <h2>Запись не должна занимать больше времени, чем сама услуга.</h2>
            <p>Клиенты пишут в разное время, уточняют окна, адрес и переносы. Вы отвечаете вместо того, чтобы работать. Одна ссылка с расписанием закрывает эту переписку.</p>
          </div>
          <ProblemPhone />
        </div>
      </section>

      <section id="showcase" ref="showcase" class="showcase-section section-pad">
        <div class="showcase-glow" />
        <div class="container">
          <UiSectionHeading
            class="reveal"
            label="Интерфейс говорит за себя сам"
            title="Все важное видно с первого взгляда"
            text="Без перегруженных настроек и сложных сценариев."
            align="center"
            inverse
          />
          <div class="showcase-tabs" role="tablist" aria-label="Экраны сервиса">
            <button
              v-for="(screen, index) in screens"
              :key="screen.label"
              class="focus-ring"
              :class="{ 'is-active': activeScreen === index }"
              type="button"
              role="tab"
              :aria-selected="activeScreen === index"
              @click="activeScreen = index"
            >{{ screen.label }}</button>
          </div>
          <ShowcaseDemo
            :key="screens[activeScreen].label"
            class="reveal"
            :screen="screens[activeScreen]"
            :active="true"
          />
        </div>
      </section>

      <section id="audience" class="audience-section section-pad">
        <div class="container audience-grid">
          <div class="audience-copy reveal">
            <UiSectionHeading
              label="Для частной практики"
              title="Подходит тем, чье время — это продукт"
              text="Меняется профессия. Сценарий остается простым: показать услугу, выбрать время, подтвердить запись."
            />
            <UiButton href="#pricing" variant="secondary" arrow>И многим другим</UiButton>
          </div>
          <div class="audience-list reveal">
            <article v-for="item in audiences" :key="item.title">
              <component :is="item.icon" :size="20" :stroke-width="1.6" />
              <span>{{ item.title }}</span>
              <ArrowRight :size="17" />
            </article>
          </div>
        </div>
      </section>

      <section id="how" class="steps-section section-pad">
        <div class="container">
          <UiSectionHeading class="reveal" label="Три шага" title="Вечером настроили. Утром уже принимаете записи." />
          <div class="steps-grid">
            <article class="step-card reveal">
              <span class="step-card__number">01</span>
              <div class="step-card__icon"><UserRound :size="24" /></div>
              <h3>Создайте профиль</h3>
              <p>Добавьте фотографию, описание, работы и услуги.</p>
            </article>
            <article class="step-card reveal">
              <span class="step-card__number">02</span>
              <div class="step-card__icon"><Clock3 :size="24" /></div>
              <h3>Откройте расписание</h3>
              <p>Выберите рабочие дни, перерывы и свободное время.</p>
            </article>
            <article class="step-card step-card--accent reveal">
              <span class="step-card__number">03</span>
              <div class="step-card__icon"><CalendarCheck2 :size="24" /></div>
              <h3>Получайте записи</h3>
              <p>Клиенты смогут выбрать услугу и время в любой момент.</p>
            </article>
          </div>
        </div>
      </section>

      <section class="comparison-section section-pad">
        <div class="container comparison-grid">
          <div class="comparison-copy reveal">
            <span class="eyebrow"><i /> Было / Стало</span>
            <h2>Переписка остается для общения. Запись берет на себя сервис.</h2>
            <p>Явьник не меняет вашу работу — только делает ее спокойнее.</p>
          </div>
          <ComparisonSwap />
        </div>
      </section>

      <section id="pricing" class="pricing-section section-pad">
        <div class="container">
          <div class="pricing-head reveal">
            <UiSectionHeading
              label="Стоимость"
              title="Первый месяц Pro — бесплатно. Дальше Free или подписка."
              text="При регистрации открывается полный Pro на 30 дней без карты. Потом остаётесь на Free или продлеваете Pro."
            />
            <ToggleGroupRoot v-model="billing" class="billing-toggle" type="single" aria-label="Период оплаты">
              <ToggleGroupItem value="month">Месяц</ToggleGroupItem>
              <ToggleGroupItem value="year">Год <small>−20%</small></ToggleGroupItem>
            </ToggleGroupRoot>
          </div>
          <div class="pricing-grid">
            <article class="price-card reveal">
              <div class="price-card__head"><div><UiChip>После пробного</UiChip><h3>Free</h3></div><strong>0 ₽</strong></div>
              <p>Базовый тариф без срока: продолжайте принимать записи с лимитами Free.</p>
              <ul>
                <li><Check :size="16" /> До 50 клиентов</li>
                <li><Check :size="16" /> До 10 записей в месяц</li>
                <li><Check :size="16" /> До 5 услуг</li>
                <li><Check :size="16" /> Уведомления на почту</li>
              </ul>
              <SignupDialog label="Начать с Pro бесплатно" variant="secondary" large />
            </article>
            <article class="price-card price-card--pro reveal">
              <div class="price-card__badge"><Sparkles :size="14" /> 1 месяц бесплатно</div>
              <div class="price-card__head"><div><UiChip>Все возможности</UiChip><h3>Pro</h3></div><strong>{{ billing === 'month' ? '500 ₽' : '4 800 ₽' }}<small>/{{ billing === 'month' ? 'мес' : 'год' }}</small></strong></div>
              <p>
                {{ billing === 'month'
                  ? 'Первая оплата месяца — ещё +1 месяц. Дальше 500 ₽/мес.'
                  : 'Год за 4 800 ₽ (−1 200 ₽). Первая оплата — ещё +3 месяца.' }}
              </p>
              <ul>
                <li><Check :size="16" /> До 1 500 клиентов</li>
                <li><Check :size="16" /> До 150 записей в месяц</li>
                <li><Check :size="16" /> До 15 услуг</li>
                <li><Check :size="16" /> Аналитика и предоплата</li>
              </ul>
              <SignupDialog label="Получить месяц Pro" large />
            </article>
          </div>
          <p class="pricing-note">1 месяц Pro бесплатно · Без карты · После — Free или платная подписка</p>
        </div>
      </section>

      <section id="faq" class="faq-section section-pad">
        <div class="container faq-grid">
          <div class="faq-copy reveal">
            <UiSectionHeading label="FAQ" title="Коротко о важном" text="Не нашли ответа? Напишите нам — без ботов и сложных форм." />
            <a href="mailto:hello@yavnik.ru">hello@yavnik.ru <ArrowRight :size="17" /></a>
          </div>
          <FaqAccordion class="reveal" />
        </div>
      </section>

      <section id="final-cta" class="final-section">
        <div class="final-orb final-orb--one" /><div class="final-orb final-orb--two" />
        <div class="container final-inner reveal">
          <span class="eyebrow"><i /> Ваше время снова ваше</span>
          <h2>Освободите время<br>для своей работы.</h2>
          <p>Пусть записью занимается Явьник.</p>
          <SignupDialog large />
          <small><Check :size="14" /> 1 месяц Pro бесплатно · без банковской карты</small>
        </div>
      </section>
    </main>

    <AppFooter />
  </div>
</template>
