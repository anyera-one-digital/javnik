export type ThemeMode = 'light' | 'dark'

/** Inline head script: применяет тему до первой отрисовки (без FOUC). */
export const YAVNIK_THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem('yavnik-theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'}var d=document.documentElement;d.classList.add('yavnik-landing');d.dataset.theme=t;d.style.colorScheme=t;var m=document.querySelector('meta[name="theme-color"]');if(m)m.setAttribute('content',t==='dark'?'#0d0d10':'#f7f7f4')}catch(e){}})();`

export function useYavnikTheme() {
  const theme = useState<ThemeMode>('yavnik-theme', () => 'light')

  const applyTheme = (next: ThemeMode) => {
    theme.value = next
    if (import.meta.client) {
      document.documentElement.classList.add('yavnik-landing')
      document.documentElement.dataset.theme = next
      document.documentElement.style.colorScheme = next
      localStorage.setItem('yavnik-theme', next)
      const meta = document.querySelector('meta[name="theme-color"]')
      if (meta) {
        meta.setAttribute('content', next === 'dark' ? '#0d0d10' : '#f7f7f4')
      }
    }
  }

  const initTheme = () => {
    if (!import.meta.client) return
    const fromDom = document.documentElement.dataset.theme
    const stored = localStorage.getItem('yavnik-theme') as ThemeMode | null
    const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    const resolved
      = (fromDom === 'light' || fromDom === 'dark' ? fromDom : null)
        ?? stored
        ?? preferred
    applyTheme(resolved)
  }

  const toggleTheme = () => applyTheme(theme.value === 'light' ? 'dark' : 'light')

  return { theme, applyTheme, initTheme, toggleTheme }
}
