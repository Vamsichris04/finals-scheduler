const User  = require('../models/User');
const Final = require('../models/Final');

const businessHours = {
  '2025-05-12': ['07:30','20:00'], // Mon–Thu 7:30–20:00
  '2025-05-13': ['07:30','20:00'],
  '2025-05-14': ['07:30','20:00'],
  '2025-05-15': ['07:30','20:00'],
  '2025-05-16': ['07:30','17:00'], // Fri 7:30–17:00
};

const MAX_HOURS    = 20;
const TARGET_HOURS = 15;

// Convert HH:MM → total minutes
function toMinutes(t){ const [h,m]=t.split(':').map(Number); return h*60+m; }
// Convert minutes → HH:MM
function toTime(m){ return `${String(Math.floor(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`; }

/**
 * 1) Subtract each student’s finals from the business hours to get
 *    an array of free intervals per user.
 */
function getFreeIntervals(users, finals){
  // … compute for each user a list of { date, start, end } where they are free …
  return /* { userId: [ {date, start, end}, … ], … } */;
}

/**
 * 2) Chop each free‐interval into 3–4 hr blocks, return global list:
 *    [ { date, startTime, endTime, freeUsers: [userId,…] }, … ]
 */
function generateTimeBlocks(freeIntervals){
  // … for each user-interval and businessHours, split into 3–4 hr blocks …
  return /* array of blocks with a freeUsers list */;
}

/**
 * 3) Greedy + round‐robin assign Window (1–2 ppl) & Remote (2–4 ppl)
 *    based on how far each is from TARGET_HOURS.
 */
function assignShifts(blocks, users, schedule, hoursWorked){
  // maintain a round-robin index per blockTime
  blocks.forEach(block => {
    const dur = (toMinutes(block.endTime)-toMinutes(block.startTime))/60;
    // WINDOW: need 1–2
    let candidates = block.freeUsers.filter(u=>hoursWorked[u]<MAX_HOURS);
    // sort by (hoursWorked < TARGET_HOURS) first, then asc hours
    candidates.sort((a,b)=>(
      (hoursWorked[a]<TARGET_HOURS?0:1) - (hoursWorked[b]<TARGET_HOURS?0:1)
      || hoursWorked[a]-hoursWorked[b]
    ));
    const windowPicks = candidates.splice(0, Math.min(2, candidates.length, 1)); 
    windowPicks.forEach(u=>{
      schedule.push({ ...block, shiftType:'Window', assignedTo:[u] });
      hoursWorked[u]+=dur;
    });
    // REMOTE: need 2–4
    candidates = block.freeUsers.filter(u=>hoursWorked[u]<MAX_HOURS);
    candidates.sort((a,b)=>(
      (hoursWorked[a]<TARGET_HOURS?0:1) - (hoursWorked[b]<TARGET_HOURS?0:1)
      || hoursWorked[a]-hoursWorked[b]
    ));
    const remotePicks = candidates.splice(0, Math.min(4, candidates.length, 2));
    schedule.push({ ...block, shiftType:'Remote', assignedTo:remotePicks });
    remotePicks.forEach(u=> hoursWorked[u]+=dur );
  });
}

/**
 * 4) Fill any blocks missing minimum coverage using floaters.
 */
function fillWithFloaters(schedule, nonFloaters, floaters, hoursWorked){
  schedule.forEach(shift=>{
    const dur = (toMinutes(shift.endTime)-toMinutes(shift.startTime))/60;
    const needed = shift.shiftType==='Window'
      ? 1 - shift.assignedTo.length
      : 2 - shift.assignedTo.length;
    if (needed>0){
      // pick floaters who are free and under MAX_HOURS
      let cands = floaters.filter(u=>
        hoursWorked[u._id]+dur<=MAX_HOURS
      );
      cands.sort((a,b)=>hoursWorked[a._id]-hoursWorked[b._id]);
      cands.slice(0,needed).forEach(f=>{
        shift.assignedTo.push(f._id);
        hoursWorked[f._id]+=dur;
      });
    }
  });
}

/**
 * 5) Summary & underworked
 */
function getSummary(schedule, users, hoursWorked){
  const underworked = users
    .filter(u=>hoursWorked[u._id]<TARGET_HOURS)
    .map(u=>({ name:u.name, hours:hoursWorked[u._id] }));
  return { schedule, underworked };
}

module.exports = async function autoAssignFinalsV3(){
  const users  = await User.find({ isActive:true });
  const finals = await Final.find();
  const nonFloaters = users.filter(u=>!u.isFloater);
  const floaters    = users.filter(u=>u.isFloater);
  const hoursWorked = Object.fromEntries(users.map(u=>[u._id,0]));

  const freeIntervals = getFreeIntervals(users, finals);
  const blocks        = generateTimeBlocks(freeIntervals);
  const schedule = [];

  assignShifts(blocks, users, schedule, hoursWorked);
  fillWithFloaters(schedule, nonFloaters, floaters, hoursWorked);

  console.log('=== Total Hours Worked ===');
  users.forEach(u=>
    console.log(u.name, hoursWorked[u._id].toFixed(2))
  );

  return getSummary(schedule, users, hoursWorked);
};
