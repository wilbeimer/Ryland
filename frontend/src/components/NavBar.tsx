import './NavBar.css'

const NAV_ITEMS = [
  { label: 'Courses', available: true },
  { label: 'Generate', available: false },
  { label: 'Weeks', available: false },
  { label: 'Quizzes', available: false },
  { label: 'Account', available: false },
] as const

type NavLabel = (typeof NAV_ITEMS)[number]['label']

type NavBarProps = {
  active?: NavLabel
}

export function NavBar({ active = 'Courses' }: NavBarProps) {
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
              <span
                className={
                  isActive
                    ? 'nav-bar__item nav-bar__item--active'
                    : 'nav-bar__item'
                }
                aria-current={isActive ? 'page' : undefined}
              >
                {label}
              </span>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
