<script setup lang="ts">
import type { Service } from '~/types'
import ServicesServiceModal from '~/components/UserPersonalAccount/services/ServiceModal.vue'
import ServicesDeleteServiceModal from '~/components/UserPersonalAccount/services/DeleteServiceModal.vue'
import ServiceCatalogList from '~/components/UserPersonalAccount/services/ServiceCatalogList.vue'
import type { ServiceFilter } from '~/components/UserPersonalAccount/services/ServiceCatalogList.vue'
import ServiceEditorPanel from '~/components/UserPersonalAccount/services/ServiceEditorPanel.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

useSeoMeta({
  title: 'Услуги'
})

const toast = useToast()
const { getAuthHeaders, refreshAccessToken } = useAuth()

const services = ref<Service[]>([])
const isLoading = ref(false)
const filter = ref<ServiceFilter>('all')
const selectedId = ref<number | null>(null)
const saving = ref(false)
const createServiceModalOpen = ref(false)
const deletingService = ref<Service | null>(null)

const selectedService = computed(
  () => services.value.find(s => s.id === selectedId.value) ?? null
)

function sortServices(list: Service[]) {
  return [...list].sort((a, b) => {
    const ao = a.sort_order ?? 0
    const bo = b.sort_order ?? 0
    if (ao !== bo) return ao - bo
    return a.id - b.id
  })
}

async function loadServices() {
  if (!process.client) return

  try {
    isLoading.value = true
    let headers = getAuthHeaders()
    if (!headers.Authorization) {
      services.value = []
      return
    }

    try {
      const data = await $fetch<any>('/api/services/', { headers })
      const list = Array.isArray(data)
        ? data
        : (data?.results && Array.isArray(data.results) ? data.results : [])
      services.value = sortServices(list as Service[])
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retry = await $fetch<any>('/api/services/', { headers })
          const list = Array.isArray(retry)
            ? retry
            : (retry?.results && Array.isArray(retry.results) ? retry.results : [])
          services.value = sortServices(list as Service[])
          return
        }
      }
      console.error('Error loading services:', error)
      services.value = []
    }
  } finally {
    isLoading.value = false
    if (selectedId.value && !services.value.some(s => s.id === selectedId.value)) {
      selectedId.value = null
    }
  }
}

onMounted(() => {
  if (process.client) loadServices()
})

function selectService(s: Service) {
  selectedId.value = s.id
}

async function saveService(payload: {
  data: Partial<Service>
  portfolioFiles: File[]
  removedPortfolioImageIds: number[]
}) {
  if (!selectedService.value) return
  const id = selectedService.value.id
  const headers = getAuthHeaders()
  if (!headers.Authorization) {
    toast.add({ title: 'Ошибка', description: 'Необходима авторизация', color: 'error' })
    return
  }

  saving.value = true
  try {
    const needsMultipart
      = payload.portfolioFiles.length > 0
      || payload.removedPortfolioImageIds.length > 0

    let updated: Service
    if (needsMultipart) {
      const formData = new FormData()
      const d = payload.data
      if (d.name != null) formData.append('name', String(d.name))
      if (d.description != null) formData.append('description', String(d.description))
      if (d.duration != null) formData.append('duration', String(d.duration))
      if (d.price != null) formData.append('price', String(d.price))
      if (d.prepayment != null) formData.append('prepayment', String(d.prepayment))
      if (d.active != null) formData.append('active', d.active ? 'true' : 'false')
      payload.portfolioFiles.forEach((file) => {
        formData.append('portfolio_images', file)
      })
      if (payload.removedPortfolioImageIds.length) {
        formData.append(
          'removed_portfolio_image_ids',
          JSON.stringify(payload.removedPortfolioImageIds)
        )
      }
      updated = await $fetch<Service>(`/api/services/${id}/`, {
        method: 'PATCH',
        headers: { Authorization: headers.Authorization as string },
        body: formData
      })
    } else {
      updated = await $fetch<Service>(`/api/services/${id}/`, {
        method: 'PATCH',
        headers,
        body: payload.data
      })
    }

    const idx = services.value.findIndex(s => s.id === id)
    if (idx !== -1) {
      services.value[idx] = { ...services.value[idx], ...updated, ...payload.data }
    }
    // Reload to refresh portfolio_images URLs
    if (needsMultipart) await loadServices()
    toast.add({ title: 'Сохранено', description: 'Услуга обновлена', color: 'success' })
  } catch (error: any) {
    toast.add({
      title: 'Ошибка',
      description: error.data?.detail || error.data?.error || error.message || 'Не удалось сохранить',
      color: 'error'
    })
  } finally {
    saving.value = false
  }
}

