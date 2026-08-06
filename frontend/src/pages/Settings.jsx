import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import {
  User,
  Shield,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Lock,
} from 'lucide-react';

export const Settings = () => {
  const { user, updateProfile, logout } = useAuth();
  const navigate = useNavigate();

  // Profile Fields
  const [name, setName] = useState(user?.name || '');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [currency, setCurrency] = useState(user?.currency || 'INR');
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(user?.twoFactorEnabled || false);
  
  // Loading & Msg states
  const [updating, setUpdating] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  
  // Deletion States
  const [confirmDeleteText, setConfirmDeleteText] = useState('');
  const [deleting, setDeleting] = useState(false);

  const currencies = ['USD', 'EUR', 'GBP', 'INR', 'JPY', 'CAD', 'AUD'];

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setSuccess('');
    setError('');

    if (password && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setUpdating(true);
    const updates = { name, currency, twoFactorEnabled };
    if (password) {
      updates.password = password;
    }

    const result = await updateProfile(updates);
    setUpdating(false);

    if (result.success) {
      setSuccess('Profile settings successfully saved!');
      setPassword('');
      setConfirmPassword('');
    } else {
      setError(result.message);
    }
  };

  const handleDeleteAccount = async (e) => {
    e.preventDefault();
    if (confirmDeleteText !== 'DELETE') {
      alert('Please type DELETE to confirm your action.');
      return;
    }

    if (!window.confirm('WARNING: Are you absolutely sure? This action is irreversible! All your history will be lost.')) {
      return;
    }

    setDeleting(true);
    try {
      const res = await api.delete('/auth/profile');
      if (res.data.success) {
        setDeleting(false);
        logout();
        navigate('/login');
      }
    } catch (err) {
      alert('Failed to delete account. Please try again.');
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {success && (
        <div className="p-3.5 rounded-xl text-xs bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 text-emerald-700 dark:text-emerald-400 flex items-center">
          <CheckCircle className="h-4.5 w-4.5 mr-2" /> {success}
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-xl text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* NAV SYNOPSIS LEFT */}
        <div className="md:col-span-1 space-y-3">
          <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
            <span className="text-xs text-slate-400 block">Logged In As</span>
            <span className="font-bold text-slate-800 dark:text-slate-200 mt-1 block">{user?.email}</span>
            <span className="text-[10px] text-brand-500 font-semibold uppercase mt-1 block tracking-wider">{user?.role} Role</span>
          </div>
        </div>

        {/* DETAILS SECTION RIGHT */}
        <div className="md:col-span-2 space-y-6">
          
          {/* PROFILE & PREFERENCES PANEL */}
          <form onSubmit={handleUpdateProfile} className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-800 dark:text-slate-100 flex items-center border-b border-slate-100 dark:border-slate-800 pb-3">
              <User className="h-5 w-5 text-brand-500 mr-2" /> Personal Profile & Settings
            </h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="form-input"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Default Ledger Currency
                </label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  className="form-input"
                >
                  {currencies.map((curr) => (
                    <option key={curr} value={curr}>{curr}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border-t border-slate-100 dark:border-slate-800 pt-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Change Password
                </label>
                <input
                  type="password"
                  placeholder="New password (optional)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            {/* Two-Factor Authentication Mock Switch */}
            <div className="border-t border-slate-100 dark:border-slate-800 pt-4 flex items-center justify-between">
              <div>
                <span className="font-semibold text-sm text-slate-800 dark:text-slate-200 flex items-center">
                  <Shield className="h-4 w-4 text-emerald-500 mr-1.5" /> Two-Factor Authentication (2FA)
                </span>
                <p className="text-[10px] text-slate-450 mt-0.5">
                  Protect account safety by requesting an authenticator verification check on logs.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={twoFactorEnabled}
                  onChange={(e) => setTwoFactorEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-slate-650 peer-checked:bg-brand-500"></div>
              </label>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={updating}
                className="flex items-center justify-center rounded-xl bg-brand-500 hover:bg-brand-600 px-5 py-2.5 text-xs font-semibold text-white transition-all shadow-md shadow-brand-500/10 cursor-pointer"
              >
                {updating ? (
                  <>
                    <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> Saving Changes...
                  </>
                ) : (
                  'Save Profile Details'
                )}
              </button>
            </div>
          </form>

          {/* DANGER DELETION ZONE */}
          <div className="bg-red-50/10 dark:bg-red-950/5 border border-red-200/50 dark:border-red-900/30 p-6 rounded-2xl space-y-4">
            <h3 className="text-base font-bold text-red-650 flex items-center border-b border-red-100 dark:border-red-950 pb-3">
              <Trash2 className="h-5 w-5 mr-2" /> Danger Zone: Delete Account
            </h3>
            
            <div className="flex items-start space-x-2 text-xs text-red-700 dark:text-red-400">
              <AlertTriangle className="h-5 w-5 mr-1 flex-shrink-0" />
              <p className="leading-relaxed">
                Deleting your account will immediately wipe out your transactions, budgets, goals, and credentials from our servers permanently. This action cannot be reversed.
              </p>
            </div>

            <form onSubmit={handleDeleteAccount} className="space-y-3 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">
                  Type <span className="font-bold text-red-600">DELETE</span> to authorize self-account deletion:
                </label>
                <input
                  type="text"
                  value={confirmDeleteText}
                  onChange={(e) => setConfirmDeleteText(e.target.value)}
                  className="form-input border-red-200 dark:border-red-900/35 focus:ring-red-100"
                  placeholder="Type DELETE"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={deleting || confirmDeleteText !== 'DELETE'}
                className="flex items-center justify-center rounded-xl bg-red-600 hover:bg-red-700 disabled:opacity-40 px-5 py-2.5 text-xs font-semibold text-white transition-all cursor-pointer shadow-md shadow-red-500/5"
              >
                {deleting ? (
                  <>
                    <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> Deleting Account...
                  </>
                ) : (
                  'Permanently Remove My Account'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
