export type Course = {
  id: string
  name: string
  description: string
  color: string
  start_date: string
}

export type Week = {
  id: string
  week_number: number
  description: string
  start_date: string
  end_date: string
}

export type AssignmentType = 'text' | 'quiz'

export type Assignment = {
  id: string
  type: AssignmentType
  name: string
  description: string
  rubric: Record<string, unknown>
  due_date: string
}

export type CalendarAssignment = Assignment & {
  course_id: string
  course_name: string
  course_color: string
}

export type CalendarWeek = {
  start_date: string
  end_date: string
  assignments: CalendarAssignment[]
}

export type GenerateCourseRequest = {
  goal: string
  level: string
  time_available: string
  timezone: string
}

export type GenerationStatus =
  | 'pending'
  | 'running'
  | 'awaiting_input'
  | 'succeeded'
  | 'incomplete'
  | 'failed'

export type GenerationJob = {
  job_id: string
  status: GenerationStatus
  detail: string | null
  course_id: string | null
  course: Course | null
  error: string | null
  questions: string[] | null
}

export type GenerateAnswersRequest = {
  answers: string[]
}

import { getAuthToken, setAuthToken } from './session'

export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(
  /\/$/,
  '',
)

async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers)
  const token = getAuthToken()
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(input, { ...init, headers })
}

/** sessionStorage key for the in-flight generate job (survives tab switches). */
export const ACTIVE_GENERATE_JOB_KEY = 'ryland-active-generate-job'

const TERMINAL_STATUSES: ReadonlySet<GenerationStatus> = new Set([
  'succeeded',
  'incomplete',
  'failed',
])

const UUID_RE =
  /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i

const JOB_LOST_MESSAGE =
  'The server restarted, so this build was lost. Start a new build to try again.'

const HEX_COLOR_RE = /^#[0-9a-fA-F]{6}$/
const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/

function isCourse(value: unknown): value is Course {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const course = value as Record<string, unknown>
  return (
    typeof course.id === 'string' &&
    typeof course.name === 'string' &&
    typeof course.description === 'string' &&
    typeof course.color === 'string' &&
    HEX_COLOR_RE.test(course.color) &&
    typeof course.start_date === 'string' &&
    ISO_DATE_RE.test(course.start_date)
  )
}

function isWeek(value: unknown): value is Week {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const week = value as Record<string, unknown>
  return (
    typeof week.id === 'string' &&
    typeof week.week_number === 'number' &&
    typeof week.description === 'string' &&
    typeof week.start_date === 'string' &&
    ISO_DATE_RE.test(week.start_date) &&
    typeof week.end_date === 'string' &&
    ISO_DATE_RE.test(week.end_date)
  )
}

function isAssignment(value: unknown): value is Assignment {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const assignment = value as Record<string, unknown>
  return (
    typeof assignment.id === 'string' &&
    (assignment.type === 'text' || assignment.type === 'quiz') &&
    typeof assignment.name === 'string' &&
    typeof assignment.description === 'string' &&
    typeof assignment.rubric === 'object' &&
    assignment.rubric !== null &&
    typeof assignment.due_date === 'string'
  )
}

function isCalendarAssignment(value: unknown): value is CalendarAssignment {
  if (!isAssignment(value)) {
    return false
  }
  const assignment = value as Record<string, unknown>
  return (
    typeof assignment.course_id === 'string' &&
    typeof assignment.course_name === 'string' &&
    typeof assignment.course_color === 'string' &&
    HEX_COLOR_RE.test(assignment.course_color)
  )
}

function isCalendarWeek(value: unknown): value is CalendarWeek {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const week = value as Record<string, unknown>
  return (
    typeof week.start_date === 'string' &&
    ISO_DATE_RE.test(week.start_date) &&
    typeof week.end_date === 'string' &&
    ISO_DATE_RE.test(week.end_date) &&
    Array.isArray(week.assignments) &&
    week.assignments.every(isCalendarAssignment)
  )
}

function isGenerationStatus(value: unknown): value is GenerationStatus {
  return (
    value === 'pending' ||
    value === 'running' ||
    value === 'awaiting_input' ||
    value === 'succeeded' ||
    value === 'incomplete' ||
    value === 'failed'
  )
}

