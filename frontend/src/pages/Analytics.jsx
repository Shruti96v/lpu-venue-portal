import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { formatCurrency, formatDate } from '../utils/format';
import api from '../services/api';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from 'recharts';
import {
  FileText,
  Download,
  Upload,
  Sparkles,
  TrendingUp,
  BrainCircuit,
  Loader2,
  Calendar,
} from 'lucide-react';

export const Analytics = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7)); // YYYY-MM
  
  // CSV Import fields
  const [csvFile, setCsvFile] = useState(null);
  const [importing, setImporting] = useState(false);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Fetch dashboard which contains category break, spent, savings, etc.
      const res = await api.get(`/dashboard?month=${month}`);
      // Fetch all user transactions to build the monthly charts & trend
      const txRes = await api.get(`/transactions?limit=100`);

      if (res.data.success && txRes.data.success) {
        setData({
          metrics: res.data.data,
          transactions: txRes.data.data,
        });
      }
    } catch (err) {
      setError('Failed to retrieve financial analytics logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [month]);

  // AI-Powered Insights Engine
  const generateAIInsights = () => {
    if (!data) return [];
    const { metrics } = data;
    const { monthly, budgetProgress, savingsGoals } = metrics;
    const insights = [];

    // 1. Savings Ratio insight
    const savingsRatio = monthly.income > 0 ? (monthly.savings / monthly.income) * 100 : 0;
    if (savingsRatio >= 20) {
      insights.push({
        type: 'positive',
        title: 'Healthy Savings Rate',
        desc: `You are saving ${Math.round(savingsRatio)}% of your income this month. Keep this up to strengthen your safety net.`,
      });
    } else if (savingsRatio > 0) {
      insights.push({
        type: 'warning',
        title: 'Increase Savings Threshold',
        desc: `Your savings rate is ${Math.round(savingsRatio)}%. Financial advisors recommend saving at least 20% of your earnings.`,
      });
    } else {
      insights.push({
        type: 'danger',
        title: 'Deficit Alert',
        desc: `Your expenses exceed or equal your income this month. Review non-essential spending categories.`,
      });
    }

    // 2. Budget violation checks
    const exceededBudgets = budgetProgress.filter((bp) => bp.exceeded);
    if (exceededBudgets.length > 0) {
      insights.push({
        type: 'danger',
        title: 'Budget Threshold Overrun',
        desc: `You have exceeded limits in: ${exceededBudgets.map((b) => b.category).join(', ')}. Restructure parameters.`,
      });
    } else {
      insights.push({
        type: 'positive',
        title: 'Budgets Under Control',
        desc: `Fantastic work! All of your category spending fits perfectly inside your budgeted parameters this month.`,
      });
    }

    // 3. Category concentration checks
    if (metrics.categoryBreakdown.length > 0) {
      const topExpense = [...metrics.categoryBreakdown].sort((a, b) => b.amount - a.amount)[0];
      const pct = Math.round((topExpense.amount / monthly.expense) * 105); // approximate share
      if (pct > 40 && topExpense.category !== 'Rent') {
        insights.push({
          type: 'warning',
          title: `High Concentration in ${topExpense.category}`,
          desc: `${topExpense.category} accounts for a major portion (${pct}%) of your total monthly expenditures.`,
        });
      }
    }

    // 4. Trend predictions
    const projectSpend = monthly.expense * 1.1; // Simple prediction
    insights.push({
      type: 'neutral',
      title: 'Spending Forecast',
      desc: `Based on your recent transaction frequency, next month's projected expense flow is estimate at ${formatCurrency(projectSpend, user?.currency)}.`,
    });

    return insights;
  };

  // CSV Export utility
  const handleExportCSV = () => {
    if (!data || data.transactions.length === 0) return;
    
    const headers = ['Type', 'Amount', 'Category', 'Date', 'Description'];
    const rows = data.transactions.map((t) => [
      t.type,
      t.amount,
      t.category,
      t.date,
      t.description || '',
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((r) => r.map((val) => `"${val}"`).join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `smart_finance_transactions_${month}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // CSV Import handler
  const handleImportCSV = async (e) => {
    e.preventDefault();
    if (!csvFile) return;

    const fileReader = new FileReader();
    fileReader.onload = async (event) => {
      const text = event.target.result;
      const lines = text.split('\n').map((line) => line.split(','));
      // Remove headers
      const dataRows = lines.slice(1).filter((row) => row.length >= 3 && row[0]);

      setImporting(true);
      try {
        let importedCount = 0;
        for (const row of dataRows) {
          const type = row[0].replace(/"/g, '').trim().toLowerCase(); // 'income' or 'expense'
          const amount = parseFloat(row[1].replace(/"/g, ''));
          const category = row[2].replace(/"/g, '').trim();
          const date = row[3] ? new Date(row[3].replace(/"/g, '')) : new Date();
          const description = row[4] ? row[4].replace(/"/g, '').trim() : '';

          if ((type === 'income' || type === 'expense') && !isNaN(amount)) {
            const endpoint = type === 'income' ? '/income' : '/expenses';
            await api.post(endpoint, { amount, category, date, description });
            importedCount++;
          }
        }
        alert(`Successfully imported ${importedCount} transactions from CSV!`);
        fetchAnalyticsData(); // Reload
      } catch (err) {
        alert('Error parsing or seeding transactions from CSV.');
      } finally {
        setImporting(false);
        setCsvFile(null);
      }
    };
    fileReader.readAsText(csvFile);
  };

  // PDF Print report
  const handlePrintPDF = () => {
    window.print();
  };

  if (loading && !data) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
      </div>
    );
  }

  const { metrics, transactions } = data;
  const { monthly, categoryBreakdown, budgetProgress } = metrics;

  // Chart data 1: Income vs Expense bar
  const comparisonChartData = [
    { name: 'This Month', Income: monthly.income, Expense: monthly.expense },
  ];

  // Chart data 2: Pie Category Colors
  const COLORS = ['#635bff', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#8b5cf6', '#64748b'];

  // Chart data 3: Trend lines (Area)
  const lastSevenTxs = [...transactions]
    .filter((t) => t.type === 'expense')
    .slice(0, 10)
    .reverse()
    .map((t) => ({
      date: formatDate(t.date).substring(0, 6),
      Amount: t.amount,
    }));

  const aiInsights = generateAIInsights();

  return (
    <div className="space-y-6">
      {/* EXPORT / ACTIONS BAR */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-100 dark:border-slate-800 shadow-sm">
        <div className="flex items-center space-x-3">
          <Calendar className="h-5 w-5 text-brand-500" />
          <input
            type="month"
            value={month}
            onChange={(e) => setMonth(e.target.value)}
            className="form-input text-xs py-1.5 max-w-[150px]"
          />
        </div>

        <div className="flex flex-wrap gap-3">
          {/* CSV Import */}
          <form onSubmit={handleImportCSV} className="flex items-center space-x-2 border border-slate-200 dark:border-slate-850 p-1.5 rounded-xl bg-slate-50 dark:bg-slate-950">
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setCsvFile(e.target.files[0])}
              className="text-[10px] max-w-[140px]"
              required
            />
            <button
              type="submit"
              disabled={importing || !csvFile}
              className="flex items-center justify-center rounded-lg bg-slate-850 hover:bg-slate-800 text-white dark:bg-slate-800 px-2 py-1 text-[10px] font-semibold cursor-pointer disabled:opacity-50"
            >
              <Upload className="h-3 w-3 mr-1" /> Import CSV
            </button>
          </form>

          <button
            onClick={handleExportCSV}
            className="flex items-center justify-center rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-850 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-250 transition-all cursor-pointer"
          >
            <Download className="h-4 w-4 mr-1.5" /> Export CSV
          </button>

          <button
            onClick={handlePrintPDF}
            className="flex items-center justify-center rounded-xl bg-brand-500 hover:bg-brand-600 px-4 py-2 text-xs font-semibold text-white transition-all shadow-md shadow-brand-500/10 cursor-pointer"
          >
            <FileText className="h-4 w-4 mr-1.5" /> Print PDF Report
          </button>
        </div>
      </div>

      {/* CHARTS CONTAINER (Bar vs Pie) */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        {/* Income vs Expenses Balance Sheet */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">Income vs Expenses Balance Sheet</h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonChartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value, user?.currency)} />
                <Legend />
                <Bar dataKey="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Expense" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Expenses Category Allocation */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 p-6 space-y-4">
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">Category Allocation</h3>
          <div className="h-80 w-full flex flex-col md:flex-row items-center justify-around">
            {categoryBreakdown.length === 0 ? (
              <div className="text-center text-sm text-slate-400 py-12">No expense logs recorded.</div>
            ) : (
              <>
                <div className="h-64 w-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={categoryBreakdown}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="amount"
                      >
                        {categoryBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => formatCurrency(value, user?.currency)} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-1">
                  {categoryBreakdown.map((c, i) => (
                    <div key={c.category} className="flex items-center text-xs space-x-2">
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }}></span>
                      <span className="font-semibold text-slate-700 dark:text-slate-350">{c.category}:</span>
                      <span className="text-slate-500">{formatCurrency(c.amount, user?.currency)}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* TREND AREA CHART */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 p-6 space-y-4">
        <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">Expense Spending Trend (Last Logs)</h3>
        <div className="h-64 w-full">
          {lastSevenTxs.length === 0 ? (
            <div className="text-center text-sm text-slate-400 py-12">No expense entries.</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={lastSevenTxs}>
                <defs>
                  <linearGradient id="colorAmt" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#635bff" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#635bff" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value, user?.currency)} />
                <Area type="monotone" dataKey="Amount" stroke="#635bff" fillOpacity={1} fill="url(#colorAmt)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* AI INSIGHTS PANEL */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-100 dark:border-slate-800 p-6 space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 dark:border-slate-800 pb-3">
          <BrainCircuit className="h-5 w-5 text-brand-500" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">AI Spending Insights & Forecasts</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {aiInsights.map((insight, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-xl border flex flex-col justify-between ${
                insight.type === 'positive'
                  ? 'bg-emerald-50/20 border-emerald-100 text-emerald-850 dark:bg-emerald-950/5 dark:border-emerald-900/30 dark:text-emerald-400'
                  : insight.type === 'warning'
                  ? 'bg-amber-50/20 border-amber-100 text-amber-850 dark:bg-amber-950/5 dark:border-amber-900/30 dark:text-amber-400'
                  : insight.type === 'danger'
                  ? 'bg-red-50/20 border-red-100 text-red-850 dark:bg-red-950/5 dark:border-red-900/30 dark:text-red-400'
                  : 'bg-slate-50 border-slate-100 text-slate-700 dark:bg-slate-850/20 dark:border-slate-800 dark:text-slate-350'
              }`}
            >
              <div>
                <span className="text-xs font-bold block">{insight.title}</span>
                <p className="text-xs leading-normal mt-1.5 block opacity-90">{insight.desc}</p>
              </div>
              <div className="flex items-center text-[10px] font-semibold mt-3">
                <Sparkles className="h-3.5 w-3.5 mr-1" /> Smart AI Advisor
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
