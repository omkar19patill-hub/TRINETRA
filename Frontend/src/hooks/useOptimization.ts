/**
 * TanStack Query hooks for the dashboard's optimization data.
 *
 * Read vs write matters here. POST /optimization/run CREATES an optimization,
 * so it is exposed as a mutation and must only fire from an explicit user
 * action, never on mount. Running it automatically would mean the dashboard
 * could never reach a genuine cold-start state.
 *
 * GET /decision/optimizations is the read that answers "does real data exist
 * yet?". It returns benchmark scenarios on a cold backend, so callers must pass
 * the result through partitionByProvenance() before display.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { UseMutationResult, UseQueryResult } from '@tanstack/react-query'

import { api } from '../lib/apiClient'
import type { ApiError } from '../lib/apiClient'
import type {
  AssetState,
  OptimizationRunRequest,
  OptimizationRunResponse,
  OptimizationSummary,
} from '../types/api'

export const optimizationKeys = {
  all: ['optimizations'] as const,
  list: () => ['optimizations', 'list'] as const,
  assets: () => ['assets'] as const,
}

/** Retrying a 4xx is pointless: the request itself is the problem. */
function retryOnlyServerErrors(failureCount: number, error: ApiError): boolean {
  if (error.status >= 400 && error.status < 500) {
    return false
  }
  return failureCount < 2
}

/**
 * Stored optimization scenarios.
 *
 * May include benchmark demonstration data. Partition before rendering.
 */
export function useOptimizations(): UseQueryResult<OptimizationSummary[], ApiError> {
  return useQuery<OptimizationSummary[], ApiError>({
    queryKey: optimizationKeys.list(),
    queryFn: () => api.get<OptimizationSummary[]>('/decision/optimizations'),
    retry: retryOnlyServerErrors,
  })
}

/** Assets currently tracked by the orchestration layer. */
export function useAssets(): UseQueryResult<AssetState[], ApiError> {
  return useQuery<AssetState[], ApiError>({
    queryKey: optimizationKeys.assets(),
    queryFn: () => api.get<AssetState[]>('/orchestration/assets'),
    retry: retryOnlyServerErrors,
  })
}

/**
 * Run a real optimization.
 *
 * A mutation, not a query: this writes to the backend's decision store. On
 * success the optimizations list is invalidated so the dashboard leaves its
 * empty state.
 */
export function useRunOptimization(): UseMutationResult<
  OptimizationRunResponse,
  ApiError,
  OptimizationRunRequest
> {
  const queryClient = useQueryClient()

  return useMutation<OptimizationRunResponse, ApiError, OptimizationRunRequest>({
    mutationFn: (request) => api.post<OptimizationRunResponse>('/optimization/run', request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: optimizationKeys.all })
    },
  })
}
