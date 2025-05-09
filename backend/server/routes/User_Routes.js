const express = require('express');
const router = express.Router();
const User = require('../models/User');

// @route   POST /api/users
// @desc    Create a new user
// @access  Public

router.post('/', async (req, res) => {
  try {
    const { name, userId, email, role, position, isCommuter, isActive} = req.body;

    // Basic Input Validation
    if (!name || !userId || !email || !role || !position) {
      return res.status(400).json({ message: "All fields are required" });
    }
    // Check if the user already exists
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(409).json({ message: "User already exists" });
    }

    // Create and save the user
    const newUser = new User({ name, userId, email, role, position, isCommuter, isActive });
    await newUser.save();

    res.status(201).json({ message: "User created successfully", user: newUser });
  } catch (err) {
      console.error('Error creating user:', err.message);
      res.status(500).json({ message: "Server error" });
  }
});

// @route   GET /api/users
// @desc    Get all users
// @access  Public
router.get('/', async (req, res) => {
  try {
    // Only return name and position (or role) fields
    const users = await User.find({}, 'name position role');
    res.json(users);
  } catch (err) {
    console.error('Error fetching users:', err.message);
    res.status(500).json({ message: "Server error" });
  }
});

router.post('/validate', async (req, res) => {
  const { email } = req.body;
  const cleanedEmail = email.trim().toLowerCase();
  if (!cleanedEmail) return res.status(400).json({ message: 'Email required' });

  // Special-case for admin (optional)
  if (cleanedEmail === 'sudersanamv@msoe.edu') {
    return res.json({
      success: true,
      user: {
        id: 'admin',
        name: 'Admin',
        email: cleanedEmail,
        role: 'admin',
        position: 'Admin'
      }
    });
  }

  const user = await User.findOne({ email: cleanedEmail });
  if (!user) return res.status(401).json({ message: 'User not found' });

  // Check if user is Tier 4
  const isAdmin = user.position === 'Tier 4';

  res.json({
    success: true,
    user: {
      id: user._id,
      name: user.name,
      email: user.email,
      role: isAdmin ? 'admin' : user.role,
      position: user.position
    }
  });
});

module.exports = router;

    