import * as React from "react"
import { Card, CardContent } from "./Card"

export interface MetricCardProps {
  label?: string
  value: string | number
  context?: React.ReactNode
  source?: string
  isDemoData?: boolean
  className?: string
}

export function MetricCard({
  label,
  value,
  context,
  source,
  isDemoData = false,
  className,
}: MetricCardProps) {
  return (
    <Card className={className}>
      <CardContent className="p-6 flex flex-col h-full justify-between gap-4">
        <div>
          {label && (
            <p className="text-sm font-medium text-text-primary mb-2 uppercase tracking-wider">
              {label}
            </p>
          )}
          <div className="text-3xl font-bold text-text-tertiary">
            {value}
          </div>
          {context && (
            <p className="mt-2 text-sm text-text-secondary leading-snug">
              {context}
            </p>
          )}
        </div>
        
        {(source || isDemoData) && (
          <div className="mt-4 pt-4 border-t border-border-default/50 text-xs text-text-inverse">
            {isDemoData ? (
              <span className="font-semibold text-accent-soft uppercase tracking-wider">Demo Data</span>
            ) : (
              <span>Source: {source}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
