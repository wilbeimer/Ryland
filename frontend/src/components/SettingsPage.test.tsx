import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SettingsPage } from './SettingsPage'

describe('SettingsPage', () => {
  it('renders sections without a generic email notifications toggle', () => {
    render(<SettingsPage theme="dark" onThemeChange={() => {}} />)

    expect(
      screen.getByRole('heading', { name: 'Profile' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Preferences' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Notifications' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Account' }),
    ).toBeInTheDocument()

    expect(
      screen.getByText(
        /your email will only be used for account confirmation and necessary notifications/i,
      ),
    ).toBeInTheDocument()
    const dueReminders = screen.getByRole('checkbox', {
      name: /due date reminders \(coming soon\)/i,
    })
    expect(dueReminders).toBeInTheDocument()
    expect(dueReminders).toBeDisabled()
    expect(
      screen.queryByRole('checkbox', { name: 'Email notifications' }),
    ).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Email')).not.toBeInTheDocument()
  })
})
