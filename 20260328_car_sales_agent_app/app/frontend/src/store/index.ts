import { create } from 'zustand'
import type { Customer, CustomerInsight, RecommendationResponse, ChatMessage } from '../types'

interface AppState {
  // Customer state
  selectedCustomer: Customer | null
  customerInsight: CustomerInsight | null
  recommendations: RecommendationResponse | null

  // Chat state
  chatMessages: ChatMessage[]
  chatSessionId: string
  isChatOpen: boolean

  // Loading states
  isLoadingCustomer: boolean
  isLoadingInsight: boolean
  isLoadingRecommendations: boolean
  isLoadingChat: boolean

  // Actions
  setSelectedCustomer: (customer: Customer | null) => void
  setCustomerInsight: (insight: CustomerInsight | null) => void
  setRecommendations: (recommendations: RecommendationResponse | null) => void
  addChatMessage: (message: ChatMessage) => void
  clearChat: () => void
  setChatSessionId: (sessionId: string) => void
  toggleChat: () => void
  setIsChatOpen: (isOpen: boolean) => void
  setIsLoadingCustomer: (loading: boolean) => void
  setIsLoadingInsight: (loading: boolean) => void
  setIsLoadingRecommendations: (loading: boolean) => void
  setIsLoadingChat: (loading: boolean) => void
  resetCustomerState: () => void
}

const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  selectedCustomer: null,
  customerInsight: null,
  recommendations: null,
  chatMessages: [],
  chatSessionId: generateSessionId(),
  isChatOpen: true,
  isLoadingCustomer: false,
  isLoadingInsight: false,
  isLoadingRecommendations: false,
  isLoadingChat: false,

  // Actions
  setSelectedCustomer: (customer) => set({ selectedCustomer: customer }),
  setCustomerInsight: (insight) => set({ customerInsight: insight }),
  setRecommendations: (recommendations) => set({ recommendations }),
  addChatMessage: (message) =>
    set((state) => ({ chatMessages: [...state.chatMessages, message] })),
  clearChat: () =>
    set({ chatMessages: [], chatSessionId: generateSessionId() }),
  setChatSessionId: (sessionId) => set({ chatSessionId: sessionId }),
  toggleChat: () => set((state) => ({ isChatOpen: !state.isChatOpen })),
  setIsChatOpen: (isOpen) => set({ isChatOpen: isOpen }),
  setIsLoadingCustomer: (loading) => set({ isLoadingCustomer: loading }),
  setIsLoadingInsight: (loading) => set({ isLoadingInsight: loading }),
  setIsLoadingRecommendations: (loading) =>
    set({ isLoadingRecommendations: loading }),
  setIsLoadingChat: (loading) => set({ isLoadingChat: loading }),
  resetCustomerState: () =>
    set({
      selectedCustomer: null,
      customerInsight: null,
      recommendations: null,
      chatMessages: [],
      chatSessionId: generateSessionId(),
    }),
}))
