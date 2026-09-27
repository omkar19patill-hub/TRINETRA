import { useLocation } from 'react-router-dom'
import { Card, CardContent } from '../../components/ui/Card'

const SCREEN_NAMES: Record<string, string> = {
  '/dashboard/intelligence': 'Threat Intelligence',
  '/dashboard/risk': 'Risk Analysis',
  '/dashboard/financial': 'Financial Risk',
  '/dashboard/investments': 'Investment Optimization',
  '/dashboard/simulation': 'What-if Simulation',
  '/dashboard/actions': 'Action Center',
}

/**
 * Stand-in for dashboard screens that are in scope but not yet built, so the
 * navigation never presents a dead link. Replaced screen by screen as each is
 * implemented.
 */
export default function DashboardPlaceholder() {
  const location = useLocation()
  const name = SCREEN_NAMES[location.pathname] ?? 'This screen'

  return (
    <Card>
      <CardContent className="p-10 text-center">
        <h1 className="text-xl font-semibold tracking-tight text-text-tertiary">{name}</h1>
        <p className="mx-auto mt-3 max-w-[420px] text-sm leading-relaxed text-text-primary">
          Not built yet. The backend endpoints for this screen already exist and are
          listed in FRONTEND_ARCHITECTURE.md; the interface is still to come.
        </p>
      </CardContent>
    </Card>
  )
}
