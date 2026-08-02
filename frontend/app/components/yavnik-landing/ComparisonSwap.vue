<script setup lang="ts">
import { Check, X } from '@lucide/vue'

const mode = ref<'before' | 'after'>('before')

const beforeItems = [
  'Уточнения времени',
  'Ручные напоминания',
  'Переносы в сообщениях',
  'Клиенты в разных чатах'
]

const afterItems = [
  'Свободное время видно сразу',
  'Напоминания автоматически',
  'Перенос без переписки',
  'Все клиенты в одном месте'
]
</script>

<template>
  <div class="comparison-stage reveal">
    <div
      class="comparison-stack"
      :class="mode === 'after' ? 'is-after' : 'is-before'"
    >
      <article
        class="swap-card swap-card--before"
        :aria-hidden="mode === 'after'"
      >
        <span class="swap-card__label">Было</span>
        <ul>
          <li
            v-for="item in beforeItems"
            :key="item"
          >
            <span class="swap-card__icon swap-card__icon--x"><X :size="14" :stroke-width="2.4" /></span>
            {{ item }}
          </li>
        </ul>
      </article>

      <article
        class="swap-card swap-card--after"
        :aria-hidden="mode === 'before'"
      >
        <span class="swap-card__label">Стало</span>
        <ul>
          <li
            v-for="item in afterItems"
            :key="item"
          >
            <span class="swap-card__icon swap-card__icon--check"><Check :size="13" :stroke-width="2.6" /></span>
            {{ item }}
          </li>
        </ul>
      </article>
    </div>

    <div
      class="comparison-toggle"
      role="tablist"
      aria-label="Было или стало"
    >
      <button
        type="button"
        role="tab"
        class="focus-ring"
        :class="{ 'is-active': mode === 'before' }"
        :aria-selected="mode === 'before'"
        @click="mode = 'before'"
      >
        Было
      </button>
      <span class="comparison-toggle__slash" aria-hidden="true">/</span>
      <button
        type="button"
        role="tab"
        class="focus-ring"
        :class="{ 'is-active': mode === 'after' }"
        :aria-selected="mode === 'after'"
        @click="mode = 'after'"
      >
        Стало
      </button>
    </div>
  </div>
</template>
