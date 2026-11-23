import { useEffect, useRef, useState } from 'react'
import { fetchCourses, type Course } from './api'
import { AssignmentPage } from './components/AssignmentPage'
import { CalendarPage } from './components/CalendarPage'
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
import { useGenerationJob } from './useGenerationJob'
import './App.css'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; courses: Course[] }

/** Tab / detail selection. Mirrored in `?course=` / `?assignment=`. */
type View =
  | { kind: 'courses' }
  | { kind: 'calendar' }
  | { kind: 'generate' }
  | { kind: 'course'; course: Course }
  | { kind: 'assignment'; assignmentId: string }

type ReturnView =
  | { kind: 'courses' }
  | { kind: 'calendar' }
  | { kind: 'course'; course: Course }

function readCourseIdFromUrl(): string | null {
  try {
    return new URLSearchParams(window.location.search).get('course')
  } catch {
    return null
  }
}

function readAssignmentIdFromUrl(): string | null {
  try {
    return new URLSearchParams(window.location.search).get('assignment')
  } catch {
    return null
  }
}

function writeDetailToUrl(detail: {
  courseId?: string | null
  assignmentId?: string | null
}): void {
  const url = new URL(window.location.href)
  if (detail.assignmentId) {
    url.searchParams.delete('course')
    url.searchParams.set('assignment', detail.assignmentId)
  } else if (detail.courseId) {
    url.searchParams.delete('assignment')
    url.searchParams.set('course', detail.courseId)
  } else {
    url.searchParams.delete('course')
    url.searchParams.delete('assignment')
  }
  const next = `${url.pathname}${url.search}${url.hash}`
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
  if (next !== current) {
    window.history.pushState({}, '', next)
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
  const [assignmentReturn, setAssignmentReturn] = useState<ReturnView>({
    kind: 'courses',
  })

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

        const assignmentId = readAssignmentIdFromUrl()
        if (assignmentId) {
          setAssignmentReturn({ kind: 'courses' })
          setView({ kind: 'assignment', assignmentId })
          return
        }

        const courseId = readCourseIdFromUrl()
        if (courseId) {
          const match = courses.find((course) => course.id === courseId)
          if (match) {
            setView({ kind: 'course', course: match })
            return
          }
          writeDetailToUrl({})
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
      const assignmentId = readAssignmentIdFromUrl()
      if (assignmentId) {
        setView({ kind: 'assignment', assignmentId })
        return
      }
      const courseId = readCourseIdFromUrl()
      if (!courseId) {
        setView((current) =>
          current.kind === 'course' || current.kind === 'assignment'
            ? { kind: 'courses' }
            : current,
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
      writeDetailToUrl({})
      setView({ kind: 'courses' })
    } else if (label === 'Calendar') {
      userNavigatedRef.current = true
      setDeletedNotice(null)
      writeDetailToUrl({})
      setView({ kind: 'calendar' })
    } else if (label === 'Generate') {
      userNavigatedRef.current = true
      setDeletedNotice(null)
      writeDetailToUrl({})
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
    setDeletedNotice(null)
    restoreFocusCourseIdRef.current = course.id
    writeDetailToUrl({ courseId: course.id })
    setView({ kind: 'course', course })
  }

  function handleSelectAssignment(assignmentId: string) {
    userNavigatedRef.current = true
    setDeletedNotice(null)
    if (view.kind === 'course') {
      setAssignmentReturn({ kind: 'course', course: view.course })
    } else if (view.kind === 'calendar') {
      setAssignmentReturn({ kind: 'calendar' })
    } else {
      setAssignmentReturn({ kind: 'courses' })
    }
    writeDetailToUrl({ assignmentId })
    setView({ kind: 'assignment', assignmentId })
  }

  function handleAssignmentBack() {
    if (assignmentReturn.kind === 'course') {
      writeDetailToUrl({ courseId: assignmentReturn.course.id })
      setView({ kind: 'course', course: assignmentReturn.course })
      return
    }
    if (assignmentReturn.kind === 'calendar') {
      writeDetailToUrl({})
      setView({ kind: 'calendar' })
      return
    }
    writeDetailToUrl({})
    setView({ kind: 'courses' })
  }

  function handleCourseDeleted(courseId: string) {
    userNavigatedRef.current = true
    restoreFocusCourseIdRef.current = null
    focusCoursesHeadingRef.current = true
    courseButtonRefs.current.delete(courseId)
    writeDetailToUrl({})
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
      : view.kind === 'calendar' ||
          (view.kind === 'assignment' && assignmentReturn.kind === 'calendar')
        ? 'Calendar'
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
            onSelectAssignment={handleSelectAssignment}
          />
        )}

        {view.kind === 'assignment' && (
          <AssignmentPage
            key={view.assignmentId}
            assignmentId={view.assignmentId}
            onBack={handleAssignmentBack}
          />
        )}

        {view.kind === 'calendar' && (
          <CalendarPage onSelectAssignment={handleSelectAssignment} />
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
