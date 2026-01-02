import { useEffect, useState } from 'react'
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  AlertCircle,
  Target,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react'
import { 
  getTransactions, 
  getGoals, 
  getAlerts,
  getSpendingAnalysis 
} from '../services/api'
import { format, subDays } from 'date-fns'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalIncome: 0,
    totalExpenses: 0,
    balance: 0,
    goalProgress: 0,
  })
  const [recentTransactions, setRecentTransactions] = useState([])
  const [alerts, setAlerts] = useState([])
  const [spendingData, setSpendingData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Get transactions
      const txnResponse = await getTransactions({ limit: 10 })
      const transactions = txnResponse.data
      
      // Calculate stats
      const income = transactions
        .filter(t => t.transaction_type === 'income')
        .reduce((sum, t) => sum + t.amount, 0)
      
      const expenses = transactions
        .filter(t => t.transaction_type === 'expense')
        .reduce((sum, t) => sum + Math.abs(t.amount), 0)
      
      // Get goals
      const goalsResponse = await getGoals()
      const goals = goalsResponse.data
      const totalProgress = goals.reduce((sum, g) => {
        return sum + (g.current_amount / g.target_amount) * 100
      }, 0) / (goals.length || 1)
      
      // Get alerts
      const alertsResponse = await getAlerts(true)
      
      // Get spending analysis
      const analysisResponse = await getSpendingAnalysis()
      
      setStats({
        totalIncome: income,
        totalExpenses: expenses,
        balance: income - expenses,
        goalProgress: totalProgress,
      })
      
      setRecentTransactions(transactions.slice(0, 5))
      setAlerts(alertsResponse.data.slice(0, 3))
      setSpendingData(analysisResponse.data.slice(0, 5))
      
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Overview of your financial health</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Income"
          value={`$${stats.totalIncome.toFixed(2)}`}
          icon={TrendingUp}
          trend="up"
          color="green"
        />
        <StatCard
          title="Total Expenses"
          value={`$${stats.totalExpenses.toFixed(2)}`}
          icon={TrendingDown}
          trend="down"
          color="red"
        />
        <StatCard
          title="Balance"
          value={`$${stats.balance.toFixed(2)}`}
          icon={DollarSign}
          trend={stats.balance >= 0 ? "up" : "down"}
          color={stats.balance >= 0 ? "green" : "red"}
        />
        <StatCard
          title="Goal Progress"
          value={`${stats.goalProgress.toFixed(1)}%`}
          icon={Target}
          trend="up"
          color="blue"
        />
      </div>

      {/* Charts and Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spending by Category */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Top Spending Categories</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={spendingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="total_amount" fill="#0ea5e9" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Transactions */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Transactions</h2>
          <div className="space-y-3">
            {recentTransactions.length > 0 ? (
              recentTransactions.map((txn) => (
                <div key={txn.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <p className="font-medium text-gray-900">{txn.description}</p>
                    <p className="text-sm text-gray-500">{txn.category || 'Uncategorized'}</p>
                  </div>
                  <div className={`font-semibold ${
                    txn.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {txn.transaction_type === 'income' ? '+' : '-'}${Math.abs(txn.amount).toFixed(2)}
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-8">No recent transactions</p>
            )}
          </div>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2 text-yellow-500" />
            Recent Alerts
          </h2>
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border-l-4 ${
                  alert.severity === 'critical' ? 'bg-red-50 border-red-500' :
                  alert.severity === 'warning' ? 'bg-yellow-50 border-yellow-500' :
                  'bg-blue-50 border-blue-500'
                }`}
              >
                <p className="font-semibold text-gray-900">{alert.title}</p>
                <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, icon: Icon, trend, color }) {
  const colorClasses = {
    green: 'text-green-600 bg-green-100',
    red: 'text-red-600 bg-red-100',
    blue: 'text-blue-600 bg-blue-100',
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className={`p-3 rounded-full ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  )
}

