import { useId, useState } from 'react'
import {
  persistCalendarView,
  resolveInitialCalendarView,
  type CalendarViewMode,
} from '../calendarView'
import type { Theme } from '../theme'
import './SettingsPage.css'

type SettingsPageProps = {
  theme: Theme
  onThemeChange: (theme: Theme) => void
  username?: string
  onSignOut?: () => void
}

/**
 * Theme and default calendar view persist locally. The signed-in username is
 * shown read-only. Email is not an editable profile field — only confirmation
 * and necessary notifications. Notification toggles remain placeholders.
 */
export function SettingsPage({
  theme,
  onThemeChange,
  username,
  onSignOut,
}: SettingsPageProps) {
  const baseId = useId()
  const nameId = `${baseId}-name`
  const themeId = `${baseId}-theme`
  const calendarViewId = `${baseId}-calendar-view`
  const notificationsHintId = `${baseId}-notifications-hint`

  const [nameDraft, setNameDraft] = useState('')
  const usernameValue = username ?? nameDraft
  const [calendarView, setCalendarView] = useState<CalendarViewMode>(() =>
    resolveInitialCalendarView(),
  )

  function handleCalendarViewChange(next: string) {
    if (next !== 'weeks' && next !== 'month') {
      return
    }
    persistCalendarView(next)
    setCalendarView(next)
  }

  return (
    <div className="settings-page">
      <p className="settings-page__note">
        Profile and notification controls are placeholders and are not saved.
      </p>

      <section
        className="settings-page__section"
        aria-labelledby={`${baseId}-profile`}
      >
        <h2 id={`${baseId}-profile`} className="settings-page__heading">
          Profile
        </h2>
        <div className="settings-page__field">
          <label className="settings-page__label" htmlFor={nameId}>
            Username
          </label>
          <input
            id={nameId}
            className="settings-page__control"
            type="text"
            name="username"
            autoComplete="username"
            placeholder="Not set"
            readOnly={username !== undefined}
            value={usernameValue}
            onChange={(event) => setNameDraft(event.target.value)}
          />
        </div>
        <p className="settings-page__hint">
          Your email will only be used for account confirmation and necessary
          notifications. We don&apos;t keep an inbox or message archive.
        </p>
      </section>

      <section
        className="settings-page__section"
        aria-labelledby={`${baseId}-preferences`}
      >
        <h2 id={`${baseId}-preferences`} className="settings-page__heading">
          Preferences
        </h2>
        <div className="settings-page__field">
          <label className="settings-page__label" htmlFor={themeId}>
            Theme
          </label>
          <select
            id={themeId}
            className="settings-page__control"
            value={theme}
            onChange={(event) => {
              const next = event.target.value
              if (next === 'light' || next === 'dark') {
                onThemeChange(next)
              }
            }}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
        <div className="settings-page__field">
          <label className="settings-page__label" htmlFor={calendarViewId}>
            Default calendar view
          </label>
          <select
            id={calendarViewId}
            className="settings-page__control"
            value={calendarView}
            onChange={(event) => handleCalendarViewChange(event.target.value)}
          >
            <option value="weeks">Weeks</option>
            <option value="month">Month</option>
          </select>
        </div>
      </section>

      <section
        className="settings-page__section"
        aria-labelledby={`${baseId}-notifications`}
      >
        <h2 id={`${baseId}-notifications`} className="settings-page__heading">
          Notifications
        </h2>
        <p id={notificationsHintId} className="settings-page__hint">
          Only necessary course reminders. No general email marketing or inbox.
        </p>
        <label className="settings-page__check">
          <input
            type="checkbox"
            checked={false}
            disabled
            aria-describedby={notificationsHintId}
          />
          Due date reminders (coming soon)
        </label>
      </section>

      <section
        className="settings-page__section"
        aria-labelledby={`${baseId}-account`}
      >
        <h2 id={`${baseId}-account`} className="settings-page__heading">
          Account
        </h2>
        <p className="settings-page__hint">
          {onSignOut
            ? 'Sign out of this account on this browser.'
            : 'Sign-out is not available yet.'}
        </p>
        <button
          type="button"
          className="settings-page__button"
          disabled={!onSignOut}
          onClick={onSignOut}
        >
          Sign out
        </button>
      </section>
    </div>
  )
}
