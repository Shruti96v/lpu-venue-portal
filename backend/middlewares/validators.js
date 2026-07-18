const { check, validationResult } = require('express-validator');

// Middleware to run validations and return validation errors
const validate = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      success: false,
      errors: errors.array().map((err) => ({
        field: err.path,
        message: err.msg,
      })),
    });
  }
  next();
};

const registerValidator = [
  check('name', 'Name is required').notEmpty().trim(),
  check('email', 'Please include a valid email').isEmail().normalizeEmail(),
  check('password', 'Password must be 6 or more characters').isLength({ min: 6 }),
  validate,
];

const loginValidator = [
  check('email', 'Please include a valid email').isEmail().normalizeEmail(),
  check('password', 'Password is required').exists(),
  validate,
];

const transactionValidator = [
  check('type', 'Type must be income or expense').isIn(['income', 'expense']),
  check('amount', 'Amount must be a positive number').isFloat({ min: 0.01 }),
  check('category', 'Category is required').notEmpty().trim(),
  check('date', 'Please provide a valid date').optional().isISO8601(),
  check('description', 'Description can be up to 200 characters').optional().isLength({ max: 200 }),
  validate,
];

const budgetValidator = [
  check('category', 'Category is required').notEmpty().trim(),
  check('amount', 'Amount must be a positive number').isFloat({ min: 0.01 }),
  check('month', 'Month must be in YYYY-MM format').optional().matches(/^\d{4}-\d{2}$/),
  validate,
];

const goalValidator = [
  check('name', 'Goal name is required').notEmpty().trim(),
  check('targetAmount', 'Target amount must be a positive number').isFloat({ min: 0.01 }),
  check('currentAmount', 'Current amount must be 0 or greater').optional().isFloat({ min: 0 }),
  check('deadline', 'Please provide a valid deadline date').isISO8601(),
  validate,
];

module.exports = {
  registerValidator,
  loginValidator,
  transactionValidator,
  budgetValidator,
  goalValidator,
};
