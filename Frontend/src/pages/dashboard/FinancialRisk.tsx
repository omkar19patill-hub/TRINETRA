import { useState } from 'react'

import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import { BudgetField } from '../../components/dashboard/BudgetField'
import { formatInr, formatScore, pickBudget } from '../../components/dashboard/format'
import { ErrorPanel, LoadingCard } from '../../components/dashboard/states'
import { useAssets, useRunOptimization } from '../../hooks/useOptimization'
import type { OptimizationRunResponse } from '../../types/api'

/** Percentage of baseline exposure removed. Guards against a zero baseline. */
function reductionPercent(baseline: number, residual: number): string | null {
  if (!Number.isFinite(baseline) || baseline <= 0) {
    return null
  }
  const pct = ((baseline - residual) / baseline) * 100
  return `${pct.toFixed(1)}% lower than baseline`
}

/* ------------------------------------------------------------------ *
 * Result — financial side only
 * ------------------------------------------------------------------ */

function FinancialDetail(props: { result: OptimizationRunResponse }) {
  const { result } = props
  const isDemoData = result.is_benchmark === true

  const ealReduction = reductionPercent(result.baseline_eal, result.residual_eal)
  const scoreReduction = reductionPercent(result.baseline_risk, result.residual_risk)

  return (
    <div className="space-y-6">
      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
          Expected annual loss
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <MetricCard
            label="Baseline EAL"
            value={formatInr(result.baseline_eal)}
            context="Modelled exposure before controls"
            isDemoData={isDemoData}
          />
          <MetricCard
            label="Residual EAL"
            value={formatInr(result.residual_eal)}
            context={ealReduction ?? 'Modelled exposure after controls'}
            isDemoData={isDemoData}
          />
          <MetricCard
            label="Loss avoided / year"
            value={formatInr(result.financial_loss_avoided)}
            context={`Against ${formatInr(result.total_cost)} invested`}
            isDemoData={isDemoData}
          />
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
          Risk score
        </h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <MetricCard
            label="Baseline risk"
            value={formatScore(result.baseline_risk)}
            context="Score before controls"
            isDemoData={isDemoData}
          />
          <MetricCard
            label="Residual risk"
            value={formatScore(result.residual_risk)}
            context={scoreReduction ?? 'Score after controls'}
            isDemoData={isDemoData}
          />
          <MetricCard
            label="Risk reduction"
            value={formatScore(result.risk_reduction)}
            context="Points removed"
            isDemoData={isDemoData}
          />
        </div>
      </section>

      <p className="text-xs text-text-inverse">
        {result.optimization_id}
        {' · model '}
        {result.model_version}
      </p>
    </div>
  )
}

/* ------------------------------------------------------------------ *
 * Screen
 * ------------------------------------------------------------------ */

export default function FinancialRisk() {
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
          Financial Risk
        </h1>
        <p className="mt-2 max-w-[560px] text-sm text-text-primary">
          What the modelled exposure costs per year, and how much of it a given budget
          removes.
        </p>
      </header>

      <BudgetField
        id="financial-budget"
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
        <FinancialDetail result={result} />
      ) : null}

      {!result && !runOptimization.isPending && !runOptimization.isError ? (
        <Card>
          <CardContent className="p-10">
            <h2 className="text-lg font-semibold tracking-tight text-text-tertiary">
              No optimization run yet
            </h2>
            <p className="mt-3 max-w-[460px] text-sm leading-relaxed text-text-primary">
              Choose a budget above and run an optimization to see the modelled financial
              exposure before and after controls are applied.
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
