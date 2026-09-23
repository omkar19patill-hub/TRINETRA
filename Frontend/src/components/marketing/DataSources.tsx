export function DataSources() {
  return (
    <section id="intelligence" className="relative border-t border-bd/60 py-24 md:py-32 overflow-hidden">
      <div className="max-w-[1320px] mx-auto px-4 sm:px-6">
        <div className="grid lg:grid-cols-2 gap-14 items-center">
          <div>
            <h2 className="text-[30px] sm:text-[36px] font-semibold text-t3 tracking-tight leading-tight">
              Built on the sources security teams already trust.
            </h2>
            <p className="mt-4 text-[16px] text-t1 leading-relaxed max-w-[440px]">
              No proprietary black box. Every risk score traces back to public, verifiable
              threat intelligence — refreshed on a schedule, not a calendar year.
            </p>
            <dl className="mt-8 space-y-5">
              <div className="flex gap-3">
                <dt className="text-t3 font-medium text-[14px] w-16 shrink-0">NVD</dt>
                <dd className="text-t1 text-[13px]">Vulnerability data, CVSS severity, affected products.</dd>
              </div>
              <div className="flex gap-3">
                <dt className="text-t3 font-medium text-[14px] w-16 shrink-0">CISA KEV</dt>
                <dd className="text-t1 text-[13px]">Confirmed, real-world exploitation signal.</dd>
              </div>
              <div className="flex gap-3">
                <dt className="text-t3 font-medium text-[14px] w-16 shrink-0">EPSS</dt>
                <dd className="text-t1 text-[13px]">Probability of exploitation in the next 30 days.</dd>
              </div>
              <div className="flex gap-3">
                <dt className="text-t3 font-medium text-[14px] w-16 shrink-0">ATT&amp;CK</dt>
                <dd className="text-t1 text-[13px]">Adversary tactics and techniques, for context.</dd>
              </div>
            </dl>
          </div>

          <div className="relative aspect-square max-w-[440px] mx-auto" aria-hidden="true">
            <svg viewBox="0 0 400 400" className="w-full h-full">
              <g stroke="#262626" strokeWidth="1.5" fill="none">
                <path d="M60 60 L200 200" className="beam-line" stroke="#3355ff" opacity="0.5"/>
                <path d="M340 60 L200 200" className="beam-line" stroke="#3355ff" opacity="0.5" style={{ animationDelay: '-4s' }}/>
                <path d="M60 340 L200 200" className="beam-line" stroke="#3355ff" opacity="0.5" style={{ animationDelay: '-9s' }}/>
                <path d="M340 340 L200 200" className="beam-line" stroke="#3355ff" opacity="0.5" style={{ animationDelay: '-13s' }}/>
              </g>
              <circle cx="200" cy="200" r="46" fill="#050505" stroke="#3355ff" strokeWidth="1.5"/>
              <text x="200" y="196" textAnchor="middle" fill="#fafafa" fontSize="11" fontFamily="Inter" fontWeight="600">Risk</text>
              <text x="200" y="211" textAnchor="middle" fill="#fafafa" fontSize="11" fontFamily="Inter" fontWeight="600">Engine</text>

              <g className="animate-float">
                <rect x="20" y="30" width="80" height="36" rx="8" fill="#050505" stroke="#333333"/>
                <text x="60" y="53" textAnchor="middle" fill="#a6a6a6" fontSize="11" fontFamily="Inter">NVD</text>
              </g>
              <g className="animate-float" style={{ animationDelay: '.3s' }}>
                <rect x="300" y="30" width="80" height="36" rx="8" fill="#050505" stroke="#333333"/>
                <text x="340" y="53" textAnchor="middle" fill="#a6a6a6" fontSize="11" fontFamily="Inter">CISA KEV</text>
              </g>
              <g className="animate-float" style={{ animationDelay: '.6s' }}>
                <rect x="20" y="330" width="80" height="36" rx="8" fill="#050505" stroke="#333333"/>
                <text x="60" y="353" textAnchor="middle" fill="#a6a6a6" fontSize="11" fontFamily="Inter">EPSS</text>
              </g>
              <g className="animate-float" style={{ animationDelay: '.9s' }}>
                <rect x="300" y="330" width="80" height="36" rx="8" fill="#050505" stroke="#333333"/>
                <text x="340" y="353" textAnchor="middle" fill="#a6a6a6" fontSize="10.5" fontFamily="Inter">ATT&amp;CK</text>
              </g>
            </svg>
          </div>
        </div>
      </div>
    </section>
  )
}
