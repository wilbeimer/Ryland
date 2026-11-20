import { useEffect, useRef, useState } from 'react'
import { fetchWeeks, type Course, type Week } from '../api'
import { WeekWidget } from './WeekWidget'
import './CoursePage.css'

type CoursePageProps = {
  course: Course
}

type WeeksState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; weeks: Week[] }

export function CoursePage({ course }: CoursePageProps) {
  const [state, setState] = useState<WeeksState>({ status: 'loading' })
  const [retryToken, setRetryToken] = useState(0)
  const titleRef = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    titleRef.current?.focus()
  }, [course.id])

  useEffect(() => {
    let cancelled = false

    fetchWeeks(course.id)
      .then((weeks) => {
        if (!cancelled) {
          setState({ status: 'ready', weeks })
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : 'Failed to load weeks'
          setState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [course.id, retryToken])

  return (
    <div className="course-page">
      <h1
        ref={titleRef}
        className="course-page__title"
        tabIndex={-1}
      >
        {course.name}
      </h1>

      <div className="course-page__weeks">
        {state.status === 'loading' && (
          <p className="course-page__status" role="status">
            Loading weeks…
          </p>
        )}

        {state.status === 'error' && (
          <div className="course-page__error" role="alert">
            <p className="course-page__status course-page__status--error">
              {state.message}
            </p>
            <button
              type="button"
              className="course-page__retry"
              onClick={() => {
                setState({ status: 'loading' })
                setRetryToken((token) => token + 1)
              }}
            >
              Retry
            </button>
          </div>
        )}

        {state.status === 'ready' && state.weeks.length === 0 && (
          <p className="course-page__status">No weeks in this course yet.</p>
        )}

        {state.status === 'ready' &&
          state.weeks.map((week, index) => (
            <WeekWidget key={week.id} week={week} index={index} />
          ))}
      </div>
    </div>
  )
}
