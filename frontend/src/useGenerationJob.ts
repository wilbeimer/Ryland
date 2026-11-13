import { useEffect, useRef, useState } from 'react'
import {
  ApiError,
  getStoredActiveJobId,
  parseConflictJobId,
  pollGenerationJob,
  setStoredActiveJobId,
  startCourseGeneration,
  type GenerateCourseRequest,
  type GenerationJob,
} from './api'

export type GenerationPhase =
  | { kind: 'idle' }
  | { kind: 'submitting' }
  | { kind: 'polling'; job: GenerationJob }
  | { kind: 'done'; job: GenerationJob }
  | { kind: 'error'; message: string; job?: GenerationJob }

function placeholderJob(jobId: string, detail = 'Resuming…'): GenerationJob {
  return {
    job_id: jobId,
    status: 'pending',
    detail,
    course_id: null,
    course: null,
    error: null,
  }
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.detail
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Course generation failed'
}

/**
 * Owns generate job_id + phase at the App level so polling survives
 * Generate tab switches. Persists the active job id in sessionStorage.
 */
export function useGenerationJob(onCourseSaved?: (job: GenerationJob) => void) {
  const [activeJobId, setActiveJobId] = useState<string | null>(() =>
    getStoredActiveJobId(),
  )
  const [phase, setPhase] = useState<GenerationPhase>(() => {
    const stored = getStoredActiveJobId()
    return stored
      ? { kind: 'polling', job: placeholderJob(stored) }
      : { kind: 'idle' }
  })
  const notifiedJobRef = useRef<string | null>(null)
  const onCourseSavedRef = useRef(onCourseSaved)

  useEffect(() => {
    onCourseSavedRef.current = onCourseSaved
  }, [onCourseSaved])

  useEffect(() => {
    if (!activeJobId) {
      return
    }

    const controller = new AbortController()
    let cancelled = false

    setStoredActiveJobId(activeJobId)

    pollGenerationJob(activeJobId, {
      signal: controller.signal,
      onUpdate: (job) => {
        if (!cancelled) {
          setPhase({ kind: 'polling', job })
        }
      },
      onRetry: () => {
        if (!cancelled) {
          setPhase((current) => {
            if (current.kind !== 'polling') {
              return current
            }
            return {
              kind: 'polling',
              job: {
                ...current.job,
                detail: 'Reconnecting…',
              },
            }
          })
        }
      },
    })
      .then((finished) => {
        if (cancelled) {
          return
        }
        setStoredActiveJobId(null)
        setActiveJobId(null)

        if (finished.status === 'failed') {
          setPhase({
            kind: 'error',
            message:
              finished.error || finished.detail || 'Course generation failed',
            job: finished,
          })
        } else {
          setPhase({ kind: 'done', job: finished })
        }

        // Timed-out failed jobs can still include a saved course_id.
        if (
          finished.course_id &&
          notifiedJobRef.current !== finished.job_id
        ) {
          notifiedJobRef.current = finished.job_id
          onCourseSavedRef.current?.(finished)
        }
      })
      .catch((error: unknown) => {
        if (
          cancelled ||
          (error instanceof DOMException && error.name === 'AbortError')
        ) {
          return
        }
        setStoredActiveJobId(null)
        setActiveJobId(null)
        setPhase({ kind: 'error', message: errorMessage(error) })
      })

    return () => {
      cancelled = true
      // Abort only when the tracked job changes or App unmounts —
      // not when switching away from the Generate tab.
      controller.abort()
    }
  }, [activeJobId])

  async function beginGeneration(body: GenerateCourseRequest): Promise<void> {
    if (phase.kind === 'submitting' || phase.kind === 'polling') {
      return
    }

    notifiedJobRef.current = null
    setPhase({ kind: 'submitting' })

    try {
      const started = await startCourseGeneration(body)
      setStoredActiveJobId(started.job_id)
      setPhase({ kind: 'polling', job: started })
      setActiveJobId(started.job_id)
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 409) {
        const conflictId = parseConflictJobId(error.detail)
        if (conflictId) {
          setStoredActiveJobId(conflictId)
          setPhase({
            kind: 'polling',
            job: placeholderJob(
              conflictId,
              'A build was already running, so I am tracking that one.',
            ),
          })
          setActiveJobId(conflictId)
          return
        }
      }
      setPhase({ kind: 'error', message: errorMessage(error) })
    }
  }

  return { phase, beginGeneration }
}
