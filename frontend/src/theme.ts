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

function systemTheme(): Theme {
  if (
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: light)').matches
  ) {
    return 'light'
  }
  return 'dark'
}

export function resolveInitialTheme(): Theme {
  return getStoredTheme() ?? systemTheme()
}

/** Apply theme to the document without persisting. */
export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
}

/** Persist an explicit user choice (call only from the toggle). */
export function persistTheme(theme: Theme): void {
  try {
    localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    // Preference still applies for this session
  }
}