function isQuestionList(value: unknown): value is string[] {
  return (
    Array.isArray(value) && value.every((item) => typeof item === 'string')
  )
}

function isGenerationJob(value: unknown): value is GenerationJob {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const job = value as Record<string, unknown>
  const courseOk =
    job.course === null || job.course === undefined || isCourse(job.course)
  const questionsOk =
    job.questions === null ||
    job.questions === undefined ||
    isQuestionList(job.questions)
  return (
    typeof job.job_id === 'string' &&
    isGenerationStatus(job.status) &&
    (job.detail === null || typeof job.detail === 'string') &&
    (job.course_id === null || typeof job.course_id === 'string') &&
    (job.error === null || typeof job.error === 'string') &&
    courseOk &&
    questionsOk
  )
}

function normalizeGenerationJob(job: GenerationJob): GenerationJob {
  return {
    ...job,
    questions: job.questions ?? null,
  }
}

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json()
    if (typeof data === 'object' && data !== null) {
      const detail = (data as Record<string, unknown>).detail
      if (typeof detail === 'string' && detail.trim()) {
        return detail
      }
      if (Array.isArray(detail)) {
        const parts = detail
          .map((item) => {
            if (typeof item === 'object' && item !== null) {
              const msg = (item as Record<string, unknown>).msg
              return typeof msg === 'string' ? msg : null
            }
            return null
          })
          .filter((msg): msg is string => Boolean(msg))
        if (parts.length > 0) {
          return parts.join('; ')
        }
      }
    }
  } catch {
    // fall through to status text
  }
  return `Request failed (${response.status})`
}

export function getStoredActiveJobId(): string | null {
  try {
    const value = sessionStorage.getItem(ACTIVE_GENERATE_JOB_KEY)
    return value && UUID_RE.test(value) ? value : null
  } catch {
    return null
  }
}

export function setStoredActiveJobId(jobId: string | null): void {
  try {
    if (jobId) {
      sessionStorage.setItem(ACTIVE_GENERATE_JOB_KEY, jobId)
    } else {
      sessionStorage.removeItem(ACTIVE_GENERATE_JOB_KEY)
    }
  } catch {
    // sessionStorage may be unavailable
  }
}

/** Pull the active job UUID out of a 409 conflict detail string. */
export function parseConflictJobId(detail: string): string | null {
  const match = detail.match(UUID_RE)
  return match ? match[0] : null
}

export async function fetchCourses(): Promise<Course[]> {
  const response = await apiFetch(`${API_BASE}/courses`)
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data) || !data.every(isCourse)) {
    throw new Error('Failed to load courses (unexpected response)')
  }

  return data
}

export async function deleteCourse(courseId: string): Promise<void> {
  const response = await apiFetch(
    `${API_BASE}/courses/${encodeURIComponent(courseId)}`,
    { method: 'DELETE' },
  )
  if (!response.ok) {
    throw new Error(`Failed to delete course (${response.status})`)
  }
}

