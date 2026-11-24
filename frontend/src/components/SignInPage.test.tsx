import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SignInPage } from './SignInPage'

describe('SignInPage', () => {
  it('asks for a username and password', () => {
    render(<SignInPage onSignedIn={() => {}} onSignUp={() => {}} />)

    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.getByLabelText('Username')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password')
    expect(screen.queryByLabelText('Email')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign up' })).toBeInTheDocument()
  })
})
