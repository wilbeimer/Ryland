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
        /email is for account confirmation and necessary notifications only/i,
      ),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('checkbox', { name: 'Due date reminders' }),
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('checkbox', { name: 'Email notifications' }),
    ).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Email')).not.toBeInTheDocument()
  })
})
