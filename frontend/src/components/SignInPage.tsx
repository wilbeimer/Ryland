import { useId, useState, type FormEvent } from 'react'
import { ApiError, resendVerification, signIn, type AuthUser } from '../api'
import './AuthPages.css'

type SignInPageProps = {
  onSignedIn: (user: AuthUser) => void
  onSignUp: () => void
}

export function SignInPage({ onSignedIn, onSignUp }: SignInPageProps) {
  const baseId = useId()
  const usernameId = `${baseId}-username`
  const passwordId = `${baseId}-password`
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [unverified, setUnverified] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    setUnverified(false)
    setSubmitting(true)
    try {
      const user = await signIn(username.trim(), password)
      onSignedIn(user)
    } catch (caught) {
      const message =
        caught instanceof ApiError
          ? caught.detail
          : caught instanceof Error
            ? caught.message
            : 'Could not sign in'
      setUnverified(caught instanceof ApiError && caught.status === 403)
      setError(message)
      setSubmitting(false)
    }
  }

  async function handleResend() {
    setError(null)
    setNotice(null)
    setSubmitting(true)
    try {
      const result = await resendVerification(username.trim(), password)
      setNotice(
        result.delivery === 'logged'
          ? 'A new verification link was printed in the API server console.'
          : 'A new verification link was sent.',
      )
      setUnverified(false)
    } catch (caught) {
      const message =
        caught instanceof ApiError
          ? caught.detail
          : caught instanceof Error
            ? caught.message
            : 'Could not resend the verification email'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <h1 className="auth-page__title">Sign in</h1>
      <p className="auth-page__note">Use your username and password.</p>
      <form className="auth-page__form" onSubmit={handleSubmit}>
        <div className="auth-page__field">
          <label className="auth-page__label" htmlFor={usernameId}>
            Username
          </label>
          <input
            id={usernameId}
            className="auth-page__input"
            name="username"
            type="text"
            autoComplete="username"
            spellCheck={false}
            required
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </div>
        <div className="auth-page__field">
          <label className="auth-page__label" htmlFor={passwordId}>
            Password
          </label>
          <input
            id={passwordId}
            className="auth-page__input"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        {error && (
          <p className="auth-page__error" role="alert">
            {error}
          </p>
        )}
        {notice && (
          <p className="auth-page__success" role="status">
            {notice}
          </p>
        )}
        {unverified && (
          <button
            className="auth-page__link"
            type="button"
            disabled={submitting}
            onClick={() => {
              void handleResend()
            }}
          >
            Resend verification email
          </button>
        )}
        <button className="auth-page__submit" type="submit" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p className="auth-page__switch">
        Need an account?{' '}
        <button type="button" className="auth-page__link" onClick={onSignUp}>
          Sign up
        </button>
      </p>
    </div>
  )
}
