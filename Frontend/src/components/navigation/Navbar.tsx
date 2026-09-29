import { useEffect, useState } from "react"
import { cn } from "../../lib/utils"
import CircularText from "./CircularText"
import PillNav from "./PillNav"
import type { PillNavItem } from "./PillNav"
import "./PillNav.trinetra.css"

const LINKS: PillNavItem[] = [
  { label: "Problem", href: "#problem" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Intelligence", href: "#intelligence" },
  { label: "Platform", href: "#platform" },
  { label: "Dashboard", href: "/dashboard" },
]

const MOBILE_ITEMS: PillNavItem[] = [...LINKS, { label: "Explore the platform", href: "#platform" }]

const MOBILE_QUERY = "(max-width: 768px)"

/** Matches PillNav's own 768px mobile switch, so the two never disagree. */
function useIsMobile() {
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia(MOBILE_QUERY).matches : false
  )

  useEffect(() => {
    const query = window.matchMedia(MOBILE_QUERY)
    const onChange = (event: MediaQueryListEvent) => setIsMobile(event.matches)
    query.addEventListener("change", onChange)
    return () => query.removeEventListener("change", onChange)
  }, [])

  return isMobile
}

export interface NavbarProps {
  isVisible?: boolean
}

export function Navbar({ isVisible = true }: NavbarProps) {
  const isMobile = useIsMobile()

  return (
    <header
      className={cn(
        "trinetra-nav fixed top-0 inset-x-0 z-50 transition-all duration-300 ease-out",
        isVisible
          ? "opacity-100 translate-y-0 visible pointer-events-auto"
          : "opacity-0 -translate-y-4 invisible pointer-events-none"
      )}
      aria-hidden={!isVisible}
    >
      <div className="max-w-[1320px] mx-auto px-4 sm:px-6 pt-4">
        <div className="relative flex items-center justify-between min-h-[44px]">
          <a
            href="#top"
            className="nav-brand relative flex items-center justify-center w-[135px] h-[135px] shrink-0"
            aria-label="TRINETRA Home"
            tabIndex={isVisible ? 0 : -1}
          >
            <div
              className={cn(
                "absolute flex items-center justify-center",
                isVisible ? "pointer-events-auto" : "pointer-events-none"
              )}
              style={{
                width: 320,
                height: 320,
                left: "50%",
                top: "50%",
                transform: "translate(-50%, -50%) scale(0.422)",
                transformOrigin: "center center",
              }}
            >
              <CircularText />
            </div>
          </a>

          <PillNav
            items={isMobile ? MOBILE_ITEMS : LINKS}
            baseColor="#FFFFFF"
            pillColor="#050505"
            pillTextColor="#FAFAFA"
            hoveredPillTextColor="#050505"
          />

          <a
            href="#platform"
            tabIndex={isVisible ? 0 : -1}
            className="nav-cta inline-flex items-center text-[13px] font-medium text-black bg-t3 hover:bg-t2 px-4 py-2 rounded-sm transition-colors"
          >
            Explore the platform
          </a>
        </div>
      </div>
    </header>
  )
}
