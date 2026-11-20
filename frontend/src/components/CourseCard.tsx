import type { KeyboardEvent } from 'react'
import type { Course } from '../api'
import './CourseCard.css'

type CourseCardProps = {
  course: Course
  index?: number
  onSelect?: (course: Course) => void
}

export function CourseCard({ course, index = 0, onSelect }: CourseCardProps) {
  const interactive = typeof onSelect === 'function'

  return (
    <article
      className={interactive ? 'course-card course-card--interactive' : 'course-card'}
      style={{ animationDelay: `${80 + index * 40}ms` }}
      {...(interactive
        ? {
            role: 'button' as const,
            tabIndex: 0,
            onClick: () => onSelect(course),
            onKeyDown: (event: KeyboardEvent<HTMLElement>) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault()
                onSelect(course)
              }
            },
          }
        : {})}
    >
      <h2 className="course-card__name" title={course.name}>
        {course.name}
      </h2>
      <div className="course-card__rule" aria-hidden="true" />
      <p className="course-card__description">{course.description}</p>
    </article>
  )
}
