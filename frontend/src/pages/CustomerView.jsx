
import { useEffect, useRef, useState } from 'react'
import { api } from '../services/api'
import {
  Send,
  UserRound,
  Leaf,
  RefreshCw,
  MessageCircle,
} from 'lucide-react'

const SESSION_KEY = 'verdant_customer_session'

function CustomerView() {
  const [customer, setCustomer] = useState({
    customer_id: 'cust_1042',
    brand_id: 'verdant-co',
    name: 'Aisha Khan',
    phone: '+919800000001',
  })

  const [conversationId, setConversationId] = useState('')
  const [token, setToken] = useState('')
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [connected, setConnected] = useState(false)

  const bottomRef = useRef(null)

  // Restore the current browser session
  useEffect(() => {
    const saved = sessionStorage.getItem(SESSION_KEY)

    if (saved) {
      try {
        const session = JSON.parse(saved)

        setCustomer(session.customer)
        setConversationId(session.conversationId)
        setToken(session.token)
      } catch {
        sessionStorage.removeItem(SESSION_KEY)
      }
    }
  }, [])

  // Load conversation when a valid session is available
  useEffect(() => {
    if (conversationId && token) {
      loadConversation(conversationId, token)
    }
  }, [conversationId, token])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function loadConversation(id, accessToken) {
    try {
      setLoading(true)
      setError('')

      const data = await api.getCustomerConversation(id, accessToken)

      setMessages(data.messages || [])
      setConnected(true)
    } catch (err) {
      setError(err.message)
      setConnected(false)
    } finally {
      setLoading(false)
    }
  }

  async function sendMessage(event) {
    event.preventDefault()

    if (!text.trim() || loading) return

    try {
      setLoading(true)
      setError('')

      const response = await api.sendCustomerMessage({
        ...customer,
        text: text.trim(),
      })

      const newConversationId = response.conversation_id
      const newToken = response.customer_access_token

      if (!newConversationId || !newToken) {
        throw new Error('Backend did not return conversation access details.')
      }

      const session = {
        customer,
        conversationId: newConversationId,
        token: newToken,
      }

      sessionStorage.setItem(SESSION_KEY, JSON.stringify(session))

      setConversationId(newConversationId)
      setToken(newToken)
      setText('')

      await loadConversation(newConversationId, newToken)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function resetConversation() {
    sessionStorage.removeItem(SESSION_KEY)
    setConversationId('')
    setToken('')
    setMessages([])
    setConnected(false)
    setError('')
    setText('')
  }

  return (
    <div className="customer-layout">
      <aside className="customer-sidebar">
        <div className="sidebar-heading">
          <UserRound size={19} />
          <h3>Customer details</h3>
        </div>

        <label>Customer ID</label>
        <input
          value={customer.customer_id}
          onChange={(e) =>
            setCustomer({ ...customer, customer_id: e.target.value })
          }
          disabled={!!conversationId}
        />

        <label>Full name</label>
        <input
          value={customer.name}
          onChange={(e) =>
            setCustomer({ ...customer, name: e.target.value })
          }
          disabled={!!conversationId}
        />

        <label>Phone number</label>
        <input
          value={customer.phone}
          onChange={(e) =>
            setCustomer({ ...customer, phone: e.target.value })
          }
          disabled={!!conversationId}
        />

        <label>Brand ID</label>
        <input value={customer.brand_id} disabled />

        <div className="customer-note">
          <Leaf size={17} />
          <p>
            You are chatting with the Verdant & Co. customer care team.
          </p>
        </div>

        <button
          className="secondary-button"
          onClick={resetConversation}
        >
          <RefreshCw size={15} />
          New customer session
        </button>
      </aside>

      <section className="chat-panel">
        <div className="chat-header">
          <div className="chat-avatar">
            <Leaf size={20} />
          </div>

          <div>
            <h3>Verdant & Co. Support</h3>
            <span>
              <span className="online-dot" /> Customer care
            </span>
          </div>

          <div className="chat-status">
            {connected ? 'Connected' : 'New conversation'}
          </div>
        </div>

        <div className="chat-messages">
          <div className="welcome-message">
            <div className="welcome-icon">
              <MessageCircle size={22} />
            </div>
            <h3>Welcome to Verdant & Co.</h3>
            <p>
              We're here to help with your orders, products and returns.
            </p>
          </div>

          {messages.map((message) => (
            <div
              key={message.message_id}
              className={`message-row ${
                message.sender_type === 'customer'
                  ? 'customer-message'
                  : 'agent-message'
              }`}
            >
              <div className="message-bubble">
                <p>{message.text}</p>
                <small>
                  {message.sender_type === 'customer'
                    ? 'You'
                    : 'Verdant & Co. Support'}
                  {' · '}
                  {new Date(message.created_at).toLocaleString()}
                </small>
              </div>
            </div>
          ))}

          {loading && (
            <div className="loading-message">Loading conversation...</div>
          )}

          <div ref={bottomRef} />
        </div>

        {error && <div className="error-banner">{error}</div>}

        <form className="chat-input-area" onSubmit={sendMessage}>
          <input
            placeholder="Type your message..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
          />

          <button
            type="submit"
            disabled={loading || !text.trim()}
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </form>

        <div className="chat-footer">
          Messages are handled securely by Verdant & Co. support.
        </div>
      </section>
    </div>
  )
}

export default CustomerView
