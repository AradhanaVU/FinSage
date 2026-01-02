import { useEffect, useState } from 'react'
import { AlertTriangle, TrendingDown, Target, BarChart3, Activity, Zap } from 'lucide-react'
import { getCashFlowRisk, stressTestCashFlow } from '../services/api'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function RiskAnalysis() {
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [horizonDays, setHorizonDays] = useState(30)
  const [stressTestResult, setStressTestResult] = useState(null)
  const [stressLoading, setStressLoading] = useState(false)
  const [stressScenarios, setStressScenarios] = useState({})

  useEffect(() => {
    loadRiskAnalysis()
  }, [horizonDays])

  const loadRiskAnalysis = async () => {
    try {
      setLoading(true)
      const response = await getCashFlowRisk(horizonDays)
      setRiskData(response.data)
    } catch (error) {
      console.error('Error loading risk analysis:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStressTest = async () => {
    if (Object.keys(stressScenarios).length === 0) {
      alert('Please add at least one stress scenario')
      return
    }

    try {
      setStressLoading(true)
      const response = await stressTestCashFlow(stressScenarios, horizonDays)
      setStressTestResult(response.data)
    } catch (error) {
      console.error('Error running stress test:', error)
      alert(`Failed to run stress test: ${error.response?.data?.detail || error.message}`)
    } finally {
      setStressLoading(false)
    }
  }

  const addStressScenario = (category, multiplier) => {
    setStressScenarios({
      ...stressScenarios,
      [category]: parseFloat(multiplier)
    })
  }

  const removeStressScenario = (category) => {
    const newScenarios = { ...stressScenarios }
    delete newScenarios[category]
    setStressScenarios(newScenarios)
  }

  const getRiskColor = (probability) => {
    if (probability < 0.1) return 'text-green-600'
    if (probability < 0.3) return 'text-yellow-600'
    if (probability < 0.5) return 'text-orange-600'
    return 'text-red-600'
  }

  const getRiskSeverity = (probability) => {
    if (probability < 0.1) return { label: 'Low', color: 'bg-green-100 text-green-800' }
    if (probability < 0.3) return { label: 'Moderate', color: 'bg-yellow-100 text-yellow-800' }
    if (probability < 0.5) return { label: 'High', color: 'bg-orange-100 text-orange-800' }
    return { label: 'Critical', color: 'bg-red-100 text-red-800' }
  }

  const COLORS = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4']

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Analyzing cash-flow risk...</p>
      </div>
    )
  }

  if (!riskData) {
    return (
      <div className="text-center py-12 bg-gray-50 rounded-lg">
        <AlertTriangle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 text-lg">No transaction data available</p>
        <p className="text-gray-500 mt-2">Add some transactions to see risk analysis</p>
      </div>
    )
  }

  const failureProb = riskData.failure_probability
  const severity = getRiskSeverity(failureProb)

  // Prepare risk drivers data for charts
  const riskDriversData = riskData.risk_drivers.slice(0, 7).map((driver, idx) => ({
    name: driver.category,
    value: driver.contribution,
    variance: driver.variance,
    cv: driver.cv
  }))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Cash-Flow Risk Analysis</h1>
          <p className="text-gray-600 mt-1">Probabilistic modeling of financial failure risk</p>
        </div>
        <div className="flex items-center space-x-4">
          <label className="text-sm text-gray-700">Horizon:</label>
          <select
            value={horizonDays}
            onChange={(e) => setHorizonDays(parseInt(e.target.value))}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={180}>180 days</option>
          </select>
        </div>
      </div>

      {/* Key Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Failure Probability</h3>
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <div className={`text-3xl font-bold ${getRiskColor(failureProb)}`}>
            {(failureProb * 100).toFixed(1)}%
          </div>
          <div className="mt-2">
            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${severity.color}`}>
              {severity.label} Risk
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-2">P(cash flow &lt; 0)</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Expected Shortfall</h3>
            <TrendingDown className="w-5 h-5 text-orange-600" />
          </div>
          <div className="text-3xl font-bold text-orange-600">
            ${Math.abs(riskData.expected_shortfall).toFixed(2)}
          </div>
          <p className="text-xs text-gray-500 mt-2">Tail risk when failure occurs</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Mean Cash Flow</h3>
            <Activity className="w-5 h-5 text-blue-600" />
          </div>
          <div className={`text-3xl font-bold ${riskData.mean_cashflow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${riskData.mean_cashflow.toFixed(2)}
          </div>
          <p className="text-xs text-gray-500 mt-2">Expected monthly net</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-gray-600">Runway</h3>
            <Zap className="w-5 h-5 text-purple-600" />
          </div>
          <div className="text-3xl font-bold text-purple-600">
            {riskData.runway_days > 0 ? Math.round(riskData.runway_days) : 0}
          </div>
          <p className="text-xs text-gray-500 mt-2">Days until expected failure</p>
        </div>
      </div>

      {/* Risk Drivers */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2 text-primary-600" />
          Risk Attribution by Category
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Which spending categories contribute most to cash-flow volatility
        </p>

        {riskData.risk_drivers.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pie Chart */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">Risk Contribution (%)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskDriversData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {riskDriversData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Bar Chart */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-3">Risk Share by Category</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={riskDriversData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No risk drivers identified</p>
        )}

        {/* Risk Drivers Table */}
        {riskData.risk_drivers.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">Detailed Risk Drivers</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-4 font-semibold text-gray-700">Category</th>
                    <th className="text-right py-2 px-4 font-semibold text-gray-700">Risk Share</th>
                    <th className="text-right py-2 px-4 font-semibold text-gray-700">Std Dev</th>
                    <th className="text-right py-2 px-4 font-semibold text-gray-700">Mean</th>
                    <th className="text-right py-2 px-4 font-semibold text-gray-700">CV</th>
                  </tr>
                </thead>
                <tbody>
                  {riskData.risk_drivers.map((driver, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-4 font-medium text-gray-900">{driver.category}</td>
                      <td className="py-2 px-4 text-right text-gray-700">
                        {driver.contribution.toFixed(1)}%
                      </td>
                      <td className="py-2 px-4 text-right text-gray-600">
                        ${driver.std.toFixed(2)}
                      </td>
                      <td className="py-2 px-4 text-right text-gray-600">
                        ${driver.mean.toFixed(2)}
                      </td>
                      <td className="py-2 px-4 text-right text-gray-600">
                        {driver.cv.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Goal-Conditioned Risks */}
      {riskData.goal_risks && riskData.goal_risks.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <Target className="w-5 h-5 mr-2 text-primary-600" />
            Goal-Conditioned Risk
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Probability of missing each financial goal based on current cash-flow risk
          </p>
          <div className="space-y-4">
            {riskData.goal_risks.map((goalRisk, idx) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg border">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">{goalRisk.goal_name}</h3>
                  <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                    goalRisk.failure_probability < 0.2 ? 'bg-green-100 text-green-800' :
                    goalRisk.failure_probability < 0.4 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {(goalRisk.failure_probability * 100).toFixed(1)}% failure risk
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm mt-3">
                  <div>
                    <span className="text-gray-600">Remaining:</span>
                    <span className="ml-2 font-semibold text-gray-900">
                      ${goalRisk.remaining_amount.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Months to Goal:</span>
                    <span className="ml-2 font-semibold text-gray-900">
                      {goalRisk.months_to_goal.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Expected Shortfall:</span>
                    <span className="ml-2 font-semibold text-red-600">
                      ${goalRisk.expected_shortfall.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stress Testing */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Zap className="w-5 h-5 mr-2 text-primary-600" />
          Stress Testing
        </h2>
        <p className="text-sm text-gray-600 mb-4">
          Apply shocks to see how risk changes (e.g., rent +10%, income -10%)
        </p>

        <div className="space-y-4">
          {/* Add Scenario */}
          <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
            <input
              type="text"
              placeholder="Category (e.g., rent, income, dining)"
              id="stressCategory"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
            <input
              type="number"
              step="0.1"
              placeholder="Multiplier (1.1 = +10%, 0.9 = -10%)"
              id="stressMultiplier"
              className="w-48 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={() => {
                const category = document.getElementById('stressCategory').value
                const multiplier = document.getElementById('stressMultiplier').value
                if (category && multiplier) {
                  addStressScenario(category, multiplier)
                  document.getElementById('stressCategory').value = ''
                  document.getElementById('stressMultiplier').value = ''
                }
              }}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Add Scenario
            </button>
          </div>

          {/* Active Scenarios */}
          {Object.keys(stressScenarios).length > 0 && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-700">Active Scenarios:</h3>
              {Object.entries(stressScenarios).map(([category, multiplier]) => (
                <div key={category} className="flex items-center justify-between p-3 bg-blue-50 rounded border border-blue-200">
                  <span className="font-medium text-gray-900">
                    {category}: {multiplier > 1 ? '+' : ''}{((multiplier - 1) * 100).toFixed(0)}%
                  </span>
                  <button
                    onClick={() => removeStressScenario(category)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          <button
            onClick={handleStressTest}
            disabled={stressLoading || Object.keys(stressScenarios).length === 0}
            className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {stressLoading ? 'Running Stress Test...' : 'Run Stress Test'}
          </button>

          {/* Stress Test Results */}
          {stressTestResult && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg border">
              <h3 className="font-semibold text-gray-900 mb-4">Stress Test Results</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">Base Failure Probability</div>
                  <div className="text-xl font-bold text-gray-900">
                    {(stressTestResult.base_risk.failure_probability * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">Shocked Failure Probability</div>
                  <div className={`text-xl font-bold ${
                    stressTestResult.shocked_risk.failure_probability > stressTestResult.base_risk.failure_probability
                      ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {(stressTestResult.shocked_risk.failure_probability * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">Change</div>
                  <div className={`text-lg font-semibold ${
                    stressTestResult.delta.failure_probability > 0 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {stressTestResult.delta.failure_probability > 0 ? '+' : ''}
                    {(stressTestResult.delta.failure_probability * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">Expected Shortfall Change</div>
                  <div className={`text-lg font-semibold ${
                    stressTestResult.delta.expected_shortfall > 0 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {stressTestResult.delta.expected_shortfall > 0 ? '+' : ''}
                    ${Math.abs(stressTestResult.delta.expected_shortfall).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Statistical Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Statistical Summary</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-600">Income Mean</div>
            <div className="font-semibold text-gray-900">
              ${riskData.income_stats?.mean?.toFixed(2) || '0.00'}
            </div>
          </div>
          <div>
            <div className="text-gray-600">Income Std Dev</div>
            <div className="font-semibold text-gray-900">
              ${riskData.income_stats?.std?.toFixed(2) || '0.00'}
            </div>
          </div>
          <div>
            <div className="text-gray-600">Expense Mean</div>
            <div className="font-semibold text-gray-900">
              ${riskData.expense_stats?.total_mean?.toFixed(2) || '0.00'}
            </div>
          </div>
          <div>
            <div className="text-gray-600">Expense Std Dev</div>
            <div className="font-semibold text-gray-900">
              ${riskData.expense_stats?.total_std?.toFixed(2) || '0.00'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

