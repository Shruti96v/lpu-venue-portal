const express = require('express');
const router = express.Router();
const { getGoals, addGoal, updateGoal, deleteGoal } = require('../controllers/goalController');
const { goalValidator } = require('../middlewares/validators');
const { protect } = require('../middlewares/auth');

router.route('/')
  .get(protect, getGoals)
  .post(protect, goalValidator, addGoal);

router.route('/:id')
  .put(protect, updateGoal)
  .delete(protect, deleteGoal);

module.exports = router;
