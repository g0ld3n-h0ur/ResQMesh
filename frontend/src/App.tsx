import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Layout } from "./components/Layout"
import { ErrorBoundary } from "./components/ErrorBoundary"
import { Dashboard } from "./pages/Dashboard"
import { AIPrediction } from "./pages/AIPrediction"
import { ResourceAllocation } from "./pages/ResourceAllocation"
import { Shelters } from "./pages/Shelters"
import { Hospitals } from "./pages/Hospitals"
import { Reports } from "./pages/Reports"
import { PriorityRanking } from "./pages/PriorityRanking"
import { Coordination } from "./pages/Coordination"
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
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="prediction" element={<AIPrediction />} />
              <Route path="resources" element={<ResourceAllocation />} />
              <Route path="shelters" element={<Shelters />} />
              <Route path="hospitals" element={<Hospitals />} />
              <Route path="reports" element={<Reports />} />
              <Route path="priority" element={<PriorityRanking />} />
              <Route path="coordination" element={<Coordination />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App

