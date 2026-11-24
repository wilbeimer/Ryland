export type CalendarViewMode = 'weeks' | 'month'

const STORAGE_KEY = 'ryland-calendar-view'

export function getStoredCalendarView(): CalendarViewMode | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    if (value === 'weeks' || value === 'month') {
      return value
    }
  } catch {
    // localStorage may be unavailable
  }
  return null
}

/** Resolution order: localStorage → weeks. */
export function resolveInitialCalendarView(): CalendarViewMode {
  return getStoredCalendarView() ?? 'weeks'
}

/** Persist an explicit user choice (Settings default, or Calendar toggle). */
export function persistCalendarView(mode: CalendarViewMode): void {
  try {
    localStorage.setItem(STORAGE_KEY, mode)
  } catch {
    // Preference still applies for this session when callers also set state
  }
}
