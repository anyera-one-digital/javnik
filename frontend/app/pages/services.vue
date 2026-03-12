<script setup lang="ts">
import type { TableColumn } from '@nuxt/ui'
import type { Service, Member } from '~/types'
import { h, resolveComponent } from 'vue'
import ServicesServiceModal from '~/components/UserPersonalAccount/services/ServiceModal.vue'
import ServicesDeleteServiceModal from '~/components/UserPersonalAccount/services/DeleteServiceModal.vue'

definePageMeta({
  layout: 'dashboard',
  middleware: 'auth'
})

const UBadge = resolveComponent('UBadge')
const UButton = resolveComponent('UButton')
const UDropdownMenu = resolveComponent('UDropdownMenu')
const UCheckbox = resolveComponent('UCheckbox')

const toast = useToast()
const { accessToken } = useAuth()

// Используем $fetch для запросов с токеном авторизации
const services = ref<Service[]>([])
const members = ref<Member[]>([])

async function loadServices() {
  if (!accessToken.value) {
    console.warn('No access token available for loading services')
    return
  }
  
  try {
    // Убеждаемся, что токен не содержит двойной Bearer
    let token = accessToken.value
    if (token) {
      // Убираем Bearer если он уже есть
      token = token.replace(/^Bearer\s+/i, '')
      // Добавляем Bearer один раз
      token = `Bearer ${token}`
    }
    
    console.log('Loading services with token:', token ? token.substring(0, 30) + '...' : 'No token')
    
    const response = await $fetch<any>('/api/services', {
      headers: {
        Authorization: token
      }
    })
    
    // Убеждаемся, что response - это массив
    let servicesArray: Service[] = []
    if (Array.isArray(response)) {
      servicesArray = response
    } else if (response && typeof response === 'object' && 'results' in response) {
      // Если это пагинированный ответ Django REST Framework
      servicesArray = response.results || []
    }
    
    console.log('Services loaded successfully:', servicesArray)
    console.log('Services count:', servicesArray.length)
    console.log('Response type:', Array.isArray(response) ? 'array' : typeof response)
    
    services.value = servicesArray
  } catch (error: any) {
    console.error('Error loading services:', error)
    console.error('Error status:', error.statusCode || error.status)
    console.error('Error details:', error.data)
    console.error('Error details (stringified):', JSON.stringify(error.data, null, 2))
    console.error('Error response:', error.response)
    console.error('Error response data:', error.response?.data)
    console.error('Error message:', error.message)
    console.error('Full error:', JSON.stringify(error, Object.getOwnPropertyNames(error), 2))
    
    // Проверяем разные типы ошибок
    const statusCode = error.statusCode || error.status || 500
    
    if (statusCode === 401) {
      toast.add({
        title: 'Ошибка авторизации',
        description: 'Токен авторизации истек или недействителен. Пожалуйста, войдите в систему заново.',
        color: 'error'
      })
      // Перенаправляем на страницу входа
      await navigateTo('/login')
      } else if (statusCode === 400) {
      let errorMessage = 'Неверный формат запроса'
      
      // Пытаемся извлечь детали ошибки
      const errorData = error.data || error.response?.data
      
      console.log('Full error object:', error)
      console.log('Error data:', errorData)
      console.log('Error data (stringified):', JSON.stringify(errorData, null, 2))
      console.log('Error data type:', typeof errorData)
      console.log('Error data keys:', errorData ? Object.keys(errorData) : 'no keys')
      
      if (errorData) {
        if (typeof errorData === 'object') {
          // Проверяем различные поля ошибки
          if (errorData.detail) {
            errorMessage = String(errorData.detail)
          } else if (errorData.message) {
            errorMessage = String(errorData.message)
          } else if (errorData.error) {
            errorMessage = String(errorData.error)
          } else {
            // Показываем все поля объекта для отладки
            const errorFields = Object.keys(errorData).map(key => {
              const value = errorData[key]
              return `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`
            }).join('\n')
            errorMessage = errorFields || JSON.stringify(errorData, null, 2)
          }
        } else if (typeof errorData === 'string') {
          errorMessage = errorData
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      toast.add({
        title: 'Ошибка запроса (400)',
        description: errorMessage,
        color: 'error',
        timeout: 15000
      })
      
      // Также выводим в консоль для отладки
      console.error('400 Bad Request details:', {
        error: JSON.stringify(error, Object.getOwnPropertyNames(error), 2),
        errorData: JSON.stringify(errorData, null, 2),
        errorMessage,
        errorKeys: errorData ? Object.keys(errorData) : []
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

async function loadMembers() {
  if (!accessToken.value) return
  
  try {
    const token = accessToken.value.startsWith('Bearer ') 
      ? accessToken.value 
      : `Bearer ${accessToken.value}`
    
    members.value = await $fetch<Member[]>('/api/members', {
      headers: {
        Authorization: token
      }
    })
  } catch (error: any) {
    console.error('Error loading members:', error)
    if (error.statusCode === 401) {
      console.warn('Unauthorized when loading members')
    }
    members.value = []
  }
}

// Загружаем данные при монтировании и при изменении токена
onMounted(async () => {
  // Убеждаемся, что токен загружен из localStorage
  if (process.client && !accessToken.value) {
    const storedToken = localStorage.getItem('auth.accessToken')
    if (storedToken) {
      accessToken.value = storedToken
    }
  }
  
  if (accessToken.value) {
    await Promise.all([loadServices(), loadMembers()])
  }
})

watch(accessToken, async (token) => {
  if (token) {
    await Promise.all([loadServices(), loadMembers()])
  }
})

async function refreshServices() {
  console.log('Refreshing services list...')
  await loadServices()
  console.log('Services list refreshed, count:', services.value.length)
}

function getMemberName(memberId: number): string {
  const index = memberId - 1
  return members.value[index]?.name || `Сотрудник #${memberId}`
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

    await $fetch(`/api/services/${service.id}/`, {
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

const columns: TableColumn<Service>[] = [
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
      const duration = row.original.duration
      return duration ? `${duration} мин` : '-'
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
]
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

