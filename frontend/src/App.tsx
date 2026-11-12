import { useEffect, useState } from 'react'
import { fetchCourses, type Course } from './api'
import { CourseCard } from './components/CourseCard'
import { NavBar } from './components/NavBar'
import './App.css'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; courses: Course[] }

export default function App() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false

    fetchCourses()
      .then((courses) => {
        if (!cancelled) {
          setState({ status: 'ready', courses })
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message =
            error instanceof Error ? error.message : 'Failed to load courses'
          setState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="home">
      <header className="home__header">
        <NavBar active="Courses" />
        <h1 className="home__title">Courses</h1>
      </header>

      <main className="home__main">
        {state.status === 'loading' && (
          <p className="home__status" role="status">
            Loading courses…
          </p>
        )}

        {state.status === 'error' && (
          <p className="home__status home__status--error" role="alert">
            {state.message}
          </p>
        )}

        {state.status === 'ready' && state.courses.length === 0 && (
          <p className="home__status">No courses yet.</p>
        )}

        {state.status === 'ready' && state.courses.length > 0 && (
          <section className="course-list" aria-label="Course list">
            {state.courses.map((course, index) => (
              <CourseCard key={course.id} course={course} index={index} />
            ))}
          </section>
        )}
      </main>
    </div>
  )
}
