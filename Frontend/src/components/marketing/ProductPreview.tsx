import { useState } from "react"

export function ProductPreview() {
  const [budget, setBudget] = useState(40)

  // Demo logic matches prototype.html
  const reduction = Math.min(78, Math.round(12 + 66 * (1 - Math.exp(-budget / 45))))
  const newScore = Math.max(18, Math.round(72 - (reduction * 0.62)))
  const newExposureCr = Math.max(3.2, Number((18.4 * (1 - reduction / 100)).toFixed(1)))

  let level = 'LOW'
  let cls = 'risk-severity-low'
  if (newScore >= 75) { level = 'CRITICAL'; cls = 'risk-severity-critical' }
  else if (newScore >= 50) { level = 'HIGH'; cls = 'risk-severity-high' }
  else if (newScore >= 25) { level = 'MEDIUM'; cls = 'risk-severity-medium' }

  return (
    <section id="platform" className="relative border-t border-bd/60 py-24 md:py-32">
      <div className="max-w-[1320px] mx-auto px-4 sm:px-6">
        <div className="max-w-[600px] mx-auto text-center">
          <h2 className="text-[30px] sm:text-[36px] font-semibold text-t3 tracking-tight leading-tight">
            Move the budget. Watch the risk number change.
          </h2>
          <p className="mt-4 text-[16px] text-t1 leading-relaxed">
            A live look at the dashboard — try the budget slider below.
          </p>
        </div>

        <div className="mt-14 max-w-[880px] mx-auto rounded-lg border border-bd bg-[#030303] overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-3.5 border-b border-bd/70">
            <span className="w-2.5 h-2.5 rounded-full bg-[#333]"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-[#333]"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-[#333]"></span>
            <span className="ml-3 text-[11px] text-t1">trinetra.app/dashboard/investments &middot; demo data</span>
          </div>

          <div className="p-6 sm:p-8 grid sm:grid-cols-3 gap-5">
            <div className="sm:col-span-1 space-y-5">
              <div className="card-shell rounded-md p-4">
                <div className="text-[11px] text-t1">Overall Risk</div>
                <div className="mt-1 text-[26px] font-semibold text-t3 tabular-nums">
                  {newScore}
                  <span className="text-[13px] text-t1 font-normal"> /100</span>
                </div>
                <div className={`mt-1 text-[11px] ${cls}`}>{level}</div>
              </div>
              <div className="card-shell rounded-md p-4">
                <div className="text-[11px] text-t1">Estimated Financial Exposure</div>
                <div className="mt-1 text-[22px] font-semibold text-accent-2 tabular-nums">&#8377;{newExposureCr} Cr</div>
                <div className="mt-1 text-[11px] text-t1">Annualized, demo data</div>
              </div>
            </div>

            <div className="sm:col-span-2 card-shell rounded-md p-5 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-[13px] font-medium text-t2">Security budget</span>
                <span className="text-[15px] font-semibold text-t3 tabular-nums">
                  &#8377;{budget >= 100 ? `${(budget / 100).toFixed(budget % 100 === 0 ? 0 : 1)} Cr` : `${budget} L`}
                </span>
              </div>
              <input 
                type="range" 
                min="10" 
                max="100" 
                value={budget} 
                step="5"
                onChange={(e) => setBudget(Number(e.target.value))}
                className="mt-6 w-full accent-accent h-1.5 rounded-full bg-strong cursor-pointer"
                aria-label="Adjust demo security budget in lakhs of rupees"
              />
              <div className="flex justify-between text-[11px] text-t1 mt-1">
                <span>&#8377;10 L</span><span>&#8377;1 Cr</span>
              </div>

              <div className="mt-6 pt-5 border-t border-bd/60 flex items-center justify-between">
                <span className="text-[13px] text-t1">Risk reduction at this budget</span>
                <span className="text-[18px] font-semibold text-low tabular-nums">{reduction}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
