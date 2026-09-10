import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Receipt,
  Target,
  TrendingUp,
  MessageSquare,
  Bell,
  Calculator,
  AlertTriangle,
  LogOut,
} from 'lucide-react'
import { useAuth } from '../services/auth'

export default function Layout({ children }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/transactions', icon: Receipt, label: 'Transactions' },
    { path: '/goals', icon: Target, label: 'Goals' },
    { path: '/insights', icon: TrendingUp, label: 'Insights' },
    { path: '/risk', icon: AlertTriangle, label: 'Risk Analysis' },
    { path: '/alerts', icon: Bell, label: 'Alerts' },
    { path: '/simulations', icon: Calculator, label: 'Simulations' },
    { path: '/chat', icon: MessageSquare, label: 'AI Coach' },
  ]

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <aside className="fixed left-0 top-0 h-full w-64 bg-white shadow-lg flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-primary-600">FinSage</h1>
          <p className="text-sm text-gray-500 mt-1">AI Finance Companion</p>
        </div>

        <nav className="mt-2 flex-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center px-6 py-3 text-gray-700 hover:bg-primary-50 hover:text-primary-600 transition-colors ${
                  isActive ? 'bg-primary-50 text-primary-600 border-r-4 border-primary-600' : ''
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                <span className="font-medium">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <p className="text-sm font-medium text-gray-900 truncate">{user?.username}</p>
          <p className="text-xs text-gray-500 truncate mb-3">{user?.email}</p>
          <button
            onClick={handleLogout}
            className="flex items-center w-full px-3 py-2 text-sm text-gray-700 rounded-lg hover:bg-gray-100"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Sign out
          </button>
        </div>
      </aside>

      <main className="ml-64 p-8">{children}</main>
    </div>
  )
}
