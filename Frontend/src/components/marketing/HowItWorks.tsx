export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative border-t border-bd/60 py-24 md:py-32">
      <div className="max-w-[1320px] mx-auto px-4 sm:px-6">
        <div className="max-w-[560px]">
          <h2 className="text-[30px] sm:text-[36px] font-semibold text-t3 tracking-tight leading-tight">
            Every stage narrows raw threat data down to one decision.
          </h2>
          <p className="mt-4 text-[16px] text-t1 leading-relaxed">
            Where should the next rupee of security budget go — and can you defend that answer
            in front of a board.
          </p>
        </div>

        <div className="mt-16 grid md:grid-cols-5 gap-px bg-bd/60 rounded-md overflow-hidden border border-bd/60">
          <div className="bg-black p-6 flex flex-col gap-3">
            <span className="text-[11px] text-t1">01</span>
            <h3 className="text-[15px] font-medium text-t3">Threat Intelligence</h3>
            <p className="text-[13px] text-t1 leading-relaxed">Live CVE, EPSS and KEV data mapped to your actual assets.</p>
          </div>
          <div className="bg-black p-6 flex flex-col gap-3">
            <span className="text-[11px] text-t1">02</span>
            <h3 className="text-[15px] font-medium text-t3">Risk Analysis</h3>
            <p className="text-[13px] text-t1 leading-relaxed">Likelihood and business impact combined into one score.</p>
          </div>
          <div className="bg-black p-6 flex flex-col gap-3">
            <span className="text-[11px] text-t1">03</span>
            <h3 className="text-[15px] font-medium text-t3">Financial Risk</h3>
            <p className="text-[13px] text-t1 leading-relaxed">Converted into an estimated &#8377; exposure range — not a single guess.</p>
          </div>
          <div className="bg-black p-6 flex flex-col gap-3">
            <span className="text-[11px] text-t1">04</span>
            <h3 className="text-[15px] font-medium text-t3">Investment Optimization</h3>
            <p className="text-[13px] text-t1 leading-relaxed">A fixed budget, allocated for maximum risk reduction.</p>
          </div>
          <div className="bg-black p-6 flex flex-col gap-3">
            <span className="text-[11px] text-t1">05</span>
            <h3 className="text-[15px] font-medium text-t3">Security Action</h3>
            <p className="text-[13px] text-t1 leading-relaxed">Fix, mitigate, accept, or transfer — with the reasoning attached.</p>
          </div>
        </div>
      </div>
    </section>
  )
}
