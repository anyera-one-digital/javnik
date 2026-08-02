<script setup lang="ts">
import { Plus } from '@lucide/vue';
import { AccordionContent, AccordionHeader, AccordionItem, AccordionRoot, AccordionTrigger } from 'reka-ui';

const items = [
  ['Нужно ли скачивать приложение?', 'Нет. Явьник работает в браузере на телефоне, планшете и компьютере. Клиенту тоже ничего устанавливать не нужно.'],
  ['Можно ли начать бесплатно?', 'Да. На тарифе Free можно создать страницу, добавить до 5 услуг и принимать первые записи без ограничения по сроку.'],
  ['Как клиент получает напоминание?', 'После записи клиент получает подтверждение и напоминание на электронную почту. Дополнительные каналы можно подключить на профессиональном тарифе.'],
  ['Подойдет ли сервис, если расписание меняется?', 'Да. Вы задаете рабочие дни, перерывы и исключения. Свободные интервалы пересчитываются автоматически.'],
  ['Можно ли принимать предоплату?', 'Сценарий предоплаты предусмотрен для Pro: вы задаете сумму или процент, а клиент оплачивает перед подтверждением записи.'],
  ['Что увидит клиент?', 'Чистую персональную страницу с вашим описанием, портфолио, услугами, ценами и только доступным для записи временем.'],
];
</script>

<template>
  <AccordionRoot class="faq-list" type="single" collapsible>
    <AccordionItem v-for="(item, index) in items" :key="item[0]" class="faq-item" :value="`item-${index}`">
      <AccordionHeader>
        <AccordionTrigger class="faq-trigger focus-ring">
          <span>{{ item[0] }}</span>
          <Plus :size="20" aria-hidden="true" />
        </AccordionTrigger>
      </AccordionHeader>
      <AccordionContent class="faq-content"><div>{{ item[1] }}</div></AccordionContent>
    </AccordionItem>
  </AccordionRoot>
</template>
