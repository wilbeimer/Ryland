import { useEffect, useState } from 'react'
import {
  fetchCalendarWeeks,
  type CalendarAssignment,
  type CalendarWeek,
} from '../api'
import { CalendarMonthView } from './CalendarMonthView'
import { WeekWidget } from './WeekWidget'
import './CalendarPage.css'

type CalendarPageProps = {
  onSelectAssignment?: (assignmentId: string) => void
}

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; weeks: CalendarWeek[] }

type CalendarViewMode = 'weeks' | 'month'

function weekOfLabel(startDate: string): string {
  const start = new Date(`${startDate}T00:00:00`)
  const label = start.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })
  return `Week of ${label}`
}

export function CalendarPage({ onSelectAssignment }: CalendarPageProps) {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [retryToken, setRetryToken] = useState(0)
  const [mode, setMode] = useState<CalendarViewMode>('weeks')

  useEffect(() => {
    let cancelled = false

    fetchCalendarWeeks()
      .then((weeks) => {
        if (!cancelled) {
          setState({ status: 'ready', weeks })
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error
              ? error.message
              : 'Failed to load calendar weeks'
          setState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [retryToken])

  return (
    <div className="calendar-page">
      <div
        className="calendar-page__modes"
        role="group"
        aria-label="Calendar view"
      >
        <button
          type="button"
          className={
            mode === 'weeks'
              ? 'calendar-page__mode calendar-page__mode--active'
              : 'calendar-page__mode'
          }
          aria-pressed={mode === 'weeks'}
          onClick={() => setMode('weeks')}
        >
          Weeks
        </button>
        <button
          type="button"
          className={
            mode === 'month'
              ? 'calendar-page__mode calendar-page__mode--active'
              : 'calendar-page__mode'
          }
          aria-pressed={mode === 'month'}
          onClick={() => setMode('month')}
        >
          Month
        </button>
      </div>

      {state.status === 'loading' && (
        <p className="calendar-page__status" role="status">
          Loading weeks…
        </p>
      )}

      {state.status === 'error' && (
        <div className="calendar-page__error" role="alert">
          <p className="calendar-page__status calendar-page__status--error">
            {state.message}
          </p>
          <button
            type="button"
            className="calendar-page__retry"
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
        <p className="calendar-page__status">No coursework yet.</p>
      )}

      {state.status === 'ready' &&
        state.weeks.length > 0 &&
        mode === 'weeks' && (
          <div className="calendar-page__weeks">
            {state.weeks.map((week, index) => (
              <WeekWidget
                key={week.start_date}
                week={{
                  id: `cal-${week.start_date}`,
                  week_number: index + 1,
                  description: '',
                  start_date: week.start_date,
                  end_date: week.end_date,
                }}
                index={index}
                label={weekOfLabel(week.start_date)}
                items={week.assignments}
                courseNameFor={(assignment) =>
                  (assignment as CalendarAssignment).course_name
                }
                courseColorFor={(assignment) =>
                  (assignment as CalendarAssignment).course_color
                }
                onSelectAssignment={
                  onSelectAssignment
                    ? (assignment) => onSelectAssignment(assignment.id)
                    : undefined
                }
              />
            ))}
          </div>
        )}

      {state.status === 'ready' &&
        state.weeks.length > 0 &&
        mode === 'month' && (
          <CalendarMonthView
            weeks={state.weeks}
            onSelectAssignment={onSelectAssignment}
          />
        )}
    </div>
  )
}
