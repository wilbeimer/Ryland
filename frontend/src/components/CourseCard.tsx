import { forwardRef, useId } from 'react'
import type { Course } from '../api'
import './CourseCard.css'

type CourseCardProps = {
  course: Course
  index?: number
  onSelect?: (course: Course) => void
}

export const CourseCard = forwardRef<HTMLButtonElement, CourseCardProps>(
  function CourseCard({ course, index = 0, onSelect }, ref) {
    const interactive = typeof onSelect === 'function'
    const nameId = useId()

    return (
      <article
        className={
          interactive ? 'course-card course-card--interactive' : 'course-card'
        }
        style={{ animationDelay: `${80 + index * 40}ms` }}
      >
        <h2 id={nameId} className="course-card__name">
          {course.name}
        </h2>
        <div
          className="course-card__rule"
          aria-hidden="true"
          style={{ background: course.color }}
        />
        <p className="course-card__description">{course.description}</p>
        {interactive && (
          <button
            ref={ref}
            type="button"
            className="course-card__open"
            aria-labelledby={nameId}
            title={course.name}
            onClick={() => onSelect(course)}
          />
        )}
      </article>
    )
  },
)
