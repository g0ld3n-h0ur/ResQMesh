import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Layout } from "./components/Layout"
import { ErrorBoundary } from "./components/ErrorBoundary"
import { Login } from "./pages/Login"
import { Dashboard } from "./pages/Dashboard"
import { CitizenSOS } from "./pages/CitizenSOS"
import { AIPrediction } from "./pages/AIPrediction"
import { ResourceAllocation } from "./pages/ResourceAllocation"
import { Shelters } from "./pages/Shelters"
import { Hospitals } from "./pages/Hospitals"
import { Reports } from "./pages/Reports"
import { PriorityRanking } from "./pages/PriorityRanking"
import { Coordination } from "./pages/Coordination"
import { RoutingRerouting } from "./pages/RoutingRerouting"
import { ProofOfDelivery } from "./pages/ProofOfDelivery"
import { AuditLogs } from "./pages/AuditLogs"
import { CSRTransparency } from "./pages/CSRTransparency"
import { SLAAnalyticsAAR } from "./pages/SLAAnalyticsAAR"
import { Settings } from "./pages/Settings"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="sos" element={<CitizenSOS />} />
              <Route path="prediction" element={<AIPrediction />} />
              <Route path="resources" element={<ResourceAllocation />} />
              <Route path="shelters" element={<Shelters />} />
              <Route path="hospitals" element={<Hospitals />} />
              <Route path="priority" element={<PriorityRanking />} />
              <Route path="coordination" element={<Coordination />} />
              <Route path="routing" element={<RoutingRerouting />} />
              <Route path="proof-of-delivery" element={<ProofOfDelivery />} />
              <Route path="audit" element={<AuditLogs />} />
              <Route path="csr" element={<CSRTransparency />} />
              <Route path="analytics" element={<SLAAnalyticsAAR />} />
              <Route path="reports" element={<Reports />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
