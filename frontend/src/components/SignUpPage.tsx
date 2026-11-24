import { useId, useState, type FormEvent } from 'react'
import { ApiError, signUp, type SignUpResult } from '../api'
import './AuthPages.css'

type SignUpPageProps = {
  onSignIn: () => void
}

export function SignUpPage({ onSignIn }: SignUpPageProps) {
  const baseId = useId()
  const usernameId = `${baseId}-username`
  const emailId = `${baseId}-email`
  const passwordId = `${baseId}-password`
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SignUpResult | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const created = await signUp({
        username: username.trim(),
        email: email.trim(),
        password,
      })
      setResult(created)
    } catch (caught) {
      const message =
        caught instanceof ApiError
          ? caught.detail
          : caught instanceof Error
            ? caught.message
            : 'Could not create the account'
      setError(message)
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <h1 className="auth-page__title">Sign up</h1>
      <p className="auth-page__note">
        Email is only used to confirm the account. You will sign in with your
        username.
      </p>
      {result ? (
        <>
          <p className="auth-page__success" role="status">
            {result.delivery === 'logged'
              ? 'Account created. Email is not configured, so the verification link was printed in the API server console.'
              : 'Account created. Check your email for a verification link.'}
          </p>
          <p className="auth-page__switch">
            Already confirmed?{' '}
            <button type="button" className="auth-page__link" onClick={onSignIn}>
              Sign in
            </button>
          </p>
        </>
      ) : (
        <>
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
                minLength={3}
                maxLength={32}
                pattern="[A-Za-z0-9_]{3,32}"
                title="3-32 letters, numbers, or underscores"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
              />
            </div>
            <div className="auth-page__field">
              <label className="auth-page__label" htmlFor={emailId}>
                Email
              </label>
              <input
                id={emailId}
                className="auth-page__input"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
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
                autoComplete="new-password"
                required
                minLength={8}
                maxLength={128}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </div>
            {error && (
              <p className="auth-page__error" role="alert">
                {error}
              </p>
            )}
            <button
              className="auth-page__submit"
              type="submit"
              disabled={submitting}
            >
              {submitting ? 'Creating account…' : 'Create account'}
            </button>
          </form>
          <p className="auth-page__switch">
            Already have an account?{' '}
            <button type="button" className="auth-page__link" onClick={onSignIn}>
              Sign in
            </button>
          </p>
        </>
      )}
    </div>
  )
}
