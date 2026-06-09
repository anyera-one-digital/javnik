import type { UserSubscription } from '~/types'

export function useSubscription() {
  const { user, fetchProfile } = useAuth()

  const subscription = computed<UserSubscription | null>(
    () => user.value?.subscription ?? null
  )

  const hasProAccess = computed(
    () => subscription.value?.effectivePlan === 'pro'
  )

  async function ensureSubscription() {
    if (!user.value?.subscription) {
      await fetchProfile()
    }
  }

  return {
    subscription,
    hasProAccess,
    ensureSubscription
  }
}
