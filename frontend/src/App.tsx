import { useEffect, useRef, useState } from 'react'
import { fetchCourses, type Course } from './api'
import { CourseCard } from './components/CourseCard'
import { GeneratePage } from './components/GeneratePage'
import { NavBar, type NavLabel } from './components/NavBar'
import { ThemeToggle } from './components/ThemeToggle'
import {
  applyTheme,
  persistTheme,
  resolveInitialTheme,
  type Theme,
} from './theme'
import { useGenerationJob } from './useGenerationJob'
import './App.css'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; courses: Course[] }

type View = Extract<NavLabel, 'Courses' | 'Generate'>

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => resolveInitialTheme())
  const [view, setView] = useState<View>('Courses')
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [coursesVersion, setCoursesVersion] = useState(0)
  const userNavigatedRef = useRef(false)

  const {
    phase: generationPhase,
    beginGeneration,
    resumedFromConflict,
  } = useGenerationJob(() => {
    setCoursesVersion((version) => version + 1)
  })

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  useEffect(() => {
    let cancelled = false
    const isInitialLoad = coursesVersion === 0

    fetchCourses()
      .then((courses) => {
        if (cancelled) {
          return
        }
        setState({ status: 'ready', courses })
        // Once we know the list is empty, open Generate so home isn't a dead end —
        // but don't override a tab the user already chose while loading.
        if (
          isInitialLoad &&
          courses.length === 0 &&
          !userNavigatedRef.current
        ) {
          setView('Generate')
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return
        }
        const message =
          error instanceof Error ? error.message : 'Failed to load courses'
        // Initial load: show the error. Later refreshes (e.g. after generate)
        // keep the last good list instead of wiping it.
        setState((prev) =>
          isInitialLoad || prev.status !== 'ready'
            ? { status: 'error', message }
            : prev,
        )
      })

    return () => {
      cancelled = true
    }
  }, [coursesVersion])

  function handleNavigate(label: NavLabel) {
    if (label === 'Courses' || label === 'Generate') {
      userNavigatedRef.current = true
      setView(label)
    }
  }

  function handleThemeToggle() {
    const next = theme === 'dark' ? 'light' : 'dark'
    persistTheme(next)
    setTheme(next)
  }

  return (
    <div className="home">
      <header className="home__header">
        <div className="home__toolbar">
          <ThemeToggle theme={theme} onToggle={handleThemeToggle} />
        </div>
        <NavBar active={view} onNavigate={handleNavigate} />
        {view === 'Courses' && <h1 className="home__title">Courses</h1>}
      </header>

      <main className="home__main">
        {/* Keep Generate mounted so form fields survive tab switches;
            job polling is owned by useGenerationJob above. */}
        <div hidden={view !== 'Generate'}>
          <GeneratePage
            phase={generationPhase}
            onBeginGeneration={beginGeneration}
            resumedFromConflict={resumedFromConflict}
          />
        </div>

        {view === 'Courses' && (
          <>
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
          </>
        )}
      </main>
    </div>
  )
}
