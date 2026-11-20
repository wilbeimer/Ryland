import type { Assignment } from '../api'
import './QuizWidget.css'

type QuizWidgetProps = {
  assignment: Assignment
}

export function QuizWidget({ assignment }: QuizWidgetProps) {
  return (
    <article className="quiz-widget">
      <h3 className="quiz-widget__name">{assignment.name}</h3>
      <div className="quiz-widget__description">
        <p className="quiz-widget__description-text">{assignment.description}</p>
      </div>
    </article>
  )
}
