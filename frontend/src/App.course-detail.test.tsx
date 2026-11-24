import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { mockApi } from './test/mockFetch'

const COURSE = {
  id: 'course-1',
  name: 'Intro to Algorithms',
  description: 'Sorting and graphs.',
  color: '#e5446d',
  start_date: '2026-01-05',
}

const WEEK = {
  id: 'week-1',
  week_number: 1,
  description: 'Foundations',
  start_date: '2026-01-05',
  end_date: '2026-01-11',
}

const ASSIGNMENTS = [
  {
    id: 'asg-1',
    type: 'text',
    name: 'Big-O Warmup',
    description: 'Explain linear search cases.',
    rubric: { clarity: 5 },
    due_date: '2026-01-07T00:00:00Z',
  },
  {
    id: 'asg-2',
    type: 'quiz',
    name: 'Complexity Check',
    description: 'Asymptotic notation quiz.',
    rubric: { score: 10 },
    due_date: '2026-01-09T00:00:00Z',
  },
]

const AUTH_USER = {
  id: '00000000-0000-0000-0000-000000000001',
  username: 'test',
  email: 'test@mail.com',
  email_verified: true,
}

function installHappyPathMocks() {
  mockApi([
    (url) =>
      url.pathname === '/api/auth/me' ? { body: AUTH_USER } : null,
    (url) =>
      url.pathname === '/api/courses'
        ? { body: [COURSE] }
        : null,
    (url) =>
      url.pathname === `/api/courses/${COURSE.id}/weeks`
        ? { body: [WEEK] }
        : null,
    (url) =>
      url.pathname === `/api/weeks/${WEEK.id}/assignments`
        ? { body: ASSIGNMENTS }
        : null,
  ])
}

describe('course detail', () => {
  beforeEach(() => {
    localStorage.setItem('ryland-auth-token', 'test-token')
    window.history.replaceState({}, '', '/')
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    })
  })

  afterEach(() => {
    localStorage.removeItem('ryland-auth-token')
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('opens a course and renders week assignment and quiz widgets in API order', async () => {
    installHappyPathMocks()
    const user = userEvent.setup()
    render(<App />)

    const openButton = await screen.findByRole('button', {
      name: COURSE.name,
    })
    expect(openButton).toHaveAttribute('title', COURSE.name)

    await user.click(openButton)

    expect(
      await screen.findByRole('heading', { level: 1, name: COURSE.name }),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 2, name: 'Week 1' })).toBeInTheDocument()

    const week = screen.getByRole('heading', { level: 2, name: 'Week 1' })
      .closest('section')
    expect(week).not.toBeNull()
    const cards = within(week as HTMLElement).getAllByRole('heading', {
      level: 3,
    })
    expect(cards.map((node) => node.textContent)).toEqual([
      'Big-O Warmup',
      'Complexity Check',
    ])
    expect(week?.querySelector('.assignment-card--text')).not.toBeNull()
    expect(week?.querySelector('.assignment-card--quiz')).not.toBeNull()
  })

  it('moves focus to the course title on open and back to the card on return', async () => {
    installHappyPathMocks()
    const user = userEvent.setup()
    render(<App />)

    const openButton = await screen.findByRole('button', {
      name: COURSE.name,
    })
    await user.click(openButton)

    const title = await screen.findByRole('heading', {
      level: 1,
      name: COURSE.name,
    })
    await waitFor(() => {
      expect(title).toHaveFocus()
    })

    await user.click(screen.getByRole('button', { name: 'Courses' }))

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: COURSE.name }),
      ).toHaveFocus()
    })
  })
})
