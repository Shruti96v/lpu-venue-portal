import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatDate } from '../utils/format';
import api from '../services/api';
import {
  Target,
  Plus,
  Trash2,
  Calendar,
  AlertCircle,
  CheckCircle2,
  ArrowUpRight,
  X,
  Loader2,
} from 'lucide-react';

export const Goals = () => {
  const { user } = useAuth();
  
  // Data state
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState(null);
  
  // Create Goal fields
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [currentAmount, setCurrentAmount] = useState('');
  const [deadline, setDeadline] = useState('');
  
  // Update progress fields
  const [addedAmount, setAddedAmount] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchGoals = async () => {
    try {
      setLoading(true);
      const res = await api.get('/goals');
      if (res.data.success) {
        setGoals(res.data.data);
      }
    } catch (err) {
      console.error('Failed to load goals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGoals();
  }, []);

  const handleCreateGoal = async (e) => {
    e.preventDefault();
    if (!name || !targetAmount || !deadline) return;

    setSubmitting(true);
    try {
      const res = await api.post('/goals', {
        name,
        targetAmount: parseFloat(targetAmount),
        currentAmount: parseFloat(currentAmount) || 0,
        deadline: new Date(deadline),
      });

      if (res.data.success) {
        setShowAddModal(false);
        // Reset form
        setName('');
        setTargetAmount('');
        setCurrentAmount('');
        setDeadline('');
        fetchGoals();
      }
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to create goal');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOpenUpdate = (goal) => {
    setSelectedGoal(goal);
    setAddedAmount('');
    setShowUpdateModal(true);
  };

  const handleUpdateProgress = async (e) => {
    e.preventDefault();
    if (!addedAmount || !selectedGoal) return;

    setSubmitting(true);
    try {
      // Calculate new total amount
      const newAmount = selectedGoal.currentAmount + parseFloat(addedAmount);
      
      const res = await api.put(`/goals/${selectedGoal._id}`, {
        currentAmount: Math.max(0, newAmount),
      });

      if (res.data.success) {
        setShowUpdateModal(false);
        fetchGoals();
      }
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to update progress');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this goal?')) return;
    try {
      const res = await api.delete(`/goals/${id}`);
      if (res.data.success) {
        fetchGoals();
      }
    } catch (err) {
      alert('Failed to delete goal.');
    }
  };

  return (
    <div className="space-y-6">
      {/* HEADER SECTION WITH QUICK STAT CARD */}
      <div className="flex items-center justify-between bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
        <div>
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center">
            <Target className="h-5 w-5 text-brand-500 mr-2" /> Savings Targets
          </h2>
          <p className="text-slate-450 text-xs mt-1">
            Build financial discipline by monitoring timelines towards big-ticket goals.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center justify-center rounded-xl bg-brand-500 hover:bg-brand-600 px-4 py-2.5 text-xs font-semibold text-white transition-all shadow-md shadow-brand-500/10 cursor-pointer"
        >
          <Plus className="h-4 w-4 mr-1.5" /> Define Goal
        </button>
      </div>

      {/* GOALS GRID */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
        </div>
      ) : goals.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 py-16 text-center text-sm text-slate-400 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
          No active savings goals found. Click define goal above to start saving.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {goals.map((g) => {
            const pct = Math.min(100, Math.round((g.currentAmount / g.targetAmount) * 100));
            const isAchieved = g.status === 'achieved' || pct >= 100;
            const isOverdue = new Date(g.deadline) < new Date() && !isAchieved;

            return (
              <div
                key={g._id}
                className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6 flex flex-col justify-between"
              >
                <div>
                  {/* Title & Delete */}
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-slate-800 dark:text-slate-200 text-base">{g.name}</h4>
                      <span className="text-[10px] text-slate-400">Created: {formatDate(g.createdAt)}</span>
                    </div>
                    <button
                      onClick={() => handleDelete(g._id)}
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-950/20 transition-all cursor-pointer"
                    >
                      <Trash2 className="h-4.5 w-4.5" />
                    </button>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-2 mt-3">
                    {isAchieved ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/20 text-emerald-650 dark:text-emerald-450">
                        <CheckCircle2 className="h-3 w-3 mr-1" /> Completed!
                      </span>
                    ) : isOverdue ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-50 dark:bg-red-950/20 text-red-650 dark:text-red-400">
                        <AlertCircle className="h-3 w-3 mr-1" /> Overdue
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-50 dark:bg-brand-950/20 text-brand-500 dark:text-brand-400">
                        Active Save
                      </span>
                    )}
                  </div>

                  {/* Financials details */}
                  <div className="grid grid-cols-2 gap-4 mt-6">
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Saved Balance</span>
                      <p className="text-base font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                        {formatCurrency(g.currentAmount, user?.currency)}
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Target goal</span>
                      <p className="text-base font-bold text-slate-800 dark:text-slate-200 mt-0.5">
                        {formatCurrency(g.targetAmount, user?.currency)}
                      </p>
                    </div>
                  </div>

                  {/* Progress gauge */}
                  <div className="mt-4 space-y-1">
                    <div className="flex justify-between items-center text-xs text-slate-450">
                      <span>Progress percentage</span>
                      <span className="font-semibold">{pct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isAchieved ? 'bg-emerald-500' : 'bg-brand-500'
                        }`}
                        style={{ width: `${pct}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Footer Controls */}
                <div className="mt-6 border-t border-slate-100 dark:border-slate-850 pt-4 flex items-center justify-between">
                  <span className="flex items-center text-xs text-slate-450">
                    <Calendar className="h-3.5 w-3.5 mr-1" /> {formatDate(g.deadline)}
                  </span>
                  
                  {!isAchieved && (
                    <button
                      onClick={() => handleOpenUpdate(g)}
                      className="flex items-center text-xs font-semibold text-brand-500 hover:text-brand-650 cursor-pointer"
                    >
                      Add Savings <ArrowUpRight className="h-4 w-4 ml-0.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* DEFINE NEW GOAL MODAL */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-2xl border border-slate-100 dark:border-slate-850 shadow-2xl p-6 relative">
            <button
              onClick={() => setShowAddModal(false)}
              className="absolute top-4 right-4 rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Define Savings Target</h3>
            
            <form onSubmit={handleCreateGoal} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Goal Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="form-input"
                  placeholder="e.g. Emergency Fund or Down Payment"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Target Amount ({user?.currency})
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={targetAmount}
                  onChange={(e) => setTargetAmount(e.target.value)}
                  className="form-input"
                  placeholder="0.00"
                  required
                  min="0.01"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Initial Saved Balance
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={currentAmount}
                  onChange={(e) => setCurrentAmount(e.target.value)}
                  className="form-input"
                  placeholder="0.00 (optional)"
                  min="0"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Target Deadline
                </label>
                <input
                  type="date"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
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
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Defining...
                  </>
                ) : (
                  'Create Savings Goal'
                )}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* ADD/SUBTRACT FUNDS MODAL */}
      {showUpdateModal && selectedGoal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 w-full max-w-sm rounded-2xl border border-slate-100 dark:border-slate-850 shadow-2xl p-6 relative">
            <button
              onClick={() => setShowUpdateModal(false)}
              className="absolute top-4 right-4 rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Add Savings to "{selectedGoal.name}"</h3>
            
            <form onSubmit={handleUpdateProgress} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Amount to Contribute ({user?.currency})
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={addedAmount}
                  onChange={(e) => setAddedAmount(e.target.value)}
                  className="form-input"
                  placeholder="0.00"
                  required
                />
                <span className="text-[10px] text-slate-400 mt-1 block">
                  Tip: Use positive values to save, or negative to withdraw.
                </span>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center rounded-xl bg-brand-500 hover:bg-brand-600 py-3 text-sm font-semibold text-white transition-all shadow-md shadow-brand-500/10 cursor-pointer"
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Depositing...
                  </>
                ) : (
                  'Confirm Contribution'
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
