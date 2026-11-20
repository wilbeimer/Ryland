import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import type { GenerateCourseRequest } from '../api'
import type { GenerationPhase } from '../useGenerationJob'
import './GeneratePage.css'

type FormFields = {
  goal: string
  timezone: string
  level: string
  time_available: string
}

export type GeneratePageProps = {
  phase: GenerationPhase
  onBeginGeneration: (body: GenerateCourseRequest) => void | Promise<void>
  onSubmitAnswers: (answers: string[]) => void | Promise<void>
  /** Failed clarifying-answer submit; survives poll updates. */
  answerError?: string | null
  /** True after a 409 resume until that build finishes. */
  resumedFromConflict?: boolean
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

function clarifyingQuestions(phase: GenerationPhase): string[] | null {
  if (phase.kind !== 'awaiting_input' && phase.kind !== 'answering') {
    return null
  }
  if (!phase.job.questions || phase.job.questions.length === 0) {
    return null
  }
  return phase.job.questions
}

type ClarifyingBoxProps = {
  formId: string
  questions: string[]
  submitting: boolean
  error: string | null
  onSubmitAnswers: (answers: string[]) => void | Promise<void>
}

/** Own answer drafts so a new question set remounts clean state via `key`. */
function ClarifyingBox({
  formId,
  questions,
  submitting,
  error,
  onSubmitAnswers,
}: ClarifyingBoxProps) {
  const headingRef = useRef<HTMLHeadingElement>(null)
  const firstInputRef = useRef<HTMLInputElement>(null)
  const [answerDrafts, setAnswerDrafts] = useState(() =>
    questions.map(() => ''),
  )

  useEffect(() => {
    const heading = headingRef.current
    if (heading) {
      heading.focus()
      return
    }
    firstInputRef.current?.focus()
  }, [])

  function handleClarifySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) {
      return
    }
    const answers = answerDrafts.map((value) => value.trim())
    if (answers.length !== questions.length || answers.some((value) => !value)) {
      return
    }
    void onSubmitAnswers(answers)
  }

  const canAnswer =
    !submitting &&
    answerDrafts.length === questions.length &&
    answerDrafts.every((value) => value.trim() !== '')

  return (
    <form
      className="generate__clarify"
      onSubmit={handleClarifySubmit}
      noValidate
      aria-labelledby={`${formId}-clarify-heading`}
    >
      <h2
        id={`${formId}-clarify-heading`}
        className="generate__clarify-title"
        ref={headingRef}
        tabIndex={-1}
      >
        A few clarifying questions
      </h2>
      <p className="generate__clarify-copy">
        Answer these so generation can continue.
      </p>

      {questions.map((question, index) => (
        <label key={`${index}-${question}`} className="generate__clarify-field">
          <span className="generate__clarify-question">{question}</span>
          <input
            ref={index === 0 ? firstInputRef : undefined}
            className="generate__input"
            type="text"
            name={`clarify-${index}`}
            autoComplete="off"
            maxLength={2000}
            value={answerDrafts[index] ?? ''}
            disabled={submitting}
            onChange={(event) => {
              const value = event.target.value
              setAnswerDrafts((prev) => {
                const next = [...prev]
                next[index] = value
                return next
              })
            }}
            required
          />
        </label>
      ))}

      <button
        type="submit"
        className="generate__cta"
        disabled={!canAnswer}
        aria-busy={submitting || undefined}
      >
        {submitting ? 'Submitting…' : 'Continue'}
      </button>

      {error && (
        <p className="generate__status generate__status--error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}

/**
 * Course generation form (Penpot Generation page).
 * Job polling lives in App via useGenerationJob so tab switches don't abort it.
 */
export function GeneratePage({
  phase,
  onBeginGeneration,
  onSubmitAnswers,
  answerError = null,
  resumedFromConflict = false,
}: GeneratePageProps) {
  const formId = useId()
  const [fields, setFields] = useState<FormFields>(() =>
    emptyFields(detectTimezone()),
  )

  const questions = clarifyingQuestions(phase)
  const showClarifying = Boolean(questions?.length)
  const answering = phase.kind === 'answering'

  function updateField<K extends keyof FormFields>(key: K, value: FormFields[K]) {
    setFields((prev) => ({ ...prev, [key]: value }))
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (
      !allFieldsFilled(fields) ||
      phase.kind === 'submitting' ||
      phase.kind === 'polling' ||
      phase.kind === 'awaiting_input' ||
      phase.kind === 'answering'
    ) {
      return
    }

    void onBeginGeneration({
      goal: fields.goal.trim(),
      level: fields.level.trim(),
      time_available: fields.time_available.trim(),
      timezone: fields.timezone.trim(),
    })
  }

  const busy =
    phase.kind === 'submitting' ||
    phase.kind === 'polling' ||
    phase.kind === 'awaiting_input' ||
    phase.kind === 'answering'
  const canSubmit = allFieldsFilled(fields) && !busy

  const statusMessage = (() => {
    if (showClarifying && questions) {
      const count = questions.length
      const noun = count === 1 ? 'question' : 'questions'
      return `Generation paused: ${count} ${noun}`
    }
    if (phase.kind === 'submitting') {
      return 'Starting course generation…'
    }
    if (phase.kind === 'answering') {
      return 'Resuming course generation…'
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

  const statusDetail =
    phase.kind === 'done' &&
    phase.job.detail &&
    phase.job.status === 'succeeded'
      ? phase.job.detail
      : null

  const showConflictNotice =
    resumedFromConflict &&
    (phase.kind === 'submitting' ||
      phase.kind === 'polling' ||
      phase.kind === 'awaiting_input' ||
      phase.kind === 'answering')

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

      {showClarifying && questions && (
        <ClarifyingBox
          key={questions.join('\0')}
          formId={formId}
          questions={questions}
          submitting={answering}
          error={answerError}
          onSubmitAnswers={onSubmitAnswers}
        />
      )}

      {showConflictNotice && (
        <p className="generate__notice" role="status">
          A build was already running. Showing its progress instead.
        </p>
      )}

      <p
        className={`generate__status generate__status--${statusTone}${
          statusMessage ? '' : ' generate__status--empty'
        }`}
        role="status"
        aria-live="polite"
      >
        {statusMessage}
        {statusDetail && (
          <span className="generate__status-detail">{statusDetail}</span>
        )}
      </p>
    </section>
  )
}
