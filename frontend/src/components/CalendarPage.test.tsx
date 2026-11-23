import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CalendarPage } from './CalendarPage'
import { mockApi } from '../test/mockFetch'

describe('CalendarPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('renders coursework grouped by calendar week with course color', async () => {
    mockApi([
      (url) =>
        url.pathname === '/api/calendar/weeks'
          ? {
              body: [
                {
                  start_date: '2026-03-02',
                  end_date: '2026-03-08',
                  assignments: [
                    {
                      id: 'a1',
                      type: 'text',
                      name: 'Alg essay',
                      description: 'Write',
                      rubric: {},
                      due_date: '2026-03-04T23:59:00-05:00',
                      course_id: 'c1',
                      course_name: 'Algebra',
                      course_color: '#e5446d',
                    },
                    {
                      id: 'a2',
                      type: 'quiz',
                      name: 'Bio quiz',
                      description: 'Quiz',
                      rubric: {},
                      due_date: '2026-03-05T03:00:00+00:00',
                      course_id: 'c2',
                      course_name: 'Biology',
                      course_color: '#0d7377',
                    },
                  ],
                },
              ],
            }
          : null,
    ])

    render(<CalendarPage />)

    expect(await screen.findByText('Alg essay')).toBeInTheDocument()
    expect(screen.getByText('Bio quiz')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Week of/ })).toBeInTheDocument()

    const alg = screen.getByText('Alg essay').closest('article')
    const bio = screen.getByText('Bio quiz').closest('article')
    expect(alg).toHaveStyle({ background: '#e5446d' })
    expect(bio).toHaveStyle({ background: '#0d7377' })
  })
})
