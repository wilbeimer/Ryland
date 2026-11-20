import { useEffect, useRef, useState } from 'react'
import {
  deleteCourse,
  fetchWeeks,
  patchCourseColor,
  type Course,
  type Week,
} from '../api'
import { ConfirmDialog } from './ConfirmDialog'
import { CourseColorPicker } from './CourseColorPicker'
import { WeekWidget } from './WeekWidget'
import './CoursePage.css'

type CoursePageProps = {
  course: Course
  onDeleted?: (courseId: string) => void
  onCourseUpdated?: (course: Course) => void
}

type WeeksState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; weeks: Week[] }

export function CoursePage({
  course,
  onDeleted,
  onCourseUpdated,
}: CoursePageProps) {
  const [state, setState] = useState<WeeksState>({ status: 'loading' })
  const [retryToken, setRetryToken] = useState(0)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [colorBusy, setColorBusy] = useState(false)
  const [colorError, setColorError] = useState<string | null>(null)
  const titleRef = useRef<HTMLHeadingElement>(null)
  const deleteButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    titleRef.current?.focus()
  }, [course.id])

  useEffect(() => {
    if (deleteError) {
      deleteButtonRef.current?.focus()
    }
  }, [deleteError])

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

  async function handleConfirmDelete() {
    setDeleting(true)
    setDeleteError(null)
    try {
      await deleteCourse(course.id)
      setConfirmOpen(false)
      onDeleted?.(course.id)
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : 'Failed to delete course'
      setDeleteError(message)
      setDeleting(false)
      setConfirmOpen(false)
    }
  }

  async function handleColorChange(color: string) {
    if (color.toLowerCase() === course.color.toLowerCase()) {
      return
    }
    setColorBusy(true)
    setColorError(null)
    try {
      const updated = await patchCourseColor(course.id, color)
      onCourseUpdated?.(updated)
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : 'Failed to update course color'
      setColorError(message)
    } finally {
      setColorBusy(false)
    }
  }

  return (
    <div className="course-page">
      <div className="course-page__heading">
        <span
          className="course-page__color-chip"
          style={{ background: course.color }}
          aria-hidden="true"
        />
        <h1 ref={titleRef} className="course-page__title" tabIndex={-1}>
          {course.name}
        </h1>
      </div>

      <CourseColorPicker
        color={course.color}
        disabled={colorBusy}
        onChange={(color) => {
          void handleColorChange(color)
        }}
      />

      {colorError && (
        <p
          className="course-page__status course-page__status--error course-page__color-error"
          role="alert"
        >
          {colorError}
        </p>
      )}

      <button
        ref={deleteButtonRef}
        type="button"
        className="course-page__delete"
        onClick={() => {
          setDeleteError(null)
          setConfirmOpen(true)
        }}
      >
        Delete course
      </button>

      {deleteError && (
        <p
          className="course-page__status course-page__status--error course-page__delete-error"
          role="alert"
        >
          {deleteError}
        </p>
      )}

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

      {confirmOpen && (
        <ConfirmDialog
          title="Delete this course?"
          message={`“${course.name}” and all of its weeks, assignments, and quizzes will be removed. This cannot be undone.`}
          confirmLabel="Delete"
          cancelLabel="Cancel"
          busy={deleting}
          onCancel={() => {
            if (!deleting) {
              setConfirmOpen(false)
              // Native dialog restore can be skipped on React unmount; put focus back.
              queueMicrotask(() => {
                deleteButtonRef.current?.focus()
              })
            }
          }}
          onConfirm={() => {
            void handleConfirmDelete()
          }}
        />
      )}
    </div>
  )
}
