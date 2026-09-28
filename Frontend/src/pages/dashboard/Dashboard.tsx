import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import { getRiskChange, partitionByProvenance } from '../../lib/apiClient'
import { formatInr, formatScore, pickBudget } from '../../components/dashboard/format'
import { ErrorPanel, LoadingCard } from '../../components/dashboard/states'
import { useAssets, useOptimizations, useRunOptimization } from '../../hooks/useOptimization'
import type { OptimizationRunResponse, RiskChangeResponse } from '../../types/api'


/* ------------------------------------------------------------------ *
 * Benchmark notice
 * ------------------------------------------------------------------ */

/**
 * Benchmark scenarios are surfaced but kept subordinate: counted and labelled
 * as demonstration data, never folded into the metrics as a real result.
 */
function BenchmarkNotice(props: { count: number }) {
  const { count } = props
  if (count === 0) {
    return null
  }

  const plural = count === 1 ? '' : 's'

  return (
    <p className="mt-6 border-t border-border-default/50 pt-5 text-xs text-text-inverse">
      {count} benchmark scenario{plural} available as demonstration data. Not shown as a
      real result.
    </p>
  )
}

/* ------------------------------------------------------------------ *
 * Prompt to run
 * ------------------------------------------------------------------ */

function RunPrompt(props: {
  title: string
  description: string
  benchmarkCount: number
  isRunning: boolean
  onRun: () => void
}) {
  const { title, description, benchmarkCount, isRunning, onRun } = props

  return (
    <Card>
      <CardContent className="p-10 text-center">
        <h2 className="text-lg font-semibold tracking-tight text-text-tertiary">{title}</h2>
        <p className="mx-auto mt-3 max-w-[460px] text-sm leading-relaxed text-text-primary">
          {description}
        </p>

        <div className="mt-6 flex justify-center">
          <Button onClick={onRun} loading={isRunning}>
            {isRunning ? 'Running optimization' : 'Run optimization'}
          </Button>
        </div>

        <BenchmarkNotice count={benchmarkCount} />
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ *
 * Result
 * ------------------------------------------------------------------ */

function ResultView(props: { result: OptimizationRunResponse; isDemoData: boolean }) {
  const { result, isDemoData } = props
  const selectionReasons = result.selection_reasons

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Risk reduction"
          value={formatScore(result.risk_reduction)}
          context={`${formatScore(result.baseline_risk)} to ${formatScore(result.residual_risk)}`}
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Loss avoided / year"
          value={formatInr(result.financial_loss_avoided)}
          context={`EAL ${formatInr(result.baseline_eal)} to ${formatInr(result.residual_eal)}`}
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Investment"
          value={formatInr(result.total_cost)}
          context={`${formatInr(result.remaining_budget)} of budget unallocated`}
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Controls funded"
          value={result.selected_controls.length}
          context={`${result.rejected_controls.length} not funded`}
          isDemoData={isDemoData}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-primary">
              Funded controls
            </h3>
            {result.selected_controls.length === 0 ? (
              <p className="mt-3 text-sm text-text-primary">
                No control fitted within this budget.
              </p>
            ) : (
              <ul className="mt-4 space-y-3">
                {result.selected_controls.map((controlId) => {
                  const reasons = selectionReasons ? selectionReasons[controlId] : undefined
                  const firstReason = reasons && reasons.length > 0 ? reasons[0] : null

                  return (
                    <li key={controlId}>
                      <Badge variant="success">{controlId}</Badge>
                      {firstReason ? (
                        <p className="mt-1.5 text-xs leading-relaxed text-text-primary">
                          {firstReason}
                        </p>
                      ) : null}
                    </li>
                  )
                })}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-primary">
              Not funded
            </h3>
            {result.rejected_controls.length === 0 ? (
              <p className="mt-3 text-sm text-text-primary">
                Every candidate control was funded.
              </p>
            ) : (
              <ul className="mt-4 flex flex-wrap gap-2">
                {result.rejected_controls.map((controlId) => (
                  <li key={controlId}>
                    <Badge variant="neutral">{controlId}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <p className="text-xs text-text-inverse">
        {result.optimization_id}
        {' · model '}
        {result.model_version}
      </p>
    </div>
  )
}

/* ------------------------------------------------------------------ *
 * Run-over-Run Risk Change (Phase 3)
 * ------------------------------------------------------------------ */

function RiskChangeSection() {
  const { data: change } = useQuery<RiskChangeResponse>({
    queryKey: ['risk-change'],
    queryFn: getRiskChange,
  })

  if (!change || !change.has_history) {
    return null
  }

  if (!change.has_baseline) {
    return (
      <section className="mb-8">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
          Baseline Risk Assessment
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <MetricCard
            label="Current Exposure"
            value={formatInr(change.current_exposure ?? 0)}
            context="Baseline Expected Annual Loss (EAL)"
            source="Assessment Storage"
          />
          <MetricCard
            label="Average Risk"
            value={formatScore(change.current_average_risk ?? 0)}
            context={`${change.current_critical_assets ?? 0} critical, ${change.current_high_risk_assets ?? 0} high-risk assets`}
            source="Assessment Storage"
          />
          <MetricCard
            label="Historical Comparison"
            value="Baseline Set"
            context="Run another bulk assessment to compute run-over-run risk change."
            source="Assessment Storage"
          />
        </div>
      </section>
    )
  }

  const absChange = change.absolute_change ?? 0
  const isExpIncreased = absChange > 0
  const pctStr =
    change.percentage_change !== null && change.percentage_change !== undefined
      ? `${change.percentage_change > 0 ? '+' : ''}${change.percentage_change.toFixed(1)}%`
      : 'N/A'

  const avgDiff = change.average_risk_change ?? 0
  const avgDiffStr = `${avgDiff > 0 ? '+' : ''}${avgDiff.toFixed(1)} pts`

  const critDiff = change.critical_assets_change ?? 0
  const critDiffStr = `${critDiff > 0 ? '+' : ''}${critDiff}`

  const highDiff = change.high_risk_assets_change ?? 0
  const highDiffStr = `${highDiff > 0 ? '+' : ''}${highDiff}`

  return (
    <section className="mb-8">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
          Run-over-Run Risk Change
        </h2>
        <span className="text-xs text-text-inverse">
          Latest vs Previous Assessment Snapshot
        </span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Current Exposure"
          value={formatInr(change.current_exposure ?? 0)}
          context={`Previous: ${formatInr(change.previous_exposure ?? 0)}`}
          source="Assessment Storage"
        />
        <MetricCard
          label="Absolute Change"
          value={`${isExpIncreased ? '+' : ''}${formatInr(absChange)}`}
          context={`Percentage: ${pctStr}`}
          source="Assessment Storage"
        />
        <MetricCard
          label="Average Risk Change"
          value={avgDiffStr}
          context={`From ${formatScore(change.previous_average_risk ?? 0)} to ${formatScore(change.current_average_risk ?? 0)}`}
          source="Assessment Storage"
        />
        <MetricCard
          label="Asset Tier Shifts"
          value={`Crit: ${critDiffStr} | High: ${highDiffStr}`}
          context={`Critical: ${change.previous_critical_assets ?? 0} → ${change.current_critical_assets ?? 0}, High: ${change.previous_high_risk_assets ?? 0} → ${change.current_high_risk_assets ?? 0}`}
          source="Assessment Storage"
        />
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ *
 * Screen
 * ------------------------------------------------------------------ */

export default function Dashboard() {
  const optimizations = useOptimizations()
  const assets = useAssets()
  const runOptimization = useRunOptimization()

  const [result, setResult] = useState<OptimizationRunResponse | null>(null)

  function handleRun() {
    const firstAsset = assets.data ? assets.data[0] : undefined

    runOptimization.mutate(
      {
        budget_limit: pickBudget(assets.data),
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

  const heading = (
    <header className="mb-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text-tertiary">Overview</h1>
      <p className="mt-2 text-sm text-text-primary">
        Current risk position, and where the next rupee of budget should go.
      </p>
    </header>
  )

  if (optimizations.isPending) {
    return (
      <div>
        {heading}
        <p className="sr-only">Loading optimizations</p>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
        </div>
      </div>
    )
  }

  if (optimizations.isError) {
    return (
      <div>
        {heading}
        <ErrorPanel
          error={optimizations.error}
          onRetry={() => {
            void optimizations.refetch()
          }}
        />
      </div>
    )
  }

  // Requirement: benchmark data must never be presented as a real result.
  const partitioned = partitionByProvenance(optimizations.data ?? [])
  const realCount = partitioned.real.length
  const benchmarkCount = partitioned.benchmark.length

  if (result) {
    return (
      <div>
        {heading}
        <RiskChangeSection />
        <ResultView result={result} isDemoData={result.is_benchmark === true} />
      </div>
    )
  }

  const hasRealData = realCount > 0
  const plural = realCount === 1 ? '' : 's'

  return (
    <div>
      {heading}
      <RiskChangeSection />
      <RunPrompt
        title={
          hasRealData
            ? `${realCount} optimization${plural} on record`
            : 'No optimization has been run yet'
        }
        description={
          hasRealData
            ? 'Run a fresh optimization to see current numbers.'
            : 'Run one to see your current risk position, the modelled financial exposure, and where the next rupee of security budget should go.'
        }
        benchmarkCount={benchmarkCount}
        isRunning={runOptimization.isPending}
        onRun={handleRun}
      />

      {runOptimization.error ? (
        <div className="mt-6">
          <ErrorPanel error={runOptimization.error} />
        </div>
      ) : null}
    </div>
  )
}

