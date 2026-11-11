import type { Course } from '../api'
import './CourseCard.css'

type CourseCardProps = {
  course: Course
  index?: number
}

export function CourseCard({ course, index = 0 }: CourseCardProps) {
  return (
    <article
      className="course-card"
      style={{ animationDelay: `${80 + index * 40}ms` }}
    >
      <h2 className="course-card__name">{course.name}</h2>
      <div className="course-card__rule" aria-hidden="true" />
      <p className="course-card__description">{course.description}</p>
    </article>
  )
}
