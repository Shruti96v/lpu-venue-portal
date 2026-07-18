const Transaction = require('../models/Transaction');

// @desc    Get transactions (Income / Expense)
// @route   GET /api/transactions
// @access  Private
exports.getTransactions = async (req, res, next) => {
  try {
    const { type, category, startDate, endDate, search, sortBy, page = 1, limit = 10 } = req.query;

    const query = { user: req.user.id };

    // Apply filters
    if (type) {
      query.type = type;
    }
    if (category) {
      query.category = category;
    }
    if (startDate || endDate) {
      query.date = {};
      if (startDate) {
        query.date.$gte = new Date(startDate);
      }
      if (endDate) {
        query.date.$lte = new Date(endDate);
      }
    }
    if (search) {
      query.$or = [
        { category: { $regex: search, $options: 'i' } },
        { description: { $regex: search, $options: 'i' } },
      ];
    }

    // Build sort options
    let sortOption = { date: -1 }; // Default: Newest first
    if (sortBy) {
      const parts = sortBy.split(':');
      sortOption[parts[0]] = parts[1] === 'desc' ? -1 : 1;
    }

    // Parse pagination variables
    const pageNum = parseInt(page, 10);
    const limitNum = parseInt(limit, 10);
    const skip = (pageNum - 1) * limitNum;

    // Fetch transactions & count total matching
    const transactions = await Transaction.find(query)
      .sort(sortOption)
      .skip(skip)
      .limit(limitNum);

    const total = await Transaction.countDocuments(query);

    res.json({
      success: true,
      count: transactions.length,
      pagination: {
        total,
        page: pageNum,
        pages: Math.ceil(total / limitNum),
        limit: limitNum,
      },
      data: transactions,
    });
  } catch (error) {
    next(error);
  }
};

// @desc    Add a transaction (Income / Expense)
// @route   POST /api/transactions
// @access  Private
exports.addTransaction = async (req, res, next) => {
  try {
    const { type, amount, category, date, description } = req.body;

    const transaction = await Transaction.create({
      user: req.user.id,
      type,
      amount,
      category,
      date: date || new Date(),
      description,
    });

    res.status(201).json({ success: true, data: transaction });
  } catch (error) {
    next(error);
  }
};

// @desc    Update a transaction
// @route   PUT /api/transactions/:id
// @access  Private
exports.updateTransaction = async (req, res, next) => {
  try {
    let transaction = await Transaction.findById(req.params.id);

    if (!transaction) {
      return res.status(404).json({ success: false, message: 'Transaction not found' });
    }

    // Verify ownership
    if (transaction.user.toString() !== req.user.id) {
      return res.status(401).json({ success: false, message: 'Not authorized to edit this transaction' });
    }

    transaction = await Transaction.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true,
    });

    res.json({ success: true, data: transaction });
  } catch (error) {
    next(error);
  }
};

// @desc    Delete a transaction
// @route   DELETE /api/transactions/:id
// @access  Private
exports.deleteTransaction = async (req, res, next) => {
  try {
    const transaction = await Transaction.findById(req.params.id);

    if (!transaction) {
      return res.status(404).json({ success: false, message: 'Transaction not found' });
    }

    // Verify ownership
    if (transaction.user.toString() !== req.user.id) {
      return res.status(401).json({ success: false, message: 'Not authorized to delete this transaction' });
    }

    await transaction.deleteOne();

    res.json({ success: true, message: 'Transaction deleted successfully' });
  } catch (error) {
    next(error);
  }
};
