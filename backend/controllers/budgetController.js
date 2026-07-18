const Budget = require('../models/Budget');
const Transaction = require('../models/Transaction');

// @desc    Get monthly budgets
// @route   GET /api/budgets
// @access  Private
exports.getBudgets = async (req, res, next) => {
  try {
    const { month } = req.query;

    // Use current month (YYYY-MM) as default
    const currentMonth = month || new Date().toISOString().slice(0, 7);

    const budgets = await Budget.find({ user: req.user.id, month: currentMonth });

    res.json({ success: true, month: currentMonth, data: budgets });
  } catch (error) {
    next(error);
  }
};

// @desc    Create or update budget
// @route   POST /api/budgets
// @access  Private
exports.setBudget = async (req, res, next) => {
  try {
    const { category, amount, month } = req.body;
    const activeMonth = month || new Date().toISOString().slice(0, 7);

    // Upsert budget to avoid duplication
    const budget = await Budget.findOneAndUpdate(
      { user: req.user.id, category, month: activeMonth },
      { amount },
      { new: true, upsert: true, runValidators: true }
    );

    res.status(201).json({ success: true, data: budget });
  } catch (error) {
    next(error);
  }
};
