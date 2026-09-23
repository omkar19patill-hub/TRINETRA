export function Footer() {
  return (
    <footer className="border-t border-bd/60 py-16">
      <div className="max-w-[1320px] mx-auto px-4 sm:px-6">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-10">
          <div className="lg:col-span-1">
            <div className="flex items-center gap-2.5">
              <img src="/images/symbol.png" alt="" className="h-6 w-6 object-contain" />
              <span className="font-semibold text-t3 text-[14px]">TRINETRA</span>
            </div>
            <p className="mt-4 text-[13px] text-t1 leading-relaxed max-w-[220px]"></p>
          </div>

          <div>
            <div className="text-[12px] text-t1 mb-3">Platform</div>
            <ul className="space-y-2 text-[13px] text-t1">
              <li><a href="#problem" className="hover:text-t3">Problem</a></li>
              <li><a href="#how-it-works" className="hover:text-t3">How it works</a></li>
              <li><a href="#intelligence" className="hover:text-t3">Intelligence</a></li>
              <li><a href="#platform" className="hover:text-t3">Dashboard preview</a></li>
            </ul>
          </div>

          <div>
            <div className="text-[12px] text-t1 mb-3">Data sources</div>
            <ul className="space-y-2 text-[13px] text-t1">
              <li>NVD</li>
              <li>CISA KEV</li>
              <li>FIRST EPSS</li>
              <li>MITRE ATT&amp;CK</li>
            </ul>
          </div>

          <div>
            <div className="text-[12px] text-t1 mb-3">Project</div>
            <ul className="space-y-2 text-[13px] text-t1">
              <li>SIH26105 &middot; Smart India Hackathon 2026</li>
              <li>Theme: Blockchain &amp; Cybersecurity</li>
              <li>Team Vajra</li>
            </ul>
          </div>
        </div>

        <div className="mt-14 pt-6 border-t border-bd/60 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-[12px] text-t1">&copy; 2026 Trinetra. Built for SIH26105.</p>
          <p className="text-[12px] text-t1">Demo data shown throughout is illustrative.</p>
        </div>
      </div>
    </footer>
  )
}
