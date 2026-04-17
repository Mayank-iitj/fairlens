export type Severity = 'Passed' | 'Warning' | 'Flagged'

export type AuditMetric = {
  metric_name: string
  group_name: string
  value: number
  threshold: number
  passed: boolean
}

export type AuditRecord = {
  id: string
  dataset_id: string
  status: string
  score: number | null
  created_at: string
}

export type AuditDetail = {
  id: string
  dataset_id: string
  status: string
  score: number | null
  created_at: string
  config: {
    target?: string
    y_pred_col?: string
    sensitive_attributes?: string[]
    thresholds?: Record<string, number>
  }
  results: AuditMetric[]
}

export type DatasetRecord = {
  id: string
  name: string
  row_count: number
  created_at: string
}

export type MonitorRecord = {
  id: string
  audit_id: string
  schedule_cron: string
  alert_config: {
    channel?: string
    threshold_drop?: number
  }
  last_run: string | null
  next_run: string | null
}

export type RemediationPreview = {
  audit_id: string
  strategy: string
  score_preview: number | null
  flagged_metrics: string[]
  recommendation_summary: string
  metrics: AuditMetric[]
}
