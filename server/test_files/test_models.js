console.log("Starting test...");

const mongoose = require('mongoose');
require("dotenv").config();

const User = require('./models/User');
const Final = require('./models/Final');
const Shift = require('./models/Shifts');

mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
})
  .then(() => {
    console.log('Connected to MongoDB');
    runTests(); // 
  })
  .catch(err => console.error('Error connecting to MongoDB:', err));

async function runTests() {
  try {
    const newUser = new User({
      name: 'Vamsi Sudersanam',
      userId: '611204',
      email: 'sudersanamv@msoe.edu',
      role: 'admin',
      position: 'Tier 4',
      isCommuter: true,
      isActive: true,
    });

    await newUser.save();
    console.log('New user created:', newUser);

    const newFinal = new Final({
      userId: newUser._id,
      date: new Date('2025-04-29'),
      startTime: '14:00',
      endTime: '16:00'
    });
    await newFinal.save();
    console.log('New final exam created:', newFinal);

    const newShift = new Shift({
      date: new Date('2025-04-29'),
      startTime: '12:00',
      endTime: '14:00',
      assignedTo: newUser._id,
      shiftType: 'Window',
      notes: 'Test shift for final exam'
    });
    
    await newShift.save();
    console.log('New shift created:', newShift);

    const users = await User.find();
    const finals = await Final.find().populate('userId');
    const shifts = await Shift.find().populate('assignedTo');

    console.log('All users:', users);
    console.log('All finals:', finals);
    console.log('All shifts:', shifts);
  } catch (err) {
    console.error('Test Failed:', err);
  } finally {
    await mongoose.disconnect();
    console.log('Disconnected from MongoDB');
  }
}
