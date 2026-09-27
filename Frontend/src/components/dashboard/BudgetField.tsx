import { Button } from '../ui/Button'
import { Card, CardContent } from '../ui/Card'
import { formatInr } from './format'

export interface BudgetFieldProps {
  /** Unique per screen, so two mounted screens cannot collide on label association. */
  id: string
  /** Raw input value. Empty string means "use the default". */
  value: string
  onChange: (value: string) => void
  /** Shown as placeholder and in the caption when the input is empty. */
  defaultBudget: number
  /** Resolved budget: the parsed input, or defaultBudget when empty. */
  effectiveBudget: number
  isValid: boolean
  isRunning: boolean
  onRun: () => void
}

/** Budget entry plus run action, shared by the screens that trigger an optimization. */
export function BudgetField(props: BudgetFieldProps) {
  const { id, value, onChange, defaultBudget, effectiveBudget, isValid, isRunning, onRun } = props

  return (
    <Card className="mb-6">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-end gap-4">
          <div className="min-w-[220px] flex-1">
            <label
              htmlFor={id}
              className="block text-sm font-medium uppercase tracking-wider text-text-primary"
            >
              Budget
            </label>
            <input
              id={id}
              type="number"
              min={0}
              step={50000}
              inputMode="numeric"
              value={value}
              placeholder={String(defaultBudget)}
              onChange={(event) => onChange(event.target.value)}
              className="mt-2 w-full rounded-sm border border-border-default bg-surface-base px-3 py-2 text-sm text-text-tertiary placeholder:text-text-inverse focus:outline-none focus:ring-1 focus:ring-text-secondary"
            />
            <p className="mt-2 text-xs text-text-inverse">
              {value.trim() === ''
                ? `Defaults to ${formatInr(defaultBudget)}`
                : formatInr(effectiveBudget)}
            </p>
          </div>

          <Button onClick={onRun} loading={isRunning} disabled={!isValid}>
            {isRunning ? 'Running optimization' : 'Run optimization'}
          </Button>
        </div>

        {isValid ? null : (
          <p className="mt-3 text-xs text-risk-critical">Enter a budget of zero or more.</p>
        )}
      </CardContent>
    </Card>
  )
}
