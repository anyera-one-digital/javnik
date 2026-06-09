<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { Service } from '~/types'
import { h, resolveComponent } from 'vue'
import ServicesServiceModal from '~/components/UserPersonalAccount/services/ServiceModal.vue'
import { formatDurationMinutes } from '~/utils/formatDuration'
import ServicesDeleteServiceModal from '~/components/UserPersonalAccount/services/DeleteServiceModal.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const UBadge = resolveComponent('UBadge')
const UButton = resolveComponent('UButton')
const UDropdownMenu = resolveComponent('UDropdownMenu')
const USwitch = resolveComponent('USwitch')

const toast = useToast()
const { accessToken } = useAuth()

const togglingServiceIds = ref<Set<number>>(new Set())

// Используем $fetch для запросов с токеном авторизации
const services = ref<Service[]>([])

function extractApiErrorMessage(errorData: unknown, fallback: string): string {
  if (!errorData) return fallback
  if (typeof errorData === 'string') return errorData
  if (typeof errorData !== 'object') return fallback
  const data = errorData as Record<string, unknown>
  if (data.detail) return String(data.detail)
  if (data.message) return String(data.message)
  if (data.error) return String(data.error)
  const fields = Object.keys(data).map((key) => {
    const value = data[key]
    return `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`
  })
  return fields.join('\n') || fallback
}

async function loadServices() {
  if (!accessToken.value) return

  try {
    let token = accessToken.value.replace(/^Bearer\s+/i, '')
    token = `Bearer ${token}`

    const response = await $fetch<any>('/api/services', {
      headers: { Authorization: token }
    })

    if (Array.isArray(response)) {
      services.value = response
    } else if (response && typeof response === 'object' && 'results' in response) {
      services.value = response.results || []
    } else {
      services.value = []
    }
  } catch (error: any) {
    const statusCode = error.statusCode || error.status || 500
    const errorData = error.data || error.response?.data
    console.error('Error loading services:', statusCode, errorData)

    if (statusCode === 401) {
      toast.add({
        title: 'Ошибка авторизации',
        description: 'Токен авторизации истек или недействителен. Пожалуйста, войдите в систему заново.',
        color: 'error'
      })
      await navigateTo('/login')
    } else if (statusCode === 400) {
      toast.add({
        title: 'Ошибка запроса',
        description: extractApiErrorMessage(errorData, error.message || 'Неверный формат запроса'),
        color: 'error',
        timeout: 15000
      })
    } else {
      toast.add({
        title: 'Ошибка загрузки',
        description: error.message || 'Не удалось загрузить услуги',
        color: 'error'
      })
    }
    services.value = []
  }
}

onMounted(async () => {
  if (process.client && !accessToken.value) {
    const storedToken = localStorage.getItem('auth.accessToken')
    if (storedToken) {
      accessToken.value = storedToken
    }
  }

  if (accessToken.value) {
    await loadServices()
  }
})

watch(accessToken, async (token) => {
  if (token) {
    await loadServices()
  }
})

async function refreshServices() {
  await loadServices()
}

const editingService = ref<Service | null>(null)
const editServiceModalOpen = ref(false)
const createServiceModalOpen = ref(false)
const deletingService = ref<Service | null>(null)

async function confirmDeleteService() {
  if (!deletingService.value) return
  
  const service = deletingService.value
  
  try {
    if (!accessToken.value) {
      toast.add({
        title: 'Ошибка',
        description: 'Необходима авторизация',
        color: 'error'
      })
      deletingService.value = null
      return
    }

    const token = accessToken.value.startsWith('Bearer ') 
      ? accessToken.value 
      : `Bearer ${accessToken.value}`

    await $fetch(`/api/services/${service.id}`, {
      method: 'DELETE',
      headers: {
        Authorization: token
      }
    })

    toast.add({
      title: 'Услуга удалена',
      description: `Услуга "${service.name}" была удалена`,
      color: 'success'
    })

    // Обновляем список услуг
    await refreshServices()
    
    // Закрываем модальное окно
    deletingService.value = null
  } catch (error: any) {
    toast.add({
      title: 'Ошибка',
      description: error.data?.message || error.message || 'Произошла ошибка при удалении услуги',
      color: 'error'
    })
  }
}

function deleteService(service: Service) {
  deletingService.value = service
}

function authHeader() {
  if (!accessToken.value) return null
  const token = accessToken.value.replace(/^Bearer\s+/i, '')
  return `Bearer ${token}`
}

