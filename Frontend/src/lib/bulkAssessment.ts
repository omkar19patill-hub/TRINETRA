/**
 * CSV parsing, row validation and batch execution for bulk risk assessment.
 *
 * Kept out of the component so the parsing and validation rules can be reasoned
 * about on their own.
 *
 * Nothing here persists. Results live in React state for the lifetime of the
 * page and are discarded on refresh.
 */

import { api } from './apiClient'
import { ApiError } from './apiClient'
import type {
  AssessmentBatchCreate,
  AssessmentBatchResponse,
  Criticality,
  FinancialCRQRequest,
  FinancialCRQResult,
  RiskCalculationRequest,
  RiskCalculationResponse,
} from '../types/api'

/* ------------------------------------------------------------------ *
 * CSV parsing
 * ------------------------------------------------------------------ */

/**
 * Split one CSV line, honouring double-quoted fields that may contain commas
 * or escaped quotes ("" inside a quoted field).
 */
function splitCsvLine(line: string): string[] {
  const fields: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i]

    if (inQuotes) {
      if (char === '"') {
        if (line[i + 1] === '"') {
          current += '"'
          i += 1
        } else {
          inQuotes = false
        }
      } else {
        current += char
      }
      continue
    }

    if (char === '"') {
      inQuotes = true
    } else if (char === ',') {
      fields.push(current)
      current = ''
    } else {
      current += char
    }
  }

  fields.push(current)
  return fields
}

/** A parsed row keyed by normalised header name. */
export type CsvRow = Record<string, string>

export interface ParsedCsv {
  headers: string[]
  rows: CsvRow[]
}

/** Normalise a header for matching: trimmed, lower-cased, BOM stripped. */
function normaliseHeader(header: string): string {
  return header.replace(/^﻿/, '').trim().toLowerCase()
}

/**
 * Parse CSV text into rows keyed by normalised header name.
 *
 * Columns are matched by header name, never by position or count, so a file
 * with additional columns parses fine and the extras are simply carried along
 * unused.
 */
export function parseCsv(text: string): ParsedCsv {
  const lines = text
    .split(/\r\n|\n|\r/)
    .filter((line) => line.trim() !== '')

  if (lines.length === 0) {
    return { headers: [], rows: [] }
  }

  const headers = splitCsvLine(lines[0]).map(normaliseHeader)

  const rows: CsvRow[] = []
  for (let i = 1; i < lines.length; i += 1) {
    const values = splitCsvLine(lines[i])
    const row: CsvRow = {}
    headers.forEach((header, index) => {
      row[header] = (values[index] ?? '').trim()
    })
    rows.push(row)
  }

  return { headers, rows }
}

/* ------------------------------------------------------------------ *
 * Validation
 * ------------------------------------------------------------------ */

/** Header names this feature reads. Any other column is ignored. */
export const REQUIRED_HEADERS = [
  'asset_id',
  'cve_id',
  'cvss',
  'epss',
  'kev',
  'internet_exposed',
  'criticality',
  'revenue_loss_per_hour',
  'downtime_hours',
] as const

const CRITICALITIES: Criticality[] = ['Critical', 'High', 'Medium', 'Low']

/** Match the backend's case-sensitive values from a case-insensitive input. */
function normaliseCriticality(value: string): Criticality | null {
  const match = CRITICALITIES.find((level) => level.toLowerCase() === value.trim().toLowerCase())
  return match ?? null
}

function parseBoolean(value: string): boolean | null {
  const normalised = value.trim().toLowerCase()
  if (['true', '1', 'yes', 'y'].includes(normalised)) return true
  if (['false', '0', 'no', 'n'].includes(normalised)) return false
  return null
}

