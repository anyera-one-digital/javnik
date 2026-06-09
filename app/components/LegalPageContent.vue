<script setup lang="ts">
export type LegalPageSlug = 'privacy' | 'terms'

export interface LegalPageData {
  slug: string
  title: string
  subtitle: string
  content: string
  seo: {
    title: string
    description: string
  }
  updatedAt: string
}

const props = defineProps<{
  slug: LegalPageSlug
  fallbackTitle: string
  fallbackDescription: string
}>()

const { data: page } = await useAsyncData(
  () => `legal-${props.slug}`,
  () => $fetch<LegalPageData | null>(`/api/landing/legal/${props.slug}`),
  {
    default: () => null,
    server: true,
    lazy: false
  }
)

const title = computed(() => page.value?.title || props.fallbackTitle)
const subtitle = computed(() => page.value?.subtitle || '')
const content = computed(() => page.value?.content || '')
const updatedAt = computed(() => {
  if (!page.value?.updatedAt) return null
  return new Date(page.value.updatedAt).toLocaleDateString('ru-RU')
})

useSeoMeta({
  title: computed(() => page.value?.seo?.title || props.fallbackTitle),
  description: computed(() => page.value?.seo?.description || props.fallbackDescription)
})
</script>

<template>
  <UContainer class="py-12 sm:py-16">
    <article class="prose prose-neutral dark:prose-invert max-w-none legal-page-content">
      <h1 class="text-2xl sm:text-3xl font-bold text-highlighted mb-4 not-prose">
        {{ title }}
      </h1>
      <p
        v-if="subtitle || updatedAt"
        class="text-muted text-sm mb-8 not-prose"
      >
        <template v-if="subtitle">
          {{ subtitle }}<br>
        </template>
        <template v-if="updatedAt">
          Редакция от {{ updatedAt }}
        </template>
      </p>

      <div
        v-if="content"
        class="legal-page-body space-y-8 text-foreground"
        v-html="content"
      />
      <p
        v-else
        class="text-muted not-prose"
      >
        Содержимое страницы временно недоступно.
      </p>
    </article>
  </UContainer>
</template>

<style scoped>
.legal-page-body :deep(section) {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.legal-page-body :deep(h2) {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--ui-text-highlighted);
  margin: 0;
}

.legal-page-body :deep(p),
.legal-page-body :deep(li) {
  color: var(--ui-text-muted);
  line-height: 1.625;
}

.legal-page-body :deep(a) {
  color: var(--ui-text-highlighted);
  text-decoration: underline;
}

.legal-page-body :deep(strong) {
  color: var(--ui-text-highlighted);
}

.legal-page-body :deep(table) {
  width: 100%;
  font-size: 0.875rem;
  border: 1px solid var(--ui-border);
}

.legal-page-body :deep(th),
.legal-page-body :deep(td) {
  padding: 0.75rem;
  border-bottom: 1px solid var(--ui-border);
  vertical-align: top;
}

.legal-page-body :deep(th) {
  font-weight: 600;
  color: var(--ui-text-highlighted);
  width: 33%;
  background: color-mix(in oklab, var(--ui-bg-elevated) 50%, transparent);
}

.legal-page-body :deep(ul) {
  list-style: none;
  padding: 0;
  margin: 0;
}

.legal-page-body :deep(ul li) {
  margin: 0.25rem 0;
}
</style>
