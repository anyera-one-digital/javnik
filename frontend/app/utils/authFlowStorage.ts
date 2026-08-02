const SIGNUP_FLOW_KEY = 'javnik.signup.flow'
const LOGIN_FLOW_KEY = 'javnik.login.flow'

export interface SignupFlowState {
  step: number
  pendingEmail: string
  email?: string
  first_name?: string
}

export interface LoginFlowState {
  step: number
  pendingEmail: string
}

function readJson<T>(key: string): T | null {
  if (!import.meta.client) return null
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

function writeJson(key: string, value: unknown) {
  if (!import.meta.client) return
  try {
    sessionStorage.setItem(key, JSON.stringify(value))
  } catch {
    // ignore quota / private mode
  }
}

export function readSignupFlow(): SignupFlowState | null {
  return readJson<SignupFlowState>(SIGNUP_FLOW_KEY)
}

export function writeSignupFlow(state: SignupFlowState) {
  writeJson(SIGNUP_FLOW_KEY, state)
}

export function clearSignupFlow() {
  if (!import.meta.client) return
  sessionStorage.removeItem(SIGNUP_FLOW_KEY)
}

export function readLoginFlow(): LoginFlowState | null {
  return readJson<LoginFlowState>(LOGIN_FLOW_KEY)
}

export function writeLoginFlow(state: LoginFlowState) {
  writeJson(LOGIN_FLOW_KEY, state)
}

export function clearLoginFlow() {
  if (!import.meta.client) return
  sessionStorage.removeItem(LOGIN_FLOW_KEY)
}
