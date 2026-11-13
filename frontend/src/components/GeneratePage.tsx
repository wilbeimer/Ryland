import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import {
  ApiError,
  pollGenerationJob,
  startCourseGeneration,
  type GenerationJob,
} from '../api'
import './GeneratePage.css'

type FormFields = {
  goal: string
  timezone: string
  level: string
  time_available: string
}

type JobPhase =
  | { kind: 'idle' }
  | { kind: 'submitting' }
  | { kind: 'polling'; job: GenerationJob }
  | { kind: 'done'; job: GenerationJob }
  | { kind: 'error'; message: string; job?: GenerationJob }

export type GeneratePageProps = {
  /** Called when a build finishes with a course (succeeded or incomplete). */
  onCourseCreated?: (job: GenerationJob) => void
}

function detectTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  } catch {
    return 'UTC'
  }
}

function emptyFields(timezone: string): FormFields {
  return {
    goal: '',
    timezone,
    level: '',
    time_available: '',
  }
}

function allFieldsFilled(fields: FormFields): boolean {
  return (
    fields.goal.trim() !== '' &&
    fields.timezone.trim() !== '' &&
    fields.level.trim() !== '' &&
    fields.time_available.trim() !== ''
  )
}

/**
 * Course generation form (Penpot Generation page).
 * Isolated route/component — swap internals freely without touching Courses home.
 */
export function GeneratePage({ onCourseCreated }: GeneratePageProps) {
  const formId = useId()
  const [fields, setFields] = useState<FormFields>(() =>
    emptyFields(detectTimezone()),
  )
  const [phase, setPhase] = useState<JobPhase>({ kind: 'idle' })
  const abortRef = useRef<AbortController | null>(null)
  const createdNotifyRef = useRef<string | null>(null)

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  function updateField<K extends keyof FormFields>(key: K, value: FormFields[K]) {
    setFields((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!allFieldsFilled(fields) || phase.kind === 'submitting' || phase.kind === 'polling') {
      return
    }

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    createdNotifyRef.current = null
    setPhase({ kind: 'submitting' })

    try {
      const started = await startCourseGeneration(
        {
          goal: fields.goal.trim(),
          level: fields.level.trim(),
          time_available: fields.time_available.trim(),
          timezone: fields.timezone.trim(),
        },
        controller.signal,
      )
      setPhase({ kind: 'polling', job: started })

      const finished = await pollGenerationJob(started.job_id, {
        signal: controller.signal,
        onUpdate: (job) => setPhase({ kind: 'polling', job }),
      })

      if (finished.status === 'failed') {
        setPhase({
          kind: 'error',
          message: finished.error || finished.detail || 'Course generation failed',
          job: finished,
        })
        return
      }

      setPhase({ kind: 'done', job: finished })
      if (
        finished.course_id &&
        createdNotifyRef.current !== finished.job_id
      ) {
        createdNotifyRef.current = finished.job_id
        onCourseCreated?.(finished)
      }
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }
      const message =
        error instanceof ApiError
          ? error.detail
          : error instanceof Error
            ? error.message
            : 'Course generation failed'
      setPhase({ kind: 'error', message })
    }
  }

  const busy = phase.kind === 'submitting' || phase.kind === 'polling'
  const canSubmit = allFieldsFilled(fields) && !busy

  const statusMessage = (() => {
    if (phase.kind === 'submitting') {
      return 'Starting course generation…'
    }
    if (phase.kind === 'polling') {
      return phase.job.detail || `Status: ${phase.job.status}`
    }
    if (phase.kind === 'done') {
      const name = phase.job.course?.name
      if (phase.job.status === 'incomplete') {
        return name
          ? `Saved “${name}”, but the build stopped early — some weeks or quizzes may be missing.`
          : 'Course saved, but the build stopped early — some weeks or quizzes may be missing.'
      }
      return name ? `Created “${name}”.` : 'Course created.'
    }
    if (phase.kind === 'error') {
      return phase.message
    }
    return null
  })()

  const statusTone =
    phase.kind === 'error'
      ? 'error'
      : phase.kind === 'done' && phase.job.status === 'incomplete'
        ? 'warning'
        : phase.kind === 'done'
          ? 'success'
          : 'progress'

  return (
    <section className="generate" aria-labelledby={`${formId}-heading`}>
      <h1 id={`${formId}-heading`} className="generate__title">
        Course Generation
      </h1>

      <form className="generate__form" onSubmit={handleSubmit} noValidate>
        <label className="generate__field">
          <span className="visually-hidden">What is your learning goal?</span>
          <input
            className="generate__input"
            type="text"
            name="goal"
            autoComplete="off"
            placeholder="What is your learning goal?"
            value={fields.goal}
            disabled={busy}
            onChange={(event) => updateField('goal', event.target.value)}
            required
          />
        </label>

        {/*
          Penpot’s second Form Input repeats the goal placeholder (copy-paste).
          That slot maps to the API’s required IANA timezone; prefilled from the browser.
        */}
        <label className="generate__field">
          <span className="visually-hidden">What is your timezone?</span>
          <input
            className="generate__input"
            type="text"
            name="timezone"
            autoComplete="off"
            placeholder="What is your timezone? (e.g. America/New_York)"
            value={fields.timezone}
            disabled={busy}
            onChange={(event) => updateField('timezone', event.target.value)}
            required
          />
        </label>

        <label className="generate__field">
          <span className="visually-hidden">
            Tell me about your experience in this.
          </span>
          <input
            className="generate__input"
            type="text"
            name="level"
            autoComplete="off"
            placeholder="Tell me about your experience in this."
            value={fields.level}
            disabled={busy}
            onChange={(event) => updateField('level', event.target.value)}
            required
          />
        </label>

        <label className="generate__field">
          <span className="visually-hidden">How much time do you have?</span>
          <input
            className="generate__input"
            type="text"
            name="time_available"
            autoComplete="off"
            placeholder="How much time do you have?"
            value={fields.time_available}
            disabled={busy}
            onChange={(event) =>
              updateField('time_available', event.target.value)
            }
            required
          />
        </label>

        <button
          type="submit"
          className="generate__cta"
          disabled={!canSubmit}
          aria-busy={busy || undefined}
        >
          {busy ? 'Generating…' : 'Generate'}
        </button>
      </form>

      {statusMessage && (
        <p
          className={`generate__status generate__status--${statusTone}`}
          role={statusTone === 'error' ? 'alert' : 'status'}
          aria-live="polite"
        >
          {statusMessage}
          {phase.kind === 'done' && phase.job.detail && phase.job.status === 'succeeded' && (
            <span className="generate__status-detail">{phase.job.detail}</span>
          )}
        </p>
      )}
    </section>
  )
}
