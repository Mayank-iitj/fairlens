export function SettingsPage() {
  return (
    <div className="space-y-4 rounded-2xl border border-caramel20 bg-white p-6 shadow-card">
      <h1 className="text-3xl font-display text-espresso">Settings</h1>
      <p className="text-muted">Production workflow settings for the guest workspace.</p>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border border-caramel20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">Access Mode</p>
          <p className="mt-1 text-sm text-espresso">Guest / no login required</p>
        </div>
        <div className="rounded-xl border border-caramel20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">Workflow</p>
          <p className="mt-1 text-sm text-espresso">Audit, reports, monitors, remediation</p>
        </div>
        <div className="rounded-xl border border-caramel20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">Demo Mode</p>
          <p className="mt-1 text-sm text-espresso">Available via the Audit Wizard demo loader</p>
        </div>
        <div className="rounded-xl border border-caramel20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">OAuth</p>
          <p className="mt-1 text-sm text-espresso">Removed from the UI</p>
        </div>
      </div>

      <button onClick={() => (window.location.href = '/dashboard')} className="rounded-full border border-caramel20 px-4 py-2 font-semibold text-espresso hover:bg-caramel10">
        Back to Dashboard
      </button>
    </div>
  )
}
