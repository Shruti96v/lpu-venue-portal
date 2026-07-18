import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatDate } from '../utils/format';
import api from '../services/api';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Briefcase,
  PlusCircle,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp as SavingsIcon,
  X,
  Plus,
  Loader2,
} from 'lucide-react';

export const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Quick Transaction Modal State
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('expense'); // 'income' or 'expense'
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await api.get('/dashboard');
      if (res.data.success) {
        setStats(res.data.data);
      }
    } catch (err) {
      setError('Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleOpenModal = (type) => {
    setModalType(type);
    // Reset form
    setAmount('');
    setCategory(type === 'income' ? 'Salary' : 'Food');
    setDate(new Date().toISOString().split('T')[0]);
    setDescription('');
    setShowModal(true);
  };

  const handleAddTransaction = async (e) => {
    e.preventDefault();
    if (!amount || !category) return;

    setSubmitting(true);
    try {
      const endpoint = modalType === 'income' ? '/income' : '/expenses';
      const res = await api.post(endpoint, {
        amount: parseFloat(amount),
        category,
        date: new Date(date),
        description,
      });

      if (res.data.success) {
        setShowModal(false);
        fetchStats(); // Refresh dashboard
      }
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to add transaction');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-200 border-t-brand-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-red-50 text-red-700 border border-red-100 text-center">
        {error}
        <button onClick={fetchStats} className="block mx-auto mt-2 text-sm font-semibold underline">
          Try Again
        </button>
      </div>
    );
  }

  const { allTime, monthly, recentTransactions, categoryBreakdown, budgetProgress, savingsGoals } = stats;

  const categories = modalType === 'income' 
    ? ['Salary', 'Freelancing', 'Investments', 'Other'] 
    : ['Food', 'Rent', 'Transport', 'Entertainment', 'Utilities', 'Shopping', 'Healthcare', 'Other'];

  return (
    <div className="space-y-6">
      {/* GREETING HERO PANEL */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            Welcome back, {user?.name}!
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Here's a review of your financial accounts and targets for this month.
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex space-x-3">
          <button
            onClick={() => handleOpenModal('income')}
            className="flex items-center justify-center rounded-xl bg-emerald-500 hover:bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white transition-all shadow-md shadow-emerald-500/10 cursor-pointer"
          >
            <Plus className="h-4 w-4 mr-1.5" /> Record Income
          </button>
          <button
            onClick={() => handleOpenModal('expense')}
            className="flex items-center justify-center rounded-xl bg-brand-500 hover:bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white transition-all shadow-md shadow-brand-500/10 cursor-pointer"
          >
            <Plus className="h-4 w-4 mr-1.5" /> Log Expense
          </button>
        </div>
      </div>

      {/* CORE FINANCIAL METRIC CARDS */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Balance Card */}
        <div className="relative overflow-hidden bg-gradient-to-br from-brand-500 to-indigo-600 p-6 rounded-2xl text-white shadow-lg shadow-brand-500/10">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <DollarSign className="h-24 w-24" />
          </div>
          <span className="text-xs font-medium text-brand-100 uppercase tracking-wider">Total Net Balance</span>
          <h3 className="text-2xl font-bold mt-2">{formatCurrency(allTime.balance, user?.currency)}</h3>
          <div className="flex items-center mt-4 text-brand-100 text-xs">
            <span className="bg-white/10 px-2 py-0.5 rounded-full mr-2 font-medium">All Time Net</span>
            <span>Total flow summary</span>
          </div>
        </div>

        {/* Monthly Income Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm relative">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Income This Month</span>
          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">{formatCurrency(monthly.income, user?.currency)}</h3>
          <div className="flex items-center mt-4 text-emerald-500 text-xs font-semibold">
            <ArrowUpRight className="h-4 w-4 mr-1" />
            <span>Active earnings</span>
          </div>
          <div className="absolute top-6 right-6 h-10 w-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 flex items-center justify-center text-emerald-500">
            <TrendingUp className="h-5 w-5" />
          </div>
        </div>

        {/* Monthly Expenses Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm relative">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Expenses This Month</span>
          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">{formatCurrency(monthly.expense, user?.currency)}</h3>
          <div className="flex items-center mt-4 text-red-500 text-xs font-semibold">
            <ArrowDownRight className="h-4 w-4 mr-1" />
            <span>Active spending</span>
          </div>
          <div className="absolute top-6 right-6 h-10 w-10 rounded-xl bg-red-50 dark:bg-red-950/20 flex items-center justify-center text-red-500">
            <TrendingDown className="h-5 w-5" />
          </div>
        </div>

        {/* Monthly Savings Card */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm relative">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Net Monthly Savings</span>
          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">{formatCurrency(monthly.savings, user?.currency)}</h3>
          <div className="flex items-center mt-4 text-indigo-500 text-xs font-semibold">
            <SavingsIcon className="h-4 w-4 mr-1" />
            <span>
              {monthly.income > 0 ? Math.round((monthly.savings / monthly.income) * 100) : 0}% savings rate
            </span>
          </div>
          <div className="absolute top-6 right-6 h-10 w-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/20 flex items-center justify-center text-indigo-500">
            <Wallet className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* MID SECTION SPLIT GRID */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* LEFT COLUMN: RECENT TRANSACTIONS (Span 2) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">Recent Transactions</h3>
            <button
              onClick={() => fetchStats()}
              className="text-xs text-brand-500 font-semibold hover:text-brand-600 transition-all cursor-pointer"
            >
              Refresh Table
            </button>
          </div>
          
          <div className="overflow-x-auto">
            {recentTransactions.length === 0 ? (
              <div className="py-12 text-center text-sm text-slate-400">
                No transactions log yet. Click record income or log expense above to start.
              </div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-100 dark:border-slate-850 text-xs text-slate-400 uppercase font-semibold">
                    <th className="py-3 pr-4">Details</th>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 pl-4 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-850 text-sm">
                  {recentTransactions.map((t) => (
                    <tr key={t._id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/20 transition-colors">
                      <td className="py-3.5 pr-4">
                        <div className="font-semibold text-slate-850 dark:text-slate-200">
                          {t.description || 'No description'}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">{formatDate(t.date)}</td>
                      <td className="py-3.5 px-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-650 dark:text-slate-350">
                          {t.category}
                        </span>
                      </td>
                      <td className={`py-3.5 pl-4 text-right font-bold ${
                        t.type === 'income' ? 'text-emerald-500' : 'text-red-500'
                      }`}>
                        {t.type === 'income' ? '+' : '-'} {formatCurrency(t.amount, user?.currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: BUDGET & GOAL METRIC METERS */}
        <div className="space-y-6">
          {/* Budget Limit Progress Bars */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">Monthly Budget Limits</h3>
            
            {budgetProgress.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400">
                No monthly budgets set yet. Configure budget targets to track spending progress.
              </div>
            ) : (
              <div className="space-y-4">
                {budgetProgress.slice(0, 4).map((bp) => {
                  const pct = Math.min(100, Math.round((bp.spent / bp.limit) * 100));
                  return (
                    <div key={bp.category} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-700 dark:text-slate-300">{bp.category}</span>
                        <span className="text-slate-400">
                          {formatCurrency(bp.spent, user?.currency)} / <span className="font-medium text-slate-500">{formatCurrency(bp.limit, user?.currency)}</span>
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            bp.exceeded 
                              ? 'bg-red-500 shadow-sm shadow-red-500/20' 
                              : pct >= 80 
                              ? 'bg-amber-500 shadow-sm shadow-amber-500/20' 
                              : 'bg-brand-500 shadow-sm shadow-brand-500/20'
                          }`}
                          style={{ width: `${pct}%` }}
                        ></div>
                      </div>
                      {bp.exceeded && (
                        <div className="flex items-center text-[10px] text-red-500 font-semibold">
                          <AlertTriangle className="h-3 w-3 mr-1" /> Budget exceeded by {formatCurrency(bp.spent - bp.limit, user?.currency)}!
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Goal Tracker Card */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">Savings Goals Status</h3>
            <div className="flex items-center justify-between bg-brand-50/50 dark:bg-slate-850/50 p-4 rounded-xl">
              <div>
                <span className="text-xs text-slate-450 block">Saved Current Goal Balance</span>
                <span className="text-lg font-bold text-slate-800 dark:text-slate-200 mt-1 block">
                  {formatCurrency(savingsGoals.current, user?.currency)}
                </span>
                <span className="text-[10px] text-slate-400 block mt-1">
                  Target: {formatCurrency(savingsGoals.target, user?.currency)}
                </span>
              </div>
              <div className="relative h-14 w-14 flex items-center justify-center rounded-full bg-brand-100 dark:bg-slate-800 text-brand-600 dark:text-brand-400 font-bold text-sm">
                {savingsGoals.percentage}%
              </div>
            </div>
            {savingsGoals.count === 0 && (
              <div className="text-center text-xs text-slate-400 py-2">
                No savings goals added yet. Create targets to save money.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* QUICK TRANSACTION MODAL POPUP */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-2xl border border-slate-100 dark:border-slate-850 shadow-2xl p-6 relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 capitalize">
              {modalType === 'income' ? 'Record Income Flow' : 'Log New Expense'}
            </h3>
            
            <form onSubmit={handleAddTransaction} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Amount ({user?.currency})
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="form-input"
                  placeholder="0.00"
                  required
                  min="0.01"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="form-input"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="form-input"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="form-input"
                  placeholder="e.g. Weekly grocery trip or consultant payout"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className={`flex w-full items-center justify-center rounded-xl py-3 text-sm font-semibold text-white transition-all shadow-md cursor-pointer ${
                  modalType === 'income'
                    ? 'bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/10'
                    : 'bg-brand-500 hover:bg-brand-600 shadow-brand-500/10'
                }`}
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Recording...
                  </>
                ) : (
                  modalType === 'income' ? 'Save Income Log' : 'Save Expense Log'
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
