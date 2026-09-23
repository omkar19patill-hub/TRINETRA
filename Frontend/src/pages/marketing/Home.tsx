import { Navbar } from "../../components/navigation/Navbar"
import { Hero } from "../../components/marketing/Hero"
import { ProblemStats } from "../../components/marketing/ProblemStats"
import { HowItWorks } from "../../components/marketing/HowItWorks"
import { DataSources } from "../../components/marketing/DataSources"
import { ProductPreview } from "../../components/marketing/ProductPreview"
import { CtaSection } from "../../components/marketing/CtaSection"
import { Footer } from "../../components/marketing/Footer"

export default function Home() {
  return (
    <>
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-[100] focus:bg-accent focus:text-white focus:px-4 focus:py-2 focus:rounded-sm">Skip to content</a>
      <Navbar />
      <main id="main">
        <Hero />
        <ProblemStats />
        <HowItWorks />
        <DataSources />
        <ProductPreview />
        <CtaSection />
      </main>
      <Footer />
    </>
  )
}
