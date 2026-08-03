<template>
  <footer class="site-footer">
    <div class="container site-footer__top">
      <div>
        <NuxtLink
          to="/"
          class="brand"
          aria-label="Явьник — главная"
        >
          <span class="brand__mark">Я</span><span>Явьник</span>
        </NuxtLink>
        <p>Онлайн-запись, в которой спокойно<br>и специалисту, и клиенту.</p>
      </div>
      <div class="site-footer__links">
        <div>
          <span>Продукт</span>
          <a href="#showcase">Возможности</a>
          <a href="#pricing">Тарифы</a>
          <a href="#how">UI Kit</a>
        </div>
        <div>
          <span>Информация</span>
          <a href="#faq">FAQ</a>
          <a href="mailto:hello@yavnik.ru">hello@yavnik.ru</a>
          <NuxtLink to="/terms">
            Пользовательское соглашение
          </NuxtLink>
          <NuxtLink to="/privacy">
            Политика конфиденциальности
          </NuxtLink>
        </div>
      </div>
    </div>
    <div class="container site-footer__bottom">
      <span>© {{ new Date().getFullYear() }} Явьник</span>
      <span>Сделано для тех, кто работает на себя</span>
    </div>
  </footer>
</template>
