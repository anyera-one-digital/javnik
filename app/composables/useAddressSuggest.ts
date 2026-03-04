interface AddressSuggestion {
  address: string
  title: string
  uri?: string
}

export const useAddressSuggest = () => {
  const { getAuthHeaders } = useAuth()

  const suggestions = ref<AddressSuggestion[]>([])
  const loading = ref(false)
  const isOpen = ref(false)
  const suppressNextSearch = ref(false)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null

  const fetchSuggestions = async (query: string) => {
    if (suppressNextSearch.value) {
      suppressNextSearch.value = false
      return
    }
    if (!query || query.trim().length < 2) {
      suggestions.value = []
      isOpen.value = false
      return
    }
    loading.value = true
    try {
      const data = await $fetch<{ results: AddressSuggestion[] }>('/api/address-suggest', {
        params: { q: query.trim() },
        headers: getAuthHeaders()
      })
      suggestions.value = data.results || []
      isOpen.value = query.trim().length >= 2
    } catch (err) {
      console.error('Address suggest error:', err)
      suggestions.value = []
    } finally {
      loading.value = false
    }
  }

  const search = (query: string) => {
    suppressNextSearch.value = false
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
