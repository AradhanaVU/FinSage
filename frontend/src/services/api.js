import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL || undefined,
  headers: {
    'Content-Type': 'application/json',
  },
})

const TOKEN_KEY = 'finsage_token'
const USER_KEY = 'finsage_user'

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setAuthSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuthSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

api.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuthSession()
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth
export const register = (data) => api.post('/api/auth/register', data)

export const login = (username, password) =>
  api.post('/api/auth/login/json', { username, password })

export const loginForm = (username, password) => {
  const body = new URLSearchParams()
  body.append('username', username)
  body.append('password', password)
  return api.post('/api/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
}

export const getMe = () => api.get('/api/auth/me')

// Transactions
export const getTransactions = (params = {}) =>
  api.get('/api/transactions/', { params })

export const createTransaction = (data) =>
  api.post('/api/transactions/', data)

export const updateTransaction = (id, data) =>
  api.put(`/api/transactions/${id}`, data)

export const assignTransactionCategory = (id, category, subcategory = null) =>
  api.patch(`/api/transactions/${id}/category`, { category, subcategory })

export const getCategories = (transactionType) =>
  api.get('/api/transactions/categories', {
    params: transactionType ? { transaction_type: transactionType } : {},
  })

export const suggestCategory = (description, amount = 0, transactionType) =>
  api.get('/api/transactions/suggest', {
    params: {
      description,
      amount,
      transaction_type: transactionType,
    },
  })

export const deleteTransaction = (id) =>
  api.delete(`/api/transactions/${id}`)

// Goals
export const getGoals = (recalculate = false) =>
  api.get('/api/goals/', { params: { recalculate } })

export const createGoal = (data) =>
  api.post('/api/goals/', data)

export const updateGoal = (id, data) =>
  api.put(`/api/goals/${id}`, data)

export const updateGoalProgress = (id, amount) =>
  api.patch(`/api/goals/${id}/progress`, null, { params: { amount } })

export const deleteGoal = (id) =>
  api.delete(`/api/goals/${id}`)

// AI Insights
export const getSpendingAnalysis = (params = {}) =>
  api.get('/api/ai/spending-analysis', { params })

export const getSpendingPatterns = (days = 90) =>
  api.get('/api/ai/patterns', { params: { days } })

export const getSpendingForecast = (daysAhead = 30) =>
  api.get('/api/ai/forecast', { params: { days_ahead: daysAhead } })

export const getAnomalies = (days = 30) =>
  api.get('/api/ai/anomalies', { params: { days } })

// Chat
export const sendChatMessage = (message, context = null) =>
  api.post('/api/chat/', { message, context })

// Alerts
export const getAlerts = (unreadOnly = false) =>
  api.get('/api/alerts/', { params: { unread_only: unreadOnly } })

export const generateAlerts = () =>
  api.post('/api/alerts/generate')

export const markAlertRead = (id) =>
  api.patch(`/api/alerts/${id}/read`)

export const deleteAlert = (id) =>
  api.delete(`/api/alerts/${id}`)

// Simulations
export const simulateGoalScenario = (goalId, reductionPercentages) =>
  api.post(`/api/simulations/goal-scenario?goal_id=${goalId}`, {
    reduction_percentages: reductionPercentages,
  })

export const monteCarloSimulation = (params) =>
  api.post('/api/simulations/monte-carlo', params)

export const calculateOpportunityCost = (spendingAmount, timeHorizonYears = 1, expectedReturn = 0.07) =>
  api.post('/api/simulations/opportunity-cost', null, {
    params: {
      spending_amount: spendingAmount,
      time_horizon_years: timeHorizonYears,
      expected_return: expectedReturn,
    },
  })

// Receipts
export const uploadReceipt = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/api/receipts/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export const getSubscriptions = () =>
  api.get('/api/receipts/subscriptions')

// Risk Analysis
export const getCashFlowRisk = (horizonDays = 30) =>
  api.get('/api/risk/cashflow-risk', { params: { horizon_days: horizonDays } })

export const stressTestCashFlow = (scenarios, horizonDays = 30) =>
  api.post(`/api/risk/stress-test?horizon_days=${horizonDays}`, scenarios)

export default api
