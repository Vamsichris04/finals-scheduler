const User = require('../models/User');
const Shift = require('../models/Shifts');
const Final = require('../models/Final');

// Check if two time slots overlap
function isConflict(final, shift) {
    const finalStart = new Date(`${final.date}T${final.startTime}`);
    const finalEnd = new Date(`${final.date}T${final.endTime}`);
    const shiftStart = new Date(`${shift.date}T${shift.startTime}`);
    const shiftEnd = new Date(`${shift.date}T${shift.endTime}`);

    return (
        (shiftStart >= finalStart && shiftStart < finalEnd) ||
        (shiftEnd > finalStart && shiftEnd <= finalEnd) ||
        (shiftStart <= finalStart && shiftEnd >= finalEnd)
      );
    }

 /**
 * Auto assign available users to shifts
 */
async function autoAssignShifts() {
    const users = await User.find();
    const finals = await Final.find();
    const shifts = await Shift.find();
  
    const assignedShifts = [];
  
    for (let shift of shifts) {
      for (let user of users) {
        const userFinals = finals.filter(f => f.userId.toString() === user._id.toString());
        const hasConflict = userFinals.some(final => isConflict(final, shift));
  
        if (!hasConflict) {
          // Assign this user to the shift
          shift.assignedTo = user._id;
          await shift.save();
          assignedShifts.push({ shiftId: shift._id, user: user.name });
          break; // stop looking, one person per shift
        }
      }
    }
    
    return assignedShifts;
  }
  
  module.exports = autoAssignShifts;