export type Theme = 'dark' | 'light'

const STORAGE_KEY = 'ryland-theme'

export function getStoredTheme(): Theme | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    if (value === 'dark' || value === 'light') {
      return value
    }
  } catch {
    // localStorage may be unavailable
  }
  return null
}

export function resolveInitialTheme(): Theme {
  return getStoredTheme() ?? 'dark'
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Preference still applies for this session
  }
}
