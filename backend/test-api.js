const { spawn } = require('child_process');
const path = require('path');

const PORT = 5005;
const BASE_URL = `http://127.0.0.1:${PORT}/api`;

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runTests() {
  console.log('Starting integration test suite...');
  let token = '';
  let adminToken = '';
  let expenseId = '';

  try {
        // 1. Authenticate Standard User
    console.log('\nTesting Auth: User Login...');
    const loginRes = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'john@smartfinance.com', password: 'password123' }),
    });
    
    if (!loginRes.ok) {
      const errText = await loginRes.text();
      throw new Error(`User login HTTP error: ${loginRes.status} - ${errText}`);
    }
    
    const loginData = await loginRes.json();
    if (!loginData.success) throw new Error('User login failed');
    token = loginData.token;
    console.log('✔ User logged in successfully.');

    // 2. Fetch Dashboard Statistics
    console.log('\nTesting Dashboard: Get Dashboard Summary...');
    const dashRes = await fetch(`${BASE_URL}/dashboard`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const dashData = await dashRes.json();
    if (!dashData.success) throw new Error('Failed to fetch dashboard');
    console.log(`✔ Dashboard loaded. Monthly Balance: $${dashData.data.monthly.income - dashData.data.monthly.expense}`);

    // 3. Add Expense
    console.log('\nTesting Expenses: Create Expense...');
    const addExpenseRes = await fetch(`${BASE_URL}/expenses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        amount: 85,
        category: 'Food',
        date: new Date().toISOString(),
        description: 'Integration test meal',
      }),
    });
    const addExpenseData = await addExpenseRes.json();
    if (!addExpenseData.success) throw new Error('Failed to add expense');
    expenseId = addExpenseData.data._id;
    console.log(`✔ Expense added. ID: ${expenseId}`);

    // 4. Get Expenses (Verify Filters)
    console.log('\nTesting Expenses: Query Expenses (Search and Category filter)...');
    const queryRes = await fetch(`${BASE_URL}/expenses?search=Integration&category=Food`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const queryData = await queryRes.json();
    if (!queryData.success || queryData.data.length === 0) throw new Error('Query validation failed');
    console.log(`✔ Expenses query matches exactly. Count: ${queryData.count}`);

    // 5. Update Expense
    console.log('\nTesting Expenses: Update Expense...');
    const updateRes = await fetch(`${BASE_URL}/expenses/${expenseId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        amount: 95,
        category: 'Food',
        description: 'Integration test meal updated',
      }),
    });
    const updateData = await updateRes.json();
    if (!updateData.success || updateData.data.amount !== 95) throw new Error('Update validation failed');
    console.log(`✔ Expense updated successfully to $${updateData.data.amount}.`);

    // 6. Delete Expense
    console.log('\nTesting Expenses: Delete Expense...');
    const delRes = await fetch(`${BASE_URL}/expenses/${expenseId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    const delData = await delRes.json();
    if (!delData.success) throw new Error('Delete expense failed');
    console.log('✔ Expense deleted successfully.');

    // 7. Get Budgets
    console.log('\nTesting Budgets: Get Monthly Budgets...');
    const budgetRes = await fetch(`${BASE_URL}/budgets`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const budgetData = await budgetRes.json();
    if (!budgetData.success) throw new Error('Failed to fetch budgets');
    console.log(`✔ Budgets retrieved. Total categories budgeted: ${budgetData.data.length}`);

    // 8. Set Budget
    console.log('\nTesting Budgets: Set/Update Budget...');
    const setBudgetRes = await fetch(`${BASE_URL}/budgets`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        category: 'Books',
        amount: 150,
      }),
    });
    const setBudgetData = await setBudgetRes.json();
    if (!setBudgetData.success) throw new Error('Failed to set budget');
    console.log(`✔ Budget set for category 'Books' at $150.`);

    // 9. Get Savings Goals
    console.log('\nTesting Goals: Get Savings Goals...');
    const goalRes = await fetch(`${BASE_URL}/goals`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const goalData = await goalRes.json();
    if (!goalData.success) throw new Error('Failed to fetch goals');
    console.log(`✔ Goals retrieved. Count: ${goalData.count}`);

    // 10. Admin Authentication
    console.log('\nTesting Admin: Authenticate Admin...');
    const adminLoginRes = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'admin@smartfinance.com', password: 'password123' }),
    });
    const adminLoginData = await adminLoginRes.json();
    if (!adminLoginData.success) throw new Error('Admin login failed');
    adminToken = adminLoginData.token;
    console.log('✔ Admin authenticated.');

    // 11. Admin Get Users
    console.log('\nTesting Admin: Get User Directory...');
    const adminUsersRes = await fetch(`${BASE_URL}/admin/users`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    const adminUsersData = await adminUsersRes.json();
    if (!adminUsersData.success) throw new Error('Admin get users failed');
    console.log(`✔ User directory fetched. Users count: ${adminUsersData.count}`);

    // 12. Admin Get Platform Stats
    console.log('\nTesting Admin: Get Platform Stats...');
    const adminStatsRes = await fetch(`${BASE_URL}/admin/stats`, {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    const adminStatsData = await adminStatsRes.json();
    if (!adminStatsData.success) throw new Error('Admin get stats failed');
    console.log(`✔ Admin stats fetched. Active registered users: ${adminStatsData.data.counts.users}`);

    console.log('\n=======================================');
    console.log('🎉 ALL INTEGRATION TESTS PASSED SUCCESSFULLY!');
    console.log('=======================================');
    return true;
  } catch (error) {
    console.error('\n❌ TEST FAILED:', error.message);
    return false;
  }
}

// Spin up server, run tests, and shut down
async function main() {
  console.log('Starting Express server for testing...');
  const serverPath = path.join(__dirname, 'server.js');
  const serverProc = spawn('node', [serverPath], {
    env: { ...process.env, PORT: PORT.toString(), NODE_ENV: 'test' },
    stdio: 'inherit',
  });

  // Give the server 3 seconds to spin up and connect to MongoDB
  await wait(3000);

  const testsPassed = await runTests();

  console.log('Shutting down testing Express server...');
  serverProc.kill();
  
  process.exit(testsPassed ? 0 : 1);
}

main();
