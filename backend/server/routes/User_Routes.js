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

module.exports = router;

    