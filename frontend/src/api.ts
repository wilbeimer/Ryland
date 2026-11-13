export type Course = {
  id: string
  name: string
  description: string
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
}

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

function isCourse(value: unknown): value is Course {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const course = value as Record<string, unknown>
  return (
    typeof course.id === 'string' &&
    typeof course.name === 'string' &&
    typeof course.description === 'string'
  )
}

function isGenerationStatus(value: unknown): value is GenerationStatus {
  return (
    value === 'pending' ||
    value === 'running' ||
    value === 'succeeded' ||
    value === 'incomplete' ||
    value === 'failed'
  )
}

function isGenerationJob(value: unknown): value is GenerationJob {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  const job = value as Record<string, unknown>
  const courseOk =
    job.course === null || job.course === undefined || isCourse(job.course)
  return (
    typeof job.job_id === 'string' &&
    isGenerationStatus(job.status) &&
    (job.detail === null || typeof job.detail === 'string') &&
    (job.course_id === null || typeof job.course_id === 'string') &&
    (job.error === null || typeof job.error === 'string') &&
    courseOk
  )
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
  const response = await fetch(`${API_BASE}/courses`)
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorDetail(response))
  }

  const data: unknown = await response.json()
  if (!Array.isArray(data) || !data.every(isCourse)) {
    throw new Error('Failed to load courses (unexpected response)')
  }

  return data
}

export async function startCourseGeneration(
  body: GenerateCourseRequest,
  signal?: AbortSignal,
): Promise<GenerationJob> {
  const response = await fetch(`${API_BASE}/courses/generate`, {
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
  return data
}

export async function fetchGenerationJob(
  jobId: string,
  signal?: AbortSignal,
): Promise<GenerationJob> {
  const response = await fetch(
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
  return data
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
