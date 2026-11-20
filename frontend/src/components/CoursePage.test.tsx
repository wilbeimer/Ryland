import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CoursePage } from './CoursePage'
import { mockApi } from '../test/mockFetch'

const COURSE = {
  id: 'course-1',
  name: 'Intro to Algorithms',
  description: 'Sorting and graphs.',
}

describe('CoursePage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('shows an error message and Retry reloads weeks', async () => {
    let attempts = 0
    mockApi([
      (url) => {
        if (url.pathname !== `/api/courses/${COURSE.id}/weeks`) {
          return null
        }
        attempts += 1
        if (attempts === 1) {
          return { status: 500, body: { detail: 'boom' } }
        }
        return {
          body: [
            { id: 'week-1', week_number: 1, description: 'Foundations' },
          ],
        }
      },
      (url) =>
        url.pathname === '/api/weeks/week-1/assignments'
          ? { body: [] }
          : null,
    ])

    const user = userEvent.setup()
    render(<CoursePage course={COURSE} />)

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent(/Failed to load weeks \(500\)/)

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { level: 2, name: 'Week 1' }),
      ).toBeInTheDocument()
    })
    expect(attempts).toBe(2)
  })
})
