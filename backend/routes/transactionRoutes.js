const express = require('express');
const router = express.Router();
const { getTransactions, addTransaction, updateTransaction, deleteTransaction } = require('../controllers/transactionController');
const { transactionValidator } = require('../middlewares/validators');
const { protect } = require('../middlewares/auth');

// Middleware to inject type filter/body based on sub-route
const forceType = (type) => (req, res, next) => {
  if (req.method === 'GET') {
    req.query.type = type;
  } else {
    req.body.type = type;
  }
  next();
};

// Expenses Routes
router.route('/expenses')
  .get(protect, forceType('expense'), getTransactions)
  .post(protect, forceType('expense'), transactionValidator, addTransaction);

router.route('/expenses/:id')
  .put(protect, forceType('expense'), transactionValidator, updateTransaction)
  .delete(protect, deleteTransaction);

// Income Routes
router.route('/income')
  .get(protect, forceType('income'), getTransactions)
  .post(protect, forceType('income'), transactionValidator, addTransaction);

router.route('/income/:id')
  .put(protect, forceType('income'), transactionValidator, updateTransaction)
  .delete(protect, deleteTransaction);

// General Transactions route (flexible for analytics/history)
router.route('/')
  .get(protect, getTransactions);

module.exports = router;
