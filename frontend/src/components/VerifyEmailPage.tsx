import { useEffect, useState } from 'react'
import { ApiError, verifyEmail } from '../api'
import './AuthPages.css'

type VerifyEmailPageProps = {
  onSignIn: () => void
}

type VerifyState =
  | { status: 'working' }
  | { status: 'done' }
  | { status: 'error'; message: string }

function readVerifyToken(): string | null {
  try {
    return new URLSearchParams(window.location.search).get('token')
  } catch {
    return null
  }
}

export function VerifyEmailPage({ onSignIn }: VerifyEmailPageProps) {
  const [state, setState] = useState<VerifyState>(() =>
    readVerifyToken()
      ? { status: 'working' }
      : {
          status: 'error',
          message: 'This verification link is missing a token.',
        },
  )

  useEffect(() => {
    const token = readVerifyToken()
    if (!token) {
      return
    }

    let cancelled = false
    verifyEmail(token)
      .then(() => {
        if (!cancelled) {
          setState({ status: 'done' })
        }
      })
      .catch((caught: unknown) => {
        if (cancelled) {
          return
        }
        const message =
          caught instanceof ApiError
            ? caught.detail
            : caught instanceof Error
              ? caught.message
              : 'Could not verify this email'
        setState({ status: 'error', message })
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="auth-page">
      <h1 className="auth-page__title">Verify email</h1>
      {state.status === 'working' && (
        <p className="auth-page__note" role="status">
          Confirming your email…
        </p>
      )}
      {state.status === 'done' && (
        <p className="auth-page__success" role="status">
          Email confirmed. You can sign in with your username and password.
        </p>
      )}
      {state.status === 'error' && (
        <p className="auth-page__error" role="alert">
          {state.message}
        </p>
      )}
      {state.status !== 'working' && (
        <p className="auth-page__switch">
          <button type="button" className="auth-page__link" onClick={onSignIn}>
            Sign in
          </button>
        </p>
      )}
    </div>
  )
}
