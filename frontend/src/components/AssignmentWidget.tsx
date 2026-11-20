import type { Assignment } from '../api'
import './AssignmentWidget.css'

type AssignmentWidgetProps = {
  assignment: Assignment
}

export function AssignmentWidget({ assignment }: AssignmentWidgetProps) {
  return (
    <article className="assignment-widget">
      <h3 className="assignment-widget__name">{assignment.name}</h3>
      <div className="assignment-widget__description">
        <p className="assignment-widget__description-text">
          {assignment.description}
        </p>
      </div>
    </article>
  )
}
