const mongoose = require('mongoose');

const  userSchema = new mongoose.Schema({
  name: { type: String, required: true, unique: true },
  userId : { type: Number, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  role: { type: String, enum: ['user', 'admin'], default: 'user' },
  position: {type: String, enum: ['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4'], default: 'Tier1'},
  isCommuter: { type: Boolean, default: false },
  isActive: { type: Boolean, default: true },
  desiredHours: { type: Number, default: 12, max: 20, min: 10 },
});

module.exports = mongoose.model('User', userSchema);
