import { useEffect, useRef, useState } from 'react'
import { fetchCourses, type Course } from './api'
import { CalendarPage } from './components/CalendarPage'
import { CourseCard } from './components/CourseCard'
import { CoursePage } from './components/CoursePage'
import { GeneratePage } from './components/GeneratePage'
import { NavBar, type NavLabel } from './components/NavBar'
import { SettingsPage } from './components/SettingsPage'
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

/** Tab / detail selection. Course detail is also mirrored in `?course=<id>`. */
type View =
  | { kind: 'courses' }
  | { kind: 'calendar' }
  | { kind: 'generate' }
  | { kind: 'settings' }
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
  const [coursesVersion, setCoursesVersion] = useState(0)
  const [deletedNotice, setDeletedNotice] = useState<string | null>(null)
  const userNavigatedRef = useRef(false)
  /** Course id to restore keyboard focus to after leaving detail. */
  const restoreFocusCourseIdRef = useRef<string | null>(null)
  const courseButtonRefs = useRef(new Map<string, HTMLButtonElement>())
  const coursesHeadingRef = useRef<HTMLHeadingElement>(null)
  const focusCoursesHeadingRef = useRef(false)

  const {
    phase: generationPhase,
    beginGeneration,
    submitAnswers,
    answerError,
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
        if (
          isInitialLoad &&
          courses.length === 0 &&
          !userNavigatedRef.current
        ) {
          setView({ kind: 'generate' })
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
    if (focusCoursesHeadingRef.current) {
      focusCoursesHeadingRef.current = false
      coursesHeadingRef.current?.focus()
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
      setDeletedNotice(null)
      if (view.kind === 'course') {
        restoreFocusCourseIdRef.current = view.course.id
      }
      writeCourseIdToUrl(null)
      setView({ kind: 'courses' })
    } else if (label === 'Calendar') {
      userNavigatedRef.current = true
      setDeletedNotice(null)
      writeCourseIdToUrl(null)
      setView({ kind: 'calendar' })
    } else if (label === 'Generate') {
      userNavigatedRef.current = true
      setDeletedNotice(null)
      writeCourseIdToUrl(null)
      setView({ kind: 'generate' })
    } else if (label === 'Account') {
      userNavigatedRef.current = true
      setDeletedNotice(null)
      writeCourseIdToUrl(null)
      setView({ kind: 'settings' })
    }
  }

  function handleThemeChange(next: Theme) {
    persistTheme(next)
    setTheme(next)
  }

  function handleThemeToggle() {
    handleThemeChange(theme === 'dark' ? 'light' : 'dark')
  }

  function handleSelectCourse(course: Course) {
    userNavigatedRef.current = true
    setDeletedNotice(null)
    restoreFocusCourseIdRef.current = course.id
    writeCourseIdToUrl(course.id)
    setView({ kind: 'course', course })
  }

  function handleCourseDeleted(courseId: string) {
    userNavigatedRef.current = true
    restoreFocusCourseIdRef.current = null
    focusCoursesHeadingRef.current = true
    courseButtonRefs.current.delete(courseId)
    writeCourseIdToUrl(null)
    setDeletedNotice('Course deleted')
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

  function handleCourseUpdated(course: Course) {
    setState((current) =>
      current.status === 'ready'
        ? {
            status: 'ready',
            courses: current.courses.map((item) =>
              item.id === course.id ? course : item,
            ),
          }
        : current,
    )
    setView((current) =>
      current.kind === 'course' && current.course.id === course.id
        ? { kind: 'course', course }
        : current,
    )
  }

  const navActive: NavLabel =
    view.kind === 'generate'
      ? 'Generate'
      : view.kind === 'calendar'
        ? 'Calendar'
        : view.kind === 'settings'
          ? 'Account'
          : 'Courses'

  return (
    <div className="home">
      <header className="home__header">
        <div className="home__toolbar">
          <ThemeToggle theme={theme} onToggle={handleThemeToggle} />
        </div>
        <NavBar active={navActive} onNavigate={handleNavigate} />
        {view.kind === 'courses' && (
          <h1 ref={coursesHeadingRef} className="home__title" tabIndex={-1}>
            Courses
          </h1>
        )}
        {view.kind === 'calendar' && (
          <h1 className="home__title" tabIndex={-1}>
            Calendar
          </h1>
        )}
        {view.kind === 'settings' && (
          <h1 className="home__title" tabIndex={-1}>
            Settings
          </h1>
        )}
      </header>

      <main className="home__main">
        {/* Keep Generate mounted so form fields survive tab switches;
            job polling is owned by useGenerationJob above. */}
        <div hidden={view.kind !== 'generate'}>
          <GeneratePage
            phase={generationPhase}
            onBeginGeneration={beginGeneration}
            onSubmitAnswers={submitAnswers}
            answerError={answerError}
            resumedFromConflict={resumedFromConflict}
          />
        </div>

        {view.kind === 'course' && (
          <CoursePage
            key={view.course.id}
            course={view.course}
            onDeleted={handleCourseDeleted}
            onCourseUpdated={handleCourseUpdated}
          />
        )}

        {view.kind === 'calendar' && <CalendarPage />}

        {view.kind === 'settings' && (
          <SettingsPage theme={theme} onThemeChange={handleThemeChange} />
        )}

        {view.kind === 'courses' && (
          <>
            {deletedNotice && (
              <p className="home__status" role="status">
                {deletedNotice}
              </p>
            )}

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
