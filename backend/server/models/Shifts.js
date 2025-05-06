const mongoose = require('mongoose');

const shiftSchema = new mongoose.Schema({
  date: { type: Date, required: true },
  startTime: { type: String, required: true },
  endTime: { type: String, required: true },
  assignedTo: { type: mongoose.Schema.Types.ObjectId, ref: 'User', default: null },
  shiftType: { type: String, enum: ['Window', 'Remote', 'Tier2', 'Tier3'], required: true },
  notes: { type: String, default: '' },
  
});

module.exports = mongoose.model('Shift', shiftSchema);
