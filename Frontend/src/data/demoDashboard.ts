import type { DemoRiskResult, RiskLevel } from "../types/marketing";

const BASE_RISK_SCORE = 72;
const BASE_EXPOSURE_CR = 18.4;

export function computeDemoRisk(budgetLakhs: number): DemoRiskResult {
  const reduction = Math.min(
    78,
    Math.round(12 + 66 * (1 - Math.exp(-budgetLakhs / 45)))
  );
  const riskScore = Math.max(18, Math.round(BASE_RISK_SCORE - reduction * 0.62));
  const exposureCr = Math.max(3.2, Number((BASE_EXPOSURE_CR * (1 - reduction / 100)).toFixed(1)));

  let riskLevel: RiskLevel = "low";
  if (riskScore >= 75) riskLevel = "critical";
  else if (riskScore >= 50) riskLevel = "high";
  else if (riskScore >= 25) riskLevel = "medium";

  return { budgetLakhs, riskScore, riskLevel, riskReductionPct: reduction, exposureCr };
}
