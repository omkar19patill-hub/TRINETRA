export function DataSources() {
  return (
    <section id="intelligence" className="relative border-t border-bd/60 py-24 md:py-32 overflow-hidden">
      <div className="max-w-[1320px] mx-auto px-4 sm:px-6">
        <div className="max-w-[680px]">
          <h2 className="text-[30px] sm:text-[36px] font-semibold text-t3 tracking-tight leading-tight">
            Built on the sources security teams already trust.
          </h2>
          <p className="mt-4 font-space-mono text-[15px] sm:text-[16px] text-t1 leading-relaxed">
            No proprietary black box. Every risk score traces back to public, verifiable
            threat intelligence — refreshed on a schedule, not a calendar year.
          </p>
          <dl className="mt-10 space-y-5">
            <div className="flex items-baseline gap-4 sm:gap-6">
              <dt className="font-serif font-medium text-t3 text-[15px] sm:text-[16px] w-28 sm:w-32 shrink-0">1. NVD</dt>
              <dd className="text-t1 text-[13px] sm:text-[14px] leading-relaxed">Vulnerability data, CVSS severity, affected products.</dd>
            </div>
            <div className="flex items-baseline gap-4 sm:gap-6">
              <dt className="font-serif font-medium text-t3 text-[15px] sm:text-[16px] w-28 sm:w-32 shrink-0">2. CISA KEV</dt>
              <dd className="text-t1 text-[13px] sm:text-[14px] leading-relaxed">Confirmed, real-world exploitation signal.</dd>
            </div>
            <div className="flex items-baseline gap-4 sm:gap-6">
              <dt className="font-serif font-medium text-t3 text-[15px] sm:text-[16px] w-28 sm:w-32 shrink-0">3. EPSS</dt>
              <dd className="text-t1 text-[13px] sm:text-[14px] leading-relaxed">Probability of exploitation in the next 30 days.</dd>
            </div>
            <div className="flex items-baseline gap-4 sm:gap-6">
              <dt className="font-serif font-medium text-t3 text-[15px] sm:text-[16px] w-28 sm:w-32 shrink-0">4. ATT&amp;CK</dt>
              <dd className="text-t1 text-[13px] sm:text-[14px] leading-relaxed">Adversary tactics and techniques, for context.</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>
  )
}
