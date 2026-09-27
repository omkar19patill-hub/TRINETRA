import type { AssetState } from '../../types/api'

/** Budget used when no tracked asset carries one of its own. */
export const FALLBACK_BUDGET = 1800000

export function pickBudget(assets: AssetState[] | undefined): number {
  const withBudget = assets?.find((asset) => asset.budget_limit > 0)
  return withBudget ? withBudget.budget_limit : FALLBACK_BUDGET
}

export function formatInr(value: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatScore(value: number): string {
  return value.toFixed(1)
}
