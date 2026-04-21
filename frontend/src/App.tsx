import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from './components/AppLayout'
import { AuditResultsPage } from './pages/AuditResultsPage'
import { AuditWizardPage } from './pages/AuditWizardPage'
import { DashboardPage } from './pages/DashboardPage'
import { HomePage } from './pages/HomePage'
import { LLMBiasDetectionPage } from './pages/LLMBiasDetectionPage'
import { MonitorPage } from './pages/MonitorPage'
import { ReportsPage } from './pages/ReportsPage'
import { SettingsPage } from './pages/SettingsPage'

function App() {
  return (
    <Routes>
      <Route path="*" element={<Navigate to="/" replace />} />
      <Route element={<AppLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/audit/new" element={<AuditWizardPage />} />
        <Route path="/audit/:id" element={<AuditResultsPage />} />
        <Route path="/llm-bias" element={<LLMBiasDetectionPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/monitor" element={<MonitorPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}

export default App
