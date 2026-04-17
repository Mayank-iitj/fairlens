import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { BiasGauge } from '../components/BiasGauge'
import { api } from '../lib/api'
import type { AuditDetail, AuditMetric, RemediationPreview } from '../types'

const tabs = ['Overview', 'Dataset Analysis', 'Fairness Metrics', 'Explainability', 'Intersectionality', 'Remediation'] as const

export function AuditResultsPage() {
  const { id = '' } = useParams()
  const [tab, setTab] = useState<(typeof tabs)[number]>('Overview')
  const [strategy, setStrategy] = useState('reweighing')

  const { data } = useQuery({
    queryKey: ['audit', id],
    queryFn: async () => (await api.get<AuditDetail>(`/audits/${id}`)).data,
    enabled: Boolean(id),
  })

  const { data: report } = useQuery({
    queryKey: ['audit-report', id],
    queryFn: async () => (await api.get<{ summary: string }>(`/audits/${id}/report`)).data,
    enabled: Boolean(id),
  })

  const { data: remediation, refetch: runRemediation, isFetching: isRunningRemediation } = useQuery({
    queryKey: ['audit-remediation', id, strategy],
    queryFn: async () => (await api.post<RemediationPreview>(`/audits/${id}/remediate`, null, { params: { strategy } })).data,
    enabled: false,
  })

  const metrics: AuditMetric[] = data?.results ?? []
  const chart = metrics.map((m) => ({ metric: m.metric_name, value: m.value, threshold: m.threshold }))
  const failedMetrics = metrics.filter((item) => !item.passed)

  const groupSummary = Object.values(
    metrics.reduce<Record<string, { group: string; count: number; failed: number }>>((acc, metric) => {
      if (!acc[metric.group_name]) {
        acc[metric.group_name] = { group: metric.group_name, count: 0, failed: 0 }
      }
      acc[metric.group_name].count += 1
      if (!metric.passed) {
        acc[metric.group_name].failed += 1
      }
      return acc
    }, {})
  )

  const intersectionalMetrics = metrics.filter((metric) => metric.group_name.includes('&') || metric.group_name.includes('|'))
  const intersectionalGroupSummary = Object.values(
    intersectionalMetrics.reduce<Record<string, { group: string; count: number; failed: number }>>((acc, metric) => {
      if (!acc[metric.group_name]) {
        acc[metric.group_name] = { group: metric.group_name, count: 0, failed: 0 }
      }
      acc[metric.group_name].count += 1
      if (!metric.passed) {
        acc[metric.group_name].failed += 1
      }
      return acc
    }, {})
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {tabs.map((item) => (
          <button key={item} onClick={() => setTab(item)} className={`rounded-full px-4 py-2 text-sm font-semibold ${tab === item ? 'bg-caramel text-white' : 'bg-white text-espresso hover:bg-caramel10'} border border-caramel20`}>
            {item}
          </button>
        ))}
      </div>

      <section className="rounded-2xl border border-caramel20 bg-white p-6 shadow-card">
        {tab === 'Overview' && (
          <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
            <div className="grid place-items-center"><BiasGauge score={data?.score ?? 0} /></div>
            <div className="space-y-4">
              <h2 className="text-2xl font-display text-espresso">Audit Verdict</h2>
              <p className="rounded-xl bg-caramel10 p-4 text-espresso">{(data?.score ?? 0) < 75 ? 'Your model shows statistically significant bias in one or more fairness metrics.' : 'No critical bias detected under the configured thresholds.'}</p>
              <div className="grid gap-3 md:grid-cols-3">
                {metrics.slice(0, 3).map((metric) => (
                  <article key={metric.metric_name} className={`rounded-xl border-l-[3px] p-3 ${metric.passed ? 'border-caramel bg-cream' : 'border-red-500 bg-red-50'}`}>
                    <p className="text-xs uppercase tracking-wide text-muted">{metric.metric_name}</p>
                    <p className="text-2xl font-display text-espresso">{metric.value}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === 'Fairness Metrics' && (
          <div>
            <h2 className="text-2xl font-display text-espresso">Metric Comparison</h2>
            <div className="mt-4 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chart}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#C48A52" />
                  <Bar dataKey="threshold" fill="#875C3C" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {tab === 'Dataset Analysis' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-display text-espresso">Dataset and Config</h2>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-caramel20 p-4">
                <p className="text-xs uppercase tracking-wide text-muted">Dataset ID</p>
                <p className="mt-1 text-sm text-espresso">{data?.dataset_id}</p>
              </div>
              <div className="rounded-xl border border-caramel20 p-4">
                <p className="text-xs uppercase tracking-wide text-muted">Created</p>
                <p className="mt-1 text-sm text-espresso">{data?.created_at ? new Date(data.created_at).toLocaleString() : '-'}</p>
              </div>
              <div className="rounded-xl border border-caramel20 p-4">
                <p className="text-xs uppercase tracking-wide text-muted">Target Column</p>
                <p className="mt-1 text-sm text-espresso">{data?.config?.target ?? '-'}</p>
              </div>
              <div className="rounded-xl border border-caramel20 p-4">
                <p className="text-xs uppercase tracking-wide text-muted">Prediction Column</p>
                <p className="mt-1 text-sm text-espresso">{data?.config?.y_pred_col ?? '-'}</p>
              </div>
            </div>

            <div className="rounded-xl border border-caramel20 p-4">
              <p className="text-xs uppercase tracking-wide text-muted">Sensitive Attributes</p>
              <p className="mt-1 text-sm text-espresso">{(data?.config?.sensitive_attributes ?? []).join(', ') || '-'}</p>
            </div>
          </div>
        )}

        {tab === 'Explainability' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-display text-espresso">Explainability Summary</h2>
            <p className="rounded-xl bg-caramel10 p-4 text-espresso">{report?.summary ?? 'Summary not available yet.'}</p>
            <div className="rounded-xl border border-caramel20 p-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-muted">Most impacted metrics</p>
              <ul className="space-y-2 text-sm text-espresso">
                {(failedMetrics.length ? failedMetrics : metrics)
                  .slice(0, 6)
                  .map((metric) => (
                    <li key={`${metric.metric_name}-${metric.group_name}`} className="rounded-lg bg-cream px-3 py-2">
                      {metric.metric_name} ({metric.group_name}) - value {metric.value.toFixed(4)} vs threshold {metric.threshold.toFixed(4)}
                    </li>
                  ))}
              </ul>
            </div>
          </div>
        )}

        {tab === 'Intersectionality' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-display text-espresso">Group Risk Breakdown</h2>
            <div className="overflow-auto">
              <table className="w-full min-w-[520px] text-left text-sm">
                <thead>
                  <tr className="text-espresso">
                    <th className="pb-2">Group</th>
                    <th className="pb-2">Metrics Checked</th>
                    <th className="pb-2">Failed</th>
                    <th className="pb-2">Pass Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {(intersectionalGroupSummary.length ? intersectionalGroupSummary : groupSummary).map((item) => {
                    const passRate = item.count ? Math.round(((item.count - item.failed) / item.count) * 100) : 0
                    return (
                      <tr key={item.group} className="border-t border-caramel20 odd:bg-cream">
                        <td className="py-2">{item.group}</td>
                        <td className="py-2">{item.count}</td>
                        <td className="py-2">{item.failed}</td>
                        <td className="py-2">{passRate}%</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === 'Remediation' && (
          <div className="space-y-4">
            <h2 className="text-2xl font-display text-espresso">Remediation Preview</h2>
            <div className="flex flex-wrap items-end gap-3">
              <div>
                <label className="mb-1 block text-sm font-semibold text-espresso">Strategy</label>
                <select value={strategy} onChange={(e) => setStrategy(e.target.value)} className="rounded-xl border border-caramel20 px-4 py-2">
                  <option value="reweighing">Reweighing</option>
                  <option value="threshold_optimization">Threshold optimization</option>
                  <option value="post_processing">Post-processing</option>
                </select>
              </div>
              <button onClick={() => runRemediation()} className="rounded-full bg-caramel px-5 py-2 font-semibold text-white hover:bg-walnut">
                {isRunningRemediation ? 'Running...' : 'Run Preview'}
              </button>
            </div>

            {remediation && (
              <div className="space-y-3 rounded-xl border border-caramel20 p-4">
                <p className="text-sm text-espresso"><span className="font-semibold">Score preview:</span> {remediation.score_preview ?? '-'}</p>
                <p className="text-sm text-espresso"><span className="font-semibold">Flagged metrics:</span> {remediation.flagged_metrics.join(', ') || 'None'}</p>
                <p className="text-sm text-muted">{remediation.recommendation_summary}</p>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  )
}
