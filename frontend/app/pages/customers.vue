<script setup lang="ts">
import type { Customer, CustomerHistoryItem } from '~/types'
import CustomersAddModal from '~/components/UserPersonalAccount/customers/AddModal.vue'
import CustomersDeleteCustomerModal from '~/components/UserPersonalAccount/customers/DeleteCustomerModal.vue'
import CustomerList from '~/components/UserPersonalAccount/customers/CustomerList.vue'
import type { CustomerListFilter } from '~/components/UserPersonalAccount/customers/CustomerList.vue'
import CustomerDetailPanel from '~/components/UserPersonalAccount/customers/CustomerDetailPanel.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

useSeoMeta({
  title: 'Клиенты'
})

const toast = useToast()
const { getAuthHeaders, refreshAccessToken } = useAuth()

const createCustomerModalOpen = ref(false)
const deletingCustomer = ref<Customer | null>(null)
const customers = ref<Customer[]>([])
const isLoading = ref(false)
const saving = ref(false)

const search = ref('')
const listFilter = ref<CustomerListFilter>('all')
const selectedId = ref<number | null>(null)
const history = ref<CustomerHistoryItem[]>([])
const loadingHistory = ref(false)

const selectedCustomer = computed(
  () => customers.value.find(c => c.id === selectedId.value) ?? null
)

async function loadCustomers() {
  if (!process.client) return

  try {
    isLoading.value = true
    let headers = getAuthHeaders()

    if (!headers.Authorization) {
      customers.value = []
      return
    }

    try {
      const data = await $fetch<any>('/api/customers/', { headers })
      if (Array.isArray(data)) {
        customers.value = data as Customer[]
      } else if (data && typeof data === 'object' && 'results' in data) {
        customers.value = Array.isArray(data.results) ? (data.results as Customer[]) : []
      } else {
        customers.value = []
      }
    } catch (error: any) {
      if (error.statusCode === 401 || error.status === 401) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          headers = getAuthHeaders()
          const retryData = await $fetch<any>('/api/customers/', { headers })
          if (Array.isArray(retryData)) {
            customers.value = retryData as Customer[]
          } else if (retryData?.results) {
            customers.value = retryData.results as Customer[]
          } else {
            customers.value = []
          }
          return
        }
      }
      console.error('Error loading customers:', error)
      customers.value = []
    }
  } finally {
    isLoading.value = false
    if (selectedId.value && !customers.value.some(c => c.id === selectedId.value)) {
      selectedId.value = null
      history.value = []
    }
  }
}

async function loadHistory(customerId: number) {
  loadingHistory.value = true
  history.value = []
  try {
    const headers = getAuthHeaders()
    if (!headers.Authorization) return
    const res = await $fetch<{ items: CustomerHistoryItem[] }>(
      `/api/customers/${customerId}/history/`,
      { headers }
    )
    history.value = Array.isArray(res?.items) ? res.items : []
  } catch (e: any) {
    console.error('Failed to load customer history', e)
    history.value = []
    toast.add({
      title: 'Не удалось загрузить историю',
      description: e?.data?.detail || e?.message || 'Попробуйте обновить страницу',
      color: 'error'
    })
  } finally {
    loadingHistory.value = false
  }
}

function selectCustomer(c: Customer) {
  selectedId.value = c.id
  loadHistory(c.id)
}

async function handleCustomerSaved() {
  await loadCustomers()
  createCustomerModalOpen.value = false
}

onMounted(() => {
  if (process.client) loadCustomers()
})

async function confirmDeleteCustomer(customer: Customer) {
  if (!deletingCustomer.value) return
  try {
    const headers = getAuthHeaders()
    if (!headers.Authorization) {
      toast.add({ title: 'Ошибка', description: 'Необходима авторизация', color: 'error' })
      deletingCustomer.value = null
      return
    }

    await $fetch(`/api/customers/${customer.id}/`, {
      method: 'DELETE',
      headers
    })

    toast.add({
      title: 'Клиент удалён',
      description: `Клиент "${customer.name}" был удалён`,
      color: 'success'
    })

    if (selectedId.value === customer.id) {
      selectedId.value = null
      history.value = []
    }
    await loadCustomers()
    deletingCustomer.value = null
  } catch (error: any) {
    toast.add({
      title: 'Ошибка',
      description: error.data?.message || error.message || 'Произошла ошибка при удалении клиента',
      color: 'error'
    })
  }
}

