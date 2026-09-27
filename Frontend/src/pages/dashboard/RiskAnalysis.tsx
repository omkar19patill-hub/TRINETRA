import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import { ErrorPanel, LoadingCard } from '../../components/dashboard/states'
import { formatScore } from '../../components/dashboard/format'
import { api } from '../../lib/apiClient'
import type { ApiError } from '../../lib/apiClient'
import { useAssets } from '../../hooks/useOptimization'
import type {
  Criticality,
  RiskCalculationRequest,
  RiskCalculationResponse,
} from '../../types/api'

const CRITICALITIES: Criticality[] = ['Critical', 'High', 'Medium', 'Low']

/** All seven fields are required by POST /risk/calculate; there are no defaults. */
const INITIAL_FORM: RiskCalculationRequest = {
  asset_id: 'AST-001',
  cve_id: 'CVE-2026-1234',
  cvss: 9.8,
  epss: 0.82,
  kev: true,
  internet_exposed: true,
  criticality: 'Critical',
}

function riskVariant(level: string): 'critical' | 'high' | 'medium' | 'low' | 'neutral' {
  switch (level.toUpperCase()) {
    case 'CRITICAL':
      return 'critical'
    case 'HIGH':
      return 'high'
    case 'MEDIUM':
      return 'medium'
    case 'LOW':
      return 'low'
    default:
      return 'neutral'
  }
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

/* ------------------------------------------------------------------ *
 * Contribution breakdown
 * ------------------------------------------------------------------ */

function ContributionBar(props: { label: string; value: number; total: number }) {
  const { label, value, total } = props
  const share = total > 0 ? Math.max(0, Math.min(100, (value / total) * 100)) : 0

  return (
    <li>
      <div className="flex items-baseline justify-between gap-4">
        <span className="text-xs text-text-primary">{label}</span>
        <span className="font-mono text-xs text-text-tertiary">{value.toFixed(3)}</span>
      </div>
      <div aria-hidden className="mt-1.5 h-1.5 w-full rounded-sm bg-surface-strong">
        <div className="h-1.5 rounded-sm bg-text-secondary" style={{ width: `${share}%` }} />
      </div>
    </li>
  )
}

function RiskResult(props: { result: RiskCalculationResponse }) {
  const { result } = props
  const calc = result.calculation

  const contributions = [
    { label: 'CVSS', value: calc.cvss_contribution },
    { label: 'EPSS', value: calc.epss_contribution },
    { label: 'Known exploited (KEV)', value: calc.kev_contribution },
    { label: 'Internet exposure', value: calc.exposure_contribution },
  ]
  const total = contributions.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="Risk score"
          value={formatScore(result.risk_score)}
          context={result.risk_level}
        />
        <MetricCard
          label="Likelihood"
          value={formatPercent(result.likelihood)}
          context="Probability of exploitation"
        />
        <MetricCard
          label="Impact"
          value={result.impact.toFixed(2)}
          context="Business impact multiplier"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
                Risk level
              </h2>
              <Badge variant={riskVariant(result.risk_level)}>{result.risk_level}</Badge>
            </div>

            <h3 className="mt-5 text-xs font-semibold uppercase tracking-wider text-text-inverse">
              Drivers
            </h3>
            {result.risk_drivers.length === 0 ? (
              <p className="mt-2 text-sm text-text-primary">No drivers reported.</p>
            ) : (
              <ul className="mt-2 space-y-1">
                {result.risk_drivers.map((driver, index) => (
                  <li key={`${driver}-${index}`} className="text-xs leading-relaxed text-text-primary">
                    {driver}
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
              Likelihood breakdown
            </h2>
            <ul className="mt-4 space-y-3">
              {contributions.map((item) => (
                <ContributionBar
                  key={item.label}
                  label={item.label}
                  value={item.value}
                  total={total}
                />
              ))}
            </ul>

            <dl className="mt-5 space-y-1.5 border-t border-border-default/50 pt-4 text-xs">
              <div className="flex justify-between gap-4">
                <dt className="text-text-inverse">CVSS normalized</dt>
                <dd className="font-mono text-text-primary">{calc.cvss_normalized.toFixed(3)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-inverse">EPSS</dt>
                <dd className="font-mono text-text-primary">{calc.epss.toFixed(3)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-inverse">KEV signal</dt>
                <dd className="font-mono text-text-primary">{calc.kev_signal}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-text-inverse">Exposure signal</dt>
                <dd className="font-mono text-text-primary">{calc.exposure_signal}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      <p className="text-xs text-text-inverse">
        {result.asset_id}
        {' · '}
        {result.cve_id}
        {' · model '}
        {result.model.version} ({result.model.type})
      </p>
    </div>
  )
}

/* ------------------------------------------------------------------ *
 * Screen
 * ------------------------------------------------------------------ */

export default function RiskAnalysis() {
  const assets = useAssets()
  const [form, setForm] = useState<RiskCalculationRequest>(INITIAL_FORM)
  const [result, setResult] = useState<RiskCalculationResponse | null>(null)

  const calculate = useMutation<RiskCalculationResponse, ApiError, RiskCalculationRequest>({
    mutationFn: (request) => api.post<RiskCalculationResponse>('/risk/calculate', request),
    onSuccess: (data) => setResult(data),
  })

  function update<K extends keyof RiskCalculationRequest>(
    key: K,
    value: RiskCalculationRequest[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  /** AssetState carries exactly the seven fields this endpoint requires. */
  function loadAsset(assetId: string) {
    const asset = assets.data?.find((candidate) => candidate.asset_id === assetId)
    if (!asset) {
      return
    }
    setForm({
      asset_id: asset.asset_id,
      cve_id: asset.cve_id,
      cvss: asset.cvss,
      epss: asset.epss,
      kev: asset.kev,
      internet_exposed: asset.internet_exposed,
      criticality: asset.criticality,
    })
  }

  const inputClass =
    'mt-2 w-full rounded-sm border border-border-default bg-surface-base px-3 py-2 text-sm text-text-tertiary placeholder:text-text-inverse focus:outline-none focus:ring-1 focus:ring-text-secondary'
  const labelClass = 'block text-sm font-medium uppercase tracking-wider text-text-primary'

  const cvssValid = form.cvss >= 0 && form.cvss <= 10
  const epssValid = form.epss >= 0 && form.epss <= 1
  const formValid =
    form.asset_id.trim() !== '' && form.cve_id.trim() !== '' && cvssValid && epssValid

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-text-tertiary">Risk Analysis</h1>
        <p className="mt-2 max-w-[560px] text-sm text-text-primary">
          Combine exploitability signals with asset criticality to produce an explainable
          risk score.
        </p>
      </header>

      <Card className="mb-6">
        <CardContent className="p-6">
          {assets.data && assets.data.length > 0 ? (
            <div className="mb-6 flex flex-wrap items-center gap-2 border-b border-border-default/50 pb-5">
              <span className="text-xs uppercase tracking-wider text-text-inverse">
                Load a tracked asset
              </span>
              {assets.data.map((asset) => (
                <Button
                  key={asset.asset_id}
                  variant="secondary"
                  size="sm"
                  onClick={() => loadAsset(asset.asset_id)}
                >
                  {asset.asset_id}
                </Button>
              ))}
            </div>
          ) : null}

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label htmlFor="risk-asset-id" className={labelClass}>
                Asset ID
              </label>
              <input
                id="risk-asset-id"
                type="text"
                value={form.asset_id}
                onChange={(event) => update('asset_id', event.target.value)}
                className={inputClass}
              />
            </div>

            <div>
              <label htmlFor="risk-cve-id" className={labelClass}>
                CVE ID
              </label>
              <input
                id="risk-cve-id"
                type="text"
                value={form.cve_id}
                onChange={(event) => update('cve_id', event.target.value)}
                className={inputClass}
              />
            </div>

            <div>
              <label htmlFor="risk-criticality" className={labelClass}>
                Criticality
              </label>
              <select
                id="risk-criticality"
                value={form.criticality}
                onChange={(event) => update('criticality', event.target.value as Criticality)}
                className={inputClass}
              >
                {CRITICALITIES.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="risk-cvss" className={labelClass}>
                CVSS
              </label>
              <input
                id="risk-cvss"
                type="number"
                min={0}
                max={10}
                step={0.1}
                value={form.cvss}
                onChange={(event) => update('cvss', Number(event.target.value))}
                className={inputClass}
              />
              {cvssValid ? null : (
                <p className="mt-1.5 text-xs text-risk-critical">Must be between 0 and 10.</p>
              )}
            </div>

            <div>
              <label htmlFor="risk-epss" className={labelClass}>
                EPSS
              </label>
              <input
                id="risk-epss"
                type="number"
                min={0}
                max={1}
                step={0.01}
                value={form.epss}
                onChange={(event) => update('epss', Number(event.target.value))}
                className={inputClass}
              />
              {epssValid ? null : (
                <p className="mt-1.5 text-xs text-risk-critical">Must be between 0 and 1.</p>
              )}
            </div>

            <fieldset className="flex items-end gap-5">
              <legend className="sr-only">Exposure signals</legend>
              <label className="flex items-center gap-2 text-sm text-text-primary">
                <input
                  type="checkbox"
                  checked={form.kev}
                  onChange={(event) => update('kev', event.target.checked)}
                  className="h-4 w-4 rounded-sm border border-border-default bg-surface-base"
                />
                In KEV
              </label>
              <label className="flex items-center gap-2 text-sm text-text-primary">
                <input
                  type="checkbox"
                  checked={form.internet_exposed}
                  onChange={(event) => update('internet_exposed', event.target.checked)}
                  className="h-4 w-4 rounded-sm border border-border-default bg-surface-base"
                />
                Internet exposed
              </label>
            </fieldset>
          </div>

          <div className="mt-6">
            <Button
              onClick={() => calculate.mutate(form)}
              loading={calculate.isPending}
              disabled={!formValid}
            >
              {calculate.isPending ? 'Calculating risk' : 'Calculate risk'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {calculate.isPending ? (
        <div>
          <p className="sr-only">Calculating risk</p>
          <div className="grid gap-4 sm:grid-cols-3">
            <LoadingCard />
            <LoadingCard />
            <LoadingCard />
          </div>
        </div>
      ) : null}

      {calculate.isError && !calculate.isPending ? (
        <ErrorPanel error={calculate.error} onRetry={() => calculate.mutate(form)} />
      ) : null}

      {result && !calculate.isPending && !calculate.isError ? <RiskResult result={result} /> : null}

      {!result && !calculate.isPending && !calculate.isError ? (
        <Card>
          <CardContent className="p-10">
            <h2 className="text-lg font-semibold tracking-tight text-text-tertiary">
              No risk calculated yet
            </h2>
            <p className="mt-3 max-w-[460px] text-sm leading-relaxed text-text-primary">
              Load a tracked asset or enter values above, then calculate to see the score and
              the exact contribution of each signal.
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
