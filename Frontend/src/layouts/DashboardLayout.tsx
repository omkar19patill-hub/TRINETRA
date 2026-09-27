import { Link, NavLink, Outlet } from 'react-router-dom'
import { cn } from '../lib/utils'

/**
 * Shell for the /dashboard product surface.
 *
 * All seven in-scope screens are listed (see docs/UI_UX.md), but only the
 * overview is built. The rest route to a placeholder rather than a dead link.
 * Continuous Monitoring is deliberately absent: it is deferred pending a
 * backend persistence decision.
 */

interface NavItem {
  to: string
  label: string
  built: boolean
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Overview', built: true },
  { to: '/dashboard/intelligence', label: 'Threat Intelligence', built: false },
  { to: '/dashboard/risk', label: 'Risk Analysis', built: false },
  { to: '/dashboard/financial', label: 'Financial Risk', built: false },
  { to: '/dashboard/investments', label: 'Investment Optimization', built: false },
  { to: '/dashboard/simulation', label: 'What-if Simulation', built: false },
  { to: '/dashboard/actions', label: 'Action Center', built: false },
]

export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-surface-base text-text-secondary">
      <div className="mx-auto flex max-w-[1320px] flex-col md:flex-row">
        <aside className="w-full border-b border-border-default md:min-h-screen md:w-64 md:shrink-0 md:border-b-0 md:border-r">
          <div className="p-6">
            <Link to="/" className="flex items-center gap-2">
              <img src="/images/symbol.png" alt="" className="h-6 w-6 object-contain" />
              <span className="text-sm font-semibold tracking-tight text-text-tertiary">
                TRINETRA
              </span>
            </Link>
          </div>

          <nav aria-label="Dashboard sections" className="px-3 pb-6">
            <ul className="space-y-1">
              {NAV_ITEMS.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === '/dashboard'}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center justify-between rounded-sm px-3 py-2 text-sm transition-colors',
                        isActive
                          ? 'bg-surface-strong text-text-tertiary'
                          : 'text-text-primary hover:bg-surface-strong hover:text-text-secondary',
                      )
                    }
                  >
                    <span>{item.label}</span>
                    {item.built ? null : (
                      <span className="text-[10px] uppercase tracking-wider text-text-inverse">
                        Soon
                      </span>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        <main className="min-w-0 flex-1 p-6 md:p-10">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
