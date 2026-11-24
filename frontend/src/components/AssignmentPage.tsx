import { useEffect, useRef, useState, type CSSProperties } from 'react'
import { fetchAssignment, type CalendarAssignment } from '../api'
import './AssignmentPage.css'

type AssignmentPageProps = {
  assignmentId: string
  onBack: () => void
}

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; assignment: CalendarAssignment }

function formatDueDate(iso: string): string {
  const due = new Date(iso)
  if (Number.isNaN(due.getTime())) {
    return iso
  }
  return due.toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function AssignmentPage({ assignmentId, onBack }: AssignmentPageProps) {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [retryToken, setRetryToken] = useState(0)
  const titleRef = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    let cancelled = false

    fetchAssignment(assignmentId)
      .then((assignment) => {
        if (!cancelled) {
          setState({ status: 'ready', assignment })
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error
              ? error.message
              : 'Failed to load assignment'
          setState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [assignmentId, retryToken])

  useEffect(() => {
    if (state.status === 'ready') {
      titleRef.current?.focus()
    }
  }, [state])

  return (
    <div className="assignment-page">
      <button type="button" className="assignment-page__back" onClick={onBack}>
        Back
      </button>

      {state.status === 'loading' && (
        <p className="assignment-page__status" role="status">
          Loading assignment…
        </p>
      )}

      {state.status === 'error' && (
        <div className="assignment-page__error" role="alert">
          <p className="assignment-page__status assignment-page__status--error">
            {state.message}
          </p>
          <button
            type="button"
            className="assignment-page__retry"
            onClick={() => {
              setState({ status: 'loading' })
              setRetryToken((token) => token + 1)
            }}
          >
            Retry
          </button>
        </div>
      )}

      {state.status === 'ready' && (
        <article
          className="assignment-page__body"
          style={
            {
              '--assignment-course-color': state.assignment.course_color,
            } as CSSProperties
          }
        >
          <p className="assignment-page__course">
            <span
              className="assignment-page__course-swatch"
              aria-hidden="true"
            />
            <span className="assignment-page__course-name">
              {state.assignment.course_name}
            </span>
          </p>
          <h1
            ref={titleRef}
            className="assignment-page__title"
            tabIndex={-1}
          >
            {state.assignment.name}
          </h1>
          <p className="assignment-page__meta">
            <span className="assignment-page__type">
              {state.assignment.type === 'quiz' ? 'Quiz' : 'Assignment'}
            </span>
            <span aria-hidden="true"> · </span>
            <span>
              Due {formatDueDate(state.assignment.due_date)}
            </span>
          </p>
          <div className="assignment-page__description">
            <h2 className="assignment-page__description-label">
              Instructions
            </h2>
            <p className="assignment-page__description-text">
              {state.assignment.description}
            </p>
          </div>
        </article>
      )}
    </div>
  )
}
