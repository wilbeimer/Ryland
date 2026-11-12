import './NavBar.css'

/** Order: middle tabs, then Generate (2nd from right), Account/profile (rightmost). */
const NAV_ITEMS = [
  { label: 'Courses', available: true },
  { label: 'Weeks', available: false },
  { label: 'Quizzes', available: false },
  { label: 'Generate', available: true },
  { label: 'Account', available: false },
] as const

export type NavLabel = (typeof NAV_ITEMS)[number]['label']

type NavBarProps = {
  active?: NavLabel
  onNavigate?: (label: NavLabel) => void
}

export function NavBar({ active = 'Courses', onNavigate }: NavBarProps) {
  return (
    <nav className="nav-bar" aria-label="Primary">
      <ul className="nav-bar__list">
        {NAV_ITEMS.map(({ label, available }) => {
          const isActive = label === active

          if (!available) {
            return (
              <li key={label}>
                <span className="nav-bar__item nav-bar__item--disabled">
                  {label}
                  <span className="visually-hidden"> (coming soon)</span>
                </span>
              </li>
            )
          }

          return (
            <li key={label}>
              <button
                type="button"
                className={
                  isActive
                    ? 'nav-bar__item nav-bar__item--active'
                    : 'nav-bar__item'
                }
                aria-current={isActive ? 'page' : undefined}
                onClick={() => onNavigate?.(label)}
              >
                {label}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
