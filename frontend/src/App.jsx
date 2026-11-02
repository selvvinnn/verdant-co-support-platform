
import { useState } from 'react'
import { Leaf, MessageCircle, Headset, LogOut } from 'lucide-react'
import './App.css'
import CustomerView from './pages/CustomerView'
import AgentView from './pages/AgentView'

function App() {
  const [view, setView] = useState('customer')

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            <Leaf size={22} />
          </div>
          <div>
            <h1>Verdant & Co.</h1>
            <span>Customer Care Platform</span>
          </div>
        </div>

        <div className="view-switch">
          <button
            className={view === 'customer' ? 'active' : ''}
            onClick={() => setView('customer')}
          >
            <MessageCircle size={16} />
            Customer
          </button>

          <button
            className={view === 'agent' ? 'active' : ''}
            onClick={() => setView('agent')}
          >
            <Headset size={16} />
            Agent
          </button>
        </div>

        <div className="header-right">
          <span className="online-dot" />
          Support workspace
        </div>
      </header>

      <main className="main-content">
        {view === 'customer' ? (
        <CustomerView />
        ) : (
        <AgentView />
        )}
      </main>
    </div>
  )
}

export default App
