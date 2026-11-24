import { useEffect, useRef, useState, type ReactNode } from 'react'
import {
  ApiError,
  fetchCourses,
  fetchCurrentUser,
  signOut,
  type AuthUser,
  type Course,
} from './api'
import { AssignmentPage } from './components/AssignmentPage'
import { CalendarPage } from './components/CalendarPage'
import { CourseCard } from './components/CourseCard'
import { CoursePage } from './components/CoursePage'
import { GeneratePage } from './components/GeneratePage'
import { NavBar, type NavLabel } from './components/NavBar'
import { SettingsPage } from './components/SettingsPage'
import { SignInPage } from './components/SignInPage'
import { SignUpPage } from './components/SignUpPage'
import { ThemeToggle } from './components/ThemeToggle'
import { VerifyEmailPage } from './components/VerifyEmailPage'
import { getAuthToken, setAuthToken } from './session'
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

/** Tab / detail selection. Mirrored in `?course=` / `?assignment=` / `?view=calendar`. */
type View =
  | { kind: 'courses' }
  | { kind: 'calendar' }
  | { kind: 'generate' }
  | { kind: 'settings' }
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

function readCalendarFromUrl(): boolean {
  try {
    return new URLSearchParams(window.location.search).get('view') === 'calendar'
  } catch {
    return false
  }
}

type AuthRoute = 'sign-in' | 'sign-up' | 'verify' | 'app'

function readAuthRoute(): AuthRoute {
  try {
    const path = window.location.pathname.replace(/\/+$/, '') || '/'
    if (path === '/sign-in') {
      return 'sign-in'
    }
    if (path === '/sign-up') {
      return 'sign-up'
    }
    if (path === '/verify-email') {
      return 'verify'
    }
  } catch {
    return 'app'
  }
  return 'app'
}

type SessionState =
  | { status: 'loading' }
  | { status: 'anonymous' }
  | { status: 'ready'; user: AuthUser }

