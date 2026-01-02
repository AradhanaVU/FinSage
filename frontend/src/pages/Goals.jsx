import { useEffect, useState } from 'react'
import { Plus, Target, TrendingUp } from 'lucide-react'
import { getGoals, createGoal, deleteGoal, updateGoalProgress } from '../services/api'

export default function Goals() {
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    target_amount: '',
    goal_type: 'savings',
    target_date: '',
    priority: 1,
  })

  useEffect(() => {
    loadGoals()
    // Auto-refresh goals every 30 seconds to update progress
    const interval = setInterval(() => {
      loadGoals(true) // Recalculate progress
    }, 30000)
    
    // Listen for transaction updates
    const handleTransactionUpdate = () => {
      setTimeout(() => loadGoals(true), 500) // Small delay to ensure backend processed
    }
    window.addEventListener('transactionAdded', handleTransactionUpdate)
    
    return () => {
      clearInterval(interval)
      window.removeEventListener('transactionAdded', handleTransactionUpdate)
    }
  }, [])

  const loadGoals = async (recalculate = false) => {
    try {
      if (recalculate) {
        setLoading(false) // Don't show loading on auto-refresh
      } else {
        setLoading(true)
      }
      const response = await getGoals(recalculate)
      setGoals(response.data)
    } catch (error) {
      console.error('Error loading goals:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const goalData = {
        ...formData,
        target_amount: parseFloat(formData.target_amount),
        target_date: formData.target_date ? new Date(formData.target_date).toISOString() : null,
        priority: parseInt(formData.priority),
      }
      await createGoal(goalData)
      setShowAddModal(false)
      setFormData({
        name: '',
        target_amount: '',
        goal_type: 'savings',
        target_date: '',
        priority: 1,
      })
      loadGoals()
    } catch (error) {
      console.error('Error creating goal:', error)
      alert('Failed to create goal')
    }
  }

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this goal?')) {
      try {
        await deleteGoal(id)
        loadGoals()
      } catch (error) {
        console.error('Error deleting goal:', error)
        alert('Failed to delete goal')
      }
    }
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-600">Loading goals...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Financial Goals</h1>
          <p className="text-gray-600 mt-1">Set and track your financial objectives</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Plus className="w-5 h-5 mr-2" />
          New Goal
        </button>
      </div>

      {/* Goals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {goals.length > 0 ? (
          goals.map((goal) => {
            const progress = (goal.current_amount / goal.target_amount) * 100
            return (
              <div key={goal.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <Target className="w-5 h-5 text-primary-600 mr-2" />
                    <h3 className="text-lg font-semibold text-gray-900">{goal.name}</h3>
                  </div>
                  <button
                    onClick={() => handleDelete(goal.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </div>
                
                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-600 mb-2">
                    <span>${goal.current_amount.toFixed(2)}</span>
                    <span>${goal.target_amount.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-primary-600 h-3 rounded-full transition-all"
                      style={{ width: `${Math.min(progress, 100)}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-500 mt-2">{progress.toFixed(1)}% complete</p>
                  <p className="text-xs text-gray-400 mt-1">
                    ${goal.current_amount.toFixed(2)} of ${goal.target_amount.toFixed(2)}
                  </p>
                </div>

                <div className="text-sm text-gray-600">
                  <p>Type: <span className="font-medium">{goal.goal_type}</span></p>
                  {goal.target_date && (
                    <p>Target: {new Date(goal.target_date).toLocaleDateString()}</p>
                  )}
                  <button
                    onClick={() => loadGoals(true)}
                    className="mt-2 text-xs text-primary-600 hover:text-primary-800"
                  >
                    ↻ Recalculate Progress
                  </button>
                </div>
              </div>
            )
          })
        ) : (
          <div className="col-span-full text-center py-12 text-gray-500">
            No goals yet. Create your first financial goal to get started!
          </div>
        )}
      </div>

      {/* Add Goal Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">New Goal</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Goal Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g., Emergency Fund"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Amount
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={formData.target_amount}
                  onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Goal Type
                </label>
                <select
                  value={formData.goal_type}
                  onChange={(e) => setFormData({ ...formData, goal_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="savings">Savings</option>
                  <option value="debt_payoff">Debt Payoff</option>
                  <option value="investment">Investment</option>
                  <option value="purchase">Purchase</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Date (optional)
                </label>
                <input
                  type="date"
                  value={formData.target_date}
                  onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority (1-5)
                </label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  Create Goal
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

