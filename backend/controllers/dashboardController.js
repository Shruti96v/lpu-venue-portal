const Transaction = require('../models/Transaction');
const Budget = require('../models/Budget');
const Goal = require('../models/Goal');

// @desc    Get dashboard metrics and summaries
// @route   GET /api/dashboard
// @access  Private
exports.getDashboardStats = async (req, res, next) => {
  try {
    const userId = req.user.id;

    // Dates for current month
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);

    // 1. All-time balances
    const allTransactions = await Transaction.find({ user: userId });
    
    let totalIncome = 0;
    let totalExpense = 0;
    
    allTransactions.forEach(t => {
      if (t.type === 'income') {
        totalIncome += t.amount;
      } else {
        totalExpense += t.amount;
      }
    });

    const totalBalance = totalIncome - totalExpense;

    // 2. Current Month Income vs Expense
    const monthlyTransactions = allTransactions.filter(t => t.date >= startOfMonth && t.date <= endOfMonth);
    
    let monthlyIncome = 0;
    let monthlyExpense = 0;
    
    monthlyTransactions.forEach(t => {
      if (t.type === 'income') {
        monthlyIncome += t.amount;
      } else {
        monthlyExpense += t.amount;
      }
    });

    // 3. Recent Transactions (last 5)
    const recentTransactions = await Transaction.find({ user: userId })
      .sort({ date: -1 })
      .limit(5);

    // 4. Category-wise expense breakdown for the current month
    const categoryBreakdown = {};
    monthlyTransactions.filter(t => t.type === 'expense').forEach(t => {
      if (!categoryBreakdown[t.category]) {
        categoryBreakdown[t.category] = 0;
      }
      categoryBreakdown[t.category] += t.amount;
    });

    const categoryBreakdownArray = Object.keys(categoryBreakdown).map(cat => ({
      category: cat,
      amount: categoryBreakdown[cat],
    }));

    // 5. Budgets progress comparison
    const currentMonthStr = now.toISOString().slice(0, 7); // YYYY-MM
    const budgets = await Budget.find({ user: userId, month: currentMonthStr });
    
    const budgetProgress = budgets.map(b => {
      const spent = monthlyTransactions
        .filter(t => t.type === 'expense' && t.category.toLowerCase() === b.category.toLowerCase())
        .reduce((sum, t) => sum + t.amount, 0);

      return {
        category: b.category,
        limit: b.amount,
        spent,
        remaining: Math.max(0, b.amount - spent),
        exceeded: spent > b.amount,
      };
    });

    // 6. Savings Goals metrics
    const goals = await Goal.find({ user: userId });
    let totalSavingsTarget = 0;
    let totalSavingsCurrent = 0;
    goals.forEach(g => {
      totalSavingsTarget += g.targetAmount;
      totalSavingsCurrent += g.currentAmount;
    });

    res.json({
      success: true,
      data: {
        allTime: {
          income: totalIncome,
          expense: totalExpense,
          balance: totalBalance,
        },
        monthly: {
          income: monthlyIncome,
          expense: monthlyExpense,
          savings: Math.max(0, monthlyIncome - monthlyExpense),
        },
        recentTransactions,
        categoryBreakdown: categoryBreakdownArray,
        budgetProgress,
        savingsGoals: {
          count: goals.length,
          target: totalSavingsTarget,
          current: totalSavingsCurrent,
          percentage: totalSavingsTarget > 0 ? Math.round((totalSavingsCurrent / totalSavingsTarget) * 100) : 0,
        },
      },
    });
  } catch (error) {
    next(error);
  }
};
