import './NavBar.css'

const NAV_ITEMS = [
  'Courses',
  'Generate',
  'Weeks',
  'Quizzes',
  'Account',
] as const

type NavBarProps = {
  active?: (typeof NAV_ITEMS)[number]
}

export function NavBar({ active = 'Courses' }: NavBarProps) {
  return (
    <nav className="nav-bar" aria-label="Primary">
      <ul className="nav-bar__list">
        {NAV_ITEMS.map((label) => (
          <li key={label}>
            <a
              className={
                label === active
                  ? 'nav-bar__item nav-bar__item--active'
                  : 'nav-bar__item'
              }
              href={label === 'Courses' ? '/' : `#${label.toLowerCase()}`}
              aria-current={label === active ? 'page' : undefined}
            >
              {label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
