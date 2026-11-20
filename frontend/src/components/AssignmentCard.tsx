import type { Assignment } from '../api'
import './AssignmentCard.css'

type AssignmentCardProps = {
  assignment: Assignment
  variant: 'text' | 'quiz'
}

export function AssignmentCard({ assignment, variant }: AssignmentCardProps) {
  return (
    <article
      className={
        variant === 'quiz'
          ? 'assignment-card assignment-card--quiz'
          : 'assignment-card assignment-card--text'
      }
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
