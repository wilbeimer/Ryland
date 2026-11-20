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

describe('CoursePage delete', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('opens a confirm dialog and Cancel leaves the course intact', async () => {
    const onDeleted = vi.fn()
    let deleteCalls = 0

    mockApi([
      (url) =>
        url.pathname === `/api/courses/${COURSE.id}/weeks`
          ? {
              body: [
                { id: 'week-1', week_number: 1, description: 'Foundations' },
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
          init?.method === 'DELETE'
        ) {
          deleteCalls += 1
          return { empty: true, status: 204 }
        }
        return null
      },
    ])

    const user = userEvent.setup()
    render(<CoursePage course={COURSE} onDeleted={onDeleted} />)

    expect(
      await screen.findByRole('heading', { level: 2, name: 'Week 1' }),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Delete course' }))

    expect(
      screen.getByRole('alertdialog', { name: 'Delete this course?' }),
    ).toBeInTheDocument()

    const deleteButton = screen.getByRole('button', { name: 'Delete course' })
    await user.click(screen.getByRole('button', { name: 'Cancel' }))

    await waitFor(() => {
      expect(
        screen.queryByRole('alertdialog', { name: 'Delete this course?' }),
      ).not.toBeInTheDocument()
    })
    expect(deleteCalls).toBe(0)
    expect(onDeleted).not.toHaveBeenCalled()
    expect(
      screen.getByRole('heading', { level: 1, name: COURSE.name }),
    ).toBeInTheDocument()
    expect(deleteButton).toHaveFocus()
  })

  it('deletes after confirm and notifies the parent', async () => {
    const onDeleted = vi.fn()
    let deleteCalls = 0

    mockApi([
      (url) =>
        url.pathname === `/api/courses/${COURSE.id}/weeks`
          ? { body: [] }
          : null,
      (url, init) => {
        if (
          url.pathname === `/api/courses/${COURSE.id}` &&
          init?.method === 'DELETE'
        ) {
          deleteCalls += 1
          return { empty: true, status: 204 }
        }
        return null
      },
    ])

    const user = userEvent.setup()
    render(<CoursePage course={COURSE} onDeleted={onDeleted} />)

    await screen.findByRole('heading', { level: 1, name: COURSE.name })
    await user.click(screen.getByRole('button', { name: 'Delete course' }))
    await user.click(screen.getByRole('button', { name: 'Delete' }))

    await waitFor(() => {
      expect(onDeleted).toHaveBeenCalledWith(COURSE.id)
    })
    expect(deleteCalls).toBe(1)
  })

  it('shows an error and restores focus when delete fails', async () => {
    const onDeleted = vi.fn()

    mockApi([
      (url) =>
        url.pathname === `/api/courses/${COURSE.id}/weeks`
          ? { body: [] }
          : null,
      (url, init) => {
        if (
          url.pathname === `/api/courses/${COURSE.id}` &&
          init?.method === 'DELETE'
        ) {
          return { status: 500, body: { detail: 'boom' } }
        }
        return null
      },
    ])

    const user = userEvent.setup()
    render(<CoursePage course={COURSE} onDeleted={onDeleted} />)

    await screen.findByRole('heading', { level: 1, name: COURSE.name })
    const deleteButton = screen.getByRole('button', { name: 'Delete course' })
    await user.click(deleteButton)
    await user.click(screen.getByRole('button', { name: 'Delete' }))

    expect(
      await screen.findByRole('alert'),
    ).toHaveTextContent(/Failed to delete course \(500\)/)
    await waitFor(() => {
      expect(
        screen.queryByRole('alertdialog', { name: 'Delete this course?' }),
      ).not.toBeInTheDocument()
    })
    expect(onDeleted).not.toHaveBeenCalled()
    expect(deleteButton).toHaveFocus()
  })
})
