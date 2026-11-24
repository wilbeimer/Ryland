import type { CSSProperties } from 'react'
import type { Assignment } from '../api'
import './AssignmentCard.css'

type AssignmentCardProps = {
  assignment: Assignment
  variant: 'text' | 'quiz'
  /** Course label shown next to the color accent (calendar view). */
  courseName?: string
  /** Accent only — left border / chip; never the card fill (AA contrast). */
  courseColor?: string
  onSelect?: (assignment: Assignment) => void
}

export function AssignmentCard({
  assignment,
  variant,
  courseName,
  courseColor,
  onSelect,
}: AssignmentCardProps) {
  const accentStyle = courseColor
    ? ({ '--assignment-course-color': courseColor } as CSSProperties)
    : undefined
  const interactive = typeof onSelect === 'function'

  return (
    <article
      className={
        variant === 'quiz'
          ? 'assignment-card assignment-card--quiz'
          : 'assignment-card assignment-card--text'
      }
      style={accentStyle}
    >
      {courseColor && (
        <div className="assignment-card__course-rule" aria-hidden="true" />
      )}
      {courseName && (
        <p className="assignment-card__course">
          {courseColor && (
            <span
              className="assignment-card__course-swatch"
              style={{ background: courseColor }}
              aria-hidden="true"
            />
          )}
          <span className="assignment-card__course-name">{courseName}</span>
        </p>
      )}
      <h3 className="assignment-card__name">{assignment.name}</h3>
      <div className="assignment-card__description">
        <p className="assignment-card__description-text">
          {assignment.description}
        </p>
      </div>
      {interactive && (
        <button
          type="button"
          className="assignment-card__open"
          aria-label={`Open ${assignment.name}`}
          onClick={() => onSelect(assignment)}
        />
      )}
    </article>
  )
}
