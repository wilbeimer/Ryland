import './GeneratePage.css'

/**
 * Placeholder Generate tab shell.
 * Swap this component's body when the real Generate UI lands.
 */
export function GeneratePage() {
  return (
    <section className="generate" aria-labelledby="generate-heading">
      <h1 id="generate-heading" className="generate__title">
        Generate
      </h1>
      <p className="generate__copy">
        Build a new course from a prompt. This workspace is a stub — the full
        generator UI will replace this page.
      </p>
      <button type="button" className="generate__cta" disabled>
        Start generating
        <span className="visually-hidden"> (coming soon)</span>
      </button>
    </section>
  )
}
