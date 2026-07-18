const express = require('express');
const router = express.Router();
const { getBudgets, setBudget } = require('../controllers/budgetController');
const { budgetValidator } = require('../middlewares/validators');
const { protect } = require('../middlewares/auth');

router.route('/')
  .get(protect, getBudgets)
  .post(protect, budgetValidator, setBudget);

module.exports = router;
