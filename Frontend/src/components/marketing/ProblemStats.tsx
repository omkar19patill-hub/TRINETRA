export function ProblemStats() {
  return (
    <section id="problem" className="relative border-t border-bd/60 py-24 md:py-32">
      <div className="max-w-[1320px] mx-auto px-4 sm:px-6">
        <div className="max-w-[620px]">
          <h2 className="text-[30px] sm:text-[36px] font-semibold text-t3 tracking-tight leading-tight">
            Thousands of vulnerabilities. One patch cycle. No way to know which ones matter.
          </h2>
          <p className="mt-4 text-[16px] text-t1 leading-relaxed">
            CVSS tells you how severe a flaw is — not how likely it is to be exploited, which
            asset it threatens, or what it would actually cost. Most risk assessments are a
            once-a-year PDF, disconnected from the language a board actually spends money in.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card-shell rounded-md p-5">
            <div className="text-[26px] font-semibold text-t3 tabular-nums">29,44,248</div>
            <div className="mt-2 text-[13px] text-t1 leading-snug">Cyber incidents in India, 2025 — up from 20,41,360 in 2024</div>
            <div className="mt-3 text-[11px] text-t1/70">CERT-In, Govt. of India</div>
          </div>
          <div className="card-shell rounded-md p-5">
            <div className="text-[26px] font-semibold text-t3 tabular-nums">31%</div>
            <div className="mt-2 text-[13px] text-t1 leading-snug">Of breaches began with an exploited software vulnerability</div>
            <div className="mt-3 text-[11px] text-t1/70">Verizon 2026 DBIR</div>
          </div>
          <div className="card-shell rounded-md p-5">
            <div className="text-[26px] font-semibold text-t3 tabular-nums">263%</div>
            <div className="mt-2 text-[13px] text-t1 leading-snug">Growth in CVE submissions between 2020 and 2025</div>
            <div className="mt-3 text-[11px] text-t1/70">NIST</div>
          </div>
          <div className="card-shell rounded-md p-5">
            <div className="text-[26px] font-semibold text-t3 tabular-nums">&#8377;22 Cr</div>
            <div className="mt-2 text-[13px] text-t1 leading-snug">Average cost of a data breach in India, 2025</div>
            <div className="mt-3 text-[11px] text-t1/70">IBM Cost of a Data Breach</div>
          </div>
        </div>
      </div>
    </section>
  )
}
