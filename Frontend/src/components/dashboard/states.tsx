import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card, CardContent } from '../ui/Card'
import type { ApiError } from '../../lib/apiClient'

/** Skeleton placeholder for a single metric card while data loads. */
export function LoadingCard() {
  return (
    <Card>
      <CardContent className="p-6">
        <div aria-hidden className="space-y-3">
          <div className="h-3 w-24 animate-pulse rounded-sm bg-surface-strong" />
          <div className="h-8 w-40 animate-pulse rounded-sm bg-surface-strong" />
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Renders a normalised ApiError. The 404-string versus 422-array distinction is
 * already resolved in apiClient.ts, so detail is always a readable string and
 * fieldErrors is present only for validation failures.
 */
export function ErrorPanel(props: { error: ApiError; onRetry?: () => void }) {
  const { error, onRetry } = props

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="critical">
            {error.isNetworkError ? 'Backend unreachable' : `Error ${error.status}`}
          </Badge>
          <p className="text-sm text-text-secondary">{error.detail}</p>
        </div>

        {error.fieldErrors && error.fieldErrors.length > 0 ? (
          <ul className="mt-4 space-y-1 border-t border-border-default/50 pt-4">
            {error.fieldErrors.map((fieldError) => (
              <li key={fieldError.field} className="text-xs text-text-primary">
                <span className="font-semibold">{fieldError.field}</span>
                {' — '}
                {fieldError.message}
              </li>
            ))}
          </ul>
        ) : null}

        {onRetry ? (
          <div className="mt-5">
            <Button variant="secondary" size="sm" onClick={onRetry}>
              Try again
            </Button>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
