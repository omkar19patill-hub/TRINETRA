import { useQuery } from '@tanstack/react-query'

import { Badge } from '../../components/ui/Badge'
import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import { ErrorPanel, LoadingCard } from '../../components/dashboard/states'
import { formatInr } from '../../components/dashboard/format'
import { api, partitionByProvenance } from '../../lib/apiClient'
import type { ApiError } from '../../lib/apiClient'
import { useOptimizations } from '../../hooks/useOptimization'
import { NoOptimizationYet } from './WhatIfSimulation'
import type {
  AlternativePortfolio,
  AlternativesResponse,
  ControlExplanation,
  OpportunityCostResponse,
  OptimizationSummary,
} from '../../types/api'

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

function signed(value: number, format: (n: number) => string): string {
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${format(value)}`
}

/* ------------------------------------------------------------------ *
 * Chosen portfolio
 * ------------------------------------------------------------------ */

function ChosenPortfolio(props: { data: AlternativesResponse; chosen: AlternativePortfolio }) {
  const { data, chosen } = props
  const isDemoData = data.is_benchmark === true

  return (
    <section>
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
        The decision
      </h2>

      <div className="mb-4 grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Chosen portfolio"
          value={chosen.objective}
          context={chosen.portfolio_id}
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Risk reduction"
          value={formatInr(chosen.risk_reduction)}
          context={`Residual ${formatInr(chosen.residual_risk)}`}
          isDemoData={isDemoData}
        />
        <MetricCard
          label="Cost"
          value={formatInr(chosen.total_cost)}
          context={
            typeof chosen.roi === 'number'
              ? `ROI ${chosen.roi.toFixed(2)}x · ${chosen.implementation_days} days`
              : `${chosen.implementation_days} days`
          }
          isDemoData={isDemoData}
        />
      </div>

      <Card>
        <CardContent className="p-6">
          <p className="max-w-[70ch] text-sm leading-relaxed text-text-primary">
            {data.decision_summary}
          </p>
          <ul className="mt-4 flex flex-wrap gap-2">
            {chosen.selected_controls.map((controlId) => (
              <li key={controlId}>
                <Badge variant="success" className="font-mono">
                  {controlId}
                </Badge>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </section>
  )
}

/* ------------------------------------------------------------------ *
 * Alternatives considered
 * ------------------------------------------------------------------ */

function AlternativesConsidered(props: {
  alternatives: AlternativePortfolio[]
  chosenId: string
}) {
  const { alternatives, chosenId } = props
  const others = alternatives.filter((portfolio) => portfolio.portfolio_id !== chosenId)

  if (others.length === 0) {
    return null
  }

  return (
    <section>
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
        Alternatives considered
        <span className="ml-2 font-normal text-text-inverse">{others.length}</span>
      </h2>

      <div className="grid gap-4 lg:grid-cols-2">
        {others.map((portfolio) => (
          <Card key={portfolio.portfolio_id}>
            <CardContent className="p-6">
              <h3 className="text-sm font-semibold text-text-tertiary">{portfolio.objective}</h3>
              <p className="mt-1 font-mono text-xs text-text-inverse">{portfolio.portfolio_id}</p>

              <dl className="mt-4 space-y-1.5 text-xs">
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">Risk reduction</dt>
                  <dd className="text-text-primary">{formatInr(portfolio.risk_reduction)}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">Cost</dt>
                  <dd className="text-text-primary">{formatInr(portfolio.total_cost)}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">Effort</dt>
                  <dd className="text-text-primary">
                    {portfolio.workforce_hours} hrs · {portfolio.implementation_days} days
                  </dd>
                </div>
              </dl>

              <ul className="mt-4 flex flex-wrap gap-2">
                {portfolio.selected_controls.map((controlId) => (
                  <li key={controlId}>
                    <Badge variant="neutral" className="font-mono">
                      {controlId}
                    </Badge>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ *
 * Opportunity cost — what was given up
 * ------------------------------------------------------------------ */

function OpportunityCost(props: { optimizationId: string }) {
  const { optimizationId } = props

  const cost = useQuery<OpportunityCostResponse, ApiError>({
    queryKey: ['decision', optimizationId, 'opportunity-cost'],
    queryFn: () =>
      api.get<OpportunityCostResponse>(`/decision/${optimizationId}/opportunity-cost`),
    retry: false,
  })

  if (cost.isPending) {
    return <LoadingCard />
  }

  if (cost.isError) {
    return <ErrorPanel error={cost.error} onRetry={() => void cost.refetch()} />
  }

  const data = cost.data

  return (
    <section>
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
        What was given up
      </h2>

      <Card className="mb-4">
        <CardContent className="p-6">
          <p className="max-w-[70ch] text-sm leading-relaxed text-text-primary">
            {data.summary_statement}
          </p>
          {data.assumptions && data.assumptions.length > 0 ? (
            <ul className="mt-4 space-y-1 border-t border-border-default/50 pt-4">
              {data.assumptions.map((assumption, index) => (
                <li key={index} className="text-xs text-text-inverse">
                  {assumption}
                </li>
              ))}
            </ul>
          ) : null}
        </CardContent>
      </Card>

      <div className="space-y-4">
        {data.comparisons.map((comparison) => (
          <Card key={comparison.compared_portfolio_id}>
            <CardContent className="p-6">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h3 className="text-sm font-semibold text-text-tertiary">
                  vs {comparison.compared_objective}
                </h3>
                <span className="font-mono text-xs text-text-inverse">
                  {comparison.compared_portfolio_id}
                </span>
              </div>

              <p className="mt-3 max-w-[70ch] text-xs leading-relaxed text-text-primary">
                {comparison.tradeoff_narrative}
              </p>

              <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-2">
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">Risk reduction difference</dt>
                  <dd className="text-text-primary">
                    {signed(comparison.risk_reduction_difference, formatInr)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">Cost difference</dt>
                  <dd className="text-text-primary">
                    {signed(comparison.cost_difference, formatInr)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">Workforce hours</dt>
                  <dd className="text-text-primary">
                    {signed(comparison.workforce_hours_difference, (n) => `${n} hrs`)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">Implementation days</dt>
                  <dd className="text-text-primary">
                    {signed(comparison.implementation_days_difference, (n) => `${n} days`)}
                  </dd>
                </div>
              </dl>

              {comparison.controls_gained && comparison.controls_gained.length > 0 ? (
                <div className="mt-4">
                  <p className="text-xs uppercase tracking-wider text-text-inverse">
                    Would have gained
                  </p>
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {comparison.controls_gained.map((controlId) => (
                      <li key={controlId}>
                        <Badge variant="low" className="font-mono">
                          {controlId}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {comparison.controls_sacrificed && comparison.controls_sacrificed.length > 0 ? (
                <div className="mt-3">
                  <p className="text-xs uppercase tracking-wider text-text-inverse">
                    Would have lost
                  </p>
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {comparison.controls_sacrificed.map((controlId) => (
                      <li key={controlId}>
                        <Badge variant="high" className="font-mono">
                          {controlId}
                        </Badge>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ *
 * Per-control rationale
 * ------------------------------------------------------------------ */

function ControlRationale(props: { optimizationId: string }) {
  const { optimizationId } = props

  const explanation = useQuery<ControlExplanation[], ApiError>({
    queryKey: ['decision', optimizationId, 'explanation'],
    queryFn: () => api.get<ControlExplanation[]>(`/decision/${optimizationId}/explanation`),
    retry: false,
  })

  if (explanation.isPending) {
    return <LoadingCard />
  }

  if (explanation.isError) {
    return <ErrorPanel error={explanation.error} onRetry={() => void explanation.refetch()} />
  }

  const entries = explanation.data
  if (entries.length === 0) {
    return null
  }

  const selected = entries.filter((entry) => entry.selected)
  const rejected = entries.filter((entry) => !entry.selected)

  function renderGroup(title: string, group: ControlExplanation[], variant: 'success' | 'neutral') {
    if (group.length === 0) {
      return null
    }

    return (
      <Card>
        <CardContent className="p-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
            {title}
            <span className="ml-2 font-normal text-text-inverse">{group.length}</span>
          </h3>
          <ul className="mt-4 space-y-5">
            {group.map((entry) => (
              <li
                key={entry.control_id ?? entry.control}
                className="border-t border-border-default/40 pt-4 first:border-t-0 first:pt-0"
              >
                <div className="flex flex-wrap items-baseline gap-2">
                  <Badge variant={variant} className="font-mono">
                    {entry.control_id ?? '—'}
                  </Badge>
                  <span className="text-sm text-text-tertiary">{entry.control}</span>
                </div>
                {typeof entry.cost === 'number' ? (
                  <p className="mt-1 text-xs text-text-inverse">
                    {formatInr(entry.cost)}
                    {typeof entry.risk_reduction === 'number'
                      ? ` · ${formatInr(entry.risk_reduction)} reduction`
                      : ''}
                  </p>
                ) : null}
                <ul className="mt-2 space-y-1">
                  {entry.reasons.map((reason, index) => (
                    <li key={index} className="text-xs leading-relaxed text-text-primary">
                      {reason}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    )
  }

  return (
    <section>
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
        Why each control was or was not funded
      </h2>
      <div className="grid gap-4 lg:grid-cols-2">
        {renderGroup('Funded', selected, 'success')}
        {renderGroup('Not funded', rejected, 'neutral')}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ *
 * Screen
 * ------------------------------------------------------------------ */

function DecisionDetail(props: { optimizationId: string }) {
  const { optimizationId } = props

  const alternatives = useQuery<AlternativesResponse, ApiError>({
    queryKey: ['decision', optimizationId, 'alternatives'],
    queryFn: () => api.get<AlternativesResponse>(`/decision/${optimizationId}/alternatives`),
    retry: false,
  })

  if (alternatives.isPending) {
    return (
      <div className="grid gap-4 sm:grid-cols-3">
        <LoadingCard />
        <LoadingCard />
        <LoadingCard />
      </div>
    )
  }

  if (alternatives.isError) {
    return (
      <ErrorPanel error={alternatives.error} onRetry={() => void alternatives.refetch()} />
    )
  }

  const data = alternatives.data
  const chosen =
    data.alternatives.find(
      (portfolio) => portfolio.portfolio_id === data.selected_portfolio_id,
    ) ?? data.alternatives[0]

  return (
    <div className="space-y-8">
      {chosen ? <ChosenPortfolio data={data} chosen={chosen} /> : null}
      <AlternativesConsidered
        alternatives={data.alternatives}
        chosenId={chosen ? chosen.portfolio_id : ''}
      />
      <OpportunityCost optimizationId={optimizationId} />
      <ControlRationale optimizationId={optimizationId} />
    </div>
  )
}

export default function ActionCenter() {
  const optimizations = useOptimizations()

  const heading = (
    <header className="mb-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text-tertiary">Action Center</h1>
      <p className="mt-2 max-w-[560px] text-sm text-text-primary">
        Why this portfolio was chosen, what else was on the table, and what choosing it
        gave up.
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

  const chosen = latestReal(optimizations.data)

  if (!chosen) {
    return (
      <div>
        {heading}
        <NoOptimizationYet what="Explaining a decision" />
      </div>
    )
  }

  return (
    <div>
      {heading}
      <Card className="mb-6">
        <CardContent className="p-6">
          <p className="text-xs uppercase tracking-wider text-text-inverse">Explaining</p>
          <p className="mt-1 font-mono text-sm text-text-tertiary">{chosen.optimization_id}</p>
          <p className="mt-1 text-xs text-text-primary">
            {chosen.title} · budget {formatInr(chosen.budget_limit)}
          </p>
        </CardContent>
      </Card>

      <DecisionDetail optimizationId={chosen.optimization_id} />
    </div>
  )
}
