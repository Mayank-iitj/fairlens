import { useState } from 'react'

import { useQuery } from '@tanstack/react-query'

import { api } from '../lib/api'
import type { AuditRecord } from '../types'

export function ReportsPage() {
  const [activeSummary, setActiveSummary] = useState<string>('')

  const { data } = useQuery({
    queryKey: ['reports-audits'],
    queryFn: async () => (await api.get<AuditRecord[]>('/audits')).data,
  })

  const downloadPdf = async (auditId: string) => {
    const response = await api.get(`/audits/${auditId}/report/pdf`, { responseType: 'blob' })
    const blobUrl = URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = `fairlens-report-${auditId}.pdf`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(blobUrl)
  }

  const loadSummary = async (auditId: string) => {
    const { data } = await api.get<{ summary: string }>(`/audits/${auditId}/report`)
    setActiveSummary(data.summary)
  }

  return (
    <div className="rounded-2xl border border-caramel20 bg-white p-6 shadow-card">
      <h1 className="text-3xl font-display text-espresso">Reports</h1>
      <p className="mt-2 text-muted">Compliance-ready exports for every audit.</p>
      <div className="mt-6 overflow-auto">
        <table className="w-full min-w-[500px] text-left text-sm">
          <thead>
            <tr className="text-espresso">
              <th className="pb-2">Audit</th>
              <th className="pb-2">Status</th>
              <th className="pb-2">Score</th>
              <th className="pb-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((row) => (
              <tr key={row.id} className="border-t border-caramel20 odd:bg-cream">
                <td className="py-2">{row.id.slice(0, 10)}</td>
                <td className="py-2">{row.status}</td>
                <td className="py-2">{row.score ?? '-'}</td>
                <td className="py-2">
                  <div className="flex gap-2">
                    <button onClick={() => loadSummary(row.id)} className="rounded-full border border-caramel20 px-3 py-1 text-xs font-semibold text-espresso hover:bg-caramel10">
                      Summary
                    </button>
                    <button onClick={() => downloadPdf(row.id)} className="rounded-full bg-caramel px-3 py-1 text-xs font-semibold text-white hover:bg-walnut">
                    PDF
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {activeSummary && (
        <div className="mt-6 rounded-xl bg-caramel10 p-4 text-sm text-espresso">
          <p className="font-semibold">Summary</p>
          <p className="mt-2">{activeSummary}</p>
        </div>
      )}
    </div>
  )
}
