export function CtaSection() {
  return (
    <section className="relative border-t border-bd/60 py-24 md:py-32">
      <div className="max-w-[900px] mx-auto px-4 sm:px-6 text-center">
        <h2 className="text-[34px] sm:text-[48px] lg:text-[56px] font-semibold leading-[1.05] tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-accent-2 to-white animate-gradient-x">
          Stop guessing where your<br className="hidden sm:block"/> security budget goes.
        </h2>
        <div className="mt-10">
          <a href="#top" className="conic-btn relative inline-flex items-center justify-center rounded-sm bg-t3 text-black text-[14px] font-medium px-7 py-3.5">
            <span className="conic-border"></span>
            <span className="relative z-10">Explore Trinetra</span>
          </a>
        </div>
      </div>
    </section>
  )
}
