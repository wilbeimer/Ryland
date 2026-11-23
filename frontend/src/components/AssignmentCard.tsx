import type { Assignment } from '../api'
import './AssignmentCard.css'

type AssignmentCardProps = {
  assignment: Assignment
  variant: 'text' | 'quiz'
  /** When set, overrides the default text/quiz accent fill (e.g. course color). */
  accentColor?: string
}

export function AssignmentCard({
  assignment,
  variant,
  accentColor,
}: AssignmentCardProps) {
  return (
    <article
      className={
        variant === 'quiz'
          ? 'assignment-card assignment-card--quiz'
          : 'assignment-card assignment-card--text'
      }
      style={accentColor ? { background: accentColor } : undefined}
    >
      <h3 className="assignment-card__name">{assignment.name}</h3>
      <div className="assignment-card__description">
        <p className="assignment-card__description-text">
          {assignment.description}
        </p>
      </div>
    </article>
  )
}
