// utils/autoAssignFinals.js

const User  = require('../models/User');
const Final = require('../models/Final');

// ─── CONFIG ────────────────────────────────────────────────────────────────────
const TARGET_HOURS = 15;   // aim for 15 hrs/week
const MAX_HOURS    = 20;   // hard cap

const WINDOW_MIN = 1, WINDOW_MAX = 2;
const REMOTE_MIN = 2, REMOTE_MAX = 4;

/**
 * For finals week we’ll break each day into three 4 hr slices:
 *   7:30–11:30, 11:30–15:30 and 15:30–19:30 (or 17:30 on Fri).
 * Feel free to adjust or derive these dynamically if you like.
 */
const DAY_SLICES = {
  '2025-05-12': [['07:30','11:30'], ['11:30','15:30'], ['15:30','19:30']],
  '2025-05-13': [['07:30','11:30'], ['11:30','15:30'], ['15:30','19:30']],
  '2025-05-14': [['07:30','11:30'], ['11:30','15:30'], ['15:30','19:30']],
  '2025-05-15': [['07:30','11:30'], ['11:30','15:30'], ['15:30','19:30']],
  // Friday closes at 17:00
  '2025-05-16': [['07:30','11:30'], ['11:30','15:30']],
};

// ─── HELPERS ───────────────────────────────────────────────────────────────────
function toMinutes(hm) {
  const [h,m] = hm.split(':').map(Number);
  return h*60 + m;
}
function toTime(mins) {
  const h = String(Math.floor(mins/60)).padStart(2,'0');
  const m = String(mins%60).padStart(2,'0');
  return `${h}:${m}`;
}
/**
 * Return true if shift [startTime,endTime] on shift.date
 * overlaps the exam slot.
 */
function isConflict(shift, exam) {
  if (!exam.date) return false;
  if (shift.date.toDateString() !== new Date(exam.date).toDateString())
    return false;
  const s0 = toMinutes( shift.startTime ),
        s1 = toMinutes( shift.endTime   );
  const e0 = toMinutes( exam.startTime ),
        e1 = toMinutes( exam.endTime   );
  return s0 < e1 && s1 > e0;
}

/**
 * Filter `users` who:
 *  • are active
 *  • respect commuter‐before-9 AM rule
 *  • have no exam conflict
 *  • would not exceed the given `hourCap` by taking a shift of length `dur`
 */
function findEligible(users, finals, shift, hoursWorked, dur, hourCap) {
  return users.filter(u => {
    if (!u.isActive)                return false;
    if (u.isCommuter && toMinutes(shift.startTime) < 9*60)
                                    return false;
    if ((hoursWorked[u._id]||0) + dur > hourCap)
                                    return false;
    // no exam conflict
    const myExams = finals.filter(f => f.userId?.toString() === u._id.toString());
    return !myExams.some(exam => isConflict(shift, exam));
  });
}

/**
 * Pick up to N workers from `pool` by:
 *  1) Favour those < TARGET_HOURS
 *  2) Then by least hoursWorked
 *  3) Then by who was assigned least‐recently
 */
function pickWorkers(pool, hoursWorked, N, lastAssigned) {
  const arr = [...pool];
  arr.sort((a,b) => {
    const ha = hoursWorked[a._id]||0, hb = hoursWorked[b._id]||0;
    // favour under TARGET_HOURS
    if (ha < TARGET_HOURS && hb >= TARGET_HOURS) return -1;
    if (hb < TARGET_HOURS && ha >= TARGET_HOURS) return 1;
    // then least hours
    if (ha !== hb) return ha - hb;
    // then round-robin tie-break
    return (lastAssigned[a._id]||0) - (lastAssigned[b._id]||0);
  });
  return arr.slice(0, N);
}

/**
 * After initial pass, loop through under-TARGET_HOURS users
 * and add them to any REMOTE slice that still has < REMOTE_MAX.
 */
