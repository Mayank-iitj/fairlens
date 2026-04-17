import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts'

import { BiasGauge } from '../components/BiasGauge'
import { api } from '../lib/api'
import type { AuditRecord, DatasetRecord } from '../types'

export function DashboardPage() {
  const { data: audits } = useQuery({
    queryKey: ['audits'],
    queryFn: async () => (await api.get<AuditRecord[]>('/audits')).data,
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => (await api.get<DatasetRecord[]>('/datasets')).data,
  })

  const completedAudits = (audits ?? []).filter((item) => item.status === 'completed' && item.score !== null)
  const avgFairness = completedAudits.length
    ? Math.round(completedAudits.reduce((total, item) => total + (item.score ?? 0), 0) / completedAudits.length)
    : 0

  const activeAlerts = (audits ?? []).filter((item) => item.status === 'failed').length

  const trend = Object.values(
    (completedAudits ?? []).reduce<Record<string, { name: string; scoreSum: number; count: number }>>((acc, item) => {
      const d = new Date(item.created_at)
      const key = `${d.getFullYear()}-${d.getMonth()}`
      if (!acc[key]) {
        acc[key] = {
          name: d.toLocaleDateString(undefined, { month: 'short' }),
          scoreSum: 0,
          count: 0,
        }
      }
      acc[key].scoreSum += item.score ?? 0
      acc[key].count += 1
      return acc
    }, {})
  ).map((entry) => ({ name: entry.name, score: Math.round(entry.scoreSum / entry.count) }))

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        {[
          ['Total Audits', String(audits?.length ?? 0)],
          ['Avg Fairness', String(avgFairness)],
          ['Datasets', String(datasets?.length ?? 0)],
          ['Active Alerts', String(activeAlerts)],
        ].map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-caramel20 bg-white p-5 shadow-card">
            <p className="text-sm text-muted">{label}</p>
            <p className="mt-2 text-3xl font-display text-espresso">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <section className="rounded-2xl border border-caramel20 bg-white p-5 shadow-card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-display text-espresso">Recent Audits</h2>
            <div className="flex gap-2">
              <Link to="/audit/new" className="rounded-full bg-caramel px-4 py-2 text-sm font-semibold text-white hover:bg-walnut">New Audit</Link>
              <Link to="/reports" className="rounded-full border border-caramel20 px-4 py-2 text-sm font-semibold text-espresso hover:bg-caramel10">View Reports</Link>
            </div>
          </div>
          <div className="overflow-auto">
            <table className="w-full min-w-[520px] text-left text-sm">
              <thead>
                <tr className="text-espresso">
                  <th className="pb-2">Audit ID</th>
                  <th className="pb-2">Status</th>
                  <th className="pb-2">Score</th>
                  <th className="pb-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {(audits ?? []).map((row) => (
                  <tr key={row.id} className="border-t border-caramel20 odd:bg-cream">
                    <td className="py-2 text-xs">{row.id.slice(0, 8)}</td>
                    <td className="py-2">
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${row.status === 'completed' ? 'bg-teal-100 text-teal-900' : row.status === 'running' ? 'bg-caramel10 text-espresso' : 'bg-orange-100 text-orange-900'}`}>
                        {row.status}
                      </span>
                    </td>
                    <td className="py-2 font-semibold text-espresso">{row.score ?? '-'}</td>
                    <td className="py-2">{new Date(row.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="space-y-4">
          <div className="rounded-2xl border border-caramel20 bg-white p-5 shadow-card">
            <h3 className="text-lg font-display text-espresso">Live Fairness Pulse</h3>
            <div className="grid place-items-center py-3">
              <BiasGauge score={avgFairness} />
            </div>
          </div>
          <div className="rounded-2xl border border-caramel20 bg-white p-5 shadow-card">
            <h3 className="text-lg font-display text-espresso">Trend</h3>
            <div className="mt-3 h-32">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend}>
                  <XAxis dataKey="name" tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Area dataKey="score" type="monotone" stroke="#C48A52" fill="#C48A5233" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