async function reorderServices(ids: number[]) {
  const prev = services.value
  const byId = new Map(prev.map(s => [s.id, s]))
  services.value = ids
    .map((id, index) => {
      const s = byId.get(id)
      return s ? { ...s, sort_order: index } : null
    })
    .filter(Boolean) as Service[]

  const headers = getAuthHeaders()
  if (!headers.Authorization) {
    services.value = prev
    return
  }

  try {
    await $fetch('/api/services/reorder', {
      method: 'POST',
      headers,
      body: { ids }
    })
  } catch (error: any) {
    services.value = prev
    toast.add({
      title: 'Ошибка',
      description: error.data?.detail || error.message || 'Не удалось изменить порядок',
      color: 'error'
    })
  }
}

async function confirmDeleteService() {
  if (!deletingService.value) return
  const service = deletingService.value
  const headers = getAuthHeaders()
  if (!headers.Authorization) {
    toast.add({ title: 'Ошибка', description: 'Необходима авторизация', color: 'error' })
    deletingService.value = null
    return
  }

  try {
    await $fetch(`/api/services/${service.id}/`, {
      method: 'DELETE',
      headers
    })
    toast.add({
      title: 'Услуга удалена',
      description: `Услуга «${service.name}» была удалена`,
      color: 'success'
    })
    if (selectedId.value === service.id) selectedId.value = null
    deletingService.value = null
    await loadServices()
  } catch (error: any) {
    toast.add({
      title: 'Ошибка',
      description: error.data?.message || error.message || 'Произошла ошибка при удалении услуги',
      color: 'error'
    })
  }
}

function openDelete(s: Service) {
  deletingService.value = s
}

async function handleCreated() {
  createServiceModalOpen.value = false
  await loadServices()
}
</script>

<template>
  <UDashboardPanel
    id="services"
    class="catalog-dashboard-panel h-full min-h-0"
    :ui="{
      root: 'h-full min-h-0 max-h-full !min-h-0 overflow-hidden',
      body: 'flex-1 min-h-0 overflow-hidden max-xl:overflow-y-auto flex flex-col gap-3 p-4 sm:p-6'
    }"
  >
    <template #header>
      <UDashboardNavbar title="Услуги">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>

        <template #right>
          <UButton
            label="Добавить услугу"
            icon="i-lucide-plus"
            class="!bg-violet-500 !text-white hover:!bg-violet-400"
            @click="createServiceModalOpen = true"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="catalog-page h-full min-h-0 overflow-hidden flex flex-col gap-3">
        <div
          v-if="isLoading && !services.length"
          class="flex-1 flex items-center justify-center text-muted text-sm"
        >
          Загрузка услуг...
        </div>

        <div
          v-else
          class="flex-1 min-h-0 overflow-hidden grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(300px,400px)] gap-3"
        >
          <ServiceCatalogList
            v-model:filter="filter"
            :services="services"
            :selected-id="selectedId"
            class="min-h-[40vh] xl:min-h-0 h-full overflow-hidden"
            @select="selectService"
            @reorder="reorderServices"
          />

          <ServiceEditorPanel
            class="hidden xl:flex h-full min-h-0 overflow-hidden"
            :service="selectedService"
            :saving="saving"
            @save="saveService"
            @remove="selectedService && openDelete(selectedService)"
          />

          <div
            v-if="selectedService"
            class="xl:hidden fixed inset-0 z-40 bg-black/50 flex items-end sm:items-center justify-center p-0 sm:p-4"
            @click.self="selectedId = null"
          >
            <div class="relative w-full sm:max-w-md h-[85vh] sm:h-[80vh] sm:rounded-[14px] overflow-hidden">
              <UButton
                icon="i-lucide-x"
                color="neutral"
                variant="ghost"
                size="sm"
                class="absolute top-3 right-12 z-10"
                aria-label="Закрыть"
                @click="selectedId = null"
              />
              <ServiceEditorPanel
                class="h-full"
                :service="selectedService"
                :saving="saving"
                @save="saveService"
                @remove="openDelete(selectedService)"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <ServicesServiceModal
    v-model="createServiceModalOpen"
    @saved="handleCreated"
  />

  <ServicesDeleteServiceModal
    :service="deletingService"
    @confirmed="confirmDeleteService"
    @cancelled="deletingService = null"
  />
</template>
