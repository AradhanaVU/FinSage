import { useEffect, useState } from 'react'
import { TrendingUp, AlertTriangle, BarChart3 } from 'lucide-react'
import { 
  getSpendingAnalysis, 
  getSpendingForecast, 
  getAnomalies,
  getSpendingPatterns 
} from '../services/api'
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend 
} from 'recharts'

export default function Insights() {
  const [spendingAnalysis, setSpendingAnalysis] = useState([])
  const [forecast, setForecast] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [patterns, setPatterns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadInsights()
  }, [])

  const loadInsights = async () => {
    try {
      setLoading(true)
      const [analysisRes, forecastRes, anomaliesRes, patternsRes] = await Promise.all([
        getSpendingAnalysis(),
        getSpendingForecast(30),
        getAnomalies(30),
        getSpendingPatterns(90),
      ])
      
      setSpendingAnalysis(analysisRes.data)
      setForecast(forecastRes.data)
      setAnomalies(anomaliesRes.data)
      setPatterns(patternsRes.data)
    } catch (error) {
      console.error('Error loading insights:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-600">Loading insights...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Insights</h1>
        <p className="text-gray-600 mt-1">Intelligent analysis of your spending patterns</p>
      </div>

      {/* Spending Analysis */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2 text-primary-600" />
          Spending Analysis by Category
        </h2>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={spendingAnalysis}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="total_amount" fill="#0ea5e9" name="Total Amount" />
            <Bar dataKey="average_amount" fill="#38bdf8" name="Average Amount" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Forecast */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <TrendingUp className="w-5 h-5 mr-2 text-primary-600" />
          30-Day Spending Forecast
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={forecast}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="predicted_amount" 
              stroke="#0ea5e9" 
              name="Predicted"
            />
            <Line 
              type="monotone" 
              dataKey="confidence_interval_lower" 
              stroke="#94a3b8" 
              strokeDasharray="5 5"
              name="Lower Bound"
            />
            <Line 
              type="monotone" 
              dataKey="confidence_interval_upper" 
              stroke="#94a3b8" 
              strokeDasharray="5 5"
              name="Upper Bound"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Anomalies */}
      {anomalies.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-yellow-500" />
            Detected Anomalies
          </h2>
          <div className="space-y-3">
            {anomalies.map((anomaly, idx) => (
              <div
                key={idx}
                className="p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded"
              >
                <p className="font-semibold text-gray-900">{anomaly.reason}</p>
                <p className="text-sm text-gray-600 mt-1">
                  Anomaly Score: {anomaly.anomaly_score} | Severity: {anomaly.severity}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Patterns */}
      {patterns.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Spending Patterns</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {patterns.map((pattern, idx) => (
              <div
                key={idx}
                className="p-4 bg-gray-50 rounded-lg"
              >
                <p className="font-semibold text-gray-900">{pattern.category}</p>
                <p className="text-sm text-gray-600 mt-1">{pattern.description}</p>
                <p className="text-xs text-gray-500 mt-2">
                  Type: {pattern.pattern_type} | Impact: {pattern.impact}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}


