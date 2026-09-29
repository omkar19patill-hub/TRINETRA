export function Hero() {
  return (
    <section id="top" className="relative overflow-hidden bg-grid">
      <div className="absolute inset-0 fade-mask-b bg-gradient-to-b from-transparent via-black/40 to-black pointer-events-none"></div>
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[700px] rounded-full bg-accent/10 blur-[120px] pointer-events-none"></div>

      <div className="relative max-w-[1320px] mx-auto px-4 sm:px-6 pt-36 pb-20 md:pt-44 md:pb-28">
        <div className="grid lg:grid-cols-2 gap-14 items-center">
          
          {/* Left: copy */}
          <div>
            <h1 className="text-[42px] sm:text-[54px] lg:text-[60px] font-semibold text-t3 leading-[1.05] tracking-tight">
              See <span className="font-instrument italic font-normal">Threat</span>.<br />
              Measure <span className="font-instrument italic font-normal">Risk</span>.<br />
              Optimize <span className="font-instrument italic font-normal">Investment</span>.
            </h1>

            <p className="mt-6 font-space-mono text-[15px] sm:text-[16px] leading-relaxed text-t1 max-w-[480px]">
              Trinetra turns raw vulnerability data into a live, rupee-denominated risk number —
              and tells you exactly where the next rupee of security budget should go.
            </p>
          </div>

          {/* Right: pipeline visualization */}
          <div className="relative hidden lg:block" aria-hidden="true">
            <svg viewBox="0 0 560 520" className="w-full h-auto overflow-visible">
              <path id="pipePath" d="M 40 60 C 200 60, 160 180, 300 200 C 440 220, 380 340, 500 380"
                    fill="none" stroke="#262626" strokeWidth="2"/>
              <path d="M 40 60 C 200 60, 160 180, 300 200 C 440 220, 380 340, 500 380"
                    fill="none" stroke="#3355ff" strokeWidth="2" className="beam-line" opacity="0.6"/>

              <circle r="5" fill="#7c93ff">
                <animateMotion dur="5s" repeatCount="indefinite"
                  path="M 40 60 C 200 60, 160 180, 300 200 C 440 220, 380 340, 500 380"/>
              </circle>

              {/* Node 1: CVE input */}
              <g transform="translate(0,30)">
                <rect x="4" y="4" width="150" height="64" rx="10" fill="#050505" stroke="#333333"/>
                <text x="20" y="28" fill="#a6a6a6" fontSize="10" fontFamily="Inter">CVE-2026-1234</text>
                <text x="20" y="46" fill="#fafafa" fontSize="13" fontFamily="Inter" fontWeight="600">Critical &middot; KEV listed</text>
              </g>

              {/* Node 2: Risk score */}
              <g transform="translate(220,150)">
                <g className="animate-float" style={{ animationDelay: '.2s' }}>
                  <rect x="4" y="4" width="150" height="64" rx="10" fill="#050505" stroke="#333333"/>
                  <text x="20" y="28" fill="#a6a6a6" fontSize="10" fontFamily="Inter">Risk Score</text>
                  <text x="20" y="48" fill="#fafafa" fontSize="18" fontFamily="Inter" fontWeight="700">89.5<tspan fill="#ef4444" fontSize="11" dx="6">CRITICAL</tspan></text>
                </g>
              </g>

              {/* Node 3: Financial exposure */}
              <g transform="translate(360,330)">
                <g className="animate-float" style={{ animationDelay: '.5s' }}>
                  <rect x="4" y="4" width="180" height="72" rx="10" fill="#050505" stroke="#3355ff"/>
                  <text x="20" y="26" fill="#a6a6a6" fontSize="10" fontFamily="Inter">Estimated Financial Exposure</text>
                  <text x="20" y="52" fill="#7c93ff" fontSize="20" fontFamily="Inter" fontWeight="700">&#8377;3.3L / yr</text>
                </g>
              </g>
            </svg>
          </div>

        </div>
      </div>
    </section>
  )
}
