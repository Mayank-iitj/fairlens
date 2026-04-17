import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { api } from '../lib/api'
import type { AuditRecord, MonitorRecord } from '../types'

export function MonitorPage() {
  const [auditId, setAuditId] = useState('')
  const [scheduleCron, setScheduleCron] = useState('0 2 * * *')
  const [channel, setChannel] = useState('email')
  const [thresholdDrop, setThresholdDrop] = useState(5)
  const queryClient = useQueryClient()

  const { data: audits } = useQuery({
    queryKey: ['monitor-audits'],
    queryFn: async () => (await api.get<AuditRecord[]>('/audits')).data,
  })

  const { data: monitors } = useQuery({
    queryKey: ['monitors'],
    queryFn: async () => (await api.get<MonitorRecord[]>('/monitors')).data,
  })

  const createMonitor = useMutation({
    mutationFn: async () =>
      api.post('/monitors', {
        audit_id: auditId,
        schedule_cron: scheduleCron,
        alert_config: {
          channel,
          threshold_drop: thresholdDrop,
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitors'] })
      setAuditId('')
    },
  })

  const deleteMonitor = useMutation({
    mutationFn: async (id: string) => api.delete(`/monitors/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['monitors'] }),
  })

  return (
    <div className="space-y-6 rounded-2xl border border-caramel20 bg-white p-6 shadow-card">
      <div>
        <h1 className="text-3xl font-display text-espresso">Continuous Monitoring</h1>
        <p className="text-muted">Create recurring checks for completed audits and configure alert channels.</p>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-semibold text-espresso">Audit</label>
          <select value={auditId} onChange={(e) => setAuditId(e.target.value)} className="w-full rounded-xl border border-caramel20 px-4 py-3">
            <option value="">Select audit</option>
            {(audits ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.id.slice(0, 8)} ({item.status})
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-semibold text-espresso">Cron schedule</label>
          <input value={scheduleCron} onChange={(e) => setScheduleCron(e.target.value)} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
        </div>
        <div>
          <label className="mb-1 block text-sm font-semibold text-espresso">Alert channel</label>
          <select value={channel} onChange={(e) => setChannel(e.target.value)} className="w-full rounded-xl border border-caramel20 px-4 py-3">
            <option value="email">Email</option>
            <option value="slack">Slack</option>
            <option value="webhook">Webhook</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-semibold text-espresso">Alert drop threshold (points)</label>
          <input type="number" value={thresholdDrop} onChange={(e) => setThresholdDrop(Number(e.target.value))} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
        </div>
      </div>

      <button
        onClick={() => createMonitor.mutate()}
        disabled={!auditId || createMonitor.isPending}
        className="w-fit rounded-full bg-caramel px-5 py-2 font-semibold text-white hover:bg-walnut disabled:opacity-60"
      >
        {createMonitor.isPending ? 'Creating...' : 'Create Monitor'}
      </button>

      <div className="overflow-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="text-espresso">
              <th className="pb-2">Monitor</th>
              <th className="pb-2">Audit</th>
              <th className="pb-2">Schedule</th>
              <th className="pb-2">Channel</th>
              <th className="pb-2">Next Run</th>
              <th className="pb-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(monitors ?? []).map((item) => (
              <tr key={item.id} className="border-t border-caramel20 odd:bg-cream">
                <td className="py-2">{item.id.slice(0, 8)}</td>
                <td className="py-2">{item.audit_id.slice(0, 8)}</td>
                <td className="py-2">{item.schedule_cron}</td>
                <td className="py-2">{item.alert_config?.channel ?? '-'}</td>
                <td className="py-2">{item.next_run ? new Date(item.next_run).toLocaleString() : '-'}</td>
                <td className="py-2">
                  <button onClick={() => deleteMonitor.mutate(item.id)} className="rounded-full border border-red-200 px-3 py-1 text-xs font-semibold text-red-700 hover:bg-red-50">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
