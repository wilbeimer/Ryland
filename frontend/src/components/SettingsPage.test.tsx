import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SettingsPage } from './SettingsPage'

describe('SettingsPage', () => {
  it('renders its section headings', () => {
    render(<SettingsPage />)

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
  })
})
