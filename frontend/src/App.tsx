import { useEffect, useRef, useState } from 'react'
import { fetchCourses, type Course } from './api'
import { CourseCard } from './components/CourseCard'
import { CoursePage } from './components/CoursePage'
import { GeneratePage } from './components/GeneratePage'
import { NavBar, type NavLabel } from './components/NavBar'
import { ThemeToggle } from './components/ThemeToggle'
import {
  applyTheme,
  persistTheme,
  resolveInitialTheme,
  type Theme,
} from './theme'
import './App.css'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; courses: Course[] }

/** Tab / detail selection. Course detail is also mirrored in `?course=<id>`. */
type View =
  | { kind: 'courses' }
  | { kind: 'generate' }
  | { kind: 'course'; course: Course }

function readCourseIdFromUrl(): string | null {
  try {
    return new URLSearchParams(window.location.search).get('course')
  } catch {
    return null
  }
}

function writeCourseIdToUrl(courseId: string | null): void {
  const url = new URL(window.location.href)
  if (courseId) {
    url.searchParams.set('course', courseId)
  } else {
    url.searchParams.delete('course')
  }
  const next = `${url.pathname}${url.search}${url.hash}`
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
  if (next !== current) {
    window.history.pushState({ courseId }, '', next)
  }
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => resolveInitialTheme())
  const [view, setView] = useState<View>({ kind: 'courses' })
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const userNavigatedRef = useRef(false)
  /** Course id to restore keyboard focus to after leaving detail. */
  const restoreFocusCourseIdRef = useRef<string | null>(null)
  const courseButtonRefs = useRef(new Map<string, HTMLButtonElement>())

  useEffect(() => {
    applyTheme(theme)
  }, [theme])

  useEffect(() => {
    let cancelled = false

    fetchCourses()
      .then((courses) => {
        if (cancelled) {
          return
        }
        setState({ status: 'ready', courses })

        const courseId = readCourseIdFromUrl()
        if (courseId) {
          const match = courses.find((course) => course.id === courseId)
          if (match) {
            setView({ kind: 'course', course: match })
            return
          }
          writeCourseIdToUrl(null)
        }

        // Once we know the list is empty, open Generate so home isn't a dead end —
        // but don't override a tab the user already chose while loading.
        if (courses.length === 0 && !userNavigatedRef.current) {
          setView({ kind: 'generate' })
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

  useEffect(() => {
    function onPopState() {
      const courseId = readCourseIdFromUrl()
      if (!courseId) {
        setView((current) =>
          current.kind === 'course' ? { kind: 'courses' } : current,
        )
        return
      }
      setState((current) => {
        if (current.status === 'ready') {
          const match = current.courses.find((course) => course.id === courseId)
          if (match) {
            setView({ kind: 'course', course: match })
          }
        }
        return current
      })
    }

    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  useEffect(() => {
    if (view.kind !== 'courses') {
      return
    }
    const courseId = restoreFocusCourseIdRef.current
    if (!courseId) {
      return
    }
    restoreFocusCourseIdRef.current = null
    const button = courseButtonRefs.current.get(courseId)
    button?.focus()
  }, [view])

  function handleNavigate(label: NavLabel) {
    if (label === 'Courses') {
      userNavigatedRef.current = true
      if (view.kind === 'course') {
        restoreFocusCourseIdRef.current = view.course.id
      }
      writeCourseIdToUrl(null)
      setView({ kind: 'courses' })
    } else if (label === 'Generate') {
      userNavigatedRef.current = true
      writeCourseIdToUrl(null)
      setView({ kind: 'generate' })
    }
  }

  function handleThemeToggle() {
    const next = theme === 'dark' ? 'light' : 'dark'
    persistTheme(next)
    setTheme(next)
  }

  function handleSelectCourse(course: Course) {
    userNavigatedRef.current = true
    restoreFocusCourseIdRef.current = course.id
    writeCourseIdToUrl(course.id)
    setView({ kind: 'course', course })
  }

  function handleCourseDeleted(courseId: string) {
    userNavigatedRef.current = true
    restoreFocusCourseIdRef.current = null
    courseButtonRefs.current.delete(courseId)
    writeCourseIdToUrl(null)
    setState((current) =>
      current.status === 'ready'
        ? {
            status: 'ready',
            courses: current.courses.filter((course) => course.id !== courseId),
          }
        : current,
    )
    setView({ kind: 'courses' })
  }

  const navActive: NavLabel =
    view.kind === 'generate' ? 'Generate' : 'Courses'

  return (
    <div className="home">
      <header className="home__header">
        <div className="home__toolbar">
          <ThemeToggle theme={theme} onToggle={handleThemeToggle} />
        </div>
        <NavBar active={navActive} onNavigate={handleNavigate} />
        {view.kind === 'courses' && <h1 className="home__title">Courses</h1>}
      </header>

      <main className="home__main">
        {/* Keep Generate mounted (hidden) so #20's polling / form state can
            survive tab switches once that PR lands. Do not remount via ternary. */}
        <div hidden={view.kind !== 'generate'}>
          <GeneratePage />
        </div>

        {view.kind === 'course' && (
          <CoursePage
            key={view.course.id}
            course={view.course}
            onDeleted={handleCourseDeleted}
          />
        )}

        {view.kind === 'courses' && (
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
                  <CourseCard
                    key={course.id}
                    course={course}
                    index={index}
                    onSelect={handleSelectCourse}
                    ref={(node) => {
                      if (node) {
                        courseButtonRefs.current.set(course.id, node)
                      } else {
                        courseButtonRefs.current.delete(course.id)
                      }
                    }}
                  />
                ))}
              </section>
            )}
          </>
        )}
      </main>
    </div>
  )
}