export async function patchCourseColor(
  courseId: string,
  color: string,
): Promise<Course> {
  const response = await apiFetch(
    `${API_BASE}/courses/${encodeURIComponent(courseId)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ color }),
    },
  )
  if (!response.ok) {
    throw new Error(`Failed to update course color (${response.status})`)
  }
  const data: unknown = await response.json()
  if (!isCourse(data)) {
    throw new Error('Failed to update course color (unexpected response)')
  }
  return data
}

export async function fetchCalendarWeeks(
  timezone?: string,
): Promise<CalendarWeek[]> {
  const params = new URLSearchParams()
  const zone =
    timezone ||
    (typeof Intl !== 'undefined'
      ? Intl.DateTimeFormat().resolvedOptions().timeZone
      : 'UTC')
  if (zone) {
    params.set('timezone', zone)
  }
  const query = params.toString()
  const response = await apiFetch(
    `${API_BASE}/calendar/weeks${query ? `?${query}` : ''}`,
  )
  if (!response.ok) {
    throw new Error(`Failed to load calendar weeks (${response.status})`)
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data) || !data.every(isCalendarWeek)) {
    throw new Error('Failed to load calendar weeks (unexpected response)')
  }

  return data
}

export async function fetchWeeks(courseId: string): Promise<Week[]> {
  const response = await apiFetch(`${API_BASE}/courses/${courseId}/weeks`)
  if (!response.ok) {
    throw new Error(`Failed to load weeks (${response.status})`)
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data) || !data.every(isWeek)) {
    throw new Error('Failed to load weeks (unexpected response)')
  }

  return data
}

/** Skips items with unknown `type` so a future assignment kind doesn't blank a week. */
export async function fetchAssignments(weekId: string): Promise<Assignment[]> {
  const response = await apiFetch(`${API_BASE}/weeks/${weekId}/assignments`)
  if (!response.ok) {
    throw new Error(`Failed to load assignments (${response.status})`)
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data)) {
    throw new Error('Failed to load assignments (unexpected response)')
  }

  return data.filter(isAssignment)
}

export async function fetchAssignment(
  assignmentId: string,
): Promise<CalendarAssignment> {
  const response = await apiFetch(
    `${API_BASE}/assignments/${encodeURIComponent(assignmentId)}`,
  )
  if (!response.ok) {
    throw new Error(`Failed to load assignment (${response.status})`)
  }

  const data: unknown = await response.json()
  if (!isCalendarAssignment(data)) {
    throw new Error('Failed to load assignment (unexpected response)')
  }

  return data
}

export async function startCourseGeneration(
  body: GenerateCourseRequest,
  signal?: AbortSignal,
): Promise<GenerationJob> {
  const response = await apiFetch(`${API_BASE}/courses/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }

  const data: unknown = await response.json()
  if (!isGenerationJob(data)) {
    throw new Error('Failed to start generation (unexpected response)')
  }
  return normalizeGenerationJob(data)
}

export async function fetchGenerationJob(
  jobId: string,
  signal?: AbortSignal,
): Promise<GenerationJob> {
  const response = await apiFetch(
    `${API_BASE}/courses/generate/${encodeURIComponent(jobId)}`,
    { signal },
  )

  if (!response.ok) {
    const detail = await readErrorDetail(response)
    if (response.status === 404) {
      throw new ApiError(404, JOB_LOST_MESSAGE)
    }
    throw new ApiError(response.status, detail)
  }

  const data: unknown = await response.json()
  if (!isGenerationJob(data)) {
    throw new Error('Failed to load generation status (unexpected response)')
  }
  return normalizeGenerationJob(data)
}

export async function submitGenerationAnswers(
  jobId: string,
  body: GenerateAnswersRequest,
  signal?: AbortSignal,
): Promise<GenerationJob> {
  const response = await apiFetch(
    `${API_BASE}/courses/generate/${encodeURIComponent(jobId)}/answers`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    },
  )

  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }

  const data: unknown = await response.json()
  if (!isGenerationJob(data)) {
    throw new Error('Failed to submit answers (unexpected response)')
  }
  return normalizeGenerationJob(data)
}

export function isTerminalGenerationStatus(
  status: GenerationStatus,
): boolean {
  return TERMINAL_STATUSES.has(status)
}

const DEFAULT_POLL_MS = 1500
const MAX_TRANSIENT_RETRIES = 4
const TRANSIENT_BACKOFF_MS = [500, 1000, 2000, 4000]

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

function isTransientPollError(error: unknown): boolean {
  if (isAbortError(error)) {
    return false
  }
  if (error instanceof ApiError) {
    // 404 means the in-memory job is gone (e.g. uvicorn --reload); not transient.
    return error.status >= 500 || error.status === 429
  }
  // Network blips (Failed to fetch, etc.) — not parse/shape errors.
  return error instanceof TypeError
}

function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      signal?.removeEventListener('abort', onAbort)
      resolve()
    }, ms)

    function onAbort() {
      window.clearTimeout(timer)
      reject(new DOMException('Polling aborted', 'AbortError'))
    }

    if (signal) {
      if (signal.aborted) {
        onAbort()
        return
      }
      signal.addEventListener('abort', onAbort, { once: true })
    }
  })
}

