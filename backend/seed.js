const mongoose = require('mongoose');
const dotenv = require('dotenv');
const bcrypt = require('bcryptjs');

// Load Models
const User = require('./models/User');
const Transaction = require('./models/Transaction');
const Budget = require('./models/Budget');
const Goal = require('./models/Goal');

dotenv.config();

const seedData = async () => {
  try {
    // Connect to database
    await mongoose.connect(process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/smart-finance-manager');

    console.log('Clearing existing database contents...');
    await User.deleteMany({});
    await Transaction.deleteMany({});
    await Budget.deleteMany({});
    await Goal.deleteMany({});

    console.log('Seeding Users...');
    
    // Create Admin
    const adminUser = await User.create({
      name: 'Admin Account',
      email: 'admin@smartfinance.com',
      password: 'password123',
      role: 'admin',
      isVerified: true,
      currency: 'USD',
    });

    // Create User
    const standardUser = await User.create({
      name: 'John Doe',
      email: 'john@smartfinance.com',
      password: 'password123',
      role: 'user',
      isVerified: true,
      currency: 'USD',
    });

    console.log('Seeding Budgets...');
    const currentMonth = new Date().toISOString().slice(0, 7); // YYYY-MM

    const budgets = [
      { user: standardUser._id, category: 'Food', amount: 400, month: currentMonth },
      { user: standardUser._id, category: 'Rent', amount: 1500, month: currentMonth },
      { user: standardUser._id, category: 'Transport', amount: 200, month: currentMonth },
      { user: standardUser._id, category: 'Entertainment', amount: 300, month: currentMonth },
      { user: standardUser._id, category: 'Utilities', amount: 250, month: currentMonth },
    ];
    await Budget.insertMany(budgets);

    console.log('Seeding Savings Goals...');
    const now = new Date();
    const threeMonthsLater = new Date(now.getFullYear(), now.getMonth() + 3, now.getDate());
    const sixMonthsLater = new Date(now.getFullYear(), now.getMonth() + 6, now.getDate());

    const goals = [
      {
        user: standardUser._id,
        name: 'Emergency Fund',
        targetAmount: 5000,
        currentAmount: 3500,
        deadline: sixMonthsLater,
        status: 'active',
      },
      {
        user: standardUser._id,
        name: 'New MacBook Pro',
        targetAmount: 2500,
        currentAmount: 2500,
        deadline: now,
        status: 'achieved',
      },
      {
        user: standardUser._id,
        name: 'Summer Trip to Europe',
        targetAmount: 4000,
        currentAmount: 1200,
        deadline: threeMonthsLater,
        status: 'active',
      },
    ];
    await Goal.insertMany(goals);

    console.log('Seeding Transactions...');
    
    // Incomes
    const incomes = [
      {
        user: standardUser._id,
        type: 'income',
        amount: 4500,
        category: 'Salary',
        date: new Date(now.getFullYear(), now.getMonth(), 1), // 1st of current month
        description: 'Monthly payroll salary direct deposit',
      },
      {
        user: standardUser._id,
        type: 'income',
        amount: 800,
        category: 'Freelancing',
        date: new Date(now.getFullYear(), now.getMonth(), 10),
        description: 'UI Design consultant project payout',
      },
      {
        user: standardUser._id,
        type: 'income',
        amount: 150,
        category: 'Investments',
        date: new Date(now.getFullYear(), now.getMonth(), 15),
        description: 'Quarterly stock portfolio dividends',
      },
    ];

    // Expenses
    const expenses = [
      {
        user: standardUser._id,
        type: 'expense',
        amount: 1200,
        category: 'Rent',
        date: new Date(now.getFullYear(), now.getMonth(), 2),
        description: 'Monthly apartment rental lease payment',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 120,
        category: 'Food',
        date: new Date(now.getFullYear(), now.getMonth(), 3),
        description: 'Weekly grocery shopping at Whole Foods',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 45,
        category: 'Food',
        date: new Date(now.getFullYear(), now.getMonth(), 5),
        description: 'Dinner outing with colleagues',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 80,
        category: 'Transport',
        date: new Date(now.getFullYear(), now.getMonth(), 6),
        description: 'Weekly gasoline refueling and tolls',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 150,
        category: 'Entertainment',
        date: new Date(now.getFullYear(), now.getMonth(), 8),
        description: 'Concert event tickets booking online',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 180,
        category: 'Utilities',
        date: new Date(now.getFullYear(), now.getMonth(), 12),
        description: 'Electricity, gas, and high-speed internet bills',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 75,
        category: 'Food',
        date: new Date(now.getFullYear(), now.getMonth(), 16),
        description: 'Mid-month kitchen staples and fruits replenishment',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 55,
        category: 'Transport',
        date: new Date(now.getFullYear(), now.getMonth(), 18),
        description: 'Uber rides for weekend transit',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 310, // Exceeds entertainment budget!
        category: 'Entertainment',
        date: new Date(now.getFullYear(), now.getMonth(), 19),
        description: 'Weekend resort stays and spa therapy',
      },
    ];

    // Seed some transactions for the previous month to enable trend comparison
    const prevMonthDate = new Date(now.getFullYear(), now.getMonth() - 1, 15);
    const prevMonthTransactions = [
      {
        user: standardUser._id,
        type: 'income',
        amount: 4500,
        category: 'Salary',
        date: new Date(now.getFullYear(), now.getMonth() - 1, 1),
        description: 'Previous month payroll salary deposit',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 1200,
        category: 'Rent',
        date: new Date(now.getFullYear(), now.getMonth() - 1, 2),
        description: 'Previous month rental lease payment',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 350,
        category: 'Food',
        date: prevMonthDate,
        description: 'Previous month cumulative groceries spend',
      },
      {
        user: standardUser._id,
        type: 'expense',
        amount: 180,
        category: 'Transport',
        date: prevMonthDate,
        description: 'Previous month fuel and subway tickets',
      },
    ];

    await Transaction.insertMany([...incomes, ...expenses, ...prevMonthTransactions]);

    console.log('Seeding completed successfully!');
    console.log(`====================================================`);
    console.log(`Standard User:`);
    console.log(`Email: john@smartfinance.com | Password: password123`);
    console.log(`----------------------------------------------------`);
    console.log(`Admin User:`);
    console.log(`Email: admin@smartfinance.com | Password: password123`);
    console.log(`====================================================`);
    
    mongoose.connection.close();
  } catch (error) {
    console.error('Seeding failed:', error);
    process.exit(1);
  }
};

seedData();
