import { useState } from 'react'

import { Badge } from '../../components/ui/Badge'
import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import { BudgetField } from '../../components/dashboard/BudgetField'
import { formatInr, formatScore, pickBudget } from '../../components/dashboard/format'
import { ErrorPanel, LoadingCard } from '../../components/dashboard/states'
import { useAssets, useRunOptimization } from '../../hooks/useOptimization'
import type { OptimizationRunResponse } from '../../types/api'

/* ------------------------------------------------------------------ *
 * dependency_resolution is typed as unknown[] on the response, so it is
 * narrowed here rather than assumed. Shape mirrors the backend's
 * ControlDependencyResolution; anything that does not match is skipped.
 * ------------------------------------------------------------------ */

interface DependencyRecord {
  control_id: string
  status: string
  bundle_cost?: number
  bundle_annual_cost?: number
  rejection_reason?: string | null
  dependencies?: unknown[]
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function toDependencyRecords(raw: unknown[] | null | undefined): DependencyRecord[] {
  if (!raw) {
    return []
  }

  const records: DependencyRecord[] = []
  for (const entry of raw) {
    if (!isRecord(entry)) {
      continue
    }
    if (typeof entry.control_id !== 'string' || typeof entry.status !== 'string') {
      continue
    }
    records.push({
      control_id: entry.control_id,
      status: entry.status,
      bundle_cost: typeof entry.bundle_cost === 'number' ? entry.bundle_cost : undefined,
      bundle_annual_cost:
        typeof entry.bundle_annual_cost === 'number' ? entry.bundle_annual_cost : undefined,
      rejection_reason:
        typeof entry.rejection_reason === 'string' ? entry.rejection_reason : null,
      dependencies: Array.isArray(entry.dependencies) ? entry.dependencies : [],
    })
  }
  return records
}

/* ------------------------------------------------------------------ *
 * Control detail lists — full reasons, not just the first
 * ------------------------------------------------------------------ */

function ControlReasonList(props: {
  heading: string
  controlIds: string[]
  reasons: Record<string, string[]> | undefined
  badgeVariant: 'success' | 'neutral'
  emptyCopy: string
}) {
  const { heading, controlIds, reasons, badgeVariant, emptyCopy } = props

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
          {heading}
          <span className="ml-2 font-normal text-text-inverse">{controlIds.length}</span>
        </h2>

        {controlIds.length === 0 ? (
          <p className="mt-3 text-sm text-text-primary">{emptyCopy}</p>
        ) : (
          <ul className="mt-4 space-y-5">
            {controlIds.map((controlId) => {
              const controlReasons = reasons ? reasons[controlId] : undefined
              const hasReasons = controlReasons && controlReasons.length > 0

              return (
                <li key={controlId} className="border-t border-border-default/40 pt-4 first:border-t-0 first:pt-0">
                  <Badge variant={badgeVariant} className="font-mono">
                    {controlId}
                  </Badge>

                  {hasReasons ? (
                    <ul className="mt-2 space-y-1">
                      {controlReasons.map((reason, index) => (
                        <li
                          key={`${controlId}-${index}`}
                          className="text-xs leading-relaxed text-text-primary"
                        >
                          {reason}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-xs text-text-inverse">No reason recorded.</p>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ *
 * Dependency resolution
 * ------------------------------------------------------------------ */

function DependencyResolution(props: { records: DependencyRecord[] }) {
  const { records } = props
  if (records.length === 0) {
    return null
  }

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
          Dependency resolution
          <span className="ml-2 font-normal text-text-inverse">{records.length}</span>
        </h2>

        <ul className="mt-4 space-y-4">
          {records.map((record) => (
            <li
              key={record.control_id}
              className="border-t border-border-default/40 pt-4 first:border-t-0 first:pt-0"
            >
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={record.status === 'selected' ? 'success' : 'neutral'} className="font-mono">
                  {record.control_id}
                </Badge>
                <span className="text-xs uppercase tracking-wider text-text-inverse">
                  {record.status}
                </span>
              </div>

              <dl className="mt-2 space-y-1 text-xs text-text-primary">
                {typeof record.bundle_cost === 'number' ? (
                  <div className="flex gap-2">
                    <dt className="text-text-inverse">Bundle cost</dt>
                    <dd>{formatInr(record.bundle_cost)}</dd>
                  </div>
                ) : null}
                {typeof record.bundle_annual_cost === 'number' ? (
                  <div className="flex gap-2">
                    <dt className="text-text-inverse">Annual cost</dt>
                    <dd>{formatInr(record.bundle_annual_cost)}</dd>
                  </div>
                ) : null}
                {record.dependencies && record.dependencies.length > 0 ? (
                  <div className="flex gap-2">
                    <dt className="text-text-inverse">Prerequisites</dt>
                    <dd>{record.dependencies.length}</dd>
                  </div>
                ) : null}
                {record.rejection_reason ? (
                  <div className="flex gap-2">
                    <dt className="text-text-inverse">Reason</dt>
                    <dd>{record.rejection_reason}</dd>
                  </div>
                ) : null}
              </dl>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ *
 * Result
 * ------------------------------------------------------------------ */

function ResultDetail(props: { result: OptimizationRunResponse }) {
  const { result } = props
  const isDemoData = result.is_benchmark === true
  const dependencyRecords = toDependencyRecords(result.dependency_resolution)

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Total cost"
          value={formatInr(result.total_cost)}
          context={`${result.selected_controls.length} controls funded`}
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Remaining budget"
          value={formatInr(result.remaining_budget)}
          context="Unallocated"
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Risk reduction"
          value={formatScore(result.risk_reduction)}
          context={`${formatScore(result.baseline_risk)} to ${formatScore(result.residual_risk)}`}
          isDemoData={isDemoData}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ControlReasonList
          heading="Funded"
          controlIds={result.selected_controls}
          reasons={result.selection_reasons}
          badgeVariant="success"
          emptyCopy="No control fitted within this budget."
        />
        <ControlReasonList
          heading="Not funded"
          controlIds={result.rejected_controls}
          reasons={result.rejection_reasons}
          badgeVariant="neutral"
          emptyCopy="Every candidate control was funded."
        />
      </div>

      <DependencyResolution records={dependencyRecords} />

      <p className="text-xs text-text-inverse">
        {result.optimization_id}
        {' · model '}
        {result.model_version}
        {' · loss avoided '}
        {formatInr(result.financial_loss_avoided)}
      </p>
    </div>
  )
}

/* ------------------------------------------------------------------ *
 * Screen
 * ------------------------------------------------------------------ */

export default function InvestmentOptimization() {
  const assets = useAssets()
  const runOptimization = useRunOptimization()

  const [budgetInput, setBudgetInput] = useState<string>('')
  const [result, setResult] = useState<OptimizationRunResponse | null>(null)

  const defaultBudget = pickBudget(assets.data)
  const effectiveBudget = budgetInput.trim() === '' ? defaultBudget : Number(budgetInput)
  const budgetIsValid = Number.isFinite(effectiveBudget) && effectiveBudget >= 0

  function handleRun() {
    if (!budgetIsValid) {
      return
    }

    const firstAsset = assets.data ? assets.data[0] : undefined

    runOptimization.mutate(
      {
        budget_limit: effectiveBudget,
        asset_id: firstAsset ? firstAsset.asset_id : undefined,
        cve_id: firstAsset ? firstAsset.cve_id : undefined,
      },
      {
        onSuccess: (data) => {
          setResult(data)
        },
      },
    )
  }

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-text-tertiary">
          Investment Optimization
        </h1>
        <p className="mt-2 max-w-[560px] text-sm text-text-primary">
          Set a budget and see exactly which controls it funds, which it does not, and the
          reasoning behind every decision.
        </p>
      </header>

      <BudgetField
        id="budget"
        value={budgetInput}
        onChange={setBudgetInput}
        defaultBudget={defaultBudget}
        effectiveBudget={effectiveBudget}
        isValid={budgetIsValid}
        isRunning={runOptimization.isPending}
        onRun={handleRun}
      />

      {runOptimization.isPending ? (
        <div>
          <p className="sr-only">Running optimization</p>
          <div className="grid gap-4 sm:grid-cols-3">
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </div>
        </div>
      ) : null}

      {runOptimization.isError && !runOptimization.isPending ? (
        <ErrorPanel error={runOptimization.error} onRetry={handleRun} />
      ) : null}

      {result && !runOptimization.isPending && !runOptimization.isError ? (
        <ResultDetail result={result} />
      ) : null}

      {!result && !runOptimization.isPending && !runOptimization.isError ? (
        <Card>
          <CardContent className="p-10">
            <h2 className="text-lg font-semibold tracking-tight text-text-tertiary">
              No optimization run yet
            </h2>
            <p className="mt-3 max-w-[460px] text-sm leading-relaxed text-text-primary">
              Choose a budget above and run an optimization. This screen shows the full
              decision detail, including every reason a control was funded or rejected.
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
