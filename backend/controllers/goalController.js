const Goal = require('../models/Goal');

// @desc    Get savings goals
// @route   GET /api/goals
// @access  Private
exports.getGoals = async (req, res, next) => {
  try {
    const goals = await Goal.find({ user: req.user.id });
    res.json({ success: true, count: goals.length, data: goals });
  } catch (error) {
    next(error);
  }
};

// @desc    Create a savings goal
// @route   POST /api/goals
// @access  Private
exports.addGoal = async (req, res, next) => {
  try {
    const { name, targetAmount, currentAmount, deadline } = req.body;

    const goal = await Goal.create({
      user: req.user.id,
      name,
      targetAmount,
      currentAmount: currentAmount || 0,
      deadline,
    });

    res.status(201).json({ success: true, data: goal });
  } catch (error) {
    next(error);
  }
};

// @desc    Update savings goal progress / details
// @route   PUT /api/goals/:id
// @access  Private
exports.updateGoal = async (req, res, next) => {
  try {
    let goal = await Goal.findById(req.params.id);

    if (!goal) {
      return res.status(404).json({ success: false, message: 'Savings goal not found' });
    }

    if (goal.user.toString() !== req.user.id) {
      return res.status(401).json({ success: false, message: 'Not authorized to edit this savings goal' });
    }

    // Automatically set status to 'achieved' if currentAmount >= targetAmount
    const updates = { ...req.body };
    if (updates.currentAmount !== undefined) {
      if (updates.currentAmount >= goal.targetAmount) {
        updates.status = 'achieved';
      } else {
        updates.status = 'active';
      }
    }

    goal = await Goal.findByIdAndUpdate(req.params.id, updates, {
      new: true,
      runValidators: true,
    });

    res.json({ success: true, data: goal });
  } catch (error) {
    next(error);
  }
};

// @desc    Delete a savings goal
// @route   DELETE /api/goals/:id
// @access  Private
exports.deleteGoal = async (req, res, next) => {
  try {
    const goal = await Goal.findById(req.params.id);

    if (!goal) {
      return res.status(404).json({ success: false, message: 'Savings goal not found' });
    }

    if (goal.user.toString() !== req.user.id) {
      return res.status(401).json({ success: false, message: 'Not authorized to delete this savings goal' });
    }

    await goal.deleteOne();

    res.json({ success: true, message: 'Savings goal deleted successfully' });
  } catch (error) {
    next(error);
  }
};
