const express = require('express');
const router = express.Router();
const Final = require('../models/Final');

// @route   POST /api/finals
// @desc    Add a final exam for a user
router.post('/', async (req, res) => {
  try {
    const { userId, date, startTime, endTime } = req.body;

    if (!userId || !date || !startTime || !endTime) {
      return res.status(400).json({ message: "All fields are required" });
    }

    const final = new Final({ userId, date, startTime, endTime });
    await final.save();
    res.status(201).json({ message: "Final added", final });
  } catch (err) {
    console.error('Error adding final:', err);
    res.status(500).json({ message: "Server error" });
  }
});

module.exports = router;
