import { useId, useState } from 'react'
import type { Theme } from '../theme'
import './SettingsPage.css'

type CalendarViewPreference = 'weeks' | 'month'

type SettingsPageProps = {
  theme: Theme
  onThemeChange: (theme: Theme) => void
}

/**
 * Basic settings layout. Name and email stay empty: there is no current-user
 * endpoint, and the server User row has no name. Theme is the app theme.
 * Other controls hold local state only and are not persisted.
 */
export function SettingsPage({ theme, onThemeChange }: SettingsPageProps) {
  const baseId = useId()
  const nameId = `${baseId}-name`
  const emailId = `${baseId}-email`
  const themeId = `${baseId}-theme`
  const calendarViewId = `${baseId}-calendar-view`

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [calendarView, setCalendarView] =
    useState<CalendarViewPreference>('weeks')
  const [emailNotifications, setEmailNotifications] = useState(false)
  const [dueReminders, setDueReminders] = useState(false)

  return (
    <div className="settings-page">
      <p className="settings-page__note">
        These controls are placeholders and are not saved.
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
            Name
          </label>
          <input
            id={nameId}
            className="settings-page__control"
            type="text"
            name="name"
            autoComplete="name"
            placeholder="Not set"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        <div className="settings-page__field">
          <label className="settings-page__label" htmlFor={emailId}>
            Email
          </label>
          <input
            id={emailId}
            className="settings-page__control"
            type="email"
            name="email"
            autoComplete="email"
            placeholder="Not set"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </div>
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
            onChange={(event) =>
              setCalendarView(event.target.value as CalendarViewPreference)
            }
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
        <label className="settings-page__check">
          <input
            type="checkbox"
            checked={emailNotifications}
            onChange={(event) => setEmailNotifications(event.target.checked)}
          />
          Email notifications
        </label>
        <label className="settings-page__check">
          <input
            type="checkbox"
            checked={dueReminders}
            onChange={(event) => setDueReminders(event.target.checked)}
          />
          Due date reminders
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
          Sign-out is not available yet.
        </p>
        <button type="button" className="settings-page__button" disabled>
          Sign out
        </button>
      </section>
    </div>
  )
}
