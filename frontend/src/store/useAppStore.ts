import { create } from 'zustand'

type AppState = {
  activeAuditId: string | null
  setActiveAuditId: (id: string | null) => void
}

export const useAppStore = create<AppState>((set) => ({
  activeAuditId: null,
  setActiveAuditId: (id) => set({ activeAuditId: id }),
}))