async function fetchGenerationJobWithRetry(
  jobId: string,
  signal?: AbortSignal,
  onRetry?: (attempt: number) => void,
): Promise<GenerationJob> {
  let attempt = 0
  for (;;) {
    try {
      return await fetchGenerationJob(jobId, signal)
    } catch (error: unknown) {
      if (isAbortError(error) || !isTransientPollError(error)) {
        throw error
      }
      if (attempt >= MAX_TRANSIENT_RETRIES) {
        throw error
      }
      const delay =
        TRANSIENT_BACKOFF_MS[
          Math.min(attempt, TRANSIENT_BACKOFF_MS.length - 1)
        ] ?? 4000
      attempt += 1
      onRetry?.(attempt)
      await sleep(delay, signal)
    }
  }
}

/** Poll until the job reaches a terminal status. Retries transient failures. */
export async function pollGenerationJob(
  jobId: string,
  options?: {
    signal?: AbortSignal
    intervalMs?: number
    onUpdate?: (job: GenerationJob) => void
    onRetry?: (attempt: number) => void
  },
): Promise<GenerationJob> {
  const intervalMs = options?.intervalMs ?? DEFAULT_POLL_MS
  const signal = options?.signal

  for (;;) {
    if (signal?.aborted) {
      throw new DOMException('Polling aborted', 'AbortError')
    }

    const job = await fetchGenerationJobWithRetry(
      jobId,
      signal,
      options?.onRetry,
    )
    options?.onUpdate?.(job)

    if (isTerminalGenerationStatus(job.status)) {
      return job
    }

    await sleep(intervalMs, signal)
  }
}

export type AuthUser = {
  id: string
  username: string
  email: string
  email_verified: boolean
}

export type SignUpResult = {
  id: string
  username: string
  email: string
  email_verified: boolean
  delivery: 'sent' | 'logged'
}

function isAuthUser(value: unknown): value is AuthUser {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const user = value as Record<string, unknown>
  return (
    typeof user.id === 'string' &&
    typeof user.username === 'string' &&
    typeof user.email === 'string' &&
    typeof user.email_verified === 'boolean'
  )
}

export async function signUp(body: {
  username: string
  password: string
  email: string
}): Promise<SignUpResult> {
  const response = await apiFetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }
  const data: unknown = await response.json()
  if (!isAuthUser(data) || typeof data !== 'object' || data === null) {
    throw new Error('Failed to sign up (unexpected response)')
  }
  const record = data as AuthUser & { delivery?: unknown }
  if (record.delivery !== 'sent' && record.delivery !== 'logged') {
    throw new Error('Failed to sign up (unexpected response)')
  }
  return {
    id: record.id,
    username: record.username,
    email: record.email,
    email_verified: record.email_verified,
    delivery: record.delivery,
  }
}

export async function resendVerification(
  username: string,
  password: string,
): Promise<SignUpResult> {
  const response = await apiFetch(`${API_BASE}/auth/resend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }
  const data: unknown = await response.json()
  if (!isAuthUser(data)) {
    throw new Error('Failed to resend verification (unexpected response)')
  }
  const record = data as AuthUser & { delivery?: unknown }
  if (record.delivery !== 'sent' && record.delivery !== 'logged') {
    throw new Error('Failed to resend verification (unexpected response)')
  }
  return {
    id: record.id,
    username: record.username,
    email: record.email,
    email_verified: record.email_verified,
    delivery: record.delivery,
  }
}

export async function verifyEmail(token: string): Promise<void> {
  const response = await apiFetch(`${API_BASE}/auth/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  })
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }
}

export async function signIn(
  username: string,
  password: string,
): Promise<AuthUser> {
  const response = await apiFetch(`${API_BASE}/auth/signin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }
  const data: unknown = await response.json()
  if (typeof data !== 'object' || data === null) {
    throw new Error('Failed to sign in (unexpected response)')
  }
  const record = data as { token?: unknown; user?: unknown }
  if (typeof record.token !== 'string' || !isAuthUser(record.user)) {
    throw new Error('Failed to sign in (unexpected response)')
  }
  setAuthToken(record.token)
  return record.user
}

export async function signOut(): Promise<void> {
  try {
    await apiFetch(`${API_BASE}/auth/signout`, { method: 'POST' })
  } finally {
    setAuthToken(null)
  }
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const response = await apiFetch(`${API_BASE}/auth/me`)
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }
  const data: unknown = await response.json()
  if (!isAuthUser(data)) {
    throw new Error('Failed to load account (unexpected response)')
  }
  return data
}