function writeDetailToUrl(detail: {
  courseId?: string | null
  assignmentId?: string | null
  calendar?: boolean
}): void {
  const url = new URL(window.location.href)
  url.searchParams.delete('course')
  url.searchParams.delete('assignment')
  url.searchParams.delete('view')
  if (detail.assignmentId) {
    url.searchParams.set('assignment', detail.assignmentId)
  } else if (detail.courseId) {
    url.searchParams.set('course', detail.courseId)
  } else if (detail.calendar) {
    url.searchParams.set('view', 'calendar')
  }
  const next = `${url.pathname}${url.search}${url.hash}`
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
  if (next !== current) {
    window.history.pushState({}, '', next)
  }
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => resolveInitialTheme())
  const [session, setSession] = useState<SessionState>(() =>
    getAuthToken() ? { status: 'loading' } : { status: 'anonymous' },
  )
  const [authRoute, setAuthRoute] = useState<AuthRoute>(() => readAuthRoute())
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
    if (!getAuthToken()) {
      return
    }
    let cancelled = false
    fetchCurrentUser()
      .then((user) => {
        if (!cancelled) {
          setSession({ status: 'ready', user })
        }
      })
      .catch(() => {
        if (cancelled) {
          return
        }
        setAuthToken(null)
        setSession({ status: 'anonymous' })
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (session.status !== 'ready') {
      return
    }
    if (authRoute === 'sign-in' || authRoute === 'sign-up') {
      window.history.replaceState({}, '', '/')
    }
  }, [session.status, authRoute])

  useEffect(() => {
    if (session.status !== 'ready') {
      return
    }
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

        if (readCalendarFromUrl()) {
          setView({ kind: 'calendar' })
          return
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
        if (error instanceof ApiError && error.status === 401) {
          setAuthToken(null)
          setSession({ status: 'anonymous' })
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
  }, [coursesVersion, session.status])

  useEffect(() => {
    function onPopState() {
      setAuthRoute(readAuthRoute())
      const assignmentId = readAssignmentIdFromUrl()
      if (assignmentId) {
        setView({ kind: 'assignment', assignmentId })
        return
      }
      const courseId = readCourseIdFromUrl()
      if (courseId) {
        setState((current) => {
          if (current.status === 'ready') {
            const match = current.courses.find(
              (course) => course.id === courseId,
            )
            if (match) {
              setView({ kind: 'course', course: match })
            }
          }
          return current
        })
        return
      }
      if (readCalendarFromUrl()) {
        setView({ kind: 'calendar' })
        return
      }
      setView((current) =>
        current.kind === 'course' ||
        current.kind === 'assignment' ||
        current.kind === 'calendar'
          ? { kind: 'courses' }
          : current,
      )
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

  function openAuth(path: '/sign-in' | '/sign-up') {
    window.history.pushState({}, '', path)
    setAuthRoute(readAuthRoute())
  }

  function handleSignedIn(user: AuthUser) {
    setSession({ status: 'ready', user })
    setState({ status: 'loading' })
    setCoursesVersion((version) => version + 1)
    window.history.pushState({}, '', '/')
    setAuthRoute('app')
  }

  function handleSignOut() {
    void signOut().finally(() => {
      setSession({ status: 'anonymous' })
      setState({ status: 'loading' })
      window.history.pushState({}, '', '/sign-in')
      setAuthRoute('sign-in')
    })
  }

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
      writeDetailToUrl({ calendar: true })
      setView({ kind: 'calendar' })
    } else if (label === 'Generate') {
      userNavigatedRef.current = true
      setDeletedNotice(null)
      writeDetailToUrl({})
      setView({ kind: 'generate' })
    } else if (label === 'Account') {
      userNavigatedRef.current = true
      setDeletedNotice(null)
      writeDetailToUrl({})
      setView({ kind: 'settings' })
    }
  }

  function handleThemeChange(next: Theme) {
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
      writeDetailToUrl({ calendar: true })
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

  function handleThemeToggle() {
    handleThemeChange(theme === 'dark' ? 'light' : 'dark')
  }

  const route: AuthRoute =
    session.status === 'ready' &&
    (authRoute === 'sign-in' || authRoute === 'sign-up')
      ? 'app'
      : authRoute

  if (route === 'verify') {
    return (
      <AuthLayout theme={theme} onToggle={handleThemeToggle}>
        <VerifyEmailPage onSignIn={() => openAuth('/sign-in')} />
      </AuthLayout>
    )
  }

  if (session.status !== 'ready') {
    return (
      <AuthLayout theme={theme} onToggle={handleThemeToggle}>
        {session.status === 'loading' ? (
          <p className="home__status" role="status">
            Loading…
          </p>
        ) : route === 'sign-up' ? (
          <SignUpPage onSignIn={() => openAuth('/sign-in')} />
        ) : (
          <SignInPage
            onSignedIn={handleSignedIn}
            onSignUp={() => openAuth('/sign-up')}
          />
        )}
      </AuthLayout>
    )
  }

  const navActive: NavLabel =
    view.kind === 'generate'
      ? 'Generate'
      : view.kind === 'calendar' ||
          (view.kind === 'assignment' && assignmentReturn.kind === 'calendar')
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

        {view.kind === 'settings' && (
          <SettingsPage
            theme={theme}
            onThemeChange={handleThemeChange}
            username={session.user.username}
            onSignOut={handleSignOut}
          />
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

function AuthLayout({
  theme,
  onToggle,
  children,
}: {
  theme: Theme
  onToggle: () => void
  children: ReactNode
}) {
  return (
    <div className="home">
      <header className="home__header">
        <div className="home__toolbar">
          <ThemeToggle theme={theme} onToggle={onToggle} />
        </div>
      </header>
      <main className="home__main">{children}</main>
    </div>
  )
}
