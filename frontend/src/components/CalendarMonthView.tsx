import { useMemo, useState, type CSSProperties } from 'react'
import type { CalendarAssignment, CalendarWeek } from '../api'
import './CalendarMonthView.css'

type CalendarMonthViewProps = {
  weeks: CalendarWeek[]
}

const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function startOfMonth(year: number, month: number): Date {
  return new Date(year, month, 1)
}

function addMonths(
  year: number,
  month: number,
  delta: number,
): { year: number; month: number } {
  const date = new Date(year, month + delta, 1)
  return { year: date.getFullYear(), month: date.getMonth() }
}

function dateKey(year: number, month: number, day: number): string {
  const m = String(month + 1).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  return `${year}-${m}-${d}`
}

/** Local calendar YYYY-MM-DD for a stored due_date instant. */
function dueDateKey(iso: string): string {
  const due = new Date(iso)
  const y = due.getFullYear()
  const m = String(due.getMonth() + 1).padStart(2, '0')
  const d = String(due.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function buildMonthCells(
  year: number,
  month: number,
): Array<{ key: string; day: number | null; inMonth: boolean }> {
  const first = startOfMonth(year, month)
  // Monday=0 … Sunday=6 to match ISO weeks.
  const mondayIndex = (first.getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const cells: Array<{ key: string; day: number | null; inMonth: boolean }> =
    []

  for (let i = 0; i < mondayIndex; i += 1) {
    cells.push({ key: `pad-start-${i}`, day: null, inMonth: false })
  }
  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push({
      key: dateKey(year, month, day),
      day,
      inMonth: true,
    })
  }
  while (cells.length % 7 !== 0) {
    cells.push({
      key: `pad-end-${cells.length}`,
      day: null,
      inMonth: false,
    })
  }
  return cells
}

function initialCursor(weeks: CalendarWeek[]): { year: number; month: number } {
  for (const week of weeks) {
    for (const assignment of week.assignments) {
      const due = new Date(assignment.due_date)
      if (!Number.isNaN(due.getTime())) {
        return { year: due.getFullYear(), month: due.getMonth() }
      }
    }
  }
  const now = new Date()
  return { year: now.getFullYear(), month: now.getMonth() }
}

export function CalendarMonthView({ weeks }: CalendarMonthViewProps) {
  const [cursor, setCursor] = useState(() => initialCursor(weeks))

  const byDay = useMemo(() => {
    const map = new Map<string, CalendarAssignment[]>()
    for (const week of weeks) {
      for (const assignment of week.assignments) {
        const key = dueDateKey(assignment.due_date)
        const list = map.get(key) ?? []
        list.push(assignment)
        map.set(key, list)
      }
    }
    return map
  }, [weeks])

  const cells = buildMonthCells(cursor.year, cursor.month)
  const title = startOfMonth(cursor.year, cursor.month).toLocaleDateString(
    undefined,
    { month: 'long', year: 'numeric' },
  )

  return (
    <div className="calendar-month">
      <div className="calendar-month__toolbar">
        <button
          type="button"
          className="calendar-month__nav"
          aria-label="Previous month"
          onClick={() => setCursor((c) => addMonths(c.year, c.month, -1))}
        >
          Previous
        </button>
        <h2 className="calendar-month__title">{title}</h2>
        <button
          type="button"
          className="calendar-month__nav"
          aria-label="Next month"
          onClick={() => setCursor((c) => addMonths(c.year, c.month, 1))}
        >
          Next
        </button>
      </div>

      <div className="calendar-month__weekdays" aria-hidden="true">
        {WEEKDAY_LABELS.map((label) => (
          <div key={label} className="calendar-month__weekday">
            {label}
          </div>
        ))}
      </div>

      <div className="calendar-month__grid" role="grid" aria-label={title}>
        {cells.map((cell) => {
          const items =
            cell.inMonth && cell.day !== null
              ? (byDay.get(dateKey(cursor.year, cursor.month, cell.day)) ?? [])
              : []
          return (
            <div
              key={cell.key}
              className={
                cell.inMonth
                  ? 'calendar-month__cell'
                  : 'calendar-month__cell calendar-month__cell--muted'
              }
              role="gridcell"
            >
              {cell.day !== null && (
                <span className="calendar-month__day">{cell.day}</span>
              )}
              <ul className="calendar-month__items">
                {items.map((item) => (
                  <li key={item.id}>
                    <div
                      className="calendar-month__item"
                      style={
                        {
                          '--assignment-course-color': item.course_color,
                        } as CSSProperties
                      }
                      title={`${item.course_name}: ${item.name}`}
                    >
                      <span
                        className="calendar-month__item-swatch"
                        aria-hidden="true"
                      />
                      <span className="calendar-month__item-text">
                        <span className="calendar-month__item-course">
                          {item.course_name}
                        </span>
                        <span className="calendar-month__item-name">
                          {item.name}
                        </span>
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )
        })}
      </div>
    </div>
  )
}
