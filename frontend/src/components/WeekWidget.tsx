import { useEffect, useState } from 'react'
import { fetchAssignments, type Assignment, type Week } from '../api'
import { AssignmentWidget } from './AssignmentWidget'
import { QuizWidget } from './QuizWidget'
import './WeekWidget.css'

type WeekWidgetProps = {
  week: Week
  index?: number
}

type ItemsState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; items: Assignment[] }

export function WeekWidget({ week, index = 0 }: WeekWidgetProps) {
  const [state, setState] = useState<ItemsState>({ status: 'loading' })

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
  }, [week.id])

  return (
    <section
      className="week-widget"
      style={{ animationDelay: `${120 + index * 80}ms` }}
      aria-labelledby={`week-${week.id}-label`}
    >
      <h2 id={`week-${week.id}-label`} className="week-widget__label">
        Week {week.week_number}
      </h2>

      {state.status === 'loading' && (
        <p className="week-widget__status" role="status">
          Loading…
        </p>
      )}

      {state.status === 'error' && (
        <p className="week-widget__status week-widget__status--error" role="alert">
          {state.message}
        </p>
      )}

      {state.status === 'ready' && state.items.length === 0 && (
        <p className="week-widget__status">No assignments this week.</p>
      )}

      {state.status === 'ready' &&
        state.items.map((item) =>
          item.type === 'quiz' ? (
            <QuizWidget key={item.id} assignment={item} />
          ) : (
            <AssignmentWidget key={item.id} assignment={item} />
          ),
        )}
    </section>
  )
}
