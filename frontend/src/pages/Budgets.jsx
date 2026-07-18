import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency } from '../utils/format';
import api from '../services/api';
import {
  Wallet,
  AlertCircle,
  CheckCircle,
  Plus,
  Loader2,
} from 'lucide-react';

export const Budgets = () => {
  const { user } = useAuth();
  
  // Data state
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Form input state
  const [category, setCategory] = useState('Food');
  const [amount, setAmount] = useState('');
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7)); // YYYY-MM
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const categories = ['Food', 'Rent', 'Transport', 'Entertainment', 'Utilities', 'Shopping', 'Healthcare', 'Other'];

  const fetchBudgetsAndSpent = async () => {
    try {
      setLoading(true);
      // Fetch stats which computes spent vs budget limits dynamically
      const res = await api.get(`/dashboard?month=${month}`);
      if (res.data.success) {
        setBudgets(res.data.data.budgetProgress);
      }
    } catch (err) {
      setError('Failed to load budget progress logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBudgetsAndSpent();
  }, [month]);

  const handleSetBudget = async (e) => {
    e.preventDefault();
    if (!amount) return;

    setSubmitting(true);
    setSuccessMsg('');
    setError('');
    
    try {
      const res = await api.post('/budgets', {
        category,
        amount: parseFloat(amount),
        month,
      });

      if (res.data.success) {
        setSuccessMsg(`Budget limits for ${category} successfully configured!`);
        setAmount('');
        fetchBudgetsAndSpent(); // Refresh progress
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update budget limit.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* HEADER SECTION WITH SET/UPDATE BUDGET FORM */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Form to set budget */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-100 flex items-center">
            <Wallet className="h-5 w-5 text-brand-500 mr-2" /> Set Category Budget
          </h3>
          <p className="text-slate-450 text-xs leading-normal">
            Establish or overwrite spending limit goals for standard budget categories.
          </p>

          {successMsg && (
            <div className="p-3 rounded-lg text-xs bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 text-emerald-700 dark:text-emerald-400 flex items-center">
              <CheckCircle className="h-4 w-4 mr-1.5 flex-shrink-0" /> {successMsg}
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSetBudget} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="form-input"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                Monthly Cap ({user?.currency})
              </label>
              <input
                type="number"
                step="0.01"
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="form-input"
                required
                min="0.01"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                Target Month
              </label>
              <input
                type="month"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
                className="form-input"
                required
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center rounded-xl bg-brand-500 hover:bg-brand-600 py-3 text-sm font-semibold text-white transition-all shadow-md shadow-brand-500/10 cursor-pointer"
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving Limit...
                </>
              ) : (
                'Configure Limit'
              )}
            </button>
          </form>
        </div>

        {/* Display budget progress cards */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
              Budget Status Summary ({month})
            </h3>
            <input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="form-input text-xs py-1.5 max-w-[140px]"
            />
          </div>

          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
            </div>
          ) : budgets.length === 0 ? (
            <div className="py-20 text-center text-sm text-slate-400">
              No budgets established for this month. Use the builder on the left to set categories limits.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {budgets.map((bp) => {
                const pct = Math.min(100, Math.round((bp.spent / bp.limit) * 100));
                return (
                  <div
                    key={bp.category}
                    className={`p-4 rounded-xl border transition-all ${
                      bp.exceeded
                        ? 'bg-red-50/20 border-red-100 dark:bg-red-950/5 dark:border-red-900/30'
                        : pct >= 80
                        ? 'bg-amber-50/20 border-amber-100 dark:bg-amber-950/5 dark:border-amber-900/30'
                        : 'bg-slate-50/50 border-slate-100 dark:bg-slate-850/20 dark:border-slate-800/50'
                    }`}
                  >
                    <div className="flex justify-between items-center text-sm font-semibold">
                      <span className="text-slate-800 dark:text-slate-200">{bp.category}</span>
                      <span className="text-slate-500 dark:text-slate-400">{pct}%</span>
                    </div>
                    
                    <div className="flex justify-between items-center text-xs text-slate-400 mt-1">
                      <span>Spent: {formatCurrency(bp.spent, user?.currency)}</span>
                      <span>Cap: {formatCurrency(bp.limit, user?.currency)}</span>
                    </div>

                    <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full mt-3 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          bp.exceeded
                            ? 'bg-red-500'
                            : pct >= 80
                            ? 'bg-amber-500'
                            : 'bg-brand-500'
                        }`}
                        style={{ width: `${pct}%` }}
                      ></div>
                    </div>

                    <div className="flex justify-between items-center mt-3 text-xs">
                      {bp.exceeded ? (
                        <span className="text-red-500 font-semibold flex items-center">
                          <AlertCircle className="h-3 w-3 mr-1" /> Over by {formatCurrency(bp.spent - bp.limit, user?.currency)}
                        </span>
                      ) : (
                        <span className="text-emerald-500 font-semibold">
                          Remaining: {formatCurrency(bp.remaining, user?.currency)}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
