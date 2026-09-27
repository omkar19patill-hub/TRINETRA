/**
 * TypeScript mirrors of the TRINETRA backend's request and response contracts.
 *
 * These are hand-written from the backend's OpenAPI schema. Every field below
 * exists in the running backend — nothing here is speculative. Optional members
 * (`?`) are those the backend does not mark as required.
 *
 * Source of truth: the backend's per-module schemas.py files, surfaced at
 * GET /openapi.json.
 * If a field is missing here, check the schema rather than guessing.
 */

/** Asset criticality accepted by the risk and financial endpoints. */
export type Criticality = 'Critical' | 'High' | 'Medium' | 'Low'

/* ------------------------------------------------------------------ *
 * POST /risk/calculate
 * ------------------------------------------------------------------ */

/** All seven fields are required by the backend; there are no defaults. */
export interface RiskCalculationRequest {
  asset_id: string
  cve_id: string
  cvss: number
  epss: number
  kev: boolean
  internet_exposed: boolean
  criticality: Criticality
}

export interface CalculationBreakdown {
  cvss_normalized: number
  epss: number
  kev_signal: number
  exposure_signal: number
  cvss_contribution: number
  epss_contribution: number
  kev_contribution: number
  exposure_contribution: number
}

export interface ModelInfo {
  version: string
  type: string
}

export interface RiskCalculationResponse {
  asset_id: string
  cve_id: string
  likelihood: number
  impact: number
  risk_score: number
  risk_level: string
  risk_drivers: string[]
  calculation: CalculationBreakdown
  model: ModelInfo
}

/* ------------------------------------------------------------------ *
 * POST /financial-crq/calculate
 * ------------------------------------------------------------------ */

/**
 * `likelihood` and `risk_score` come from a prior POST /risk/calculate.
 * Calling this endpoint without them returns 422.
 */
export interface FinancialCRQRequest {
  asset_id: string
  likelihood: number
  risk_score: number
  criticality: Criticality
  revenue_loss_per_hour: number
  downtime_hours: number
  cve_id?: string
  incident_response_cost?: number
  recovery_cost?: number
  regulatory_legal_cost?: number
  customer_business_impact?: number
  baseline_annual_frequency?: number
  currency?: string
}

/* ------------------------------------------------------------------ *
 * POST /optimization/run
 * ------------------------------------------------------------------ */

/**
 * Only `budget_limit` is required. The endpoint runs the whole pipeline
 * internally (risk -> financial -> control selection), so omitted inputs fall
 * back to backend defaults rather than failing.
 */
export interface OptimizationRunRequest {
  budget_limit: number
  asset_id?: string
  optimization_id?: string
  asset_type?: string
  cve_id?: string
  candidate_control_ids?: string[]
  existing_controls?: string[]
  cvss?: number
  epss?: number
  kev?: boolean
  internet_exposed?: boolean
  criticality?: Criticality
  revenue_loss_per_hour?: number
  downtime_hours?: number
  incident_response_cost?: number
  recovery_cost?: number
  regulatory_legal_cost?: number
  customer_business_impact?: number
  strategy?: string
  record_to_decision_store?: boolean
}

/**
 * `selected_controls` and `rejected_controls` contain stable control IDs
 * (e.g. "CTRL-MFA"), not human-readable names. Names are available from
 * AlternativesResponse -> alternatives[].control_explanations[].control.
 */
export interface OptimizationRunResponse {
  selected_controls: string[]
  rejected_controls: string[]
  total_cost: number
  remaining_budget: number
  baseline_risk: number
  residual_risk: number
  risk_reduction: number
  baseline_eal: number
  residual_eal: number
  financial_loss_avoided: number
  selection_reasons: Record<string, string[]>
  rejection_reasons: Record<string, string[]>
  model_version: string
  optimization_id: string
  data_source: string
  is_benchmark: boolean
  assessment_id?: string | null
  dependency_resolution?: unknown[] | null
}

/* ------------------------------------------------------------------ *
 * GET /decision/{optimization_id}/alternatives
 * ------------------------------------------------------------------ */

export interface ControlExplanation {
  control: string
  selected: boolean
  reasons: string[]
  control_id?: string | null
  cost?: number | null
  risk_reduction?: number | null
}

/** `selected_controls` holds control IDs, consistent with OptimizationRunResponse. */
export interface AlternativePortfolio {
  portfolio_id: string
  objective: string
  total_cost: number
  risk_reduction: number
  residual_risk: number
  workforce_hours: number
  implementation_days: number
  selected_controls: string[]
  control_explanations?: ControlExplanation[] | null
  is_selected?: boolean
  roi?: number | null
}

export interface AlternativesResponse {
  optimization_id: string
  baseline_risk: number
  budget_limit: number
  selected_portfolio_id: string
  alternatives: AlternativePortfolio[]
  decision_summary: string
  currency?: string
  data_source?: string
  is_benchmark?: boolean
  model_version?: string
  assessment_id?: string | null
}

/* ------------------------------------------------------------------ *
 * GET /orchestration/assets
 * ------------------------------------------------------------------ */

/** Current tracked state of one asset, as held by the orchestration layer. */
export interface AssetState {
  asset_id: string
  name: string
  cve_id: string
  cvss: number
  epss: number
  kev: boolean
  internet_exposed: boolean
  criticality: Criticality
  is_patched: boolean
  revenue_loss_per_hour: number
  downtime_hours: number
  incident_response_cost: number
  recovery_cost: number
  regulatory_fine_estimate: number
  customer_impact_cost: number
  budget_limit: number
}

/* ------------------------------------------------------------------ *
 * GET /decision/optimizations
 * ------------------------------------------------------------------ */

/**
 * A stored optimization scenario.
 *
 * On a cold backend this endpoint returns BENCHMARK scenarios
 * (OPT-BENCHMARK-001, OPT-ENTERPRISE-001) because the store falls back to
 * demonstration data when no real optimization has been run. Always filter with
 * partitionByProvenance() before treating any entry as a real result.
 */
export interface OptimizationSummary {
  optimization_id: string
  title: string
  baseline_risk: number
  budget_limit: number
  selected_portfolio_id: string
  created_at: string
  currency?: string
  data_source?: string
  is_benchmark?: boolean
  model_version?: string
  assessment_id?: string | null
}

/* ------------------------------------------------------------------ *
 * Provenance
 * ------------------------------------------------------------------ */

/**
 * Shape shared by anything that may be benchmark demonstration data rather than
 * a real optimizer result. See isBenchmark() / partitionByProvenance() in
 * lib/apiClient.ts — benchmark records must never be presented as real results.
 */
export interface ProvenanceMarked {
  is_benchmark?: boolean
  data_source?: string
}
