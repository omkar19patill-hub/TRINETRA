import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { Badge } from '../../components/ui/Badge'
import { Card, CardContent } from '../../components/ui/Card'
import { MetricCard } from '../../components/ui/MetricCard'
import { ErrorPanel, LoadingCard } from '../../components/dashboard/states'
import { api } from '../../lib/apiClient'
import type { ApiError } from '../../lib/apiClient'
import type {
  EnrichedVulnerability,
  VulnerabilityListItem,
  VulnerabilityListResponse,
} from '../../types/api'

type SeverityVariant = 'critical' | 'high' | 'medium' | 'low' | 'neutral'

function severityVariant(severity: string): SeverityVariant {
  switch (severity.toUpperCase()) {
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

function formatEpss(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return '—'
  }
  return `${(value * 100).toFixed(1)}%`
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return '—'
  }
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? value : parsed.toISOString().slice(0, 10)
}

/* ------------------------------------------------------------------ *
 * Enriched detail
 * ------------------------------------------------------------------ */

function EnrichedDetail(props: { cveId: string }) {
  const { cveId } = props

  const detail = useQuery<EnrichedVulnerability, ApiError>({
    queryKey: ['vulnerability', cveId, 'enriched'],
    queryFn: () => api.get<EnrichedVulnerability>(`/vulnerabilities/${cveId}/enriched`),
    retry: false,
  })

  if (detail.isPending) {
    return (
      <div className="grid gap-4 sm:grid-cols-3">
        <LoadingCard />
        <LoadingCard />
        <LoadingCard />
      </div>
    )
  }

  if (detail.isError) {
    return <ErrorPanel error={detail.error} onRetry={() => void detail.refetch()} />
  }

  const data = detail.data
  const sources = data.source_metadata?.sources ?? []
  const freshness = data.data_freshness

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard
          label="CVSS"
          value={data.cvss.toFixed(1)}
          context={data.cvss_version ? `v${data.cvss_version}` : undefined}
        />
        <MetricCard
          label="EPSS"
          value={formatEpss(data.epss)}
          context={`${(data.epss_percentile * 100).toFixed(1)}th percentile`}
        />
        <MetricCard
          label="Known exploited"
          value={data.kev ? 'Yes' : 'No'}
          context={data.known_ransomware_use ? 'Linked to ransomware' : 'No ransomware link recorded'}
        />
      </div>

      <Card>
        <CardContent className="p-6">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="font-mono text-sm font-semibold text-text-tertiary">{data.cve_id}</h2>
            <Badge variant={severityVariant(data.severity)}>{data.severity}</Badge>
          </div>

          <p className="mt-4 max-w-[70ch] text-sm leading-relaxed text-text-primary">
            {data.description}
          </p>

          {data.cvss_vector ? (
            <p className="mt-4 break-all font-mono text-xs text-text-inverse">{data.cvss_vector}</p>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
              Sources
            </h3>
            {sources.length === 0 ? (
              <p className="mt-3 text-sm text-text-primary">No source metadata reported.</p>
            ) : (
              <ul className="mt-4 flex flex-wrap gap-2">
                {sources.map((source) => (
                  <li key={source}>
                    <Badge variant="neutral">{source}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-text-tertiary">
              Data freshness
            </h3>
            {freshness ? (
              <dl className="mt-4 space-y-2 text-xs">
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">NVD last modified</dt>
                  <dd className="text-text-primary">{formatDate(freshness.nvd_last_modified)}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">EPSS date</dt>
                  <dd className="text-text-primary">{formatDate(freshness.epss_date)}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">KEV checked</dt>
                  <dd className="text-text-primary">{formatDate(freshness.kev_checked_at)}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-text-inverse">Ingested</dt>
                  <dd className="text-text-primary">{formatDate(freshness.ingested_at)}</dd>
                </div>
              </dl>
            ) : (
              <p className="mt-3 text-sm text-text-primary">No freshness data reported.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ *
 * List
 * ------------------------------------------------------------------ */

function VulnerabilityRow(props: {
  item: VulnerabilityListItem
  isSelected: boolean
  onSelect: (cveId: string) => void
}) {
  const { item, isSelected, onSelect } = props

  return (
    <li>
      <button
        type="button"
        onClick={() => onSelect(item.cve_id)}
        aria-expanded={isSelected}
        className={`flex w-full flex-wrap items-center gap-3 border-t border-border-default/40 px-1 py-3 text-left transition-colors first:border-t-0 hover:bg-surface-strong ${
          isSelected ? 'bg-surface-strong' : ''
        }`}
      >
        <span className="min-w-[150px] flex-1 font-mono text-sm text-text-tertiary">
          {item.cve_id}
        </span>
        <Badge variant={severityVariant(item.severity)}>{item.severity}</Badge>
        <span className="w-20 text-xs text-text-primary">CVSS {item.cvss.toFixed(1)}</span>
        <span className="w-24 text-xs text-text-primary">EPSS {formatEpss(item.epss)}</span>
        <span className="w-28 text-xs">
          {item.kev ? (
            <Badge variant="critical">KEV</Badge>
          ) : (
            <span className="text-text-inverse">Not in KEV</span>
          )}
        </span>
      </button>
    </li>
  )
}

/* ------------------------------------------------------------------ *
 * Screen
 * ------------------------------------------------------------------ */

export default function ThreatIntelligence() {
  const [selected, setSelected] = useState<string | null>(null)

  const list = useQuery<VulnerabilityListResponse, ApiError>({
    queryKey: ['vulnerabilities', 'list'],
    queryFn: () => api.get<VulnerabilityListResponse>('/vulnerabilities'),
    retry: false,
  })

  function handleSelect(cveId: string) {
    setSelected((current) => (current === cveId ? null : cveId))
  }

  const heading = (
    <header className="mb-8">
      <h1 className="text-2xl font-semibold tracking-tight text-text-tertiary">
        Threat Intelligence
      </h1>
      <p className="mt-2 max-w-[560px] text-sm text-text-primary">
        Vulnerabilities currently ingested from NVD, EPSS and the CISA KEV catalog. Select
        one to see its enriched detail.
      </p>
    </header>
  )

  if (list.isPending) {
    return (
      <div>
        {heading}
        <p className="sr-only">Loading vulnerabilities</p>
        <div className="grid gap-4 sm:grid-cols-3">
          <LoadingCard />
          <LoadingCard />
          <LoadingCard />
        </div>
      </div>
    )
  }

  if (list.isError) {
    return (
      <div>
        {heading}
        <ErrorPanel error={list.error} onRetry={() => void list.refetch()} />
      </div>
    )
  }

  const items = list.data.vulnerabilities ?? []
  const kevCount = items.filter((item) => item.kev).length

  if (items.length === 0) {
    return (
      <div>
        {heading}
        <Card>
          <CardContent className="p-10">
            <h2 className="text-lg font-semibold tracking-tight text-text-tertiary">
              No vulnerabilities ingested
            </h2>
            <p className="mt-3 max-w-[460px] text-sm leading-relaxed text-text-primary">
              The intelligence cache is empty. Once a sync has run, ingested CVEs will appear
              here with their CVSS, EPSS and KEV signals.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div>
      {heading}

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <MetricCard label="Ingested" value={list.data.total} context="Vulnerabilities in cache" />
        <MetricCard label="Known exploited" value={kevCount} context="Present in CISA KEV" />
        <MetricCard
          label="Showing"
          value={items.length}
          context={`Page ${list.data.page} · ${list.data.page_size} per page`}
        />
      </div>

      <Card className="mb-6">
        <CardContent className="p-6">
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-text-tertiary">
            Vulnerabilities
          </h2>
          <ul>
            {items.map((item) => (
              <VulnerabilityRow
                key={item.cve_id}
                item={item}
                isSelected={selected === item.cve_id}
                onSelect={handleSelect}
              />
            ))}
          </ul>
        </CardContent>
      </Card>

      {selected ? <EnrichedDetail cveId={selected} /> : null}
    </div>
  )
}
