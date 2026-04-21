import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { AlertCircle, CheckCircle, XCircle, AlertTriangle, Loader2, Copy, Check } from 'lucide-react'

import { api } from '../lib/api'
import type { LLMBiasAnalysisResponse, BiasDetectionResult } from '../types'

export function LLMBiasDetectionPage() {
  const [textInput, setTextInput] = useState('')
  const [copied, setCopied] = useState(false)

  // Fetch history
  const { data: history, refetch: refetchHistory } = useQuery({
    queryKey: ['llm-bias-history'],
    queryFn: async () => (await api.get('/llm-bias/history')).data,
    enabled: true,
  })

  // Analyze mutation
  const analyzeMutation = useMutation({
    mutationFn: async (text: string) => {
      const response = await api.post('/llm-bias/analyze', { text })
      return response.data as LLMBiasAnalysisResponse
    },
    onSuccess: () => {
      setTextInput('')
      refetchHistory()
    },
  })

  const handleAnalyze = () => {
    if (textInput.trim().length < 10) {
      alert('Please enter at least 10 characters of text')
      return
    }
    analyzeMutation.mutate(textInput)
  }

  const severityConfig = {
    low: { bg: 'bg-green-50', text: 'text-green-700', icon: CheckCircle, label: 'Low Risk' },
    medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', icon: AlertTriangle, label: 'Medium Risk' },
    high: { bg: 'bg-orange-50', text: 'text-orange-700', icon: AlertCircle, label: 'High Risk' },
    critical: { bg: 'bg-red-50', text: 'text-red-700', icon: XCircle, label: 'Critical Risk' },
  }

  const getSeverityBadge = (severity: string) => {
    const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.low
    const Icon = config.icon
    return (
      <div className={`flex items-center gap-2 rounded-full px-3 py-1 ${config.bg} ${config.text}`}>
        <Icon size={16} />
        <span className="text-sm font-semibold">{config.label}</span>
      </div>
    )
  }

  const getBiasLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      very_low: 'from-green-400 to-green-600',
      low: 'from-lime-400 to-lime-600',
      moderate: 'from-yellow-400 to-yellow-600',
      high: 'from-orange-400 to-orange-600',
      critical: 'from-red-400 to-red-600',
    }
    return colors[level] || colors.moderate
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold text-espresso">LLM Bias Detection</h1>
        <p className="text-lg text-muted">
          Analyze Large Language Model outputs for bias, toxicity, stereotyping, and fairness issues
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Input Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Analysis Input */}
          <div className="rounded-lg border border-caramel20 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-xl font-semibold text-espresso">Analyze LLM Output</h2>
            <div className="space-y-4">
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Paste the LLM output text here to analyze for bias..."
                className="h-48 w-full rounded-lg border border-caramel20 bg-cream p-4 text-espresso placeholder-muted focus:border-caramel focus:outline-none"
              />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">{textInput.length} characters</span>
                <button
                  onClick={handleAnalyze}
                  disabled={analyzeMutation.isPending || textInput.length < 10}
                  className="flex items-center gap-2 rounded-lg bg-caramel px-6 py-2 font-semibold text-white transition hover:bg-caramel-dark disabled:opacity-50"
                >
                  {analyzeMutation.isPending && <Loader2 size={16} className="animate-spin" />}
                  Analyze
                </button>
              </div>
            </div>
          </div>

          {/* Current Analysis Results */}
          {analyzeMutation.data && (
            <div className="rounded-lg border border-caramel20 bg-white p-6 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-espresso">Analysis Results</h3>

              {/* Overall Score */}
              <div className={`mb-6 rounded-lg bg-gradient-to-r ${getBiasLevelColor(analyzeMutation.data.bias_level)} p-6 text-white`}>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-sm font-medium opacity-90">Overall Bias Score</p>
                    <p className="text-4xl font-bold">{(analyzeMutation.data.overall_bias_score * 100).toFixed(1)}%</p>
                    <p className="mt-2 text-sm opacity-90">Risk Level: {analyzeMutation.data.bias_level.toUpperCase()}</p>
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div className="mb-6 rounded-lg bg-cream p-4">
                <p className="text-sm font-medium text-espresso">{analyzeMutation.data.summary}</p>
              </div>

              {/* Detected Biases */}
              <div className="mb-6">
                <h4 className="mb-3 font-semibold text-espresso">Detected Biases</h4>
                <div className="space-y-3">
                  {analyzeMutation.data.detected_biases.map((bias, idx) => (
                    <div key={idx} className="rounded-lg border border-caramel10 bg-cream p-4">
                      <div className="mb-2 flex items-start justify-between">
                        <div>
                          <p className="font-medium text-espresso">{bias.category}</p>
                          <p className="text-sm text-muted">{bias.algorithm}</p>
                        </div>
                        {getSeverityBadge(bias.severity)}
                      </div>
                      <div className="mb-3 w-full rounded-full bg-white h-2">
                        <div
                          className="h-full rounded-full bg-caramel transition-all"
                          style={{ width: `${bias.score * 100}%` }}
                        />
                      </div>
                      <p className="text-sm text-muted">{bias.description}</p>
                      {bias.evidence.length > 0 && (
                        <div className="mt-2 space-y-1">
                          <p className="text-xs font-medium text-espresso">Evidence:</p>
                          {bias.evidence.slice(0, 3).map((e, i) => (
                            <p key={i} className="text-xs text-muted">• {e}</p>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Risks */}
              {analyzeMutation.data.risks.length > 0 && (
                <div className="mb-6">
                  <h4 className="mb-3 font-semibold text-espresso">Identified Risks</h4>
                  <div className="space-y-2">
                    {analyzeMutation.data.risks.map((risk, idx) => (
                      <div key={idx} className="flex gap-2 text-sm text-muted">
                        <AlertCircle size={16} className="flex-shrink-0 text-orange-500" />
                        <span>{risk}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              <div>
                <h4 className="mb-3 font-semibold text-espresso">Recommendations</h4>
                <div className="space-y-2">
                  {analyzeMutation.data.recommendations.map((rec, idx) => (
                    <div key={idx} className="flex gap-2 text-sm text-muted">
                      <CheckCircle size={16} className="flex-shrink-0 text-green-500" />
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Error State */}
          {analyzeMutation.isError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
              <p className="font-semibold">Analysis Failed</p>
              <p className="text-sm">{analyzeMutation.error?.message || 'An error occurred during analysis'}</p>
            </div>
          )}
        </div>

        {/* History Sidebar */}
        <div className="space-y-4">
          <div className="rounded-lg border border-caramel20 bg-white p-6 shadow-sm">
            <h3 className="mb-4 font-semibold text-espresso">Recent Analyses</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {(history?.items || []).length > 0 ? (
                history.items.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => copyToClipboard(item.text_input)}
                    className="w-full text-left rounded-lg border border-caramel10 p-3 transition hover:bg-cream"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-espresso">{item.text_input}</p>
                        <p className="text-xs text-muted">
                          {new Date(item.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div
                        className={`flex-shrink-0 rounded-full px-2 py-1 text-xs font-semibold ${
                          {
                            very_low: 'bg-green-100 text-green-700',
                            low: 'bg-lime-100 text-lime-700',
                            moderate: 'bg-yellow-100 text-yellow-700',
                            high: 'bg-orange-100 text-orange-700',
                            critical: 'bg-red-100 text-red-700',
                          }[item.bias_level as keyof typeof { very_low: '' }]
                        }`}
                      >
                        {(item.overall_bias_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  </button>
                ))
              ) : (
                <p className="text-center text-sm text-muted">No analyses yet</p>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="rounded-lg border border-caramel20 bg-white p-6 shadow-sm">
            <h3 className="mb-4 font-semibold text-espresso">Statistics</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted">Total Analyses</span>
                <span className="font-semibold text-espresso">{history?.total || 0}</span>
              </div>
              <div className="h-px bg-caramel10" />
              <div className="text-xs text-muted">
                <p>Bias Detection is powered by advanced ML algorithms including:</p>
                <ul className="mt-2 space-y-1 list-disc list-inside">
                  <li>Gender Bias Detection</li>
                  <li>Toxicity Analysis</li>
                  <li>Stereotype Detection</li>
                  <li>Sentiment Bias Analysis</li>
                  <li>Representation Fairness</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
