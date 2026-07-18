const User = require('../models/User');
const Transaction = require('../models/Transaction');
const Budget = require('../models/Budget');
const Goal = require('../models/Goal');

// @desc    Get all users
// @route   GET /api/admin/users
// @access  Private/Admin
exports.getUsers = async (req, res, next) => {
  try {
    const users = await User.find({}).select('-password');
    res.json({ success: true, count: users.length, data: users });
  } catch (error) {
    next(error);
  }
};

// @desc    Delete user account and their records
// @route   DELETE /api/admin/users/:id
// @access  Private/Admin
exports.deleteUser = async (req, res, next) => {
  try {
    const user = await User.findById(req.params.id);

    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }

    if (user.role === 'admin' && user._id.toString() === req.user.id) {
      return res.status(400).json({ success: false, message: 'Admin cannot delete their own account' });
    }

    // Cascade delete user files
    await Transaction.deleteMany({ user: user._id });
    await Budget.deleteMany({ user: user._id });
    await Goal.deleteMany({ user: user._id });
    
    // Delete user
    await user.deleteOne();

    res.json({ success: true, message: 'User and all associated data deleted successfully' });
  } catch (error) {
    next(error);
  }
};

// @desc    Get platform-wide diagnostics and analytics
// @route   GET /api/admin/stats
// @access  Private/Admin
exports.getStats = async (req, res, next) => {
  try {
    const totalUsers = await User.countDocuments({});
    const totalTransactions = await Transaction.countDocuments({});
    const totalBudgets = await Budget.countDocuments({});
    const totalGoals = await Goal.countDocuments({});

    // Compute total volume flow
    const transactions = await Transaction.find({});
    let totalIncomeVolume = 0;
    let totalExpenseVolume = 0;

    transactions.forEach(t => {
      if (t.type === 'income') {
        totalIncomeVolume += t.amount;
      } else {
        totalExpenseVolume += t.amount;
      }
    });

    // Breakdown roles
    const adminCount = await User.countDocuments({ role: 'admin' });
    const userCount = await User.countDocuments({ role: 'user' });

    res.json({
      success: true,
      data: {
        counts: {
          users: totalUsers,
          transactions: totalTransactions,
          budgets: totalBudgets,
          goals: totalGoals,
        },
        volume: {
          income: totalIncomeVolume,
          expense: totalExpenseVolume,
          net: totalIncomeVolume - totalExpenseVolume,
        },
        roles: {
          admins: adminCount,
          users: userCount,
        }
      }
    });
  } catch (error) {
    next(error);
  }
};
