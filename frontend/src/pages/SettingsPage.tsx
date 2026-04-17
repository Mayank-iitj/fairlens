import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { api } from '../lib/api'

type UserProfile = {
  id: string
  email: string
  name: string
  role: string
}

export function SettingsPage() {
  const navigate = useNavigate()
  const { data } = useQuery({
    queryKey: ['me'],
    queryFn: async () => (await api.get<UserProfile>('/users/me')).data,
  })

  const handleLogout = () => {
    localStorage.removeItem('fairlens_access_token')
    localStorage.removeItem('fairlens_refresh_token')
    navigate('/login')
  }

  return (
    <div className="space-y-4 rounded-2xl border border-caramel20 bg-white p-6 shadow-card">
      <h1 className="text-3xl font-display text-espresso">Settings</h1>
      <p className="text-muted">Account and security settings for your FairLens workspace.</p>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border border-caramel20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">User ID</p>
          <p className="mt-1 text-sm text-espresso">{data?.id ?? '-'}</p>
        </div>
        <div className="rounded-xl border border-caramel20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">Role</p>
          <p className="mt-1 text-sm text-espresso">{data?.role ?? '-'}</p>
        </div>
        <div className="rounded-xl border border-caramel20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">Name</p>
          <p className="mt-1 text-sm text-espresso">{data?.name ?? '-'}</p>
        </div>
        <div className="rounded-xl border border-caramel20 p-4">
          <p className="text-xs uppercase tracking-wide text-muted">Email</p>
          <p className="mt-1 text-sm text-espresso">{data?.email ?? '-'}</p>
        </div>
      </div>

      <button onClick={handleLogout} className="rounded-full border border-red-200 px-4 py-2 font-semibold text-red-700 hover:bg-red-50">
        Sign Out
      </button>
    </div>
  )
}
