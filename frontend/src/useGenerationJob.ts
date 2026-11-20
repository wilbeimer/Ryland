import { useEffect, useRef, useState } from 'react'
import {
  ApiError,
  getStoredActiveJobId,
  parseConflictJobId,
  pollGenerationJob,
  setStoredActiveJobId,
  startCourseGeneration,
  submitGenerationAnswers,
  type GenerateCourseRequest,
  type GenerationJob,
} from './api'

export type GenerationPhase =
  | { kind: 'idle' }
  | { kind: 'submitting' }
  | { kind: 'polling'; job: GenerationJob }
  | { kind: 'awaiting_input'; job: GenerationJob }
  | { kind: 'answering'; job: GenerationJob }
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
    questions: null,
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

function phaseFromJob(job: GenerationJob): GenerationPhase {
  if (
    job.status === 'awaiting_input' &&
    job.questions &&
    job.questions.length > 0
  ) {
    return { kind: 'awaiting_input', job }
  }
  return { kind: 'polling', job }
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
  /** Set on 409 resume; cleared when that build reaches a terminal phase. */
  const [resumedFromConflict, setResumedFromConflict] = useState(false)
  const notifiedJobRef = useRef<string | null>(null)
  const onCourseSavedRef = useRef(onCourseSaved)
  const answeringRef = useRef(false)

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
        if (cancelled) {
          return
        }
        // Keep the answering spinner until the server leaves awaiting_input.
        if (answeringRef.current && job.status === 'awaiting_input') {
          setPhase({ kind: 'answering', job })
          return
        }
        if (job.status !== 'awaiting_input') {
          answeringRef.current = false
        }
        setPhase(phaseFromJob(job))
      },
      onRetry: () => {
        if (!cancelled) {
          setPhase((current) => {
            if (current.kind !== 'polling' && current.kind !== 'answering') {
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
        answeringRef.current = false
        setStoredActiveJobId(null)
        setActiveJobId(null)
        setResumedFromConflict(false)

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
        answeringRef.current = false
        setStoredActiveJobId(null)
        setActiveJobId(null)
        setResumedFromConflict(false)
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
    if (
      phase.kind === 'submitting' ||
      phase.kind === 'polling' ||
      phase.kind === 'awaiting_input' ||
      phase.kind === 'answering'
    ) {
      return
    }

    notifiedJobRef.current = null
    answeringRef.current = false
    setResumedFromConflict(false)
    setPhase({ kind: 'submitting' })

    try {
      const started = await startCourseGeneration(body)
      setStoredActiveJobId(started.job_id)
      setPhase(phaseFromJob(started))
      setActiveJobId(started.job_id)
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 409) {
        const conflictId = parseConflictJobId(error.detail)
        if (conflictId) {
          setStoredActiveJobId(conflictId)
          setResumedFromConflict(true)
          setPhase({
            kind: 'polling',
            job: placeholderJob(conflictId),
          })
          setActiveJobId(conflictId)
          return
        }
      }
      setPhase({ kind: 'error', message: errorMessage(error) })
    }
  }

  async function submitAnswers(answers: string[]): Promise<void> {
    if (phase.kind !== 'awaiting_input') {
      return
    }

    const job = phase.job
    answeringRef.current = true
    setPhase({ kind: 'answering', job })

    try {
      const updated = await submitGenerationAnswers(job.job_id, { answers })
      answeringRef.current = false
      setPhase(phaseFromJob(updated))
    } catch (error: unknown) {
      answeringRef.current = false
      // Stay on the clarifying box so the user can retry.
      setPhase({
        kind: 'awaiting_input',
        job: {
          ...job,
          detail: errorMessage(error),
        },
      })
    }
  }

  return {
    phase,
    beginGeneration,
    submitAnswers,
    resumedFromConflict,
  }
}
