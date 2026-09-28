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

/**
 * Result of POST /financial-crq/calculate.
 *
 * `monte_carlo_input` is the payload this result can be fed into for a
 * simulation; it is left untyped here because no screen currently runs one.
 */
export interface FinancialCRQResult {
  asset_id: string
  likelihood: number
  baseline_annual_frequency: number
  annual_event_frequency: number
  downtime_loss: number
  incident_response_cost: number
  recovery_cost: number
  regulatory_legal_cost: number
  customer_business_impact: number
  total_loss_magnitude: number
  expected_annual_loss: number
  currency: string
  assumptions: string[]
  model_version: string
  explanation: string[]
  cve_id?: string | null
  monte_carlo_input?: unknown
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
 * GET /vulnerabilities
 * ------------------------------------------------------------------ */

export interface VulnerabilityListItem {
  cve_id: string
  cvss: number
  severity: string
  epss: number
  kev: boolean
  known_ransomware_use: boolean
  ingested_at: string
  last_modified_at: string
}

export interface VulnerabilityListResponse {
  total: number
  page: number
  page_size: number
  vulnerabilities: VulnerabilityListItem[]
}

/* ------------------------------------------------------------------ *
 * GET /vulnerabilities/{cve_id}/enriched
 * ------------------------------------------------------------------ */

/** Where each intelligence signal came from. */
export interface VulnerabilitySourceMetadata {
  cvss_source?: string
  epss_source?: string
  kev_source?: string
  sources?: string[]
  source_statuses?: Record<string, string>
}

/** When each upstream feed was last seen. */
export interface VulnerabilityDataFreshness {
  nvd_last_modified?: string
  epss_date?: string
  kev_checked_at?: string
  source_updated_at?: string
  ingested_at?: string
}

export interface EnrichedVulnerability {
  cve_id: string
  cvss: number
  cvss_version: string
  cvss_vector: string
  epss: number
  epss_percentile: number
  kev: boolean
  known_ransomware_use: boolean
  severity: string
  description: string
  source_metadata?: VulnerabilitySourceMetadata
  data_freshness?: VulnerabilityDataFreshness
}

/* ------------------------------------------------------------------ *
 * POST /optimization/before-after
 * ------------------------------------------------------------------ */

/**
 * Supply either an existing optimization_id, or run_parameters to simulate a
 * scenario that has not been run. Set record_to_decision_store: false on
 * run_parameters so a what-if simulation does not persist into the store.
 */
export interface BeforeAfterRequest {
  optimization_id?: string
  run_parameters?: OptimizationRunRequest
}

/** Risk and loss position at one point in time. */
export interface RiskSnapshot {
  risk_score: number
  risk_level: string
  likelihood: number
  impact: number
  expected_annual_loss: number
  total_loss_magnitude: number
  annual_event_frequency: number
  downtime_loss: number
}

export interface DeltaMetrics {
  risk_reduction_points: number
  risk_reduction_percent: number
  financial_loss_avoided: number
  financial_loss_avoided_percent: number
  total_investment_cost: number
  net_annual_financial_benefit: number
  return_on_security_investment: number
}

export interface BeforeAfterResponse {
  optimization_id: string
  baseline: RiskSnapshot
  residual: RiskSnapshot
  deltas: DeltaMetrics
  controls_applied: string[]
  model_version?: string
  data_source?: string
  is_benchmark?: boolean
}

/* ------------------------------------------------------------------ *
 * GET /decision/{optimization_id}/marginal-budget
 * ------------------------------------------------------------------ */

export interface MarginalBudgetEvaluation {
  additional_budget: number
  additional_risk_reduction: number
  marginal_reduction_per_rupee: number
  total_budget: number
  total_risk_reduction: number
  efficiency_assessment: string
  explanation: string
  additional_controls_selected?: string[]
}

export interface MarginalBudgetResponse {
  optimization_id: string
  base_budget: number
  base_risk_reduction: number
  evaluations: MarginalBudgetEvaluation[]
  diminishing_returns_observed: boolean
  recommendation: string
  currency?: string
  data_source?: string
  is_benchmark?: boolean
  model_version?: string
  assessment_id?: string | null
}

/* ------------------------------------------------------------------ *
 * GET /decision/{optimization_id}/opportunity-cost
 * ------------------------------------------------------------------ */

/** `controls_gained` / `controls_sacrificed` hold control IDs. */
export interface OpportunityCostComparison {
  compared_portfolio_id: string
  compared_objective: string
  selected_risk_reduction: number
  compared_risk_reduction: number
  risk_reduction_difference: number
  cost_difference: number
  workforce_hours_difference: number
  implementation_days_difference: number
  tradeoff_narrative: string
  controls_gained?: string[]
  controls_sacrificed?: string[]
}

export interface OpportunityCostResponse {
  optimization_id: string
  selected_portfolio_id: string
  selected_portfolio_name: string
  selected_risk_reduction: number
  selected_total_cost: number
  comparisons: OpportunityCostComparison[]
  summary_statement: string
  currency?: string
  assumptions?: string[]
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

/* ------------------------------------------------------------------ *
 * POST /risk/assessment-batch
 * ------------------------------------------------------------------ */

export interface AssessmentResultItem {
  asset_id: string
  asset_name?: string | null
  risk_score: number
  financial_exposure: number
  cve_id?: string | null
  criticality?: Criticality | null
  assessment_data?: Record<string, unknown>
}

export interface AssessmentBatchCreate {
  batch_id?: string
  source?: string
  total_rows: number
  successful_rows: number
  failed_rows: number
  status?: string
  results: AssessmentResultItem[]
  risk_appetite?: number | null
}

export interface RiskSnapshotResponse {
  id: string
  batch_id?: string | null
  timestamp: string
  total_exposure: number
  average_risk: number
  critical_assets: number
  high_risk_assets: number
  risk_appetite?: number | null
  created_at: string
}

export interface AssessmentBatchResponse {
  batch_id: string
  created_at: string
  source: string
  total_rows: number
  successful_rows: number
  failed_rows: number
  status: string
  snapshot: RiskSnapshotResponse
}

export interface RiskChangeResponse {
  has_history: boolean
  has_baseline: boolean
  current_snapshot?: RiskSnapshotResponse | null
  previous_snapshot?: RiskSnapshotResponse | null
  previous_exposure?: number | null
  current_exposure?: number | null
  absolute_change?: number | null
  percentage_change?: number | null
  previous_average_risk?: number | null
  current_average_risk?: number | null
  average_risk_change?: number | null
  previous_critical_assets?: number | null
  current_critical_assets?: number | null
  critical_assets_change?: number | null
  previous_high_risk_assets?: number | null
  current_high_risk_assets?: number | null
  high_risk_assets_change?: number | null
}


