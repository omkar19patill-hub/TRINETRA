import { useMemo, useRef, useState } from 'react'

import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import { formatInr, formatScore } from '../../components/dashboard/format'
import {
  REQUIRED_HEADERS,
  aggregate,
  parseCsv,
  runBatch,
  validateRows,
} from '../../lib/bulkAssessment'
import type { InvalidRow, RowResult, RowSuccess, ValidRow } from '../../lib/bulkAssessment'

type SortKey = 'asset_id' | 'risk_score' | 'expected_annual_loss'
type SortDirection = 'asc' | 'desc'

function severityVariant(level: string): 'critical' | 'high' | 'medium' | 'low' | 'neutral' {
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

/** Required by scope: batch results are never persisted. */
function NotSavedNotice() {
  return (
    <div className="mb-6 rounded-sm border border-border-default bg-surface-strong px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wider text-text-secondary">
        Live batch run — not saved. Re-upload to re-run.
      </p>
    </div>
  )
}

/* ------------------------------------------------------------------ *
 * Results table
 * ------------------------------------------------------------------ */

function ResultsTable(props: { rows: RowSuccess[] }) {
  const { rows } = props
  const [sortKey, setSortKey] = useState<SortKey>('expected_annual_loss')
  const [direction, setDirection] = useState<SortDirection>('desc')

  const sorted = useMemo(() => {
    const copy = [...rows]
    copy.sort((a, b) => {
      let comparison = 0
      if (sortKey === 'asset_id') {
        comparison = a.assetId.localeCompare(b.assetId)
      } else if (sortKey === 'risk_score') {
        comparison = a.risk.risk_score - b.risk.risk_score
      } else {
        comparison = a.financial.expected_annual_loss - b.financial.expected_annual_loss
      }
      return direction === 'asc' ? comparison : -comparison
    })
    return copy
  }, [rows, sortKey, direction])

  function toggle(key: SortKey) {
    if (key === sortKey) {
      setDirection((current) => (current === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setDirection(key === 'asset_id' ? 'asc' : 'desc')
    }
  }

  function arrow(key: SortKey): string {
    if (key !== sortKey) return ''
    return direction === 'asc' ? ' ↑' : ' ↓'
  }

  const headerClass =
    'px-1 py-2 text-left text-xs font-semibold uppercase tracking-wider text-text-inverse hover:text-text-secondary'

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
          Per-asset results
          <span className="ml-2 font-normal text-text-inverse">{rows.length}</span>
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] border-collapse">
            <thead>
              <tr className="border-b border-border-default">
                <th scope="col">
                  <button type="button" onClick={() => toggle('asset_id')} className={headerClass}>
                    Asset{arrow('asset_id')}
                  </button>
                </th>
                <th scope="col" className="px-1 py-2 text-left text-xs font-semibold uppercase tracking-wider text-text-inverse">
                  CVE
                </th>
                <th scope="col">
                  <button type="button" onClick={() => toggle('risk_score')} className={headerClass}>
                    Risk score{arrow('risk_score')}
                  </button>
                </th>
                <th scope="col" className="px-1 py-2 text-left text-xs font-semibold uppercase tracking-wider text-text-inverse">
                  Level
                </th>
                <th scope="col">
                  <button
                    type="button"
                    onClick={() => toggle('expected_annual_loss')}
                    className={headerClass}
                  >
                    Expected annual loss{arrow('expected_annual_loss')}
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((row) => (
                <tr key={`${row.lineNumber}-${row.assetId}`} className="border-b border-border-default/40">
                  <td className="px-1 py-2.5 font-mono text-xs text-text-tertiary">{row.assetId}</td>
                  <td className="px-1 py-2.5 font-mono text-xs text-text-primary">{row.cveId}</td>
                  <td className="px-1 py-2.5 text-xs text-text-primary">
                    {formatScore(row.risk.risk_score)}
                  </td>
                  <td className="px-1 py-2.5">
                    <Badge variant={severityVariant(row.risk.risk_level)}>
                      {row.risk.risk_level}
                    </Badge>
                  </td>
                  <td className="px-1 py-2.5 text-xs text-text-primary">
                    {formatInr(row.financial.expected_annual_loss)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

/* ------------------------------------------------------------------ *
 * Failure reporting
 * ------------------------------------------------------------------ */

function RejectedRows(props: { rows: InvalidRow[] }) {
  const { rows } = props
  if (rows.length === 0) return null

  return (
    <Card className="mb-6">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="high">Not sent</Badge>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
            {rows.length} row{rows.length === 1 ? '' : 's'} rejected before sending
          </h2>
        </div>
        <p className="mt-2 text-xs text-text-inverse">
          These rows were missing or had invalid required fields, so no request was made for
          them.
        </p>
        <ul className="mt-4 space-y-2">
          {rows.map((row) => (
            <li key={row.lineNumber} className="text-xs text-text-primary">
              <span className="font-mono text-text-tertiary">Line {row.lineNumber}</span>
              {' · '}
              <span className="font-mono">{row.assetId}</span>
              {' — '}
              {row.problems.join('; ')}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

function FailedRows(props: { rows: RowResult[] }) {
  const failures = props.rows.filter((row) => row.status === 'failed')
  if (failures.length === 0) return null

  return (
    <Card className="mb-6">
      <CardContent className="p-6">
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant="critical">Failed</Badge>
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
            {failures.length} row{failures.length === 1 ? '' : 's'} failed during processing
          </h2>
        </div>
        <p className="mt-2 text-xs text-text-inverse">
          These are excluded from the totals above.
        </p>
        <ul className="mt-4 space-y-2">
          {failures.map((row) => (
            <li key={row.lineNumber} className="text-xs text-text-primary">
              <span className="font-mono text-text-tertiary">Line {row.lineNumber}</span>
              {' · '}
              <span className="font-mono">{row.assetId}</span>
              {' · '}
              <span className="uppercase text-text-inverse">
                {row.status === 'failed' ? row.stage : ''}
              </span>
              {' — '}
              {row.status === 'failed' ? row.detail : ''}
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

export default function BulkAssessment() {
  const inputRef = useRef<HTMLInputElement>(null)

  const [fileName, setFileName] = useState<string | null>(null)
  const [parseError, setParseError] = useState<string | null>(null)
  const [missingHeaders, setMissingHeaders] = useState<string[]>([])
  const [rejected, setRejected] = useState<InvalidRow[]>([])
  const [pending, setPending] = useState<ValidRow[]>([])
  const [results, setResults] = useState<RowResult[] | null>(null)
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null)
  const [isRunning, setIsRunning] = useState(false)

  function reset() {
    setParseError(null)
    setMissingHeaders([])
    setRejected([])
    setPending([])
    setResults(null)
    setProgress(null)
  }

  async function handleFile(file: File) {
    reset()
    setFileName(file.name)

    let text: string
    try {
      text = await file.text()
    } catch {
      setParseError('Could not read that file.')
      return
    }

    const parsed = parseCsv(text)
    if (parsed.rows.length === 0) {
      setParseError('No data rows found. The file needs a header row and at least one row.')
      return
    }

    const outcome = validateRows(parsed)
    if (outcome.missingHeaders.length > 0) {
      setMissingHeaders(outcome.missingHeaders)
      return
    }

    setRejected(outcome.invalid)
    setPending(outcome.valid)
  }

  async function handleRun() {
    if (pending.length === 0) return

    setIsRunning(true)
    setProgress({ done: 0, total: pending.length })
    const batch = await runBatch(pending, (done, total) => setProgress({ done, total }))
    setResults(batch)
    setIsRunning(false)
  }

  const summary = results ? aggregate(results) : null
  const successes = results
    ? results.filter((row): row is RowSuccess => row.status === 'ok')
    : []

  return (
    <div>
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-text-tertiary">
          Bulk Risk Assessment
        </h1>
        <p className="mt-2 max-w-[560px] text-sm text-text-primary">
          Upload a CSV of assets to run each one through the risk and financial engines, and
          see where portfolio exposure is concentrated.
        </p>
      </header>

      <NotSavedNotice />

      <Card className="mb-6">
        <CardContent className="p-6">
          <label
            htmlFor="bulk-csv"
            className="block text-sm font-medium uppercase tracking-wider text-text-primary"
          >
            Asset CSV
          </label>
          <input
            id="bulk-csv"
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) void handleFile(file)
            }}
            className="mt-2 block w-full text-sm text-text-primary file:mr-4 file:rounded-sm file:border file:border-border-default file:bg-surface-strong file:px-4 file:py-2 file:text-sm file:text-text-secondary hover:file:bg-surface-raised"
          />

          <p className="mt-3 text-xs text-text-inverse">
            Required columns, matched by header name: {REQUIRED_HEADERS.join(', ')}. Any other
            columns are ignored.
          </p>

          {fileName ? (
            <p className="mt-3 text-xs text-text-primary">
              <span className="font-mono text-text-tertiary">{fileName}</span>
              {pending.length > 0 ? ` · ${pending.length} row(s) ready` : ''}
              {rejected.length > 0 ? ` · ${rejected.length} rejected` : ''}
            </p>
          ) : null}

          {pending.length > 0 && !results ? (
            <div className="mt-5">
              <Button onClick={handleRun} loading={isRunning}>
                {isRunning ? 'Processing' : `Assess ${pending.length} asset(s)`}
              </Button>
            </div>
          ) : null}

          {results ? (
            <div className="mt-5">
              <Button
                variant="secondary"
                onClick={() => {
                  reset()
                  setFileName(null)
                  if (inputRef.current) inputRef.current.value = ''
                }}
              >
                Upload another file
              </Button>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {parseError ? (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant="critical">File problem</Badge>
              <p className="text-sm text-text-secondary">{parseError}</p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {missingHeaders.length > 0 ? (
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant="critical">Missing columns</Badge>
              <p className="text-sm text-text-secondary">
                The file is missing required column{missingHeaders.length === 1 ? '' : 's'}:{' '}
                <span className="font-mono">{missingHeaders.join(', ')}</span>
              </p>
            </div>
            <p className="mt-2 text-xs text-text-inverse">
              Nothing was sent. Additional columns are fine; these specific ones are needed.
            </p>
          </CardContent>
        </Card>
      ) : null}

      <RejectedRows rows={rejected} />

      {isRunning && progress ? (
        <Card className="mb-6">
          <CardContent className="p-6">
            <p className="text-sm text-text-secondary">
              {progress.done} of {progress.total} processed
            </p>
            <div
              aria-hidden
              className="mt-3 h-1.5 w-full overflow-hidden rounded-sm bg-surface-strong"
            >
              <div
                className="h-1.5 rounded-sm bg-text-secondary transition-all"
                style={{ width: `${(progress.done / progress.total) * 100}%` }}
              />
            </div>
          </CardContent>
        </Card>
      ) : null}

      {summary && results ? (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Assets assessed"
              value={summary.assessed}
              context={summary.failed > 0 ? `${summary.failed} failed` : 'All rows succeeded'}
            />
            <MetricCard
              label="Portfolio exposure"
              value={formatInr(summary.totalExpectedAnnualLoss)}
              context="Total expected annual loss"
            />
            <MetricCard
              label="Mean risk score"
              value={formatScore(summary.meanRiskScore)}
              context="Across assessed assets"
            />
            <MetricCard
              label="Highest exposure"
              value={
                summary.topByExposure.length > 0
                  ? formatInr(summary.topByExposure[0].financial.expected_annual_loss)
                  : '—'
              }
              context={
                summary.topByExposure.length > 0 ? summary.topByExposure[0].assetId : 'No results'
              }
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardContent className="p-6">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
                  By risk level
                </h2>
                <ul className="mt-4 space-y-2">
                  {Object.entries(summary.byRiskLevel).map(([level, count]) => (
                    <li key={level} className="flex items-center justify-between gap-4">
                      <Badge variant={severityVariant(level)}>{level}</Badge>
                      <span className="text-sm text-text-primary">{count}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
                  By criticality
                </h2>
                <ul className="mt-4 space-y-2">
                  {Object.entries(summary.byCriticality).map(([level, count]) => (
                    <li key={level} className="flex items-center justify-between gap-4">
                      <Badge variant={severityVariant(level)}>{level}</Badge>
                      <span className="text-sm text-text-primary">{count}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {summary.topByExposure.length > 0 ? (
            <Card>
              <CardContent className="p-6">
                <h2 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
                  Highest-risk assets
                </h2>
                <ul className="mt-4 space-y-3">
                  {summary.topByExposure.map((row) => (
                    <li
                      key={`${row.lineNumber}-top`}
                      className="flex flex-wrap items-center justify-between gap-3 border-t border-border-default/40 pt-3 first:border-t-0 first:pt-0"
                    >
                      <span className="font-mono text-sm text-text-tertiary">{row.assetId}</span>
                      <Badge variant={severityVariant(row.risk.risk_level)}>
                        {row.risk.risk_level}
                      </Badge>
                      <span className="text-sm text-text-primary">
                        {formatInr(row.financial.expected_annual_loss)}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : null}

          <FailedRows rows={results} />

          {successes.length > 0 ? <ResultsTable rows={successes} /> : null}
        </div>
      ) : null}

      {!fileName && !parseError ? (
        <Card>
          <CardContent className="p-10">
            <h2 className="text-lg font-semibold tracking-tight text-text-tertiary">
              No file uploaded yet
            </h2>
            <p className="mt-3 max-w-[460px] text-sm leading-relaxed text-text-primary">
              Choose a CSV above. Each row is validated before anything is sent, then run
              through the risk and financial engines.
            </p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}
