# Видео для блока showcase на лендинге

Положите сюда mp4 (желательно H.264, без звука в превью-версии или короткие ролики 8–20 сек).

Имена по вкладкам:

- `showcase-profile.mp4` — Профиль
- `showcase-schedule.mp4` — Расписание
- `showcase-analytics.mp4` — Аналитика
- `showcase-clients.mp4` — Клиенты
- `showcase-services.mp4` — Услуги

Затем в `app/pages/index.vue` у соответствующего экрана укажите:

```ts
video: '/videos/showcase-profile.mp4'
```

Превью в окне браузера играет без звука (autoplay). Кнопка «Со звуком» открывает полный плеер.
