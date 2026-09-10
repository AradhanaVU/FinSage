import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Goals from './pages/Goals'
import Insights from './pages/Insights'
import RiskAnalysis from './pages/RiskAnalysis'
import Alerts from './pages/Alerts'
import Simulations from './pages/Simulations'
import Chat from './pages/Chat'
import Login from './pages/Login'
import Register from './pages/Register'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './services/auth'

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/transactions" element={<Transactions />} />
                    <Route path="/goals" element={<Goals />} />
                    <Route path="/insights" element={<Insights />} />
                    <Route path="/risk" element={<RiskAnalysis />} />
                    <Route path="/alerts" element={<Alerts />} />
                    <Route path="/simulations" element={<Simulations />} />
                    <Route path="/chat" element={<Chat />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
