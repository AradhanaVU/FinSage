import { useEffect, useState } from 'react'
import { Bell, AlertCircle, AlertTriangle, Info, X, RefreshCw, CheckCircle, Trash2 } from 'lucide-react'
import { getAlerts, generateAlerts, markAlertRead, deleteAlert } from '../services/api'
import { format } from 'date-fns'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [filter, setFilter] = useState('all') // 'all', 'unread', 'read'

  useEffect(() => {
    loadAlerts()
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadAlerts, 30000)
    return () => clearInterval(interval)
  }, [filter])

  const loadAlerts = async () => {
    try {
      setLoading(true)
      const unreadOnly = filter === 'unread'
      const response = await getAlerts(unreadOnly)
      setAlerts(response.data)
    } catch (error) {
      console.error('Error loading alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateAlerts = async () => {
    try {
      setGenerating(true)
      const response = await generateAlerts()
      const generated = response.data.generated || 0
      const skipped = response.data.skipped || 0
      let message = `Generated ${generated} new alert${generated !== 1 ? 's' : ''}!`
      if (skipped > 0) {
        message += ` (Skipped ${skipped} duplicate${skipped !== 1 ? 's' : ''})`
      }
      alert(message)
      loadAlerts()
    } catch (error) {
      console.error('Error generating alerts:', error)
      alert(`Failed to generate alerts: ${error.response?.data?.detail || error.message}`)
    } finally {
      setGenerating(false)
    }
  }

  const handleMarkRead = async (alertId) => {
    try {
      await markAlertRead(alertId)
      loadAlerts()
    } catch (error) {
      console.error('Error marking alert as read:', error)
    }
  }

  const handleDelete = async (alertId) => {
    if (!confirm('Are you sure you want to delete this alert?')) return
    
    try {
      await deleteAlert(alertId)
      loadAlerts()
    } catch (error) {
      console.error('Error deleting alert:', error)
    }
  }

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="w-5 h-5 text-red-600" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />
      case 'info':
        return <Info className="w-5 h-5 text-blue-600" />
      default:
        return <Bell className="w-5 h-5 text-gray-600" />
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-200'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200'
      case 'info':
        return 'bg-blue-50 border-blue-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const unreadCount = alerts.filter(a => !a.read).length

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alerts & Notifications</h1>
          <p className="text-gray-600 mt-1">Stay informed about your financial health</p>
        </div>
        <button
          onClick={handleGenerateAlerts}
          disabled={generating}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <RefreshCw className={`w-5 h-5 mr-2 ${generating ? 'animate-spin' : ''}`} />
          {generating ? 'Generating...' : 'Generate Alerts'}
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2 border-b border-gray-200">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 font-medium transition-colors ${
            filter === 'all'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          All ({alerts.length})
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`px-4 py-2 font-medium transition-colors ${
            filter === 'unread'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Unread ({unreadCount})
        </button>
        <button
          onClick={() => setFilter('read')}
          className={`px-4 py-2 font-medium transition-colors ${
            filter === 'read'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Read ({alerts.length - unreadCount})
        </button>
      </div>

      {/* Alerts List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading alerts...</p>
        </div>
      ) : alerts.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <Bell className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">No alerts found</p>
          <p className="text-gray-500 mt-2">Click "Generate Alerts" to analyze your finances and create personalized alerts</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-6 rounded-lg border-2 ${getSeverityColor(alert.severity)} ${
                !alert.read ? 'ring-2 ring-primary-200' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="mt-1">
                    {getSeverityIcon(alert.severity)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{alert.title}</h3>
                      {!alert.read && (
                        <span className="px-2 py-1 text-xs font-semibold bg-primary-600 text-white rounded-full">
                          New
                        </span>
                      )}
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                        alert.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-gray-700 mb-3">{alert.message}</p>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>{format(new Date(alert.created_at), 'MMM d, yyyy h:mm a')}</span>
                      <span className="capitalize">{alert.alert_type?.replace('_', ' ')}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  {!alert.read && (
                    <button
                      onClick={() => handleMarkRead(alert.id)}
                      className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                      title="Mark as read"
                    >
                      <CheckCircle className="w-5 h-5" />
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(alert.id)}
                    className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete alert"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

