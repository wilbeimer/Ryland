import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { mockApi } from '../test/mockFetch'
import { AssignmentPage } from './AssignmentPage'

describe('AssignmentPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('shows title, course color, due date, and instructions', async () => {
    mockApi([
      (url) =>
        url.pathname === '/api/assignments/a1'
          ? {
              body: {
                id: 'a1',
                type: 'text',
                name: 'Alg essay',
                description: 'Write a short proof.',
                rubric: {},
                due_date: '2026-03-04T23:59:00-05:00',
                course_id: 'c1',
                course_name: 'Algebra',
                course_color: '#e5446d',
              },
            }
          : null,
    ])

    render(<AssignmentPage assignmentId="a1" onBack={() => undefined} />)

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: 'Alg essay' }),
      ).toBeInTheDocument()
    })
    expect(screen.getByText('Algebra')).toBeInTheDocument()
    expect(screen.getByText('Write a short proof.')).toBeInTheDocument()
    expect(screen.getByText(/Due /)).toBeInTheDocument()
    const body = screen.getByRole('heading', { name: 'Alg essay' }).closest(
      '.assignment-page__body',
    )
    expect(body).toHaveStyle({
      ['--assignment-course-color' as string]: '#e5446d',
    })
  })
})
