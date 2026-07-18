import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatDate } from '../utils/format';
import api from '../services/api';
import {
  Users,
  Database,
  Volume2,
  Trash2,
  TrendingUp,
  Shield,
  Loader2,
  RefreshCw,
} from 'lucide-react';

export const Admin = () => {
  const { user } = useAuth();
  
  // Data states
  const [adminStats, setAdminStats] = useState(null);
  const [usersList, setUsersList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const fetchAdminDetails = async () => {
    try {
      setLoading(true);
      setError('');
      
      const statsRes = await api.get('/admin/stats');
      const usersRes = await api.get('/admin/users');

      if (statsRes.data.success && usersRes.data.success) {
        setAdminStats(statsRes.data.data);
        setUsersList(usersRes.data.data);
      }
    } catch (err) {
      setError('Failed to fetch administrative platform analytics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminDetails();
  }, []);

  const handleDeleteUser = async (targetUserId) => {
    const targetUser = usersList.find((u) => u._id === targetUserId);
    if (!targetUser) return;

    if (!window.confirm(`Are you absolutely sure you want to DELETE user "${targetUser.name}" (${targetUser.email}) and all their financial transactions/budgets/goals? This cascade is permanent.`)) {
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.delete(`/admin/users/${targetUserId}`);
      if (res.data.success) {
        alert('User account successfully purged.');
        fetchAdminDetails(); // Reload directory
      }
    } catch (err) {
      alert(err.response?.data?.message || 'Purging user failed.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !adminStats) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-red-50 text-red-700 text-center border border-red-100">
        {error}
        <button onClick={fetchAdminDetails} className="block mx-auto mt-2 text-sm font-semibold underline">
          Requery Data
        </button>
      </div>
    );
  }

  const { counts, volume, roles } = adminStats;

  return (
    <div className="space-y-6">
      
      {/* STATS TILES CARD BAR */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Users */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm relative">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Registered Users</span>
          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">{counts.users}</h3>
          <div className="flex items-center mt-3 text-slate-400 text-xs">
            <span>{roles.admins} Admins • {roles.users} Standard</span>
          </div>
          <div className="absolute top-6 right-6 h-10 w-10 rounded-xl bg-brand-50 dark:bg-brand-950/20 flex items-center justify-center text-brand-500">
            <Users className="h-5 w-5" />
          </div>
        </div>

        {/* Database records */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm relative">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Data Records</span>
          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">
            {counts.transactions + counts.budgets + counts.goals}
          </h3>
          <div className="flex items-center mt-3 text-slate-400 text-xs">
            <span>{counts.transactions} txs • {counts.budgets} budgets • {counts.goals} goals</span>
          </div>
          <div className="absolute top-6 right-6 h-10 w-10 rounded-xl bg-violet-50 dark:bg-violet-950/20 flex items-center justify-center text-violet-500">
            <Database className="h-5 w-5" />
          </div>
        </div>

        {/* Global Volume flow */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm relative">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Platform Volume Flow</span>
          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">
            {formatCurrency(volume.income + volume.expense, user?.currency)}
          </h3>
          <div className="flex items-center mt-3 text-emerald-500 text-xs font-semibold">
            <span>Flowing income & expense aggregates</span>
          </div>
          <div className="absolute top-6 right-6 h-10 w-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 flex items-center justify-center text-emerald-500">
            <Volume2 className="h-5 w-5" />
          </div>
        </div>

        {/* Platform Net Balance */}
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm relative">
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Platform Net Yield</span>
          <h3 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-2">
            {formatCurrency(volume.net, user?.currency)}
          </h3>
          <div className="flex items-center mt-3 text-indigo-500 text-xs font-semibold">
            <span>Total platform capital balances</span>
          </div>
          <div className="absolute top-6 right-6 h-10 w-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/20 flex items-center justify-center text-indigo-500">
            <TrendingUp className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* USER LIST DIRECTORY */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">User Account Directory</h3>
          <button
            onClick={fetchAdminDetails}
            className="flex items-center text-xs font-semibold text-brand-500 hover:text-brand-655"
          >
            <RefreshCw className="h-3.5 w-3.5 mr-1" /> Reload Directory
          </button>
        </div>

        <div className="overflow-x-auto">
          {usersList.length === 0 ? (
            <div className="py-12 text-center text-sm text-slate-400">No users registered yet.</div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-850 text-xs text-slate-400 uppercase font-semibold">
                  <th className="py-3 pr-4">User Details</th>
                  <th className="py-3 px-4">Role</th>
                  <th className="py-3 px-4">Joined Date</th>
                  <th className="py-3 px-4">Status Check</th>
                  <th className="py-3 pl-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-850 text-sm">
                {usersList.map((u) => (
                  <tr key={u._id} className="hover:bg-slate-50/50 dark:hover:bg-slate-850/20 transition-colors">
                    <td className="py-3.5 pr-4">
                      <div>
                        <div className="font-semibold text-slate-850 dark:text-slate-200">{u.name}</div>
                        <div className="text-xs text-slate-400 mt-0.5">{u.email}</div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 capitalize">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        u.role === 'admin' 
                          ? 'bg-purple-50 text-purple-650 dark:bg-purple-950/20 dark:text-purple-400' 
                          : 'bg-slate-100 text-slate-650 dark:bg-slate-800 dark:text-slate-400'
                      }`}>
                        {u.role === 'admin' && <Shield className="h-3 w-3 mr-1" />}
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">{formatDate(u.createdAt)}</td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-650 dark:bg-emerald-950/20 dark:text-emerald-450">
                        Verified Account
                      </span>
                    </td>
                    <td className="py-3.5 pl-4 text-right">
                      {u._id === user._id ? (
                        <span className="text-xs text-slate-400 italic">Self Account</span>
                      ) : (
                        <button
                          onClick={() => handleDeleteUser(u._id)}
                          disabled={submitting}
                          className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-950/20 transition-colors cursor-pointer disabled:opacity-40"
                        >
                          <Trash2 className="h-4.5 w-4.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
