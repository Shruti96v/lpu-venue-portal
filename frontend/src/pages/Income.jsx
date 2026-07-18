import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatDate } from '../utils/format';
import api from '../services/api';
import {
  Search,
  Plus,
  Edit2,
  Trash2,
  ChevronLeft,
  ChevronRight,
  X,
  Loader2,
} from 'lucide-react';

export const Income = () => {
  const { user } = useAuth();
  
  // Data State
  const [incomes, setIncomes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalIncomes, setTotalIncomes] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  
  // Filters State
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [sortBy, setSortBy] = useState('date:desc');
  
  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add'); // 'add' or 'edit'
  const [currentId, setCurrentId] = useState('');
  const [amount, setAmount] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Salary');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const categories = ['Salary', 'Freelancing', 'Investments', 'Other'];

  const fetchIncomes = async () => {
    try {
      setLoading(true);
      const res = await api.get(
        `/income?page=${page}&limit=7&search=${search}&category=${category}&sortBy=${sortBy}`
      );
      if (res.data.success) {
        setIncomes(res.data.data);
        setPages(res.data.pagination.pages);
        setTotalIncomes(res.data.pagination.total);
      }
    } catch (err) {
      console.error('Failed to load income logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncomes();
  }, [page, category, sortBy]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchIncomes();
  };

  const handleOpenAddModal = () => {
    setModalMode('add');
    setAmount('');
    setSelectedCategory('Salary');
    setDate(new Date().toISOString().split('T')[0]);
    setDescription('');
    setShowModal(true);
  };

  const handleOpenEditModal = (inc) => {
    setModalMode('edit');
    setCurrentId(inc._id);
    setAmount(inc.amount.toString());
    setSelectedCategory(inc.category);
    setDate(new Date(inc.date).toISOString().split('T')[0]);
    setDescription(inc.description || '');
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!amount || !selectedCategory) return;

    setSubmitting(true);
    try {
      if (modalMode === 'add') {
        const res = await api.post('/income', {
          amount: parseFloat(amount),
          category: selectedCategory,
          date: new Date(date),
          description,
        });
        if (res.data.success) {
          setShowModal(false);
          setPage(1);
          fetchIncomes();
        }
      } else {
        const res = await api.put(`/income/${currentId}`, {
          amount: parseFloat(amount),
          category: selectedCategory,
          date: new Date(date),
          description,
        });
        if (res.data.success) {
          setShowModal(false);
          fetchIncomes();
        }
      }
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to save income log');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this income log?')) return;
    try {
      const res = await api.delete(`/income/${id}`);
      if (res.data.success) {
        fetchIncomes();
      }
    } catch (err) {
      alert('Failed to delete income log.');
    }
  };

  return (
    <div className="space-y-6">
      {/* FILTER & HEADER BAR */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search income description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="form-input pl-10"
            />
          </div>
          <button
            type="submit"
            className="rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-850 dark:hover:bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 cursor-pointer"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap gap-3 items-center">
          {/* Category Filter */}
          <div className="relative">
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="form-input text-xs py-2.5 min-w-[130px]"
            >
              <option value="">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Sort By Dropdown */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setPage(1);
              }}
              className="form-input text-xs py-2.5 min-w-[150px]"
            >
              <option value="date:desc">Newest First</option>
              <option value="date:asc">Oldest First</option>
              <option value="amount:desc">Amount: High to Low</option>
              <option value="amount:asc">Amount: Low to High</option>
            </select>
          </div>

          <button
            onClick={handleOpenAddModal}
            className="flex items-center justify-center rounded-xl bg-emerald-500 hover:bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white transition-all shadow-md shadow-emerald-500/10 cursor-pointer"
          >
            <Plus className="h-4 w-4 mr-1.5" /> Record Income
          </button>
        </div>
      </div>

      {/* INCOME TABLE CARD */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex h-48 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
            </div>
          ) : incomes.length === 0 ? (
            <div className="py-16 text-center text-sm text-slate-400">
              No matching income records found.
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-850 text-xs text-slate-400 uppercase font-semibold">
                  <th className="py-3 pr-4">Description</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4 text-right">Amount</th>
                  <th className="py-3 pl-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-850 text-sm">
                {incomes.map((inc) => (
                  <tr key={inc._id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/20 transition-colors">
                    <td className="py-3.5 pr-4 font-semibold text-slate-850 dark:text-slate-200">
                      {inc.description || 'No description'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{formatDate(inc.date)}</td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/20 text-emerald-650 dark:text-emerald-400">
                        {inc.category}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold text-emerald-500">
                      +{formatCurrency(inc.amount, user?.currency)}
                    </td>
                    <td className="py-3.5 pl-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleOpenEditModal(inc)}
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                        >
                          <Edit2 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(inc._id)}
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-950/20 transition-colors cursor-pointer"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* PAGINATION CONTROL ROW */}
        {!loading && pages > 1 && (
          <div className="flex items-center justify-between border-t border-slate-100 dark:border-slate-850 pt-4 mt-4">
            <span className="text-xs text-slate-450">
              Showing page <span className="font-semibold">{page}</span> of <span className="font-semibold">{pages}</span> ({totalIncomes} logs)
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="rounded-lg border border-slate-200 dark:border-slate-800 p-2 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50 transition-colors cursor-pointer"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() => setPage(Math.min(pages, page + 1))}
                disabled={page === pages}
                className="rounded-lg border border-slate-200 dark:border-slate-800 p-2 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50 transition-colors cursor-pointer"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ADD/EDIT MODAL POPUP */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-2xl border border-slate-100 dark:border-slate-850 shadow-2xl p-6 relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 rounded-xl p-1.5 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">
              {modalMode === 'add' ? 'Record Income Flow' : 'Modify Income Details'}
            </h3>
            
            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
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
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
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
                  placeholder="e.g. Consulting pay or salary bonus"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center rounded-xl bg-emerald-500 hover:bg-emerald-600 py-3 text-sm font-semibold text-white transition-all shadow-md shadow-emerald-500/10 cursor-pointer"
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                  </>
                ) : (
                  modalMode === 'add' ? 'Record Income' : 'Save Modifications'
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
