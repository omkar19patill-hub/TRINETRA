import { ArrowUp } from "lucide-react"
import { cn } from "../../lib/utils"

export interface BackToTopProps {
  isVisible: boolean
}

export function BackToTop({ isVisible }: BackToTopProps) {
  const scrollToTop = () => {
    const heroElement = document.getElementById("top")
    if (heroElement) {
      heroElement.scrollIntoView({ behavior: "smooth" })
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" })
    }
  }

  return (
    <button
      type="button"
      onClick={scrollToTop}
      aria-label="Back to top"
      aria-hidden={!isVisible}
      tabIndex={isVisible ? 0 : -1}
      className={cn(
        "group fixed bottom-6 right-6 z-40 sm:bottom-8 sm:right-8",
        "inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full",
        "bg-muted/85 hover:bg-strong border border-bd/80 hover:border-t1/50",
        "text-t2 hover:text-t3 text-[12px] sm:text-[13px] font-medium tracking-normal",
        "shadow-lg shadow-black/50 backdrop-blur-md",
        "transition-all duration-300 ease-out active:scale-95 cursor-pointer",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-2",
        isVisible
          ? "opacity-100 translate-y-0 visible pointer-events-auto"
          : "opacity-0 translate-y-3 invisible pointer-events-none"
      )}
    >
      <ArrowUp className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-t1 group-hover:text-t3 transition-colors" />
      <span>Back to top</span>
    </button>
  )
}
