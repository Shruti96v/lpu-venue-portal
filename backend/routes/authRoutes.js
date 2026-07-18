const express = require('express');
const router = express.Router();
const { register, login, forgotPassword, resetPassword, getProfile, updateProfile, deleteProfile } = require('../controllers/authController');
const { registerValidator, loginValidator } = require('../middlewares/validators');
const { protect } = require('../middlewares/auth');

router.post('/register', registerValidator, register);
router.post('/login', loginValidator, login);
router.post('/forgot-password', forgotPassword);
router.post('/reset-password', resetPassword);

router.route('/profile')
  .get(protect, getProfile)
  .put(protect, updateProfile)
  .delete(protect, deleteProfile);

module.exports = router;
