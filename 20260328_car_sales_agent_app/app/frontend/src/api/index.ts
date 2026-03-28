import type {
  Customer,
  CustomerInsight,
  RecommendationResponse,
  TableInfo,
  EvaluationRecord,
  DashboardStats,
  APIResponse,
  ChatRequest,
} from '../types'

const API_BASE = '/api'

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(error.detail || error.error || 'API request failed')
  }

  const data: APIResponse<T> = await response.json()

  if (!data.success && data.error) {
    throw new Error(data.error)
  }

  return data.data as T
}

// Customer API
export const customerAPI = {
  list: (params?: { limit?: number; offset?: number; search?: string }) => {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    if (params?.search) query.set('search', params.search)
    const queryString = query.toString()
    return fetchAPI<Customer[]>(`/customers${queryString ? `?${queryString}` : ''}`)
  },

  get: (customerId: string) =>
    fetchAPI<Customer>(`/customers/${customerId}`),

  getInsights: (customerId: string) =>
    fetchAPI<CustomerInsight>(`/customers/${customerId}/insights`),

  getInteraction: (customerId: string) =>
    fetchAPI<{ transcript: string; interaction_date?: string; interaction_type?: string; key_quotes?: string[] }>(`/customers/${customerId}/interaction`),
}

// Recommendations API
export const recommendationAPI = {
  get: (customerId: string) =>
    fetchAPI<RecommendationResponse>(`/customers/${customerId}/recommendations`),

  regenerate: (customerId: string, feedback?: string) =>
    fetchAPI<RecommendationResponse>('/recommendations/regenerate', {
      method: 'POST',
      body: JSON.stringify({ customer_id: customerId, feedback }),
    }),
}

// Chat API
export const chatAPI = {
  send: async (request: ChatRequest) => {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    const data = await response.json()
    return data.response as string
  },

  sendStream: async function* (request: ChatRequest) {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') return
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) yield parsed.content
            if (parsed.error) throw new Error(parsed.error)
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  },

  getHistory: (sessionId: string) =>
    fetchAPI<Array<{ role: string; content: string }>>(`/chat/history/${sessionId}`),

  clearHistory: (sessionId: string) =>
    fetchAPI<{ message: string }>(`/chat/history/${sessionId}`, {
      method: 'DELETE',
    }),
}

// Admin API
// Note: Admin endpoints return flexible data structures for LLMOps monitoring
// Each component defines its own TypeScript interfaces matching the backend response
export const adminAPI = {
  getStats: () => fetchAPI<DashboardStats>('/admin/stats'),

  // Returns MLflow trace data with full request/response/spans structure
  listTraces: (params?: {
    limit?: number
    offset?: number
    request_type?: string
    status?: string
  }) => {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    if (params?.request_type) query.set('request_type', params.request_type)
    if (params?.status) query.set('status', params.status)
    const queryString = query.toString()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return fetchAPI<any[]>(`/admin/traces${queryString ? `?${queryString}` : ''}`)
  },

  getTrace: (traceId: string) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    fetchAPI<any>(`/admin/traces/${traceId}`),

  // Returns Serving Endpoint metrics with timeseries data
  getGatewayMetrics: () =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    fetchAPI<any>('/admin/gateway/metrics'),

  listTables: () =>
    fetchAPI<TableInfo[]>('/admin/catalog/tables'),

  previewTable: (tableName: string, limit?: number) => {
    const query = limit ? `?limit=${limit}` : ''
    return fetchAPI<Record<string, unknown>[]>(
      `/admin/catalog/tables/${tableName}/preview${query}`
    )
  },

  // Returns { summary, evaluations } with MLflow evaluation metrics
  listEvaluations: (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const queryString = query.toString()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return fetchAPI<any>(
      `/admin/evaluations${queryString ? `?${queryString}` : ''}`
    )
  },

  createEvaluation: (evaluation: {
    trace_id: string
    rating: number
    feedback?: string
    ground_truth?: string
  }) =>
    fetchAPI<EvaluationRecord>('/admin/evaluations', {
      method: 'POST',
      body: JSON.stringify(evaluation),
    }),
}
