import { Menu, X } from "lucide-react"
import { useState } from "react"

export function Navbar() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <header className="fixed top-0 inset-x-0 z-50">
      <div className="max-w-[1320px] mx-auto px-4 sm:px-6 pt-4">
        <div className="flex items-center justify-between rounded-xl border border-bd/70 bg-black/60 backdrop-blur-xl px-4 py-2.5">
          <a href="#top" className="flex items-center gap-2.5 shrink-0">
            <img src="/images/symbol.png" alt="" className="h-7 w-7 object-contain" />
            <span className="font-semibold tracking-tight text-t3 text-[15px]">TRINETRA</span>
          </a>

          <nav className="hidden md:flex items-center gap-1 rounded-full bg-gradient-to-br from-white/[0.06] to-transparent border border-white/[0.06] px-1.5 py-1.5 absolute left-1/2 -translate-x-1/2">
            <a href="#problem" className="px-4 py-1.5 text-[13px] text-t1 hover:text-t3 rounded-full hover:bg-white/[0.06] transition-colors">Problem</a>
            <a href="#how-it-works" className="px-4 py-1.5 text-[13px] text-t1 hover:text-t3 rounded-full hover:bg-white/[0.06] transition-colors">How it works</a>
            <a href="#intelligence" className="px-4 py-1.5 text-[13px] text-t1 hover:text-t3 rounded-full hover:bg-white/[0.06] transition-colors">Intelligence</a>
            <a href="#platform" className="px-4 py-1.5 text-[13px] text-t1 hover:text-t3 rounded-full hover:bg-white/[0.06] transition-colors">Platform</a>
          </nav>

          <div className="flex items-center gap-2">
            <a href="#platform" className="hidden sm:inline-flex items-center text-[13px] font-medium text-black bg-t3 hover:bg-t2 px-4 py-2 rounded-sm transition-colors">
              Explore the platform
            </a>
            <button 
              onClick={() => setIsOpen(!isOpen)}
              aria-label="Open menu" 
              aria-expanded={isOpen} 
              className="md:hidden p-2 text-t2"
            >
              {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {isOpen && (
          <div className="md:hidden mt-2 rounded-xl border border-bd/70 bg-black/95 backdrop-blur-xl p-3 flex flex-col gap-1">
            <a href="#problem" onClick={() => setIsOpen(false)} className="px-3 py-2.5 text-sm text-t1 hover:text-t3 rounded-sm">Problem</a>
            <a href="#how-it-works" onClick={() => setIsOpen(false)} className="px-3 py-2.5 text-sm text-t1 hover:text-t3 rounded-sm">How it works</a>
            <a href="#intelligence" onClick={() => setIsOpen(false)} className="px-3 py-2.5 text-sm text-t1 hover:text-t3 rounded-sm">Intelligence</a>
            <a href="#platform" onClick={() => setIsOpen(false)} className="px-3 py-2.5 text-sm text-t1 hover:text-t3 rounded-sm">Platform</a>
            <a href="#platform" onClick={() => setIsOpen(false)} className="mt-1 text-center text-sm font-medium text-black bg-t3 px-4 py-2.5 rounded-sm">Explore the platform</a>
          </div>
        )}
      </div>
    </header>
  )
}
