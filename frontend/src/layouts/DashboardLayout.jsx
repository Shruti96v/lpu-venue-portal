import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';
import api from '../services/api';
import {
  LayoutDashboard,
  TrendingDown,
  TrendingUp,
  Wallet,
  Target,
  PieChart,
  Settings,
  Users,
  LogOut,
  Sun,
  Moon,
  Menu,
  X,
  Bell,
} from 'lucide-react';

export const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const { darkMode, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [showAlertsDropdown, setShowAlertsDropdown] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Fetch dashboard stats to run real-time checks on budgets & goals for alerts
  useEffect(() => {
    const checkAlerts = async () => {
      try {
        const res = await api.get('/dashboard');
        if (res.data.success) {
          const { budgetProgress, savingsGoals } = res.data.data;
          const activeAlerts = [];

          // Budget alerts
          budgetProgress.forEach((bp) => {
            if (bp.exceeded) {
              activeAlerts.push({
                id: `budget-${bp.category}`,
                type: 'danger',
                message: `Budget Exceeded: Spent $${bp.spent} of $${bp.limit} in ${bp.category}!`,
              });
            } else if (bp.spent / bp.limit >= 0.8) {
              activeAlerts.push({
                id: `budget-warn-${bp.category}`,
                type: 'warning',
                message: `Approaching Budget: Spent $${bp.spent} of $${bp.limit} (80%+) in ${bp.category}!`,
              });
            }
          });

          // Savings Goal achievements
          if (savingsGoals && savingsGoals.percentage >= 100) {
            activeAlerts.push({
              id: 'goals-achieved',
              type: 'success',
              message: `Congratulations! Savings goals are 100% completed!`,
            });
          }

          setAlerts(activeAlerts);
        }
      } catch (err) {
        console.error('Failed to check notifications:', err);
      }
    };
    checkAlerts();
  }, [location.pathname]); // Run check on page changes

  const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Expenses', href: '/expenses', icon: TrendingDown },
    { name: 'Income', href: '/income', icon: TrendingUp },
    { name: 'Budgets', href: '/budgets', icon: Wallet },
    { name: 'Savings Goals', href: '/goals', icon: Target },
    { name: 'Analytics', href: '/analytics', icon: PieChart },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  // Include admin link if user is admin
  if (user && user.role === 'admin') {
    navigation.push({ name: 'Admin Panel', href: '/admin', icon: Users });
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const pageTitle = navigation.find((item) => item.href === location.pathname)?.name || 'Smart Finance';

  return (
    <div className="flex h-screen bg-brand-50 dark:bg-slate-950 font-sans overflow-hidden">
      {/* MOBILE SIDEBAR MODAL */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <div className="relative flex w-full max-w-xs flex-1 flex-col bg-white dark:bg-slate-900 pt-5 pb-4 px-4 transition-transform duration-300">
            <div className="flex items-center justify-between px-2">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-brand-500 to-indigo-500 bg-clip-text text-transparent">
                Smart Finance
              </span>
              <button
                type="button"
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                onClick={() => setSidebarOpen(false)}
              >
                <X className="h-6 w-6" />
              </button>
            </div>
            <nav className="mt-8 flex-1 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center rounded-xl px-4 py-3 text-sm font-medium transition-all duration-150 ${
                      isActive
                        ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/20'
                        : 'text-slate-600 hover:bg-brand-50 hover:text-brand-500 dark:text-slate-400 dark:hover:bg-slate-800'
                    }`}
                  >
                    <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
            <div className="border-t border-slate-100 dark:border-slate-800 pt-4">
              <button
                onClick={handleLogout}
                className="flex w-full items-center rounded-xl px-4 py-3 text-sm font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-all duration-150"
              >
                <LogOut className="mr-3 h-5 w-5 flex-shrink-0" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DESKTOP SIDEBAR */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-white dark:bg-slate-900 border-r border-slate-100 dark:border-slate-800">
        <div className="flex flex-col flex-1 min-h-0">
          <div className="flex items-center h-16 flex-shrink-0 px-6 border-b border-slate-100 dark:border-slate-800">
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-brand-500 to-indigo-500 bg-clip-text text-transparent">
              Smart Finance
            </span>
          </div>
          <div className="flex flex-col flex-1 overflow-y-auto pt-6 px-4">
            <nav className="flex-1 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center rounded-xl px-4 py-3 text-sm font-medium transition-all duration-150 ${
                      isActive
                        ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/20'
                        : 'text-slate-600 hover:bg-brand-50 hover:text-brand-500 dark:text-slate-350 dark:hover:bg-slate-800 dark:hover:text-brand-500'
                    }`}
                  >
                    <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
            <div className="py-4 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={handleLogout}
                className="flex w-full items-center rounded-xl px-4 py-3 text-sm font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 transition-all duration-150"
              >
                <LogOut className="mr-3 h-5 w-5 flex-shrink-0" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT WRAPPER */}
      <div className="flex flex-col flex-1 md:pl-64 overflow-hidden">
        {/* TOP HEADERBAR */}
        <header className="flex h-16 items-center justify-between px-6 bg-white/70 dark:bg-slate-900/60 backdrop-blur-md border-b border-slate-100 dark:border-slate-800 z-10">
          <div className="flex items-center">
            <button
              type="button"
              className="md:hidden rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-6 w-6" />
            </button>
            <h1 className="hidden md:block text-xl font-semibold text-slate-800 dark:text-slate-100">
              {pageTitle}
            </h1>
          </div>

          <div className="flex items-center space-x-4">
            {/* Theme Switcher */}
            <button
              onClick={toggleTheme}
              className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-150"
              aria-label="Toggle Theme"
            >
              {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </button>

            {/* Notifications Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowAlertsDropdown(!showAlertsDropdown)}
                className="relative rounded-xl p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-150"
              >
                <Bell className="h-5 w-5" />
                {alerts.length > 0 && (
                  <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white dark:ring-slate-900"></span>
                )}
              </button>

              {showAlertsDropdown && (
                <div className="absolute right-0 mt-2 w-80 rounded-xl bg-white dark:bg-slate-950 border border-slate-100 dark:border-slate-800 shadow-xl py-2 z-50">
                  <div className="px-4 py-2 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                    <span className="font-semibold text-sm text-slate-800 dark:text-slate-200">Alerts & Notifications</span>
                    {alerts.length > 0 && (
                      <span className="text-xs bg-brand-100 text-brand-500 px-2 py-0.5 rounded-full font-medium">
                        {alerts.length} New
                      </span>
                    )}
                  </div>
                  <div className="max-h-60 overflow-y-auto px-2 py-1">
                    {alerts.length === 0 ? (
                      <div className="py-6 text-center text-xs text-slate-400">All clear! No alerts.</div>
                    ) : (
                      alerts.map((a) => (
                        <div
                          key={a.id}
                          className={`my-1 p-2 rounded-lg text-xs leading-normal border ${
                            a.type === 'danger'
                              ? 'bg-red-50 border-red-100 text-red-700 dark:bg-red-950/20 dark:border-red-900/30 dark:text-red-400'
                              : a.type === 'warning'
                              ? 'bg-amber-50 border-amber-100 text-amber-700 dark:bg-amber-950/20 dark:border-amber-900/30 dark:text-amber-400'
                              : 'bg-emerald-50 border-emerald-100 text-emerald-700 dark:bg-emerald-950/20 dark:border-emerald-900/30 dark:text-emerald-400'
                          }`}
                        >
                          {a.message}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Profile Pill */}
            <div className="flex items-center space-x-2 border-l border-slate-150 dark:border-slate-800 pl-4">
              <div className="flex flex-col text-right">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">{user?.name}</span>
                <span className="text-[10px] text-slate-400 capitalize">{user?.role}</span>
              </div>
              <div className="h-8 w-8 rounded-full bg-brand-500 flex items-center justify-center text-white font-bold text-sm uppercase ring-2 ring-brand-100 dark:ring-slate-800">
                {user?.name?.substring(0, 2)}
              </div>
            </div>
          </div>
        </header>

        {/* CONTAINER FOR DASHBOARD PAGES */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50 dark:bg-slate-950">
          {children}
        </main>
      </div>
    </div>
  );
};
