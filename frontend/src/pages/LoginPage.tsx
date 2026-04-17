import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api } from '../lib/api'

type GoogleCredentialResponse = {
  credential?: string
}

type GoogleIdAPI = {
  initialize: (config: { client_id: string; callback: (response: GoogleCredentialResponse) => void }) => void
  renderButton: (element: HTMLElement, options: { theme?: string; size?: string; width?: number; text?: string }) => void
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: GoogleIdAPI
      }
    }
  }
}

export function LoginPage() {
  const navigate = useNavigate()
  const googleButtonRef = useRef<HTMLDivElement | null>(null)
  const [googleError, setGoogleError] = useState<string | null>(null)

  const googleClientId = (import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined)?.trim()

  useEffect(() => {
    if (!googleClientId) {
      setGoogleError('Google auth is not configured. Set VITE_GOOGLE_CLIENT_ID.')
      return
    }

    const scriptId = 'google-identity-services'
    const existing = document.getElementById(scriptId) as HTMLScriptElement | null

    const initializeGoogle = () => {
      const buttonHost = googleButtonRef.current
      const google = window.google
      if (!buttonHost || !google) {
        setGoogleError('Google auth failed to initialize. Please refresh and try again.')
        return
      }

      buttonHost.innerHTML = ''
      google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response: GoogleCredentialResponse) => {
          const idToken = response.credential
          if (!idToken) {
            setGoogleError('Google sign-in did not return a token.')
            return
          }

          try {
            const { data } = await api.post('/auth/google', { id_token: idToken })
            localStorage.setItem('fairlens_access_token', data.access_token)
            localStorage.setItem('fairlens_refresh_token', data.refresh_token)
            navigate('/dashboard')
          } catch {
            setGoogleError('Google sign-in failed. Please try again.')
          }
        },
      })

      google.accounts.id.renderButton(buttonHost, {
        theme: 'outline',
        size: 'large',
        width: 360,
        text: 'continue_with',
      })
    }

    if (existing) {
      initializeGoogle()
      return
    }

    const script = document.createElement('script')
    script.id = scriptId
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.defer = true
    script.onload = initializeGoogle
    script.onerror = () => setGoogleError('Unable to load Google sign-in script.')
    document.head.appendChild(script)
  }, [googleClientId, navigate])


  return (
    <div className="grid min-h-screen place-items-center bg-cream px-4">
      <div className="w-full max-w-md space-y-4 rounded-2xl border border-caramel20 bg-white p-6 shadow-card">
        <h1 className="text-3xl font-display text-espresso">Welcome Back</h1>
        <p className="text-sm text-muted">Sign in with Google only.</p>
        <div ref={googleButtonRef} className="min-h-[44px]" />
        {googleError && <p className="text-sm text-red-600">{googleError}</p>}
      </div>
    </div>
  )
}
