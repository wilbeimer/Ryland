import { NavLink, Outlet } from 'react-router-dom'

export default function Layout() {
   return (
      <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
         {/* Sidebar */}
         <nav style={{
            width: '220px',
            background: '#1a1a2e',
            color: 'white',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px 0',
            gap: '4px',
            flexShrink: 0,
         }}>
         <div style={{ padding: '0 20px 24px', fontSize: '18px', fontWeight: '600' }}>
          My Curriculum
        </div>

        <NavItem to="/" label="Dashboard" />
        <NavItem to="/courses" label="Courses" />
        <NavItem to="/assignments" label="Assignments" />
        <NavItem to="/grades" label="Grades" />
      </nav>

      {/* Main content */}
      <main className='main-content' style={{ flex: 1, overflow: 'auto' }}>
        <Outlet />
      </main>

      </div>
   )
   
}

function NavItem({ to, label }) {
  return (
    <NavLink
      to={to}
      end
      style={({ isActive }) => ({
        display: 'block',
        padding: '10px 20px',
        color: isActive ? 'white' : '#aaa',
        background: isActive ? '#2a2a4a' : 'transparent',
        textDecoration: 'none',
        borderLeft: isActive ? '3px solid #6c63ff' : '3px solid transparent',
        fontSize: '14px',
      })}
    >
      {label}
    </NavLink>
  )
}
