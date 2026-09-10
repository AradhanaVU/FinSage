export const DEFAULT_CATEGORIES = [
  'Income',
  'Investment Income',
  'Housing',
  'Bills & Utilities',
  'Food & Dining',
  'Groceries',
  'Transportation',
  'Shopping',
  'Entertainment',
  'Subscriptions',
  'Healthcare',
  'Fitness & Wellness',
  'Personal Care',
  'Education',
  'Insurance',
  'Banking & Fees',
  'Investments',
  'Debt & Loans',
  'Travel',
  'Gifts & Donations',
  'Business Expenses',
  'Kids & Family',
  'Pets',
  'Taxes',
  'Other',
]

export const CATEGORY_STYLES = {
  Income: 'bg-emerald-100 text-emerald-800',
  'Investment Income': 'bg-emerald-100 text-emerald-800',
  Housing: 'bg-amber-100 text-amber-800',
  'Bills & Utilities': 'bg-yellow-100 text-yellow-800',
  'Food & Dining': 'bg-orange-100 text-orange-800',
  Groceries: 'bg-lime-100 text-lime-800',
  Transportation: 'bg-sky-100 text-sky-800',
  Shopping: 'bg-pink-100 text-pink-800',
  Entertainment: 'bg-violet-100 text-violet-800',
  Subscriptions: 'bg-indigo-100 text-indigo-800',
  Healthcare: 'bg-rose-100 text-rose-800',
  'Fitness & Wellness': 'bg-teal-100 text-teal-800',
  'Personal Care': 'bg-fuchsia-100 text-fuchsia-800',
  Education: 'bg-blue-100 text-blue-800',
  Insurance: 'bg-slate-200 text-slate-800',
  'Banking & Fees': 'bg-gray-200 text-gray-800',
  Investments: 'bg-cyan-100 text-cyan-800',
  'Debt & Loans': 'bg-red-100 text-red-800',
  Travel: 'bg-purple-100 text-purple-800',
  'Gifts & Donations': 'bg-green-100 text-green-800',
  'Business Expenses': 'bg-stone-200 text-stone-800',
  'Kids & Family': 'bg-orange-100 text-orange-900',
  Pets: 'bg-amber-100 text-amber-900',
  Taxes: 'bg-neutral-200 text-neutral-800',
  Other: 'bg-gray-100 text-gray-700',
  Uncategorized: 'bg-gray-100 text-gray-700',
}

export function categoryClass(category) {
  return CATEGORY_STYLES[category] || 'bg-gray-100 text-gray-700'
}

export function money(value) {
  const amount = Number.isFinite(value) ? value : 0
  return amount.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  })
}
