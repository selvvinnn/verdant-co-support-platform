
import { useEffect, useState } from 'react'
import {
  Search,
  LogIn,
  LogOut,
  Send,
  CheckCircle2,
  RefreshCw,
  UserRound,
  Bot,
  MessageSquare,
  Clock,
  AlertCircle,
  Leaf,
} from 'lucide-react'

import { api } from '../services/api'

const AGENT_SESSION_KEY = 'verdant_agent_token'

function AgentView() {
  const [token, setToken] = useState(
    () => sessionStorage.getItem(AGENT_SESSION_KEY) || ''
  )

  const [agent, setAgent] = useState(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [inviteCode, setInviteCode] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)

  const [conversations, setConversations] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [conversation, setConversation] = useState(null)

  const [draftEdits, setDraftEdits] = useState({})
  const [search, setSearch] = useState('')

  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  // Restore and validate agent session
  useEffect(() => {
    if (token) {
      initializeAgent(token)
    }
  }, [])

  async function initializeAgent(accessToken) {
    try {
      setLoading(true)
      setError('')

      const profile = await api.getAgentProfile(accessToken)

      setAgent(profile)

      await loadConversations(accessToken)
    } catch (err) {
      sessionStorage.removeItem(AGENT_SESSION_KEY)
      setToken('')
      setAgent(null)
      setError(err.message || 'Agent session expired. Please log in again.')
    } finally {
      setLoading(false)
    }
  }

  // Agent login
  async function handleLogin(event) {
    event.preventDefault()

    try {
      setLoading(true)
      setError('')

      const result = await api.agentLogin(email, password)

      sessionStorage.setItem(
        AGENT_SESSION_KEY,
        result.access_token
      )

      setToken(result.access_token)
      setAgent(result.agent)

      setPassword('')

      await loadConversations(result.access_token)
    } catch (err) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  // Agent registration
async function handleRegister(event) {
  event.preventDefault()

  try {
    setLoading(true)
    setError('')
    setNotice('')

    await api.agentRegister(email, password, inviteCode)

    setNotice('Account created successfully. Please sign in.')

    setIsRegistering(false)
    setPassword('')
    setInviteCode('')
  } catch (err) {
    setError(err.message || 'Registration failed')
  } finally {
    setLoading(false)
  }
}

  // Load all conversations
  async function loadConversations(accessToken = token) {
    try {
      const result = await api.getAgentConversations(accessToken)

      const items = result.conversations || []

      setConversations(items)

      // Select the first conversation if none is selected
      if (items.length > 0) {
        const stillExists = items.some(
          (item) => item.conversation_id === selectedId
        )

        if (!selectedId || !stillExists) {
          await selectConversation(
            items[0].conversation_id,
            accessToken
          )
        }
      } else {
        setSelectedId('')
        setConversation(null)
      }
    } catch (err) {
      setError(err.message || 'Could not load conversations')
    }
  }

  // Load one conversation
  async function selectConversation(
    conversationId,
    accessToken = token
  ) {
    try {
      setSelectedId(conversationId)
      setConversation(null)
      setDraftEdits({})
      setError('')

      const result = await api.getAgentConversation(
        conversationId,
        accessToken
      )

      setConversation(result)
    } catch (err) {
      setError(err.message || 'Could not load conversation')
    }
  }

  // Save edited draft
  async function saveDraft(draft) {
    const text =
      draftEdits[draft.id] ?? draft.draft_text ?? ''

    if (!text.trim()) {
      setError('Draft cannot be empty.')
      return
    }

    try {
      setActionLoading(draft.id)
      setError('')
      setNotice('')

      await api.updateDraft(draft.id, text.trim(), token)

      setNotice('Draft saved successfully.')

      await selectConversation(selectedId)
    } catch (err) {
      setError(err.message || 'Could not save draft')
    } finally {
      setActionLoading('')
    }
  }

  // Approve draft
  async function approveDraft(draft) {
    const text =
      draftEdits[draft.id] ?? draft.draft_text ?? ''

    if (!text.trim()) {
      setError('Draft cannot be empty.')
      return
    }

    try {
      setActionLoading(draft.id)
      setError('')
      setNotice('')

      // Save the latest edit before approval
      await api.updateDraft(draft.id, text.trim(), token)

      // Approve the saved draft
      await api.approveDraft(draft.id, token)

      setNotice('Reply approved and added to the conversation.')

      // Refresh conversation and list
      await selectConversation(selectedId)
      await loadConversations(token)
    } catch (err) {
      setError(err.message || 'Could not approve draft')
    } finally {
      setActionLoading('')
    }
  }

  function handleLogout() {
    sessionStorage.removeItem(AGENT_SESSION_KEY)

    setToken('')
    setAgent(null)
    setConversations([])
    setSelectedId('')
    setConversation(null)
    setDraftEdits({})
    setError('')
    setNotice('')
  }

  const filteredConversations = conversations.filter((item) => {
    const query = search.toLowerCase()

    return (
      item.customer?.name?.toLowerCase().includes(query) ||
      item.customer?.phone?.toLowerCase().includes(query) ||
      item.customer?.id?.toLowerCase().includes(query) ||
      item.latest_message?.toLowerCase().includes(query)
    )
  })


    // Login and registration screen
    if (!token || !agent) {
    return (
        <div className="agent-login-page">
        <form
            className="login-card"
            onSubmit={isRegistering ? handleRegister : handleLogin}
        >
            <div className="login-icon">
            <Leaf size={27} />
            </div>

            <p className="eyebrow">VERDANT & CO. SUPPORT</p>

            <h2>{isRegistering ? 'Create account' : 'Welcome back'}</h2>

            <p className="login-description">
            {isRegistering
                ? 'Register as an authorized support agent using your invitation code.'
                : 'Sign in to manage customer conversations and review AI replies.'}
            </p>

            <label>Email address</label>
            <input
            type="email"
            placeholder="agent@verdantco.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
            />

            <label>Password</label>
            <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            required
            />

            {isRegistering && (
            <>
                <label>Invitation code</label>
                <input
                type="password"
                placeholder="Enter your invitation code"
                value={inviteCode}
                onChange={(event) => setInviteCode(event.target.value)}
                required
                />
            </>
            )}

            {error && (
            <div className="agent-error">
                <AlertCircle size={15} />
                {error}
            </div>
            )}

            {notice && (
            <div className="agent-notice">
                <CheckCircle2 size={15} />
                {notice}
            </div>
            )}

            <button className="login-button" disabled={loading}>
            <LogIn size={17} />
            {loading
                ? 'Please wait...'
                : isRegistering
                ? 'Create account'
                : 'Sign in'}
            </button>

            <button
            type="button"
            className="auth-switch-button"
            onClick={() => {
                setIsRegistering(!isRegistering)
                setError('')
                setNotice('')
                setPassword('')
                setInviteCode('')
            }}
            >
            {isRegistering
                ? 'Already have an account? Sign in'
                : 'New agent? Create an account'}
            </button>

            <span className="login-footer">
            Authorized support agents only
            </span>
        </form>
        </div>
    )
    }

  return (
    <div className="agent-workspace">

      {/* LEFT: CONVERSATION LIST */}
      <aside className="conversation-sidebar">

        <div className="agent-sidebar-header">
          <div>
            <p className="eyebrow">SUPPORT INBOX</p>
            <h2>Conversations</h2>
          </div>

          <span className="conversation-count">
            {conversations.length}
          </span>
        </div>

        <div className="agent-search">
          <Search size={16} />
          <input
            placeholder="Search conversations..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        <div className="conversation-list">
          {filteredConversations.map((item) => (
            <button
              key={item.conversation_id}
              className={`conversation-item ${
                selectedId === item.conversation_id
                  ? 'selected'
                  : ''
              }`}
              onClick={() =>
                selectConversation(item.conversation_id)
              }
            >
              <div className="customer-avatar">
                {item.customer?.name?.charAt(0)?.toUpperCase() || 'C'}
              </div>

              <div className="conversation-preview">
                <div className="conversation-name-row">
                  <strong>{item.customer?.name || 'Customer'}</strong>
                  <span>{item.status}</span>
                </div>

                <p>{item.latest_message || 'No messages yet'}</p>

                <small>{item.customer?.phone}</small>
              </div>
            </button>
          ))}

          {filteredConversations.length === 0 && (
            <div className="empty-sidebar">
              <MessageSquare size={25} />
              <p>No conversations found.</p>
            </div>
          )}
        </div>

        <div className="agent-sidebar-footer">
          <div className="agent-profile">
            <div className="profile-avatar">
              {agent.email?.charAt(0)?.toUpperCase() || 'A'}
            </div>

            <div>
              <strong>Support Agent</strong>
              <small>{agent.email}</small>
            </div>
          </div>

          <button
            className="logout-button"
            onClick={handleLogout}
            title="Sign out"
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>

      {/* CENTRE: CONVERSATION */}
      <section className="agent-chat-panel">

        {!conversation ? (
          <div className="agent-empty-state">
            <MessageSquare size={35} />
            <h2>
              {loading
                ? 'Loading conversations...'
                : 'Select a conversation'}
            </h2>
            <p>Choose a customer from your support inbox.</p>
          </div>
        ) : (
          <>
            <div className="agent-chat-header">
              <div className="customer-avatar large">
                {conversation.customer?.name?.charAt(0)?.toUpperCase() || 'C'}
              </div>

              <div>
                <h3>{conversation.customer?.name}</h3>
                <span>{conversation.customer?.phone}</span>
              </div>

              <span className="conversation-status">
                {conversation.status}
              </span>
            </div>

            <div className="agent-messages">
              {conversation.messages?.map((message) => (
                <div
                  key={message.message_id}
                  className={`agent-message-row ${
                    message.sender_type === 'agent'
                      ? 'sent'
                      : 'received'
                  }`}
                >
                  <div className="agent-message-bubble">
                    <p>{message.text}</p>

                    <small>
                      {message.sender_type === 'agent'
                        ? 'Agent'
                        : 'Customer'}
                      {' · '}
                      {new Date(message.created_at).toLocaleString()}
                    </small>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      {/* RIGHT: AI DRAFT PANEL */}
      <aside className="draft-sidebar">

        <div className="draft-panel-header">
          <div className="draft-icon">
            <Bot size={19} />
          </div>

          <div>
            <h3>AI Reply Assistant</h3>
            <span>Review before sending</span>
          </div>

          <button
            className="refresh-button"
            onClick={() => loadConversations(token)}
            title="Refresh conversations"
          >
            <RefreshCw size={16} />
          </button>
        </div>

        <div className="draft-panel-content">

          {error && (
            <div className="agent-error">
              <AlertCircle size={15} />
              {error}
            </div>
          )}

          {notice && (
            <div className="agent-notice">
              <CheckCircle2 size={15} />
              {notice}
            </div>
          )}

          {!conversation ? (
            <div className="draft-empty">
              <Bot size={29} />
              <p>Select a conversation to review its AI drafts.</p>
            </div>
          ) : (
            <>
              {conversation.messages
                ?.filter((message) => message.ai_draft)
                .map((message) => {
                  const draft = message.ai_draft
                  const draftText =
                    draftEdits[draft.id] ?? draft.draft_text ?? ''

                  return (
                    <div className="draft-card" key={draft.id}>
                      <div className="draft-card-heading">
                        <strong>Suggested reply</strong>
                        <span className={`draft-status ${draft.status}`}>
                          {draft.status}
                        </span>
                      </div>

                      {draft.status === 'failed' ? (
                        <div className="draft-failed">
                          <AlertCircle size={17} />
                          <p>
                            {draft.error_message ||
                              'AI draft generation failed.'}
                          </p>
                        </div>
                      ) : draft.status === 'approved' ? (
                        <div className="draft-approved">
                          <CheckCircle2 size={17} />
                          <span>This reply has been approved.</span>
                        </div>
                      ) : (
                        <>
                          <p className="draft-description">
                            Review and edit the suggested response before approving.
                          </p>

                          <textarea
                            value={draftText}
                            onChange={(event) =>
                              setDraftEdits((previous) => ({
                                ...previous,
                                [draft.id]: event.target.value,
                              }))
                            }
                            placeholder="AI suggested reply..."
                            rows={9}
                          />

                          <div className="draft-actions">
                            <button
                              className="save-draft-button"
                              disabled={actionLoading === draft.id}
                              onClick={() => saveDraft(draft)}
                            >
                              Save changes
                            </button>

                            <button
                              className="approve-draft-button"
                              disabled={actionLoading === draft.id}
                              onClick={() => approveDraft(draft)}
                            >
                              <CheckCircle2 size={16} />
                              {actionLoading === draft.id
                                ? 'Processing...'
                                : 'Approve reply'}
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  )
                })}

              {!conversation.messages?.some(
                (message) => message.ai_draft
              ) && (
                <div className="draft-empty">
                  <Bot size={29} />
                  <p>No AI drafts available for this conversation.</p>
                </div>
              )}
            </>
          )}
        </div>

        <div className="draft-panel-footer">
          <Clock size={14} />
          AI replies require agent approval.
        </div>
      </aside>
    </div>
  )
}

export default AgentView