function balanceHours(schedule, coreUsers, hoursWorked, finals) {
  const under = coreUsers.filter(u => (hoursWorked[u._id]||0) < TARGET_HOURS);
  under.forEach(u => {
    let need = TARGET_HOURS - (hoursWorked[u._id]||0);
    for (let shift of schedule) {
      if (need <= 0) break;
      if (shift.shiftType !== 'Remote') continue;
      if (shift.assignedTo.length >= REMOTE_MAX) continue;
      // no double‐up
      if (shift.assignedTo.some(x => x._id.toString() === u._id.toString()))
        continue;
      // no exam conflict
      if (finals.some(f => f.userId?.toString()===u._id.toString() && isConflict(shift,f)))
        continue;
      // add them
      shift.assignedTo.push({ _id:u._id, name:u.name });
      const dur = (toMinutes(shift.endTime)-toMinutes(shift.startTime))/60;
      hoursWorked[u._id] += dur;
      need -= dur;
    }
  });
}

// ─── MAIN ─────────────────────────────────────────────────────────────────────
async function autoAssignFinals() {
  const users  = await User.find({ isActive:true });
  const finals = await Final.find();

  const core     = users.filter(u => !u.isFloater);
  const floaters = users.filter(u =>  u.isFloater);

  // track assignment state
  const schedule = [];
  const violations = [];
  const hoursWorked = {};
  const lastWin = {}, lastRem = {};
  users.forEach(u => hoursWorked[u._id] = 0);

  for (let [dateStr, slices] of Object.entries(DAY_SLICES)) {
    for (let [start,end] of slices) {
      const dur = (toMinutes(end) - toMinutes(start)) / 60;
      const shift = { date:new Date(dateStr), startTime:start, endTime:end };

      // 1) WINDOW
      let pool = findEligible(core, finals, shift, hoursWorked, dur, TARGET_HOURS);
      if (pool.length < WINDOW_MIN)
        pool = findEligible(floaters, finals, shift, hoursWorked, dur, MAX_HOURS);
      const winCount = Math.min(WINDOW_MAX, WINDOW_MIN);
      const win = pickWorkers(pool, hoursWorked, winCount, lastWin);
      if (win.length < WINDOW_MIN)
        violations.push(`Window undercovered ${dateStr} ${start}`);
      schedule.push({
        ...shift,
        shiftType: 'Window',
        assignedTo: win.map(u=>({ _id:u._id, name:u.name }))
      });
      win.forEach(u=>{
        hoursWorked[u._id] += dur;
        lastWin[u._id] = Date.now();
      });

      // 2) REMOTE
      pool = findEligible(core, finals, shift, hoursWorked, dur, TARGET_HOURS);
      if (pool.length < REMOTE_MIN)
        pool = findEligible(floaters, finals, shift, hoursWorked, dur, MAX_HOURS);
      const rem = pickWorkers(pool, hoursWorked, REMOTE_MIN, lastRem);
      if (rem.length < REMOTE_MIN)
        violations.push(`Remote undercovered ${dateStr} ${start}`);
      schedule.push({
        ...shift,
        shiftType: 'Remote',
        assignedTo: rem.map(u=>({ _id:u._id, name:u.name }))
      });
      rem.forEach(u=>{
        hoursWorked[u._id] += dur;
        lastRem[u._id] = Date.now();
      });
    }
  }

  // gently top‐off under-TARGET_HOURS core users
  balanceHours(schedule, core, hoursWorked, finals);

  // build summary
  const underworked = core
    .filter(u => hoursWorked[u._id] < TARGET_HOURS)
    .map(u=>({ name:u.name, hours: hoursWorked[u._id].toFixed(1) }));

  return {
    summary: {
      totalBlocks: schedule.length,
      violations,
      underworked,
      allConstraintsMet: violations.length === 0
    },
    schedule
  };
}

module.exports = autoAssignFinals;
