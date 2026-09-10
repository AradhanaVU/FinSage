import { useEffect, useMemo, useState } from 'react'
import { Plus, Search, Upload, Camera, Sparkles } from 'lucide-react'
import {
  getTransactions,
  createTransaction,
  deleteTransaction,
  uploadReceipt,
  getCategories,
  suggestCategory,
  assignTransactionCategory,
} from '../services/api'
import { format } from 'date-fns'
import { categoryClass, money, DEFAULT_CATEGORIES } from '../utils/categories'

const emptyForm = {
  amount: '',
  description: '',
  transaction_type: 'expense',
  merchant: '',
  date: new Date().toISOString().split('T')[0],
  category: '',
}

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [categories, setCategories] = useState(DEFAULT_CATEGORIES)
  const [formCategories, setFormCategories] = useState(DEFAULT_CATEGORIES)
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showReceiptModal, setShowReceiptModal] = useState(false)
  const [uploadingReceipt, setUploadingReceipt] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [formData, setFormData] = useState(emptyForm)
  const [suggestion, setSuggestion] = useState(null)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [savingId, setSavingId] = useState(null)

  useEffect(() => {
    loadTransactions()
    loadCategories()
  }, [])

  useEffect(() => {
    loadFormCategories(formData.transaction_type)
  }, [formData.transaction_type])

  useEffect(() => {
    if (!showAddModal || !formData.description.trim() || formData.category) {
      if (!formData.description.trim()) setSuggestion(null)
      return
    }
    const handle = setTimeout(async () => {
      try {
        const res = await suggestCategory(
          formData.description,
          parseFloat(formData.amount) || 0,
          formData.transaction_type
        )
        setSuggestion(res.data)
      } catch (error) {
        console.error('Error suggesting category:', error)
      }
    }, 280)
    return () => clearTimeout(handle)
  }, [formData.description, formData.amount, formData.transaction_type, formData.category, showAddModal])

  const loadCategories = async () => {
    try {
      const response = await getCategories()
      setCategories(response.data.categories || [])
    } catch (error) {
      console.error('Error loading categories:', error)
    }
  }

  const loadFormCategories = async (transactionType) => {
    try {
      const response = await getCategories(transactionType)
      setFormCategories(response.data.categories || [])
    } catch (error) {
      console.error('Error loading categories:', error)
    }
  }

  const loadTransactions = async () => {
    try {
      setLoading(true)
      const response = await getTransactions({ limit: 500 })
      setTransactions(response.data)
    } catch (error) {
      console.error('Error loading transactions:', error)
    } finally {
      setLoading(false)
    }
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return transactions.filter((txn) => {
      if (typeFilter !== 'all' && txn.transaction_type !== typeFilter) return false
      if (categoryFilter !== 'all' && txn.category !== categoryFilter) return false
      if (!q) return true
      return (
        (txn.description || '').toLowerCase().includes(q) ||
        (txn.merchant || '').toLowerCase().includes(q) ||
        (txn.category || '').toLowerCase().includes(q)
      )
    })
  }, [transactions, search, typeFilter, categoryFilter])

  const totals = useMemo(() => {
    const income = filtered
      .filter((t) => t.transaction_type === 'income')
      .reduce((sum, t) => sum + Math.abs(t.amount), 0)
    const expenses = filtered
      .filter((t) => t.transaction_type === 'expense')
      .reduce((sum, t) => sum + Math.abs(t.amount), 0)
    return { income, expenses, net: income - expenses }
  }, [filtered])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const transactionData = {
        amount: parseFloat(formData.amount),
        description: formData.description,
        transaction_type: formData.transaction_type,
        merchant: formData.merchant || null,
        date: new Date(formData.date).toISOString(),
      }
      if (formData.category) {
        transactionData.category = formData.category
      }
      await createTransaction(transactionData)
      setShowAddModal(false)
      setFormData({ ...emptyForm, date: new Date().toISOString().split('T')[0] })
      setSuggestion(null)
      loadTransactions()
    } catch (error) {
      console.error('Error creating transaction:', error)
      alert('Failed to create transaction')
    }
  }

  const handleCategoryChange = async (id, category) => {
    try {
      setSavingId(id)
      const response = await assignTransactionCategory(id, category)
      setTransactions((prev) => prev.map((txn) => (txn.id === id ? response.data : txn)))
    } catch (error) {
      console.error('Error assigning category:', error)
      alert('Could not update category')
    } finally {
      setSavingId(null)
    }
  }

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this transaction?')) {
      try {
        await deleteTransaction(id)
        loadTransactions()
      } catch (error) {
        console.error('Error deleting transaction:', error)
        alert('Failed to delete transaction')
      }
    }
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file)
      const reader = new FileReader()
      reader.onloadend = () => setPreviewUrl(reader.result)
      reader.readAsDataURL(file)
    } else {
      alert('Please select an image file')
    }
  }

  const handleReceiptUpload = async () => {
    if (!selectedFile) {
      alert('Please select a receipt image first')
      return
    }
    try {
      setUploadingReceipt(true)
      const response = await uploadReceipt(selectedFile)
      alert(`Receipt processed! Created transaction: ${response.data.transaction.description}`)
      setShowReceiptModal(false)
      setSelectedFile(null)
      setPreviewUrl(null)
      loadTransactions()
    } catch (error) {
      console.error('Error uploading receipt:', error)
      const errorMsg = error.response?.data?.detail || 'Failed to process receipt. Make sure Tesseract OCR is installed.'
      alert(errorMsg)
    } finally {
      setUploadingReceipt(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12 text-gray-600">Loading transactions...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Transactions</h1>
          <p className="text-gray-600 mt-1">Review, recategorize, and add spending in one place.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowReceiptModal(true)}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Camera className="w-5 h-5 mr-2" />
            Scan Receipt
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-5 h-5 mr-2" />
            Add Transaction
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SummaryCard label="Income" value={money(totals.income)} tone="text-green-700" />
        <SummaryCard label="Expenses" value={money(totals.expenses)} tone="text-red-700" />
        <SummaryCard label="Net" value={money(totals.net)} tone={totals.net >= 0 ? 'text-green-700' : 'text-red-700'} />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex flex-col gap-3 md:flex-row md:items-center">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
          <input
            type="search"
            placeholder="Search description, merchant, or category"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg"
        >
          <option value="all">All types</option>
          <option value="expense">Expenses</option>
          <option value="income">Income</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg"
        >
          <option value="all">All categories</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {filtered.length > 0 ? (
              filtered.map((txn) => (
                <tr key={txn.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {format(new Date(txn.date), 'MMM dd, yyyy')}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div className="font-medium">{txn.description}</div>
                    {txn.merchant && <div className="text-xs text-gray-500">{txn.merchant}</div>}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1 min-w-[180px]">
                      <select
                        value={txn.category || 'Other'}
                        disabled={savingId === txn.id}
                        onChange={(e) => handleCategoryChange(txn.id, e.target.value)}
                        className={`px-2 py-1 text-xs font-medium rounded-lg border-0 cursor-pointer ${categoryClass(txn.category || 'Other')}`}
                      >
                        {categories.map((cat) => (
                          <option key={cat} value={cat}>{cat}</option>
                        ))}
                      </select>
                      <span className="text-[11px] text-gray-500">
                        {txn.ai_categorized
                          ? `Suggested · ${Math.round((txn.confidence_score || 0) * 100)}% sure`
                          : 'Assigned by you'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      txn.transaction_type === 'income'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {txn.transaction_type}
                    </span>
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-semibold ${
                    txn.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {txn.transaction_type === 'income' ? '+' : '-'}{money(Math.abs(txn.amount))}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onClick={() => handleDelete(txn.id)} className="text-red-600 hover:text-red-900">
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                  No matching transactions. Try a different filter or add one.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-1">Add Transaction</h2>
            <p className="text-sm text-gray-500 mb-4">Leave category on Auto and we will suggest one. You can always change it later.</p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={formData.transaction_type}
                  onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value, category: '' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  type="text"
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Auto-suggest</option>
                  {formCategories.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                {!formData.category && suggestion && (
                  <div className="mt-2 flex items-start gap-2 text-sm bg-primary-50 text-primary-800 rounded-lg p-3">
                    <Sparkles className="w-4 h-4 mt-0.5 shrink-0" />
                    <div>
                      <p>
                        Suggested <span className="font-semibold">{suggestion.category}</span>
                        {suggestion.confidence != null && (
                          <span> ({Math.round(suggestion.confidence * 100)}% confidence)</span>
                        )}
                      </p>
                      {suggestion.matched_phrases?.length > 0 && (
                        <p className="text-xs text-primary-700 mt-1">
                          Matched: {suggestion.matched_phrases.slice(0, 3).join(', ')}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                <input
                  type="date"
                  required
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Merchant (optional)</label>
                <input
                  type="text"
                  value={formData.merchant}
                  onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                  Add Transaction
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false)
                    setSuggestion(null)
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showReceiptModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
              <Camera className="w-6 h-6 mr-2 text-green-600" />
              Scan Receipt
            </h2>
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                {previewUrl ? (
                  <div>
                    <img src={previewUrl} alt="Receipt preview" className="max-h-64 mx-auto rounded mb-3" />
                    <p className="text-sm text-gray-600">{selectedFile?.name}</p>
                  </div>
                ) : (
                  <div>
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                    <p className="text-gray-600 mb-2">Upload a receipt image</p>
                    <p className="text-xs text-gray-500">JPG, PNG (Max 10MB)</p>
                  </div>
                )}
                <input type="file" accept="image/*" onChange={handleFileSelect} className="hidden" id="receipt-upload" />
                <label
                  htmlFor="receipt-upload"
                  className="mt-3 inline-block px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 cursor-pointer"
                >
                  {previewUrl ? 'Change Image' : 'Select Image'}
                </label>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
                We read the merchant and total, then suggest a category. You can correct the category on the transactions list.
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleReceiptUpload}
                  disabled={!selectedFile || uploadingReceipt}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {uploadingReceipt ? 'Processing...' : 'Process Receipt'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowReceiptModal(false)
                    setSelectedFile(null)
                    setPreviewUrl(null)
                  }}
                  disabled={uploadingReceipt}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function SummaryCard({ label, value, tone }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${tone}`}>{value}</p>
    </div>
  )
}
