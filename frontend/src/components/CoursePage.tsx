import { useEffect, useState } from 'react'
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
  }, [course.id])

  return (
    <div className="course-page">
      <h1 className="course-page__title">{course.name}</h1>

      <div className="course-page__weeks">
        {state.status === 'loading' && (
          <p className="course-page__status" role="status">
            Loading weeks…
          </p>
        )}

        {state.status === 'error' && (
          <p className="course-page__status course-page__status--error" role="alert">
            {state.message}
          </p>
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
