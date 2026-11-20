import { useEffect, useState } from 'react'
import { fetchAssignments, type Assignment, type Week } from '../api'
import { AssignmentCard } from './AssignmentCard'
import './WeekWidget.css'

type WeekWidgetProps = {
  week: Week
  index?: number
}

function formatWeekRange(startDate: string, endDate: string): string {
  const start = new Date(`${startDate}T00:00:00`)
  const end = new Date(`${endDate}T00:00:00`)
  const sameMonth =
    start.getFullYear() === end.getFullYear() &&
    start.getMonth() === end.getMonth()
  const startLabel = start.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  })
  const endLabel = end.toLocaleDateString(undefined, {
    month: sameMonth ? undefined : 'short',
    day: 'numeric',
    year: 'numeric',
  })
  return `${startLabel} – ${endLabel}`
}

type ItemsState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; items: Assignment[] }

export function WeekWidget({ week, index = 0 }: WeekWidgetProps) {
  const [state, setState] = useState<ItemsState>({ status: 'loading' })
  const [retryToken, setRetryToken] = useState(0)

  useEffect(() => {
    let cancelled = false

    fetchAssignments(week.id)
      .then((items) => {
        if (!cancelled) {
          setState({ status: 'ready', items })
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error
              ? error.message
              : 'Failed to load assignments'
          setState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [week.id, retryToken])

  return (
    <section
      className="week-widget"
      style={{ animationDelay: `${120 + index * 80}ms` }}
      aria-labelledby={`week-${week.id}-label`}
    >
      <h2 id={`week-${week.id}-label`} className="week-widget__label">
        Week {week.week_number}
      </h2>
      <p className="week-widget__dates">
        {formatWeekRange(week.start_date, week.end_date)}
      </p>

      {state.status === 'loading' && (
        <p className="week-widget__status" role="status">
          Loading…
        </p>
      )}

      {state.status === 'error' && (
        <div className="week-widget__error" role="alert">
          <p className="week-widget__status week-widget__status--error">
            {state.message}
          </p>
          <button
            type="button"
            className="week-widget__retry"
            onClick={() => {
              setState({ status: 'loading' })
              setRetryToken((token) => token + 1)
            }}
          >
            Retry
          </button>
        </div>
      )}

      {state.status === 'ready' && state.items.length === 0 && (
        <p className="week-widget__status">No assignments this week.</p>
      )}

      {state.status === 'ready' &&
        state.items.map((item) => (
          <AssignmentCard
            key={item.id}
            assignment={item}
            variant={item.type === 'quiz' ? 'quiz' : 'text'}
          />
        ))}
    </section>
  )
}
