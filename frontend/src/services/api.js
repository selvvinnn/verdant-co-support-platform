
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.detail || `Request failed: ${response.status}`)
  }

  return data
}

export const api = {
  // Customer
  sendCustomerMessage: (payload) =>
    request('/api/customer/messages', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getCustomerConversation: (conversationId, token) =>
    request(`/api/customer/conversations/${conversationId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }),
    
  agentRegister: (email, password, invite_code) =>
    request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, invite_code }),
    }),

  // Agent
  agentLogin: (email, password) =>
    request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  getAgentProfile: (token) =>
    request('/api/agent/me', {
      headers: { Authorization: `Bearer ${token}` },
    }),

  getAgentConversations: (token) =>
    request('/api/agent/conversations', {
      headers: { Authorization: `Bearer ${token}` },
    }),

  getAgentConversation: (conversationId, token) =>
    request(`/api/agent/conversations/${conversationId}`, {
      headers: { Authorization: `Bearer ${token}` },
    }),

  updateDraft: (draftId, draftText, token) =>
    request(`/api/agent/drafts/${draftId}`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ draft_text: draftText }),
    }),

  approveDraft: (draftId, token) =>
    request(`/api/agent/drafts/${draftId}/approve`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }),
}
