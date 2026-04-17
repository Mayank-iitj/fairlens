import { NavLink, Outlet } from 'react-router-dom'

const links = [
  ['/', 'Home'],
  ['/dashboard', 'Dashboard'],
  ['/audit/new', 'New Audit'],
  ['/reports', 'Reports'],
  ['/monitor', 'Monitor'],
  ['/settings', 'Settings'],
]

export function AppLayout() {
  return (
    <div className="min-h-screen bg-cream text-muted">
      <header className="border-b border-caramel20 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <NavLink to="/" className="font-display text-2xl text-espresso">
            FairLens
          </NavLink>
          <nav className="flex flex-wrap gap-3 text-sm font-semibold">
            {links.map(([to, label]) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `rounded-full px-3 py-2 transition ${
                    isActive ? 'bg-caramel text-white' : 'text-espresso hover:bg-caramel10 hover:text-walnut'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
