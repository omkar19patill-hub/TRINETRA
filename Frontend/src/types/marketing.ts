export interface StatCard {
  value: string;
  label: string;
  source: string;
}

export interface PipelineStage {
  index: number;
  title: string;
  description: string;
}

export interface DataSource {
  name: string;
  description: string;
}

export type RiskLevel = "critical" | "high" | "medium" | "low";

export interface DemoRiskResult {
  budgetLakhs: number;
  riskScore: number;
  riskLevel: RiskLevel;
  riskReductionPct: number;
  exposureCr: number;
}
