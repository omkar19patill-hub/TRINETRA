import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"
import { Loader2 } from "lucide-react"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-sm text-sm font-medium ring-offset-surface-base transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-text-secondary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        primary:
          "bg-text-tertiary text-surface-base hover:opacity-90 relative overflow-hidden group",
        secondary:
          "border border-border-default bg-transparent text-text-secondary hover:bg-surface-strong",
        ghost:
          "text-text-secondary hover:bg-surface-strong hover:text-text-tertiary",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-sm px-3",
        lg: "h-11 rounded-sm px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={props.disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {/* Animated conic border effect for primary button on hover */}
        {variant === "primary" && !loading && (
          <span className="absolute inset-0 -z-10 bg-[conic-gradient(from_90deg_at_50%_50%,transparent_0%,var(--accent-soft)_50%,transparent_100%)] opacity-0 group-hover:opacity-100 group-hover:animate-spin transition-opacity duration-300 pointer-events-none mix-blend-overlay" />
        )}
        <span className="relative z-10 flex items-center justify-center gap-2">{children}</span>
      </Comp>
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