function openDelete(c: Customer) {
  deletingCustomer.value = c
}

async function saveCustomer(payload: Partial<Customer>) {
  if (!selectedCustomer.value) return
  const id = selectedCustomer.value.id
  const headers = getAuthHeaders()
  if (!headers.Authorization) {
    toast.add({ title: 'Ошибка', description: 'Необходима авторизация', color: 'error' })
    return
  }
  if (!payload.email?.trim()) {
    toast.add({ title: 'Ошибка', description: 'Укажите email клиента', color: 'error' })
    return
  }
  if (!payload.name || payload.name.trim().length < 2) {
    toast.add({ title: 'Ошибка', description: 'Укажите имя клиента', color: 'error' })
    return
  }

  saving.value = true
  try {
    const updated = await $fetch<Customer>(`/api/customers/${id}/`, {
      method: 'PATCH',
      headers,
      body: payload
    })
    const idx = customers.value.findIndex(c => c.id === id)
    if (idx !== -1) {
      customers.value[idx] = { ...customers.value[idx], ...updated, ...payload }
    }
    toast.add({ title: 'Сохранено', description: 'Данные клиента обновлены', color: 'success' })
  } catch (error: any) {
    toast.add({
      title: 'Ошибка',
      description: error.data?.detail || error.data?.error || error.data?.email?.[0] || error.data?.message || error.message || 'Не удалось сохранить',
      color: 'error'
    })
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UDashboardPanel
    id="customers"
    class="catalog-dashboard-panel h-full min-h-0"
    :ui="{
      root: 'h-full min-h-0 max-h-full !min-h-0 overflow-hidden',
      body: 'flex-1 min-h-0 overflow-hidden max-xl:overflow-y-auto flex flex-col gap-3 p-4 sm:p-6'
    }"
  >
    <template #header>
      <UDashboardNavbar title="Клиенты">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>

        <template #right>
          <UButton
            label="Добавить клиента"
            icon="i-lucide-plus"
            class="!bg-violet-500 !text-white hover:!bg-violet-400"
            @click="createCustomerModalOpen = true"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <div class="catalog-page h-full min-h-0 overflow-hidden flex flex-col gap-3">
        <div
          v-if="isLoading && !customers.length"
          class="flex-1 flex items-center justify-center text-muted text-sm"
        >
          Загрузка клиентов...
        </div>

        <div
          v-else
          class="flex-1 min-h-0 overflow-hidden grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(300px,380px)] gap-3"
        >
          <CustomerList
            v-model:search="search"
            v-model:filter="listFilter"
            :customers="customers"
            :selected-id="selectedId"
            class="min-h-[40vh] xl:min-h-0 h-full overflow-hidden"
            @select="selectCustomer"
          />

          <!-- Desktop panel: высота экрана, кнопки внизу карточки -->
          <CustomerDetailPanel
            class="hidden xl:flex h-full min-h-0 overflow-hidden"
            :customer="selectedCustomer"
            :history="history"
            :loading-history="loadingHistory"
            :saving="saving"
            @save="saveCustomer"
            @remove="selectedCustomer && openDelete(selectedCustomer)"
            @book="navigateTo('/schedule')"
          />

          <!-- Mobile overlay panel -->
          <div
            v-if="selectedCustomer"
            class="xl:hidden fixed inset-0 z-40 bg-black/50 flex items-end sm:items-center justify-center p-0 sm:p-4"
            @click.self="selectedId = null"
          >
            <div class="relative w-full sm:max-w-md h-[85vh] sm:h-[80vh] sm:rounded-[14px] overflow-hidden">
              <UButton
                icon="i-lucide-x"
                color="neutral"
                variant="ghost"
                size="sm"
                class="absolute top-3 left-3 z-10"
                aria-label="Закрыть"
                @click="selectedId = null"
              />
              <CustomerDetailPanel
                class="h-full"
                :customer="selectedCustomer"
                :history="history"
                :loading-history="loadingHistory"
                :saving="saving"
                @save="saveCustomer"
                @remove="openDelete(selectedCustomer)"
                @book="navigateTo('/schedule')"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <CustomersAddModal
    v-model="createCustomerModalOpen"
    @saved="handleCustomerSaved"
  />

  <CustomersDeleteCustomerModal
    :customer="deletingCustomer"
    @confirmed="deletingCustomer && confirmDeleteCustomer(deletingCustomer)"
    @cancelled="deletingCustomer = null"
  />
</template>
