import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import Home from './pages/marketing/Home'
import DashboardLayout from './layouts/DashboardLayout'
import Dashboard from './pages/dashboard/Dashboard'
import InvestmentOptimization from './pages/dashboard/InvestmentOptimization'
import FinancialRisk from './pages/dashboard/FinancialRisk'
import ThreatIntelligence from './pages/dashboard/ThreatIntelligence'
import RiskAnalysis from './pages/dashboard/RiskAnalysis'
import WhatIfSimulation from './pages/dashboard/WhatIfSimulation'
import ActionCenter from './pages/dashboard/ActionCenter'
import BulkAssessment from './pages/dashboard/BulkAssessment'
import NotFound from './pages/NotFound'
import AppBackground from './components/background/AppBackground'
import './styles/globals.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Backend results are deterministic for a given input, so refetching on
      // every window focus would add load without changing what is displayed.
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppBackground />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="intelligence" element={<ThreatIntelligence />} />
            <Route path="risk" element={<RiskAnalysis />} />
            <Route path="financial" element={<FinancialRisk />} />
            <Route path="investments" element={<InvestmentOptimization />} />
            <Route path="simulation" element={<WhatIfSimulation />} />
            <Route path="actions" element={<ActionCenter />} />
            <Route path="bulk-assessment" element={<BulkAssessment />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
