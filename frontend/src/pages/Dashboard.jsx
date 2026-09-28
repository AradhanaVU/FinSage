import { useCallback, useEffect, useState } from 'react'
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Target,
} from 'lucide-react'
import {
  getTransactions,
  getGoals,
  getAlerts,
} from '../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function buildSpendingData(transactions) {
  const totals = {}
  for (const txn of transactions) {
    if (txn.transaction_type !== 'expense') continue
    const category = txn.category || 'Uncategorized'
    totals[category] = (totals[category] || 0) + Math.abs(Number(txn.amount) || 0)
  }
  return Object.entries(totals)
    .map(([category, total_amount]) => ({ category, total_amount: Math.round(total_amount * 100) / 100 }))
    .sort((a, b) => b.total_amount - a.total_amount)
    .slice(0, 5)
}

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
  const [hasLoaded, setHasLoaded] = useState(false)

  const loadDashboardData = useCallback(async ({ soft = false } = {}) => {
    try {
      if (!soft) setLoading(true)

      const txnResponse = await getTransactions({ limit: 1000 })
      const transactions = Array.isArray(txnResponse.data) ? txnResponse.data : []

      const income = transactions
        .filter((t) => t.transaction_type === 'income')
        .reduce((sum, t) => sum + Math.abs(Number(t.amount) || 0), 0)

      const expenses = transactions
        .filter((t) => t.transaction_type === 'expense')
        .reduce((sum, t) => sum + Math.abs(Number(t.amount) || 0), 0)

      const goalsResponse = await getGoals()
      const goals = Array.isArray(goalsResponse.data) ? goalsResponse.data : []
      const funded = goals.reduce((sum, g) => sum + Math.max(0, Number(g.current_amount) || 0), 0)
      const targeted = goals.reduce((sum, g) => sum + Math.max(0, Number(g.target_amount) || 0), 0)
      const totalProgress = targeted > 0 ? (funded / targeted) * 100 : 0

      const alertsResponse = await getAlerts(true)
      const alertList = Array.isArray(alertsResponse.data) ? alertsResponse.data : []

      setStats({
        totalIncome: income,
        totalExpenses: expenses,
        balance: income - expenses,
        goalProgress: totalProgress,
      })
      setRecentTransactions(transactions.slice(0, 5))
      setAlerts(alertList.slice(0, 3))
      setSpendingData(buildSpendingData(transactions))
      setHasLoaded(true)
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadDashboardData()

    const softRefresh = () => loadDashboardData({ soft: true })
    const onVisibility = () => {
      if (document.visibilityState === 'visible') softRefresh()
    }

    window.addEventListener('focus', softRefresh)
    document.addEventListener('visibilitychange', onVisibility)
    const interval = setInterval(softRefresh, 15000)

    return () => {
      window.removeEventListener('focus', softRefresh)
      document.removeEventListener('visibilitychange', onVisibility)
      clearInterval(interval)
    }
  }, [loadDashboardData])

  if (loading && !hasLoaded) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Income minus expenses across all loaded transactions</p>
        </div>
        <button
          type="button"
          onClick={() => loadDashboardData({ soft: true })}
          className="shrink-0 px-3 py-2 text-sm font-medium text-primary-700 bg-primary-50 rounded-lg hover:bg-primary-100"
        >
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Income"
          value={`$${stats.totalIncome.toFixed(2)}`}
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          title="Total Expenses"
          value={`$${stats.totalExpenses.toFixed(2)}`}
          icon={TrendingDown}
          color="red"
        />
        <StatCard
          title="Balance"
          value={`$${stats.balance.toFixed(2)}`}
          icon={DollarSign}
          color={stats.balance >= 0 ? 'green' : 'red'}
        />
        <StatCard
          title="Goal Progress"
          value={`${stats.goalProgress.toFixed(1)}%`}
          icon={Target}
          color="blue"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Top Spending Categories</h2>
          {spendingData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={spendingData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total_amount" fill="#0ea5e9" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center rounded-lg border border-dashed border-gray-200 bg-gray-50 text-sm text-gray-500">
              No expense categories yet. Add a transaction to see the chart.
            </div>
          )}
        </div>

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

function StatCard({ title, value, icon: Icon, color }) {
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