async function toggleServiceActive(service: Service, active: boolean) {
  if (togglingServiceIds.value.has(service.id)) return

  const previous = service.active !== false
  const nextIds = new Set(togglingServiceIds.value)
  nextIds.add(service.id)
  togglingServiceIds.value = nextIds

  const index = services.value.findIndex(item => item.id === service.id)
  if (index !== -1) {
    services.value[index] = { ...services.value[index], active }
  }

  const authorization = authHeader()
  if (!authorization) {
    if (index !== -1) {
      services.value[index] = { ...services.value[index], active: previous }
    }
    togglingServiceIds.value = new Set([...togglingServiceIds.value].filter(id => id !== service.id))
    return
  }

  try {
    await $fetch(`/api/services/${service.id}`, {
      method: 'PATCH',
      headers: { Authorization: authorization },
      body: { active }
    })
    toast.add({
      title: active ? 'Услуга включена' : 'Услуга отключена',
      description: active
        ? `«${service.name}» снова доступна для записи`
        : `«${service.name}» скрыта из записи до повторного включения`,
      color: 'success'
    })
  } catch (error: any) {
    if (index !== -1) {
      services.value[index] = { ...services.value[index], active: previous }
    }
    toast.add({
      title: 'Ошибка',
      description: error.data?.detail || error.data?.error || error.message || 'Не удалось изменить статус услуги',
      color: 'error'
    })
  } finally {
    togglingServiceIds.value = new Set([...togglingServiceIds.value].filter(id => id !== service.id))
  }
}

function getRowItems(service: Service) {
  return [
    {
      type: 'label',
      label: 'Действия'
    },
    {
      label: 'Редактировать',
      icon: 'i-lucide-edit',
      onSelect: () => {
        editingService.value = service
        editServiceModalOpen.value = true
      }
    },
    {
      type: 'separator'
    },
    {
      label: 'Удалить',
      icon: 'i-lucide-trash',
      color: 'error' as const,
      onSelect: () => {
        deleteService(service)
      }
    }
  ]
}

const columns = computed<TableColumn<Service>[]>(() => [
  {
    accessorKey: 'name',
    header: 'Название',
    cell: ({ row }) => {
      return h('p', { class: 'font-medium text-highlighted' }, row.original.name)
    }
  },
  {
    accessorKey: 'duration',
    header: 'Длительность',
    cell: ({ row }) => {
      return formatDurationMinutes(row.original.duration)
    }
  },
  {
    accessorKey: 'price',
    header: 'Цена',
    cell: ({ row }) => {
      const price = row.original.price
      return price
        ? h('span', { class: 'font-medium' }, `${Math.round(price).toLocaleString('ru-RU')} ₽`)
        : '-'
    }
  },
  {
    accessorKey: 'active',
    header: () => h('span', { class: 'whitespace-nowrap font-medium' }, 'Онлайн-запись'),
    cell: ({ row }) => {
      const service = row.original
      const isActive = service.active !== false
      const isToggling = togglingServiceIds.value.has(service.id)

      return h('div', { class: 'flex items-center gap-2.5' }, [
        h(USwitch, {
          modelValue: isActive,
          color: 'neutral',
          disabled: isToggling,
          'onUpdate:modelValue': (value: boolean) => toggleServiceActive(service, value)
        }),
        h('span', { class: 'text-sm text-muted whitespace-nowrap min-w-[2.25rem]' }, isActive ? 'Вкл' : 'Выкл')
      ])
    }
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
            items: getRowItems(row.original)
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
])
</script>

<template>
  <UDashboardPanel id="services">
    <template #header>
      <UDashboardNavbar title="Услуги">
        <template #leading>
          <div class="hidden"><UDashboardSidebarCollapse /></div>
        </template>

        <template #right>
          <UButton 
            label="Добавить услугу" 
            icon="i-lucide-plus" 
            color="neutral"
            variant="solid"
            class="!bg-gray-900 !text-white hover:!bg-gray-800 dark:!bg-white dark:!text-gray-900 dark:hover:!bg-gray-100"
            @click="createServiceModalOpen = true"
          />
          <ServicesServiceModal
            v-model="editServiceModalOpen"
            :service="editingService || undefined"
            @saved="() => { refreshServices(); editingService = null; editServiceModalOpen = false }"
          />
          <ServicesDeleteServiceModal
            :service="deletingService"
            @confirmed="confirmDeleteService"
            @cancelled="deletingService = null"
          />
        </template>
      </UDashboardNavbar>
    </template>

    <template #body>
      <UTable
        :data="services"
        :columns="columns"
        class="shrink-0"
        :ui="{
          base: 'table-fixed border-separate border-spacing-0',
          thead: '[&>tr]:bg-elevated/50 [&>tr]:after:content-none',
          tbody: '[&>tr]:last:[&>td]:border-b-0',
          th: 'py-2 first:rounded-l-lg last:rounded-r-lg border-y border-default first:border-l last:border-r',
          td: 'border-b border-default',
          separator: 'h-0'
        }"
      />
    </template>
  </UDashboardPanel>

  <!-- Модал создания новой услуги -->
  <ServicesServiceModal
    v-model="createServiceModalOpen"
    @saved="() => { refreshServices(); createServiceModalOpen = false }"
  />
</template>

