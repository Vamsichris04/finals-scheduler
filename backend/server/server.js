const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const finalRoutes = require('./routes/Final_Routes'); 
const userRoutes = require('./routes/User_Routes'); 
const shiftRoutes = require('./routes/Shift_Routes'); 

console.log("TYPE finalRoutes", typeof finalRoutes);
console.log("TYPE userRoutes", typeof userRoutes);
console.log("TYPE shiftRoutes", typeof shiftRoutes);

const app = express();
app.use(cors());
app.use(express.json());
// Test the connection to MongoDB
console.log("DEBUG MONGO_URI:", process.env.MONGO_URI);

mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('MongoDB connected'))
  .catch(err => {
    console.error('MongoDB connection error:', err.message);
  });

app.use('/api/users', userRoutes);
app.use('/api/finals', finalRoutes);
app.use('/api/shifts', shiftRoutes);
app.use('/api/validate', userRoutes);
app.use('/api/users/validate', userRoutes);

// Start the server
app.listen(5000, () => console.log('Server started on port 5000'));

