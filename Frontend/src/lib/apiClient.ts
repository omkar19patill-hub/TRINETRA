/**
 * Typed HTTP client for the TRINETRA backend.
 *
 * ---------------------------------------------------------------------------
 * BENCHMARK DATA — READ THIS BEFORE BUILDING ANY SCREEN
 * ---------------------------------------------------------------------------
 * The backend ships benchmark ("demo") scenarios alongside real optimizer
 * results. They are NOT interchangeable, and some endpoints return benchmark
 * rows without being asked.
 *
 * Verified behaviour:
 *   - GET /decision/optimizations returns TWO benchmark scenarios on a cold
 *     backend, because the store falls back to benchmark data when no real
 *     optimization has been run yet.
 *   - GET /decision/{id}/* returns 404 for an unknown id rather than silently
 *     substituting benchmark data. Passing ?demo_mode=true opts in explicitly.
 *
 * Therefore: any caller handling a list-style response MUST check `is_benchmark`
 * per item and MUST NOT render benchmark data as though it were a real result,
 * even implicitly (no silent inclusion in totals, counts, charts or "latest
 * result" panels). Use isBenchmark() or partitionByProvenance() below, and label
 * benchmark data visibly in the UI — see docs/MOCK_DATA.md.
 *
 * ---------------------------------------------------------------------------
 * ERRORS
 * ---------------------------------------------------------------------------
 * FastAPI returns `detail` in two different shapes, both handled here:
 *   - 404 / 500: detail is a STRING
 *   - 422:       detail is an ARRAY of {type, loc, msg, input} objects
 * Every failure is normalised into an ApiError with a human-readable `detail`
 * string, plus `fieldErrors` when the backend reported per-field problems.
 */

import { env } from '../config/env'
import type { ProvenanceMarked } from '../types/api'

/** A single field-level validation problem, parsed from a 422 response. */
export interface FieldError {
  /** Dotted path to the offending field, e.g. "body.asset_id". */
  field: string
  message: string
}

/** Raw shape of one entry in FastAPI's 422 `detail` array. */
interface RawValidationEntry {
  loc?: unknown
  msg?: unknown
  type?: unknown
}

export class ApiError extends Error {
  /** HTTP status, or 0 when the request never reached the server. */
  readonly status: number
  /** Always a human-readable string, whatever shape the backend used. */
  readonly detail: string
  /** Present only when the backend reported per-field validation errors (422). */
  readonly fieldErrors?: FieldError[]

  constructor(status: number, detail: string, fieldErrors?: FieldError[]) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.fieldErrors = fieldErrors
  }

  /** True when the resource does not exist — e.g. no optimization with that id yet. */
  get isNotFound(): boolean {
    return this.status === 404
  }

  /** True when the request body failed backend validation. */
  get isValidationError(): boolean {
    return this.status === 422
  }

  /** True when the backend could not be reached at all. */
  get isNetworkError(): boolean {
    return this.status === 0
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

/** Turn a 422 `loc` array such as ["body", "asset_id"] into "body.asset_id". */
function formatLocation(loc: unknown): string {
  if (!Array.isArray(loc)) return 'request'
  const parts = loc.filter((p): p is string | number => typeof p === 'string' || typeof p === 'number')
  return parts.length > 0 ? parts.join('.') : 'request'
}

function parseValidationEntries(entries: unknown[]): FieldError[] {
  const parsed: FieldError[] = []
  for (const entry of entries) {
    if (!isRecord(entry)) continue
    const raw = entry as RawValidationEntry
    const message = typeof raw.msg === 'string' ? raw.msg : 'Invalid value'
    parsed.push({ field: formatLocation(raw.loc), message })
  }
  return parsed
}

/**
 * Normalise any error body into a readable message plus optional field errors.
 * Handles the string form (404/500) and the array form (422) explicitly.
 */
function normaliseErrorBody(status: number, body: unknown): ApiError {
  if (isRecord(body) && 'detail' in body) {
    const detail = body.detail

    if (typeof detail === 'string') {
      return new ApiError(status, detail)
    }

    if (Array.isArray(detail)) {
      const fieldErrors = parseValidationEntries(detail)
      const summary =
        fieldErrors.length > 0
          ? fieldErrors.map((f) => `${f.field}: ${f.message}`).join('; ')
          : `Request validation failed (HTTP ${status}).`
      return new ApiError(status, summary, fieldErrors)
    }
  }

  return new ApiError(status, `Request failed with HTTP ${status}.`)
}

type QueryValue = string | number | boolean

function buildUrl(path: string, params?: Record<string, QueryValue | undefined>): string {
  const url = `${env.apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
  if (!params) return url

  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.append(key, String(value))
  }
  const query = search.toString()
  return query ? `${url}?${query}` : url
}

async function apiRequest<T>(path: string, init?: RequestInit, params?: Record<string, QueryValue | undefined>): Promise<T> {
  let response: Response
  try {
    response = await fetch(buildUrl(path, params), {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })
  } catch {
    throw new ApiError(0, 'Unable to reach the TRINETRA backend. Check that it is running.')
  }

  if (!response.ok) {
    let body: unknown = null
    try {
      body = await response.json()
    } catch {
      // Non-JSON error body (e.g. a proxy failure) — fall through to the generic message.
    }
    throw normaliseErrorBody(response.status, body)
  }

  if (response.status === 204) {
    return undefined as T
  }

  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError(response.status, 'Backend returned a response that was not valid JSON.')
  }
}

export const api = {
  get: <T>(path: string, params?: Record<string, QueryValue | undefined>): Promise<T> =>
    apiRequest<T>(path, { method: 'GET' }, params),

  post: <T>(path: string, body?: unknown, params?: Record<string, QueryValue | undefined>): Promise<T> =>
    apiRequest<T>(
      path,
      { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) },
      params,
    ),
}

/* ------------------------------------------------------------------ *
 * Benchmark provenance guards — see the file header.
 * ------------------------------------------------------------------ */

/** True when a record is backend benchmark/demo data rather than a real result. */
export function isBenchmark(item: ProvenanceMarked): boolean {
  return item.is_benchmark === true || item.data_source === 'benchmark'
}

/**
 * Split a list into genuine optimizer results and benchmark demonstration data.
 *
 * Prefer this over filtering inline, so that benchmark rows are always an
 * explicit decision at the call site rather than something a screen forgets to
 * consider. Rendering `benchmark` entries is allowed only when they are clearly
 * labelled as demo data.
 */
export function partitionByProvenance<T extends ProvenanceMarked>(
  items: T[],
): { real: T[]; benchmark: T[] } {
  const real: T[] = []
  const benchmark: T[] = []
  for (const item of items) {
    if (isBenchmark(item)) benchmark.push(item)
    else real.push(item)
  }
  return { real, benchmark }
}
