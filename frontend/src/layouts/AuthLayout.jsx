import React from 'react';
import { useTheme } from '../hooks/useTheme';
import { Sun, Moon } from 'lucide-react';

export const AuthLayout = ({ children }) => {
  const { darkMode, toggleTheme } = useTheme();

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
      {/* Theme switcher fixed button */}
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 rounded-xl p-2.5 bg-white dark:bg-slate-900 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 shadow-sm z-50 transition-all"
        aria-label="Toggle Theme"
      >
        {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
      </button>

      {/* LEFT COLUMN: VISUAL BRAND PANEL */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-brand-900 overflow-hidden flex-col justify-between p-12 text-white">
        {/* Decorative Grid and Gradients */}
        <div className="absolute inset-0 bg-gradient-to-tr from-brand-600 to-indigo-800 opacity-90 z-0"></div>
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,_var(--tw-gradient-stops))] from-teal-400/20 via-transparent to-transparent z-0"></div>
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-indigo-500/10 blur-3xl"></div>

        <div className="relative z-10 flex items-center">
          <span className="text-2xl font-bold tracking-tight text-white">
            Smart Finance
          </span>
        </div>

        <div className="relative z-10 my-auto max-w-md">
          <h2 className="text-4xl font-extrabold tracking-tight leading-tight">
            Take Control of Your Financial Future.
          </h2>
          <p className="mt-4 text-slate-200 text-base leading-relaxed">
            Monitor expenses, set category budgets, track goals, and generate AI-powered spending forecasts—all from a single secure FinTech dashboard.
          </p>
        </div>

        <div className="relative z-10 flex items-center space-x-4 border-t border-white/10 pt-6">
          <div className="flex -space-x-2">
            <div className="h-8 w-8 rounded-full bg-teal-400 border-2 border-brand-900 flex items-center justify-center text-xs font-semibold text-brand-900">JD</div>
            <div className="h-8 w-8 rounded-full bg-amber-400 border-2 border-brand-900 flex items-center justify-center text-xs font-semibold text-brand-900">SA</div>
            <div className="h-8 w-8 rounded-full bg-purple-400 border-2 border-brand-900 flex items-center justify-center text-xs font-semibold text-brand-900">MR</div>
          </div>
          <span className="text-xs text-slate-350">Trusted by over 10,000+ personal finance managers.</span>
        </div>
      </div>

      {/* RIGHT COLUMN: ACTION FORM PANEL */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 sm:p-12 md:p-16">
        <div className="w-full max-w-md space-y-6">
          {children}
        </div>
      </div>
    </div>
  );
};
