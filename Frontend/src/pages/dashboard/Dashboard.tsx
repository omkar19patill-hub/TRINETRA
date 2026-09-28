import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import {
  getRiskChange,
  getRiskIntelligence,
  partitionByProvenance,
  setRiskAppetite,
} from '../../lib/apiClient'
import { formatInr, formatScore, pickBudget } from '../../components/dashboard/format'
import { ErrorPanel, LoadingCard } from '../../components/dashboard/states'
import { useAssets, useOptimizations, useRunOptimization } from '../../hooks/useOptimization'
import type {
  OptimizationRunResponse,
  RiskChangeResponse,
  RiskIntelligenceResponse,
} from '../../types/api'



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
 * Risk Intelligence & Governance (Phase 4)
 * ------------------------------------------------------------------ */

function RiskIntelligenceSection() {
  const queryClient = useQueryClient()
  const [isEditingAppetite, setIsEditingAppetite] = useState(false)
  const [appetiteInput, setAppetiteInput] = useState('')

  const intelQuery = useQuery<RiskIntelligenceResponse>({
    queryKey: ['risk-intelligence'],
    queryFn: getRiskIntelligence,
  })

  const changeQuery = useQuery<RiskChangeResponse>({
    queryKey: ['risk-change'],
    queryFn: getRiskChange,
  })

  const updateAppetite = useMutation({
    mutationFn: (newAppetite: number) => setRiskAppetite(newAppetite),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['risk-intelligence'] })
      setIsEditingAppetite(false)
    },
  })

  const intel = intelQuery.data
  const change = changeQuery.data

  if (!intel || !intel.has_exposure) {
    return null
  }

  function handleSaveAppetite(e: React.FormEvent) {
    e.preventDefault()
    const num = parseFloat(appetiteInput)
    if (!isNaN(num) && num >= 0) {
      updateAppetite.mutate(num)
    }
  }

  // Determine badge variant and label
  let statusVariant: 'success' | 'medium' | 'critical' | 'neutral' = 'neutral'
  let statusLabel = 'NOT CONFIGURED'
  let statusContext = 'Set organizational risk appetite to evaluate compliance'

  if (intel.status === 'WITHIN_APPETITE') {
    statusVariant = 'success'
    statusLabel = 'WITHIN APPETITE'
    statusContext = 'Exposure is within acceptable threshold'
  } else if (intel.status === 'AT_APPETITE') {
    statusVariant = 'medium'
    statusLabel = 'AT APPETITE'
    statusContext = 'Exposure exactly matches threshold limit'
  } else if (intel.status === 'ABOVE_APPETITE') {
    statusVariant = 'critical'
    statusLabel = 'ABOVE APPETITE'
    statusContext = `${formatInr(intel.risk_debt ?? 0)} sitting above risk appetite`
  }

  // Change metrics from Phase 3
  const absChange = change?.absolute_change ?? 0
  const isExpIncreased = absChange > 0
  const pctStr =
    change?.percentage_change !== null && change?.percentage_change !== undefined
      ? `${change.percentage_change > 0 ? '+' : ''}${change.percentage_change.toFixed(1)}%`
      : null

  const exposureContext = change?.has_baseline
    ? `Prev: ${formatInr(change.previous_exposure ?? 0)} (${isExpIncreased ? '+' : ''}${formatInr(absChange)}${pctStr ? `, ${pctStr}` : ''})`
    : 'Baseline Expected Annual Loss'

  return (
    <section className="mb-8 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
            Risk Intelligence & Governance
          </h2>
          <Badge variant={statusVariant}>{statusLabel}</Badge>
        </div>
        <div>
          {!isEditingAppetite ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setAppetiteInput(
                  intel.risk_appetite !== null && intel.risk_appetite !== undefined
                    ? String(intel.risk_appetite)
                    : ''
                )
                setIsEditingAppetite(true)
              }}
            >
              {intel.has_risk_appetite ? 'Adjust Appetite' : 'Configure Risk Appetite'}
            </Button>
          ) : null}
        </div>
      </div>

      {isEditingAppetite ? (
        <Card className="border-border-default/80 bg-surface-muted/50 p-4">
          <form onSubmit={handleSaveAppetite} className="flex flex-wrap items-center gap-3">
            <label htmlFor="appetite-input" className="text-xs font-medium text-text-primary">
              Set Monetary Risk Appetite (₹ INR):
            </label>
            <input
              id="appetite-input"
              type="number"
              min="0"
              step="1000"
              required
              placeholder="e.g. 3000000"
              value={appetiteInput}
              onChange={(e) => setAppetiteInput(e.target.value)}
              className="rounded-md border border-border-default bg-surface-base px-3 py-1.5 text-sm text-text-secondary outline-none focus:border-border-hover focus:ring-1 focus:ring-border-hover"
            />
            <Button type="submit" size="sm" loading={updateAppetite.isPending}>
              Save Appetite
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setIsEditingAppetite(false)}
            >
              Cancel
            </Button>
          </form>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Financial Exposure"
          value={formatInr(intel.current_exposure ?? 0)}
          context={exposureContext}
          source="Assessment Storage"
        />
        <MetricCard
          label="Risk Appetite"
          value={intel.has_risk_appetite ? formatInr(intel.risk_appetite ?? 0) : 'Not configured'}
          context="Maximum acceptable cyber exposure"
          source="Organizational Policy"
        />
        <MetricCard
          label="Cyber Risk Debt"
          value={intel.has_risk_appetite && intel.risk_debt != null ? formatInr(intel.risk_debt) : '—'}
          context={
            intel.has_risk_appetite && intel.risk_debt != null && intel.risk_debt > 0
              ? 'Unmitigated excess loss exposure'
              : 'Zero unmitigated risk debt'
          }
          source="Continuous CRQ Engine"
        />

        <MetricCard
          label="Appetite Compliance"
          value={statusLabel}
          context={statusContext}
          source="Risk Governance"
        />
      </div>

      {change?.has_baseline ? (
        <div className="mt-2 grid gap-4 sm:grid-cols-3">
          <MetricCard
            label="Run-over-Run Delta"
            value={`${isExpIncreased ? '+' : ''}${formatInr(absChange)}`}
            context={pctStr ? `Exposure change: ${pctStr}` : 'Exposure unchanged'}
            source="Phase 3 Detector"
          />
          <MetricCard
            label="Average Risk Score"
            value={formatScore(change.current_average_risk ?? 0)}
            context={`Change: ${
              change.average_risk_change !== null && (change.average_risk_change ?? 0) > 0 ? '+' : ''
            }${(change.average_risk_change ?? 0).toFixed(1)} pts`}
            source="Assessment Storage"
          />
          <MetricCard
            label="Asset Criticality Shifts"
            value={`Crit: ${
              change.critical_assets_change !== null && (change.critical_assets_change ?? 0) > 0 ? '+' : ''
            }${change.critical_assets_change ?? 0} | High: ${
              change.high_risk_assets_change !== null && (change.high_risk_assets_change ?? 0) > 0 ? '+' : ''
            }${change.high_risk_assets_change ?? 0}`}
            context={`Critical: ${change.previous_critical_assets ?? 0} → ${change.current_critical_assets ?? 0}, High: ${change.previous_high_risk_assets ?? 0} → ${change.current_high_risk_assets ?? 0}`}
            source="Assessment Storage"
          />
        </div>
      ) : null}
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
        <RiskIntelligenceSection />
        <ResultView result={result} isDemoData={result.is_benchmark === true} />
      </div>
    )
  }

  const hasRealData = realCount > 0
  const plural = realCount === 1 ? '' : 's'

  return (
    <div>
      {heading}
      <RiskIntelligenceSection />
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

