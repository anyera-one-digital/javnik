<script setup lang="ts">
definePageMeta({
  layout: 'default'
})

useSeoMeta({
  title: 'Политика конфиденциальности',
  description: 'Политика конфиденциальности сервиса Bookly'
})
</script>

<template>
  <UContainer class="py-12 sm:py-16">
    <article class="prose prose-neutral dark:prose-invert max-w-none">
      <h1 class="text-2xl sm:text-3xl font-bold text-highlighted mb-8">
        Политика конфиденциальности
      </h1>
      <p class="text-muted text-sm mb-8">
        Последнее обновление: {{ new Date().toLocaleDateString('ru-RU') }}
      </p>

      <div class="space-y-6 text-foreground">
        <section>
          <h2 class="text-lg font-semibold mb-3">1. Общие положения</h2>
          <p class="text-muted leading-relaxed">
            Настоящая Политика конфиденциальности определяет порядок обработки и защиты персональных данных 
            пользователей сервиса Bookly (далее — «Сервис»). Используя Сервис, вы даёте согласие на сбор, 
            хранение и обработку ваших персональных данных в соответствии с настоящей Политикой.
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold mb-3">2. Какие данные мы собираем</h2>
          <p class="text-muted leading-relaxed mb-3">
            При регистрации и использовании Сервиса мы можем собирать:
          </p>
          <ul class="list-disc list-inside text-muted space-y-1 ml-2">
            <li>Контактные данные: email, номер телефона</li>
            <li>Учётные данные: имя пользователя, имя и фамилия</li>
            <li>Данные профиля: специальность, описание, адрес оказания услуг</li>
            <li>Данные о бронированиях и записях клиентов</li>
            <li>Технические данные: IP-адрес, данные cookies, информация о браузере</li>
          </ul>
        </section>

        <section>
          <h2 class="text-lg font-semibold mb-3">3. Цели обработки данных</h2>
          <p class="text-muted leading-relaxed">
            Персональные данные используются для предоставления функционала Сервиса, организации бронирований, 
            связи с пользователями, улучшения качества работы и обеспечения безопасности.
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold mb-3">4. Защита данных</h2>
          <p class="text-muted leading-relaxed">
            Мы применяем технические и организационные меры для защиты персональных данных от несанкционированного 
            доступа, изменения, раскрытия или уничтожения. Доступ к данным имеют только уполномоченные лица.
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold mb-3">5. Передача данных третьим лицам</h2>
          <p class="text-muted leading-relaxed">
            Мы не передаём персональные данные третьим лицам, за исключением случаев, предусмотренных 
            законодательством или необходимых для оказания услуг (например, платёжные системы, хостинг).
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold mb-3">6. Права пользователя</h2>
          <p class="text-muted leading-relaxed">
            Вы имеете право запросить доступ к своим данным, их исправление или удаление. Для этого 
            обратитесь через форму обратной связи или на указанный контактный адрес.
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold mb-3">7. Изменения</h2>
          <p class="text-muted leading-relaxed">
            Мы вправе вносить изменения в настоящую Политику. Актуальная версия всегда доступна на данной странице. 
            Продолжение использования Сервиса после изменений означает ваше согласие с обновлённой Политикой.
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold mb-3">8. Контакты</h2>
          <p class="text-muted leading-relaxed">
            По вопросам, связанным с обработкой персональных данных, вы можете обратиться через форму 
            обратной связи в приложении или на указанный в Сервисе контактный адрес.
          </p>
        </section>
      </div>
    </article>
  </UContainer>
</template>
