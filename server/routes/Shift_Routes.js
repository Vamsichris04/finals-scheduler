const express = require('express');
const router = express.Router();
const Shift = require('../models/Shifts');
const autoAssignFinals = require('../utils/autoAssignFinals');

// @route   POST /api/shifts
// @desc    Add a new shift
// @access  Public

router.post('/finalschedule', async (req, res) => {
  try {
    const result = await autoAssignFinals();
    res.status(200).json(result);
  } catch (err) {
    console.error("Finals week V2 assignment failed:", err);
    res.status(500).json({ message: "Server error" });
  }
});

  

router.post('/', async (req, res) => {
    try {
        const { date, startTime, endTime, shiftType, notes, assignedTo } = req.body;

        const newShift = new Shift({
            date,
            startTime,
            endTime,
            shiftType,
            notes,
            assignedTo: assignedTo || null
        });

        await newShift.save();
        res.status(201).json({ message: "Shift created", shift: newShift });
    } catch (err) {
        console.error("Error creating shift:", err.message);
        res.status(500).json({ message: "Server error" });
    }
});

module.exports = router;
