const TOKEN_KEY = 'ryland-auth-token'

export function getAuthToken(): string | null {
  try {
    const value = localStorage.getItem(TOKEN_KEY)
    return value && value.trim() ? value : null
  } catch {
    return null
  }
}

export function setAuthToken(token: string | null): void {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  } catch {
    // localStorage may be unavailable
  }
}