function parseNumber(value: string): number | null {
  if (value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

/** One row that passed validation, ready to send. */
export interface ValidRow {
  /** 1-based line number in the source file, for reporting. */
  lineNumber: number
  risk: RiskCalculationRequest
  revenue_loss_per_hour: number
  downtime_hours: number
}

export interface InvalidRow {
  lineNumber: number
  assetId: string
  problems: string[]
}

export interface ValidationOutcome {
  valid: ValidRow[]
  invalid: InvalidRow[]
  /** Required headers absent from the file entirely. */
  missingHeaders: string[]
}

/**
 * Validate parsed rows against the required field set.
 *
 * A row is rejected only for a missing or invalid REQUIRED field. Additional
 * columns are ignored, never a cause for rejection.
 */
export function validateRows(parsed: ParsedCsv): ValidationOutcome {
  const missingHeaders = REQUIRED_HEADERS.filter((header) => !parsed.headers.includes(header))
  if (missingHeaders.length > 0) {
    return { valid: [], invalid: [], missingHeaders }
  }

  const valid: ValidRow[] = []
  const invalid: InvalidRow[] = []

  parsed.rows.forEach((row, index) => {
    // +2: one for the header line, one to make it 1-based.
    const lineNumber = index + 2
    const problems: string[] = []

    const assetId = row.asset_id
    const cveId = row.cve_id
    if (!assetId) problems.push('asset_id is empty')
    if (!cveId) problems.push('cve_id is empty')

    const cvss = parseNumber(row.cvss)
    if (cvss === null) problems.push('cvss is not a number')
    else if (cvss < 0 || cvss > 10) problems.push(`cvss ${cvss} is outside 0-10`)

    const epss = parseNumber(row.epss)
    if (epss === null) problems.push('epss is not a number')
    else if (epss < 0 || epss > 1) problems.push(`epss ${epss} is outside 0-1`)

    const kev = parseBoolean(row.kev)
    if (kev === null) problems.push(`kev "${row.kev}" is not a boolean`)

    const exposed = parseBoolean(row.internet_exposed)
    if (exposed === null) problems.push(`internet_exposed "${row.internet_exposed}" is not a boolean`)

    const criticality = normaliseCriticality(row.criticality)
    if (criticality === null) {
      problems.push(`criticality "${row.criticality}" is not Critical, High, Medium or Low`)
    }

    const revenueLoss = parseNumber(row.revenue_loss_per_hour)
    if (revenueLoss === null) problems.push('revenue_loss_per_hour is not a number')
    else if (revenueLoss < 0) problems.push('revenue_loss_per_hour is negative')

    const downtimeHours = parseNumber(row.downtime_hours)
    if (downtimeHours === null) problems.push('downtime_hours is not a number')
    else if (downtimeHours < 0) problems.push('downtime_hours is negative')

    if (
      problems.length > 0 ||
      cvss === null ||
      epss === null ||
      kev === null ||
      exposed === null ||
      criticality === null ||
      revenueLoss === null ||
      downtimeHours === null
    ) {
      invalid.push({ lineNumber, assetId: assetId || '(no asset_id)', problems })
      return
    }

    valid.push({
      lineNumber,
      risk: {
        asset_id: assetId,
        cve_id: cveId,
        cvss,
        epss,
        kev,
        internet_exposed: exposed,
        criticality,
      },
      revenue_loss_per_hour: revenueLoss,
      downtime_hours: downtimeHours,
    })
  })

  return { valid, invalid, missingHeaders: [] }
}

/* ------------------------------------------------------------------ *
 * Execution
 * ------------------------------------------------------------------ */

export interface RowSuccess {
  status: 'ok'
  lineNumber: number
  assetId: string
  cveId: string
  criticality: Criticality
  risk: RiskCalculationResponse
  financial: FinancialCRQResult
}

export interface RowFailure {
  status: 'failed'
  lineNumber: number
  assetId: string
  /** Which call failed, so a partial failure is attributable. */
  stage: 'risk' | 'financial'
  detail: string
}

export type RowResult = RowSuccess | RowFailure

/** Bounded so a large file does not fire every request at once. */
export const CONCURRENCY = 4

/**
 * Run one row through risk/calculate then financial-crq/calculate.
 *
 * likelihood and risk_score are taken from this row's own risk response, never
 * from the CSV.
 */
async function assessRow(row: ValidRow): Promise<RowResult> {
  let risk: RiskCalculationResponse
  try {
    risk = await api.post<RiskCalculationResponse>('/risk/calculate', row.risk)
  } catch (error) {
    return {
      status: 'failed',
      lineNumber: row.lineNumber,
      assetId: row.risk.asset_id,
      stage: 'risk',
      detail: error instanceof ApiError ? error.detail : 'Unexpected error',
    }
  }

  const financialRequest: FinancialCRQRequest = {
    asset_id: row.risk.asset_id,
    cve_id: row.risk.cve_id,
    likelihood: risk.likelihood,
    risk_score: risk.risk_score,
    criticality: row.risk.criticality,
    revenue_loss_per_hour: row.revenue_loss_per_hour,
    downtime_hours: row.downtime_hours,
  }

  try {
    const financial = await api.post<FinancialCRQResult>(
      '/financial-crq/calculate',
      financialRequest,
    )
    return {
      status: 'ok',
      lineNumber: row.lineNumber,
      assetId: row.risk.asset_id,
      cveId: row.risk.cve_id,
      criticality: row.risk.criticality,
      risk,
      financial,
    }
  } catch (error) {
    return {
      status: 'failed',
      lineNumber: row.lineNumber,
      assetId: row.risk.asset_id,
      stage: 'financial',
      detail: error instanceof ApiError ? error.detail : 'Unexpected error',
    }
  }
}

/**
 * Process rows with bounded concurrency, reporting progress as each completes.
 * Results are returned in the original row order.
 */
export async function runBatch(
  rows: ValidRow[],
  onProgress: (completed: number, total: number) => void,
): Promise<RowResult[]> {
  const results: RowResult[] = new Array(rows.length)
  let nextIndex = 0
  let completed = 0

  async function worker(): Promise<void> {
    for (;;) {
      const index = nextIndex
      nextIndex += 1
      if (index >= rows.length) {
        return
      }
      results[index] = await assessRow(rows[index])
      completed += 1
      onProgress(completed, rows.length)
    }
  }

  const workers = Array.from({ length: Math.min(CONCURRENCY, rows.length) }, () => worker())
  await Promise.all(workers)
  return results
}

/* ------------------------------------------------------------------ *
 * Aggregation — computed over successful rows only
 * ------------------------------------------------------------------ */

export interface BatchAggregate {
  assessed: number
  failed: number
  totalExpectedAnnualLoss: number
  meanRiskScore: number
  byRiskLevel: Record<string, number>
  byCriticality: Record<string, number>
  topByExposure: RowSuccess[]
}

export function aggregate(results: RowResult[]): BatchAggregate {
  const successes = results.filter((result): result is RowSuccess => result.status === 'ok')
  const failed = results.length - successes.length

  const byRiskLevel: Record<string, number> = {}
  const byCriticality: Record<string, number> = {}
  let totalEal = 0
  let totalScore = 0

  for (const row of successes) {
    totalEal += row.financial.expected_annual_loss
    totalScore += row.risk.risk_score
    byRiskLevel[row.risk.risk_level] = (byRiskLevel[row.risk.risk_level] ?? 0) + 1
    byCriticality[row.criticality] = (byCriticality[row.criticality] ?? 0) + 1
  }

  const topByExposure = [...successes]
    .sort((a, b) => b.financial.expected_annual_loss - a.financial.expected_annual_loss)
    .slice(0, 5)

  return {
    assessed: successes.length,
    failed,
    totalExpectedAnnualLoss: totalEal,
    meanRiskScore: successes.length > 0 ? totalScore / successes.length : 0,
    byRiskLevel,
    byCriticality,
    topByExposure,
  }
}

/* ------------------------------------------------------------------ *
 * Persistence (Phase 1)
 * ------------------------------------------------------------------ */

export async function persistAssessmentBatch(
  source: string,
  totalRows: number,
  results: RowResult[],
  riskAppetite?: number | null,
): Promise<AssessmentBatchResponse | null> {
  const successes = results.filter((result): result is RowSuccess => result.status === 'ok')
  const failed = results.length - successes.length

  const payload: AssessmentBatchCreate = {
    source: source || 'bulk_assessment_csv',
    total_rows: totalRows,
    successful_rows: successes.length,
    failed_rows: failed,
    status: 'COMPLETED',
    risk_appetite: riskAppetite ?? null,
    results: successes.map((row) => ({
      asset_id: row.assetId,
      asset_name: row.assetId,
      cve_id: row.cveId,
      criticality: row.criticality,
      risk_score: row.risk.risk_score,
      financial_exposure: row.financial.expected_annual_loss,
      assessment_data: {
        lineNumber: row.lineNumber,
        likelihood: row.risk.likelihood,
        impact: row.risk.impact,
        risk_level: row.risk.risk_level,
        risk_drivers: row.risk.risk_drivers,
        calculation: row.risk.calculation,
        downtime_loss: row.financial.downtime_loss,
        incident_response_cost: row.financial.incident_response_cost,
        recovery_cost: row.financial.recovery_cost,
        regulatory_legal_cost: row.financial.regulatory_legal_cost,
        customer_business_impact: row.financial.customer_business_impact,
        total_loss_magnitude: row.financial.total_loss_magnitude,
        annual_event_frequency: row.financial.annual_event_frequency,
      },
    })),
  }

  try {
    return await api.post<AssessmentBatchResponse>('/risk/assessment-batch', payload)
  } catch (error) {
    console.error('Failed to persist assessment batch:', error)
    return null
  }
}

