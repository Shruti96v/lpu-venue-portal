import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { AuthLayout } from '../layouts/AuthLayout';
import { Loader2 } from 'lucide-react';

export const ForgotPassword = () => {
  const { forgotPassword } = useAuth();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [simulatedToken, setSimulatedToken] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) {
      setError('Please enter your email.');
      return;
    }
    setError('');
    setMessage('');
    setLoading(true);

    const result = await forgotPassword(email);
    setLoading(false);

    if (result.success) {
      setMessage('Password reset simulated successfully! Link generated.');
      if (result.token) {
        setSimulatedToken(result.token);
      }
    } else {
      setError(result.message);
    }
  };

  return (
    <AuthLayout>
      <div className="text-center lg:text-left">
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white">
          Reset password
        </h2>
        <p className="mt-2 text-sm text-slate-555 dark:text-slate-400">
          Enter your email to receive a password recovery token.
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg text-xs bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 text-red-700 dark:text-red-400">
          {error}
        </div>
      )}

      {message && (
        <div className="p-3 rounded-lg text-xs bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/30 text-emerald-700 dark:text-emerald-400 space-y-2">
          <p>{message}</p>
          {simulatedToken && (
            <div className="mt-2 p-2 bg-white dark:bg-slate-900 rounded border border-emerald-100 dark:border-emerald-900/50">
              <span className="font-semibold">Demo Quick Link:</span>{' '}
              <Link
                to={`/reset-password?token=${simulatedToken}`}
                className="underline text-brand-500 font-medium block mt-1 hover:text-brand-600"
              >
                Go to Reset Screen with Token
              </Link>
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Email Address
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="form-input"
            placeholder="name@company.com"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center rounded-xl bg-brand-500 py-3 text-sm font-semibold text-white hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-200 disabled:opacity-50 transition-all cursor-pointer shadow-md shadow-brand-500/10"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Simulating mail send...
            </>
          ) : (
            'Send Reset Token'
          )}
        </button>
      </form>

      <div className="text-center">
        <p className="text-sm text-slate-555 dark:text-slate-400">
          Remember your password?{' '}
          <Link
            to="/login"
            className="font-semibold text-brand-500 hover:text-brand-600 transition-colors"
          >
            Sign In
          </Link>
        </p>
      </div>
    </AuthLayout>
  );
};
