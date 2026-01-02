import { useEffect, useState } from 'react'
import { Calculator, TrendingUp, Target, DollarSign, BarChart3 } from 'lucide-react'
import { getGoals, getTransactions, simulateGoalScenario, monteCarloSimulation, calculateOpportunityCost } from '../services/api'

export default function Simulations() {
  const [activeTab, setActiveTab] = useState('goal') // 'goal', 'monte', 'opportunity'
  const [goals, setGoals] = useState([])
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(false)

  // Goal Scenario State
  const [selectedGoal, setSelectedGoal] = useState('')
  const [reductionPercentages, setReductionPercentages] = useState({})
  const [scenarioResult, setScenarioResult] = useState(null)

  // Monte Carlo State
  const [monteCarloParams, setMonteCarloParams] = useState({
    initial_investment: 1000,
    monthly_contribution: 200,
    years: 10,
    expected_return: 7,
    volatility: 15,
    simulations: 1000
  })
  const [monteCarloResult, setMonteCarloResult] = useState(null)

  // Opportunity Cost State
  const [opportunityParams, setOpportunityParams] = useState({
    spending_amount: 100,
    time_horizon_years: 1,
    expected_return: 7
  })
  const [opportunityResult, setOpportunityResult] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [goalsRes, txnRes] = await Promise.all([
        getGoals(),
        getTransactions({ limit: 100 })
      ])
      setGoals(goalsRes.data)
      setTransactions(txnRes.data)

      // Extract categories for reduction percentages
      const categories = [...new Set(txnRes.data
        .filter(t => t.transaction_type === 'expense' && t.category)
        .map(t => t.category)
      )]
      const initialReductions = {}
      categories.forEach(cat => {
        initialReductions[cat] = 0
      })
      setReductionPercentages(initialReductions)
    } catch (error) {
      console.error('Error loading data:', error)
    }
  }

  const handleGoalScenario = async () => {
    if (!selectedGoal) {
      alert('Please select a goal')
      return
    }

    try {
      setLoading(true)
      const response = await simulateGoalScenario(selectedGoal, reductionPercentages)
      setScenarioResult(response.data)
    } catch (error) {
      console.error('Error running scenario:', error)
      let errorMessage = 'Failed to run scenario'
      if (error.response?.data) {
        const detail = error.response.data.detail
        if (Array.isArray(detail)) {
          errorMessage = detail.map(err => err.msg || JSON.stringify(err)).join(', ')
        } else if (typeof detail === 'string') {
          errorMessage = detail
        } else if (detail) {
          errorMessage = JSON.stringify(detail)
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleMonteCarlo = async () => {
    try {
      setLoading(true)
      const params = {
        initial_investment: parseFloat(monteCarloParams.initial_investment),
        monthly_contribution: parseFloat(monteCarloParams.monthly_contribution),
        years: parseInt(monteCarloParams.years),
        expected_return: parseFloat(monteCarloParams.expected_return) / 100,
        volatility: parseFloat(monteCarloParams.volatility) / 100,
        simulations: parseInt(monteCarloParams.simulations)
      }
      const response = await monteCarloSimulation(params)
      setMonteCarloResult(response.data)
    } catch (error) {
      console.error('Error running Monte Carlo:', error)
      let errorMessage = 'Failed to run simulation'
      if (error.response?.data) {
        const detail = error.response.data.detail
        if (Array.isArray(detail)) {
          errorMessage = detail.map(err => err.msg || JSON.stringify(err)).join(', ')
        } else if (typeof detail === 'string') {
          errorMessage = detail
        } else if (detail) {
          errorMessage = JSON.stringify(detail)
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleOpportunityCost = async () => {
    try {
      setLoading(true)
      const response = await calculateOpportunityCost(
        parseFloat(opportunityParams.spending_amount),
        parseFloat(opportunityParams.time_horizon_years),
        parseFloat(opportunityParams.expected_return) / 100
      )
      setOpportunityResult(response.data)
    } catch (error) {
      console.error('Error calculating opportunity cost:', error)
      let errorMessage = 'Failed to calculate opportunity cost'
      if (error.response?.data) {
        const detail = error.response.data.detail
        if (Array.isArray(detail)) {
          errorMessage = detail.map(err => err.msg || JSON.stringify(err)).join(', ')
        } else if (typeof detail === 'string') {
          errorMessage = detail
        } else if (detail) {
          errorMessage = JSON.stringify(detail)
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      alert(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const categories = [...new Set(transactions
    .filter(t => t.transaction_type === 'expense' && t.category)
    .map(t => t.category)
  )]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Financial Simulations</h1>
        <p className="text-gray-600 mt-1">Model different scenarios and plan your financial future</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('goal')}
          className={`px-6 py-3 font-medium transition-colors flex items-center space-x-2 ${
            activeTab === 'goal'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Target className="w-5 h-5" />
          <span>Goal Scenarios</span>
        </button>
        <button
          onClick={() => setActiveTab('monte')}
          className={`px-6 py-3 font-medium transition-colors flex items-center space-x-2 ${
            activeTab === 'monte'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <BarChart3 className="w-5 h-5" />
          <span>Monte Carlo</span>
        </button>
        <button
          onClick={() => setActiveTab('opportunity')}
          className={`px-6 py-3 font-medium transition-colors flex items-center space-x-2 ${
            activeTab === 'opportunity'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <DollarSign className="w-5 h-5" />
          <span>Opportunity Cost</span>
        </button>
      </div>

      {/* Goal Scenario Tab */}
      {activeTab === 'goal' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Goal Scenario Simulation</h2>
          <p className="text-gray-600 mb-6">
            See how reducing spending in different categories affects your goal timeline
          </p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Goal
              </label>
              <select
                value={selectedGoal}
                onChange={(e) => setSelectedGoal(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="">-- Select a goal --</option>
                {goals.map(goal => (
                  <option key={goal.id} value={goal.id}>
                    {goal.name} (${goal.current_amount.toFixed(2)} / ${goal.target_amount.toFixed(2)})
                  </option>
                ))}
              </select>
            </div>

            {selectedGoal && categories.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Spending Reductions by Category (%)
                </label>
                <div className="space-y-3">
                  {categories.map(category => (
                    <div key={category} className="flex items-center space-x-4">
                      <label className="w-48 text-sm text-gray-700">{category}</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={reductionPercentages[category] || 0}
                        onChange={(e) => setReductionPercentages({
                          ...reductionPercentages,
                          [category]: parseFloat(e.target.value) || 0
                        })}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                      />
                      <span className="text-sm text-gray-500 w-8">%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleGoalScenario}
              disabled={loading || !selectedGoal}
              className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Running Simulation...' : 'Run Scenario'}
            </button>

            {scenarioResult && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-3">Scenario Results</h3>
                {scenarioResult.scenarios && scenarioResult.scenarios.map((scenario, idx) => (
                  <div key={idx} className="mb-4 p-4 bg-white rounded border">
                    <h4 className="font-semibold text-lg text-gray-900 mb-2">{scenario.scenario_name}</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Monthly Contribution:</span>
                        <span className="ml-2 font-semibold text-gray-900">${scenario.monthly_contribution?.toFixed(2)}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Months to Goal:</span>
                        <span className="ml-2 font-semibold text-gray-900">{scenario.months_to_goal}</span>
                      </div>
                      {scenario.savings_from_reductions > 0 && (
                        <div>
                          <span className="text-gray-600">Savings from Reductions:</span>
                          <span className="ml-2 font-semibold text-green-600">
                            ${scenario.savings_from_reductions.toFixed(2)}/month
                          </span>
                        </div>
                      )}
                      {scenario.months_saved > 0 && (
                        <div>
                          <span className="text-gray-600">Time Saved:</span>
                          <span className="ml-2 font-semibold text-green-600">
                            {scenario.months_saved} months
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {scenarioResult.time_saved_days > 0 && (
                  <p className="text-sm text-green-600 mt-2">
                    You could reach your goal {scenarioResult.time_saved_days} days faster!
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Monte Carlo Tab */}
      {activeTab === 'monte' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Monte Carlo Investment Simulation</h2>
          <p className="text-gray-600 mb-6">
            Project potential investment outcomes using probabilistic modeling
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Initial Investment ($)
              </label>
              <input
                type="number"
                value={monteCarloParams.initial_investment}
                onChange={(e) => setMonteCarloParams({ ...monteCarloParams, initial_investment: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Monthly Contribution ($)
              </label>
              <input
                type="number"
                value={monteCarloParams.monthly_contribution}
                onChange={(e) => setMonteCarloParams({ ...monteCarloParams, monthly_contribution: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Years
              </label>
              <input
                type="number"
                value={monteCarloParams.years}
                onChange={(e) => setMonteCarloParams({ ...monteCarloParams, years: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Expected Return (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={monteCarloParams.expected_return}
                onChange={(e) => setMonteCarloParams({ ...monteCarloParams, expected_return: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Volatility (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={monteCarloParams.volatility}
                onChange={(e) => setMonteCarloParams({ ...monteCarloParams, volatility: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Simulations
              </label>
              <input
                type="number"
                value={monteCarloParams.simulations}
                onChange={(e) => setMonteCarloParams({ ...monteCarloParams, simulations: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <button
            onClick={handleMonteCarlo}
            disabled={loading}
            className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Running Simulation...' : 'Run Monte Carlo Simulation'}
          </button>

          {monteCarloResult && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-3">Simulation Results ({monteCarloResult.simulations} runs)</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">Mean Outcome</div>
                  <div className="text-xl font-bold text-primary-600">
                    ${monteCarloResult.mean_outcome.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">Median Outcome</div>
                  <div className="text-xl font-bold text-primary-600">
                    ${monteCarloResult.median_outcome.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">5th Percentile</div>
                  <div className="text-lg font-semibold text-red-600">
                    ${monteCarloResult.percentile_5.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">95th Percentile</div>
                  <div className="text-lg font-semibold text-green-600">
                    ${monteCarloResult.percentile_95.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">25th Percentile</div>
                  <div className="text-lg font-semibold text-gray-900">
                    ${monteCarloResult.percentile_25.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">75th Percentile</div>
                  <div className="text-lg font-semibold text-gray-900">
                    ${monteCarloResult.percentile_75.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                  </div>
                </div>
              </div>
              <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
                <div className="text-sm text-gray-600">Success Probability (2x return)</div>
                <div className="text-2xl font-bold text-blue-600">
                  {(monteCarloResult.success_probability * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Opportunity Cost Tab */}
      {activeTab === 'opportunity' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Opportunity Cost Calculator</h2>
          <p className="text-gray-600 mb-6">
            See what you could earn by investing instead of spending
          </p>

          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Spending Amount ($)
              </label>
              <input
                type="number"
                step="0.01"
                value={opportunityParams.spending_amount}
                onChange={(e) => setOpportunityParams({ ...opportunityParams, spending_amount: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Horizon (Years)
              </label>
              <input
                type="number"
                step="0.1"
                value={opportunityParams.time_horizon_years}
                onChange={(e) => setOpportunityParams({ ...opportunityParams, time_horizon_years: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Expected Return (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={opportunityParams.expected_return}
                onChange={(e) => setOpportunityParams({ ...opportunityParams, expected_return: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <button
            onClick={handleOpportunityCost}
            disabled={loading}
            className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Calculating...' : 'Calculate Opportunity Cost'}
          </button>

          {opportunityResult && (
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-3">Opportunity Cost Analysis</h3>
              <div className="space-y-3">
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">Spending Amount</div>
                  <div className="text-xl font-bold text-gray-900">${opportunityResult.spending_amount.toFixed(2)}</div>
                </div>
                <div className="p-3 bg-white rounded border">
                  <div className="text-sm text-gray-600">Potential Investment Return</div>
                  <div className="text-xl font-bold text-green-600">
                    ${opportunityResult.potential_investment_return.toFixed(2)}
                  </div>
                </div>
                <div className="p-3 bg-red-50 rounded border border-red-200">
                  <div className="text-sm text-gray-600">Opportunity Cost</div>
                  <div className="text-2xl font-bold text-red-600">
                    ${opportunityResult.opportunity_cost.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    (What you're giving up by spending instead of investing)
                  </div>
                </div>
                <div className="p-3 bg-blue-50 rounded border border-blue-200">
                  <div className="text-sm font-medium text-gray-700">Recommendation</div>
                  <div className="text-sm text-gray-700 mt-1">{opportunityResult.recommendation}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

