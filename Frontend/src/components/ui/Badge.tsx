import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-xl border border-border-default px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-text-secondary focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "bg-surface-strong text-text-secondary",
        critical:
          "border-risk-critical/30 bg-risk-critical/10 text-risk-critical",
        high:
          "border-risk-high/30 bg-risk-high/10 text-risk-high",
        medium:
          "border-risk-medium/30 bg-risk-medium/10 text-risk-medium",
        low:
          "border-risk-low/30 bg-risk-low/10 text-risk-low",
        success:
          "border-risk-low/30 bg-risk-low/10 text-risk-low",
        neutral:
          "border-border-default bg-surface-muted text-text-primary",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
