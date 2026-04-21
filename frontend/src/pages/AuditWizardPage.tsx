import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '../lib/api'
import type { DatasetRecord } from '../types'

const steps = ['Upload', 'Configure', 'Thresholds', 'Review']

export function AuditWizardPage() {
  const [step, setStep] = useState(0)
  const [datasetId, setDatasetId] = useState('')
  const [datasetName, setDatasetName] = useState('')
  const [datasetFile, setDatasetFile] = useState<File | null>(null)
  const [target, setTarget] = useState('approved')
  const [predictionColumn, setPredictionColumn] = useState('prediction')
  const [sensitiveInput, setSensitiveInput] = useState('gender,race')
  const [disparateImpact, setDisparateImpact] = useState(0.8)
  const [demographicParityDiff, setDemographicParityDiff] = useState(0.1)
  const [equalizedOddsDiff, setEqualizedOddsDiff] = useState(0.1)
  const [predictiveParityDiff, setPredictiveParityDiff] = useState(0.05)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => (await api.get<DatasetRecord[]>('/datasets')).data,
  })

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!datasetFile) {
        throw new Error('Select a dataset file before uploading.')
      }

      const formData = new FormData()
      formData.append('file', datasetFile)
      formData.append('name', datasetName.trim() || datasetFile.name)

      const { data } = await api.post<{ dataset_id: string }>('/datasets/upload', formData, {
      })
      return data
    },
    onSuccess: (data) => {
      setDatasetId(data.dataset_id)
      setErrorMessage(null)
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
    onError: () => setErrorMessage('Dataset upload failed. Verify file format and try again.'),
  })

  const mutation = useMutation({
    mutationFn: async () => {
      if (!datasetId.trim()) {
        throw new Error('Please choose or upload a dataset.')
      }

      const config_json = {
        target,
        y_pred_col: predictionColumn,
        sensitive_attributes: sensitiveInput
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
        thresholds: {
          disparate_impact: disparateImpact,
          demographic_parity_diff: demographicParityDiff,
          equalized_odds_diff: equalizedOddsDiff,
          predictive_parity_diff: predictiveParityDiff,
        },
      }
      const { data } = await api.post('/audits', { dataset_id: datasetId, config_json })
      return data
    },
    onError: (error) => {
      const message = error instanceof Error ? error.message : 'Unable to run audit with current configuration.'
      setErrorMessage(message)
    },
    onSuccess: (data) => navigate(`/audit/${data.audit_id}`),
  })

  const canGoNext = () => {
    if (step === 0) {
      return Boolean(datasetId.trim())
    }
    if (step === 1) {
      return Boolean(target.trim() && predictionColumn.trim() && sensitiveInput.trim())
    }
    return true
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3">
        {steps.map((label, index) => (
          <button key={label} onClick={() => setStep(index)} className={`rounded-full px-4 py-2 text-sm font-semibold ${step === index ? 'bg-caramel text-white' : step > index ? 'bg-caramel10 text-espresso' : 'bg-white text-muted'} border border-caramel20`}>
            {label}
          </button>
        ))}
      </div>

      <section className="rounded-2xl border border-caramel20 bg-white p-6 shadow-card">
        {step === 0 && (
          <div className="space-y-3">
            <h2 className="text-2xl font-display text-espresso">Upload Dataset</h2>
            <p>Select an existing dataset or upload a new CSV/JSON/XLSX file.</p>
            <label className="block text-sm font-semibold text-espresso">Existing dataset</label>
            <select value={datasetId} onChange={(e) => setDatasetId(e.target.value)} className="w-full rounded-xl border border-caramel20 px-4 py-3">
              <option value="">Choose dataset</option>
              {(datasets ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.row_count} rows)
                </option>
              ))}
            </select>

            <div className="rounded-xl border border-caramel20 p-4">
              <p className="mb-2 text-sm font-semibold text-espresso">Upload new dataset</p>
              <input value={datasetName} onChange={(e) => setDatasetName(e.target.value)} placeholder="Dataset display name" className="mb-3 w-full rounded-xl border border-caramel20 px-4 py-3" />
              <input
                type="file"
                accept=".csv,.json,.xlsx"
                onChange={(e) => setDatasetFile(e.target.files?.[0] ?? null)}
                className="mb-3 w-full rounded-xl border border-caramel20 px-4 py-3"
              />
              <button
                onClick={() => uploadMutation.mutate()}
                disabled={!datasetFile || uploadMutation.isPending}
                className="rounded-full bg-caramel px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
              >
                {uploadMutation.isPending ? 'Uploading...' : 'Upload Dataset'}
              </button>
            </div>

            <div className="rounded-xl border border-caramel20 bg-caramel10 p-4">
              <p className="mb-2 text-sm font-semibold text-espresso">Real-time audit workflow</p>
              <p className="text-sm text-muted">Upload a real dataset, configure the target and prediction columns, then run the audit directly against production metrics and Groq-generated summaries.</p>
            </div>
          </div>
        )}
        {step === 1 && (
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-semibold text-espresso">Target column</label>
              <input value={target} onChange={(e) => setTarget(e.target.value)} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold text-espresso">Prediction column</label>
              <input value={predictionColumn} onChange={(e) => setPredictionColumn(e.target.value)} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
            </div>
            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-semibold text-espresso">Sensitive attributes (comma separated)</label>
              <input value={sensitiveInput} onChange={(e) => setSensitiveInput(e.target.value)} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
            </div>
          </div>
        )}
        {step === 2 && (
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-semibold text-espresso">Disparate impact threshold</label>
              <input type="number" step="0.01" value={disparateImpact} onChange={(e) => setDisparateImpact(Number(e.target.value))} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold text-espresso">Demographic parity diff threshold</label>
              <input type="number" step="0.01" value={demographicParityDiff} onChange={(e) => setDemographicParityDiff(Number(e.target.value))} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold text-espresso">Equalized odds diff threshold</label>
              <input type="number" step="0.01" value={equalizedOddsDiff} onChange={(e) => setEqualizedOddsDiff(Number(e.target.value))} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold text-espresso">Predictive parity diff threshold</label>
              <input type="number" step="0.01" value={predictiveParityDiff} onChange={(e) => setPredictiveParityDiff(Number(e.target.value))} className="w-full rounded-xl border border-caramel20 px-4 py-3" />
            </div>
          </div>
        )}
        {step === 3 && (
          <div className="space-y-2 text-sm text-muted">
            <p><span className="font-semibold text-espresso">Dataset:</span> {datasetId}</p>
            <p><span className="font-semibold text-espresso">Target:</span> {target}</p>
            <p><span className="font-semibold text-espresso">Prediction:</span> {predictionColumn}</p>
            <p><span className="font-semibold text-espresso">Sensitive attributes:</span> {sensitiveInput}</p>
            <p><span className="font-semibold text-espresso">Thresholds:</span> DI {disparateImpact}, DPD {demographicParityDiff}, EOD {equalizedOddsDiff}, PPD {predictiveParityDiff}</p>
          </div>
        )}
        {errorMessage && <p className="mt-3 text-sm text-red-600">{errorMessage}</p>}
        <div className="mt-6 flex justify-between">
          <button disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))} className="rounded-full border border-caramel20 px-4 py-2 font-semibold text-espresso hover:bg-caramel10">Back</button>
          {step < 3 ? (
            <button disabled={!canGoNext()} onClick={() => setStep((s) => Math.min(3, s + 1))} className="rounded-full bg-caramel px-5 py-2 font-semibold text-white hover:bg-walnut disabled:opacity-60">Next</button>
          ) : (
            <button onClick={() => mutation.mutate()} className="rounded-full bg-caramel px-5 py-2 font-semibold text-white hover:bg-walnut">
              {mutation.isPending ? 'Running...' : 'Run Audit'}
            </button>
          )}
        </div>
      </section>
    </div>
  )
}
