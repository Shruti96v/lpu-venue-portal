const express = require('express');
const router = express.Router();
const { getUsers, deleteUser, getStats } = require('../controllers/adminController');
const { protect, admin } = require('../middlewares/auth');

router.use(protect);
router.use(admin);

router.get('/users', getUsers);
router.delete('/users/:id', deleteUser);
router.get('/stats', getStats);

module.exports = router;
