import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import { ErrorPanel, LoadingCard } from '../../components/dashboard/states'
import { formatInr, formatScore } from '../../components/dashboard/format'
import { api, partitionByProvenance } from '../../lib/apiClient'
import type { ApiError } from '../../lib/apiClient'
import { useOptimizations } from '../../hooks/useOptimization'
import type {
  BeforeAfterRequest,
  BeforeAfterResponse,
  MarginalBudgetResponse,
  OptimizationSummary,
  RiskSnapshot,
} from '../../types/api'

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`
}

/** Most recently created real optimization, or null when none exist. */
function latestReal(records: OptimizationSummary[] | undefined): OptimizationSummary | null {
  if (!records || records.length === 0) {
    return null
  }
  const { real } = partitionByProvenance(records)
  if (real.length === 0) {
    return null
  }
  const sorted = [...real].sort((a, b) => (a.created_at < b.created_at ? 1 : -1))
  return sorted[0]
}

/* ------------------------------------------------------------------ *
 * Empty state — no real optimization to simulate against
 * ------------------------------------------------------------------ */

export function NoOptimizationYet(props: { what: string }) {
  const { what } = props

  return (
    <Card>
      <CardContent className="p-10">
        <h2 className="text-lg font-semibold tracking-tight text-text-tertiary">
          No optimization to work from
        </h2>
        <p className="mt-3 max-w-[500px] text-sm leading-relaxed text-text-primary">
          {what} needs a real optimization result. Run one first — benchmark
          scenarios are demonstration data and are deliberately not used here.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/dashboard/investments">
            <Button>Run an optimization</Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="secondary">Back to overview</Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ *
 * Before / after
 * ------------------------------------------------------------------ */

function SnapshotColumn(props: { title: string; snapshot: RiskSnapshot; muted?: boolean }) {
  const { title, snapshot, muted } = props

  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-text-inverse">{title}</h3>
      <p
        className={`mt-2 text-3xl font-bold ${muted ? 'text-text-secondary' : 'text-text-tertiary'}`}
      >
        {formatScore(snapshot.risk_score)}
      </p>
      <div className="mt-2">
        <Badge variant="neutral">{snapshot.risk_level}</Badge>
      </div>
      <dl className="mt-4 space-y-1.5 text-xs">
        <div className="flex justify-between gap-4">
          <dt className="text-text-inverse">Expected annual loss</dt>
          <dd className="text-text-primary">{formatInr(snapshot.expected_annual_loss)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-text-inverse">Loss magnitude</dt>
          <dd className="text-text-primary">{formatInr(snapshot.total_loss_magnitude)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-text-inverse">Likelihood</dt>
          <dd className="text-text-primary">{formatPercent(snapshot.likelihood * 100)}</dd>
        </div>
      </dl>
    </div>
  )
}

function SimulationResult(props: { result: BeforeAfterResponse }) {
  const { result } = props
  const isDemoData = result.is_benchmark === true
  const deltas = result.deltas

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Risk reduction"
          value={formatPercent(deltas.risk_reduction_percent)}
          context={`${formatScore(deltas.risk_reduction_points)} points removed`}
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Loss avoided"
          value={formatInr(deltas.financial_loss_avoided)}
          context={`${formatPercent(deltas.financial_loss_avoided_percent)} of exposure`}
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Net benefit"
          value={formatInr(deltas.net_annual_financial_benefit)}
          context={`ROSI ${deltas.return_on_security_investment.toFixed(2)}x`}
          isDemoData={isDemoData}
        />
      </div>

      <Card>
        <CardContent className="p-6">
          <h2 className="mb-5 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
            Before and after
          </h2>
          <div className="grid gap-8 sm:grid-cols-2">
            <SnapshotColumn title="Before — no controls" snapshot={result.baseline} muted />
            <SnapshotColumn title="After — controls applied" snapshot={result.residual} />
          </div>

          <div className="mt-6 border-t border-border-default/50 pt-5">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-inverse">
              Controls applied
              <span className="ml-2 font-normal">{result.controls_applied.length}</span>
            </h3>
            {result.controls_applied.length === 0 ? (
              <p className="mt-2 text-sm text-text-primary">
                No control fitted within this budget.
              </p>
            ) : (
              <ul className="mt-3 flex flex-wrap gap-2">
                {result.controls_applied.map((controlId) => (
                  <li key={controlId}>
                    <Badge variant="success" className="font-mono">
                      {controlId}
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-4 text-xs text-text-inverse">
              Investment {formatInr(deltas.total_investment_cost)}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

/* ------------------------------------------------------------------ *
 * Marginal budget
 * ------------------------------------------------------------------ */

function MarginalBudget(props: { optimizationId: string }) {
  const { optimizationId } = props

  const marginal = useQuery<MarginalBudgetResponse, ApiError>({
    queryKey: ['decision', optimizationId, 'marginal-budget'],
    queryFn: () =>
      api.get<MarginalBudgetResponse>(`/decision/${optimizationId}/marginal-budget`),
    retry: false,
  })

  if (marginal.isPending) {
    return <LoadingCard />
  }

  if (marginal.isError) {
    return <ErrorPanel error={marginal.error} onRetry={() => void marginal.refetch()} />
  }

  const data = marginal.data

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
          Each additional rupee
        </h2>
        <p className="mt-2 max-w-[60ch] text-xs text-text-primary">{data.recommendation}</p>

        {data.diminishing_returns_observed ? (
          <div className="mt-3">
            <Badge variant="medium">Diminishing returns observed</Badge>
          </div>
        ) : null}

        <ul className="mt-5 space-y-4">
          {data.evaluations.map((evaluation) => (
            <li
              key={evaluation.total_budget}
              className="border-t border-border-default/40 pt-4 first:border-t-0 first:pt-0"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="text-sm text-text-tertiary">
                  +{formatInr(evaluation.additional_budget)}
                </span>
                <span className="font-mono text-xs text-text-primary">
                  {evaluation.marginal_reduction_per_rupee.toFixed(2)} per ₹
                </span>
              </div>
              <p className="mt-1 text-xs text-text-inverse">
                Total {formatInr(evaluation.total_budget)} · buys{' '}
                {formatInr(evaluation.additional_risk_reduction)} more reduction ·{' '}
                {evaluation.efficiency_assessment}
              </p>
              <p className="mt-1.5 text-xs leading-relaxed text-text-primary">
                {evaluation.explanation}
              </p>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ *
 * Screen
 * ------------------------------------------------------------------ */

export default function WhatIfSimulation() {
  const optimizations = useOptimizations()
  const [budgetInput, setBudgetInput] = useState<string>('')
  const [result, setResult] = useState<BeforeAfterResponse | null>(null)

  const simulate = useMutation<BeforeAfterResponse, ApiError, BeforeAfterRequest>({
    mutationFn: (request) => api.post<BeforeAfterResponse>('/optimization/before-after', request),
    onSuccess: (data) => setResult(data),
  })

  const heading = (
    <header className="mb-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text-tertiary">
        What-if Simulation
      </h1>
      <p className="mt-2 max-w-[560px] text-sm text-text-primary">
        Move the budget and see how the risk position changes, without committing the
        result.
      </p>
    </header>
  )

  if (optimizations.isPending) {
    return (
      <div>
        {heading}
        <p className="sr-only">Loading optimizations</p>
        <div className="grid gap-4 sm:grid-cols-3">
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
        <ErrorPanel error={optimizations.error} onRetry={() => void optimizations.refetch()} />
      </div>
    )
  }

  const baseline = latestReal(optimizations.data)

  if (!baseline) {
    return (
      <div>
        {heading}
        <NoOptimizationYet what="Simulating a different budget" />
      </div>
    )
  }

  const effectiveBudget =
    budgetInput.trim() === '' ? baseline.budget_limit : Number(budgetInput)
  const budgetIsValid = Number.isFinite(effectiveBudget) && effectiveBudget >= 0

  function handleSimulate() {
    if (!budgetIsValid || !baseline) {
      return
    }
    simulate.mutate({
      run_parameters: {
        budget_limit: effectiveBudget,
        // A simulation must not persist into the decision store.
        record_to_decision_store: false,
      },
    })
  }

  return (
    <div>
      {heading}

      <Card className="mb-6">
        <CardContent className="p-6">
          <p className="text-xs uppercase tracking-wider text-text-inverse">Simulating against</p>
          <p className="mt-1 font-mono text-sm text-text-tertiary">{baseline.optimization_id}</p>
          <p className="mt-1 text-xs text-text-primary">
            {baseline.title} · committed budget {formatInr(baseline.budget_limit)}
          </p>

          <div className="mt-5 flex flex-wrap items-end gap-4 border-t border-border-default/50 pt-5">
            <div className="min-w-[220px] flex-1">
              <label
                htmlFor="simulation-budget"
                className="block text-sm font-medium uppercase tracking-wider text-text-primary"
              >
                Simulated budget
              </label>
              <input
                id="simulation-budget"
                type="number"
                min={0}
                step={50000}
                inputMode="numeric"
                value={budgetInput}
                placeholder={String(baseline.budget_limit)}
                onChange={(event) => setBudgetInput(event.target.value)}
                className="mt-2 w-full rounded-sm border border-border-default bg-surface-base px-3 py-2 text-sm text-text-tertiary placeholder:text-text-inverse focus:outline-none focus:ring-1 focus:ring-text-secondary"
              />
              <p className="mt-2 text-xs text-text-inverse">
                {budgetInput.trim() === ''
                  ? `Defaults to the committed ${formatInr(baseline.budget_limit)}`
                  : formatInr(effectiveBudget)}
              </p>
            </div>

            <Button onClick={handleSimulate} loading={simulate.isPending} disabled={!budgetIsValid}>
              {simulate.isPending ? 'Simulating' : 'Simulate'}
            </Button>
          </div>

          {budgetIsValid ? null : (
            <p className="mt-3 text-xs text-risk-critical">Enter a budget of zero or more.</p>
          )}
        </CardContent>
      </Card>

      {simulate.isPending ? (
        <div className="mb-6">
          <p className="sr-only">Running simulation</p>
          <div className="grid gap-4 sm:grid-cols-3">
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </div>
        </div>
      ) : null}

      {simulate.isError && !simulate.isPending ? (
        <div className="mb-6">
          <ErrorPanel error={simulate.error} onRetry={handleSimulate} />
        </div>
      ) : null}

      {result && !simulate.isPending && !simulate.isError ? (
        <div className="mb-6">
          <SimulationResult result={result} />
        </div>
      ) : null}

      {!result && !simulate.isPending && !simulate.isError ? (
        <Card className="mb-6">
          <CardContent className="p-10">
            <h2 className="text-lg font-semibold tracking-tight text-text-tertiary">
              No simulation run yet
            </h2>
            <p className="mt-3 max-w-[460px] text-sm leading-relaxed text-text-primary">
              Adjust the budget above and simulate. Results are not saved to the decision
              store.
            </p>
          </CardContent>
        </Card>
      ) : null}

      <MarginalBudget optimizationId={baseline.optimization_id} />
    </div>
  )
}
