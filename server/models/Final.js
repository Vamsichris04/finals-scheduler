// Represents a sibgle final exam for a user
// and stores the date and time of the exam

const mongoose = require('mongoose');

const finalSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true,  unique: true },
    date: { type: Date, required: true },
    startTime: { type: String, required: true }, // e.g. "14:00"
    endTime: { type: String, required: true }     // e.g. "16:00"
});

module.exports = mongoose.model('Final', finalSchema);
