interface AddressSuggestion {
  address: string
  title: string
  uri?: string
  lat?: number | null
  lon?: number | null
}

export const useAddressSuggest = () => {
  const { getAuthHeaders } = useAuth()

  const suggestions = ref<AddressSuggestion[]>([])
  const loading = ref(false)
  const isOpen = ref(false)
  const suppressNextSearch = ref(false)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  let requestId = 0

  const fetchSuggestions = async (query: string) => {
    if (suppressNextSearch.value) {
      suppressNextSearch.value = false
      return
    }
    const q = query.trim()
    if (q.length < 2) {
      suggestions.value = []
      isOpen.value = false
      return
    }

    const headers = getAuthHeaders()
    if (!headers.Authorization) {
      suggestions.value = []
      isOpen.value = false
      return
    }

    const currentRequest = ++requestId
    loading.value = true
    isOpen.value = true
    try {
      // Nginx проксирует /api/* на Django — вызываем бэкенд напрямую.
      const data = await $fetch<{ results: AddressSuggestion[] }>('/api/auth/address-suggest/', {
        params: { q },
        headers: headers as HeadersInit
      })
      if (currentRequest !== requestId) return
      suggestions.value = Array.isArray(data?.results) ? data.results : []
      isOpen.value = true
    } catch (err) {
      if (currentRequest !== requestId) return
      console.error('Address suggest error:', err)
      suggestions.value = []
      isOpen.value = true
    } finally {
      if (currentRequest === requestId) {
        loading.value = false
      }
    }
  }

  const search = (query: string) => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      fetchSuggestions(query)
    }, 300)
  }

  const select = (item: AddressSuggestion) => {
    suppressNextSearch.value = true
    isOpen.value = false
    return item.address
  }

  const close = () => {
    isOpen.value = false
  }

  return { suggestions, loading, isOpen, search, select, close }
}
