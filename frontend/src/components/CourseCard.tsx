import { forwardRef } from 'react'
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

    return (
      <article
        className={
          interactive ? 'course-card course-card--interactive' : 'course-card'
        }
        style={{ animationDelay: `${80 + index * 40}ms` }}
      >
        {interactive ? (
          <button
            ref={ref}
            type="button"
            className="course-card__open"
            onClick={() => onSelect(course)}
          >
            <h2 className="course-card__name" title={course.name}>
              {course.name}
            </h2>
            <div className="course-card__rule" aria-hidden="true" />
            <p className="course-card__description">{course.description}</p>
          </button>
        ) : (
          <>
            <h2 className="course-card__name" title={course.name}>
              {course.name}
            </h2>
            <div className="course-card__rule" aria-hidden="true" />
            <p className="course-card__description">{course.description}</p>
          </>
        )}
      </article>
    )
  },
)
