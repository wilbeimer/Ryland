import { useId, useState, type FormEvent } from 'react'
import { ApiError, signIn, type AuthUser } from '../api'
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
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
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
      setError(message)
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
