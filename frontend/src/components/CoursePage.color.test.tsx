import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CoursePage } from './CoursePage'
import { mockApi } from '../test/mockFetch'

const COURSE = {
  id: 'course-1',
  name: 'Intro to Algorithms',
  description: 'Sorting and graphs.',
  color: '#e5446d',
  start_date: '2026-01-05',
}

describe('CoursePage color and week dates', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('shows week date range and patches course color', async () => {
    const onCourseUpdated = vi.fn()
    let patchedColor: string | null = null

    mockApi([
      (url) =>
        url.pathname === `/api/courses/${COURSE.id}/weeks`
          ? {
              body: [
                {
                  id: 'week-1',
                  week_number: 1,
                  description: 'Foundations',
                  start_date: '2026-01-05',
                  end_date: '2026-01-11',
                },
              ],
            }
          : null,
      (url) =>
        url.pathname === '/api/weeks/week-1/assignments'
          ? { body: [] }
          : null,
      (url, init) => {
        if (
          url.pathname === `/api/courses/${COURSE.id}` &&
          init?.method === 'PATCH'
        ) {
          const body = JSON.parse(String(init.body)) as { color: string }
          patchedColor = body.color
          return {
            body: {
              ...COURSE,
              color: body.color,
            },
          }
        }
        return null
      },
    ])

    const user = userEvent.setup()
    render(
      <CoursePage course={COURSE} onCourseUpdated={onCourseUpdated} />,
    )

    expect(
      await screen.findByText((text) => /Jan/.test(text) && /5/.test(text)),
    ).toBeInTheDocument()

    await user.click(
      screen.getByRole('button', { name: 'Course color Rose' }),
    )
    await user.click(
      screen.getByRole('button', { name: 'Set course color to Teal' }),
    )

    await waitFor(() => {
      expect(patchedColor).toBe('#0d7377')
      expect(onCourseUpdated).toHaveBeenCalledWith(
        expect.objectContaining({ color: '#0d7377' }),
      )
    })
  })
})
