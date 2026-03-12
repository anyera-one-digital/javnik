<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import { getPaginationRowModel } from '@tanstack/table-core'
import type { Row } from '@tanstack/table-core'
import type { Customer } from '~/types'
import { h, resolveComponent } from 'vue'
import CustomersAddModal from '~/components/UserPersonalAccount/customers/AddModal.vue'
import CustomersDeleteCustomerModal from '~/components/UserPersonalAccount/customers/DeleteCustomerModal.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const UButton = resolveComponent('UButton')
const UDropdownMenu = resolveComponent('UDropdownMenu')

const toast = useToast()
const table = useTemplateRef('table')

const columnVisibility = ref()

const createCustomerModalOpen = ref(false)
const editCustomerModalOpen = ref(false)
const editingCustomer = ref<Customer | null>(null)
const deletingCustomer = ref<Customer | null>(null)
const customers = ref<Customer[]>([])
const isLoading = ref(false)
const { getAuthHeaders, refreshAccessToken } = useAuth()

async function loadCustomers() {
  if (!process.client) return
  
  try {
    isLoading.value = true
    let headers = getAuthHeaders()
    
    if (!headers.Authorization) {
      console.warn('No auth token available for loading customers')
      customers.value = []
      return
    }
    
    try {
      const data = await $fetch<any>('/api/customers', {
        headers
      })
      
      // Убеждаемся, что data - это массив
      if (Array.isArray(data)) {
        customers.value = data as Customer[]
      } else if (data && typeof data === 'object' && 'results' in data) {
        // Если это пагинированный ответ
        customers.value = Array.isArray(data.results) ? (data.results as Customer[]) : []
      } else {
        customers.value = []
      }
    } catch (error: any) {
      // Если получили 401, пытаемся обновить токен
      if (error.statusCode === 401 || error.status === 401) {
        console.log('Got 401 for customers, attempting to refresh token...')
        const refreshed = await refreshAccessToken()
        
        if (refreshed) {
          console.log('Token refreshed, retrying customers request...')
          headers = getAuthHeaders()
          
          try {
            const retryData = await $fetch<any>('/api/customers', {
              headers
            })
            
            if (Array.isArray(retryData)) {
              customers.value = retryData as Customer[]
            } else if (retryData && typeof retryData === 'object' && 'results' in retryData) {
              customers.value = Array.isArray(retryData.results) ? (retryData.results as Customer[]) : []
            } else {
              customers.value = []
            }
            return
          } catch (retryError) {
            console.error('Retry customers after refresh failed:', retryError)
          }
        }
      }
      
      console.error('Error loading customers:', error)
      customers.value = []
    }
  } catch (error: any) {
    console.error('Unexpected error loading customers:', error)
    customers.value = []
  } finally {
    isLoading.value = false
  }
}

async function handleCustomerSaved() {
  await loadCustomers()
  createCustomerModalOpen.value = false
}

// Загружаем клиентов при монтировании
onMounted(() => {
  if (process.client) {
    loadCustomers()
  }
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
      headers: getAuthHeaders()
    })

    toast.add({
      title: 'Клиент удалён',
      description: `Клиент "${customer.name}" был удалён`,
      color: 'success'
    })

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

function deleteCustomer(customer: Customer) {
  deletingCustomer.value = customer
}

function getRowItems(row: Row<Customer>) {
  return [
    {
      type: 'label',
      label: 'Действия'
    },
    {
      label: 'Редактировать',
      icon: 'i-lucide-edit',
      onSelect() {
        editingCustomer.value = row.original
        editCustomerModalOpen.value = true
      }
    },
    {
      type: 'separator'
    },
    {
      label: 'Удалить',
      icon: 'i-lucide-trash',
      color: 'error' as const,
      onSelect() {
        deleteCustomer(row.original)
      }
    }
  ]
}

const columns: TableColumn<Customer>[] = [
  {
    accessorKey: 'name',
    header: 'Имя',
    cell: ({ row }) => h('p', { class: 'font-medium text-highlighted' }, row.original.name)
  },
  {
    accessorKey: 'email',
    header: 'Email',
    cell: ({ row }) => row.original.email || '-'
  },
  {
    accessorKey: 'phone',
    header: 'Телефон',
    cell: ({ row }) => row.original.phone || '-'
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      return h(
        'div',
        { class: 'text-right' },
        h(
          UDropdownMenu,
          {
            content: {
              align: 'end'
            },
            items: getRowItems(row)
          },
          () =>
            h(UButton, {
              icon: 'i-lucide-ellipsis-vertical',
              color: 'neutral',
              variant: 'ghost',
              class: 'ml-auto'
            })
        )
      )
    }
  }
]

const pagination = ref({
  pageIndex: 0,
  pageSize: 10
})
</script>

<template>
  <UDashboardPanel id="customers">
    <template #header>
      <UDashboardNavbar title="Клиенты">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>

        <template #right>
          <UButton 
            label="Добавить клиента" 
            icon="i-lucide-plus" 
            color="neutral"
            variant="solid"
            class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
            @click="createCustomerModalOpen = true"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <UTable
        ref="table"
        v-model:column-visibility="columnVisibility"
        v-model:pagination="pagination"
        :pagination-options="{
          getPaginationRowModel: getPaginationRowModel()
        }"
        class="shrink-0"
        :data="customers"
        :columns="columns"
        :loading="isLoading"
        :ui="{
          base: 'table-fixed border-separate border-spacing-0',
          thead: '[&>tr]:bg-elevated/50 [&>tr]:after:content-none',
          tbody: '[&>tr]:last:[&>td]:border-b-0',
          th: 'py-2 first:rounded-l-lg last:rounded-r-lg border-y border-default first:border-l last:border-r',
          td: 'border-b border-default',
          separator: 'h-0'
        }"
      />

      <div class="flex items-center justify-between gap-3 border-t border-default pt-4 mt-auto">
        <div class="text-sm text-muted">
          Всего {{ table?.tableApi?.getFilteredRowModel().rows.length || 0 }} клиентов
        </div>

        <div class="flex items-center gap-1.5">
          <UPagination
            :default-page="(table?.tableApi?.getState().pagination.pageIndex || 0) + 1"
            :items-per-page="table?.tableApi?.getState().pagination.pageSize"
            :total="table?.tableApi?.getFilteredRowModel().rows.length"
            active-color="neutral"
            @update:page="(p: number) => table?.tableApi?.setPageIndex(p - 1)"
          />
        </div>
      </div>
    </template>
  </UDashboardPanel>

  <!-- Модал создания нового клиента -->
  <CustomersAddModal
    v-model="createCustomerModalOpen"
    @saved="handleCustomerSaved"
  />

  <!-- Модал редактирования клиента -->
  <CustomersAddModal
    v-model="editCustomerModalOpen"
    :customer="editingCustomer"
    @saved="() => { loadCustomers(); editingCustomer = null; editCustomerModalOpen = false }"
  />

  <!-- Модал удаления клиента -->
  <CustomersDeleteCustomerModal
    :customer="deletingCustomer"
    @confirmed="deletingCustomer && confirmDeleteCustomer(deletingCustomer)"
    @cancelled="deletingCustomer = null"
  />
</template>
