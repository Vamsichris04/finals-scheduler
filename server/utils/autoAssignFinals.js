// utils/autoAssignFinals.js

const User  = require('../models/User');
const Final = require('../models/Final');

// === CONFIG ===
const businessHours = {
    '2025-05-12': ['07:30', '20:00'],
    '2025-05-13': ['07:30', '20:00'],
    '2025-05-14': ['07:30', '20:00'],
    '2025-05-15': ['07:30', '20:00'],
    '2025-05-16': ['07:30', '17:00'],
};

const TARGET_HOURS = 15;
const MAX_HOURS    = 20;

const WINDOW_MIN = 1, WINDOW_MAX = 2;
const REMOTE_MIN = 2, REMOTE_MAX = 4;

// === HELPERS ===
function toMinutes(hm) {
    const [h, m] = hm.split(':').map(Number);
    return h * 60 + m;
}
function toTime(mins) {
    const h = String(Math.floor(mins / 60)).padStart(2, '0');
    const m = String(mins % 60).padStart(2, '0');
    return `${h}:${m}`;
}

function roundUpToHour(minutes) {
    return Math.ceil(minutes / 60) * 60;
}

// Build flexible time blocks for a day, ending on the hour
function generateTimeBlocksForDay(dateStr, start, end) {
    const out = [];
    let cur = roundUpToHour(toMinutes(start));
    const endMin = toMinutes(end);
    const minBlockSize = 120; // 2 hours in minutes

    while (cur < endMin) {
        for (let duration = 120; duration <= 240; duration += 60) { // 2, 3, or 4 hour blocks
            const blockEnd = cur + duration;
            if (blockEnd <= endMin && blockEnd % 60 === 0) {
                out.push({
                    date: new Date(dateStr),
                    startTime: toTime(cur),
                    endTime: toTime(blockEnd),
                });
            }
        }
        cur += 60; // Move by the smallest time unit (1 hour for potential starts)
    }

    // Simple approach to avoid too many overlapping blocks: filter and ensure reasonable spacing
    const filteredOut = [];
    if (out.length > 0) {
        filteredOut.push(out[0]);
        for (let i = 1; i < out.length; i++) {
            const lastBlockEnd = toMinutes(filteredOut[filteredOut.length - 1].endTime);
            if (toMinutes(out[i].startTime) >= lastBlockEnd) {
                filteredOut.push(out[i]);
            }
        }
    }
    return filteredOut;
}

// Does shift conflict exam?
function isConflict(shift, exam) {
    if (!exam.date) return false;
    if (shift.date.toDateString() !== new Date(exam.date).toDateString()) return false;
    const s0 = toMinutes(shift.startTime), s1 = toMinutes(shift.endTime);
    const e0 = toMinutes(exam.startTime),  e1 = toMinutes(exam.endTime);
    return s0 < e1 && s1 > e0;
}

// Stage-based eligible finder
function findEligible(users, finals, shift, hoursWorked, dur, minStage) {
    return users.filter(u => {
        if (!u.isActive) return false;
        if (u.isCommuter && toMinutes(shift.startTime) < 9 * 60) return false;
        if ((hoursWorked[u._id] || 0) + dur > (minStage === 2 ? MAX_HOURS : TARGET_HOURS)) return false;
        const myExams = finals.filter(f => f.userId?.toString() === u._id.toString());
        return !myExams.some(ex => isConflict(shift, ex));
    });
}

// pick up to N workers by least‐hours (with round robin tie-breaker)
function pickWorkers(pool, hoursWorked, N, lastAssigned = {}) {
    pool.sort((a, b) => {
        const hoursA = hoursWorked[a._id] || 0;
        const hoursB = hoursWorked[b._id] || 0;

        // Prioritize workers below TARGET_HOURS
        if (hoursA < TARGET_HOURS && hoursB >= TARGET_HOURS) return -1;
        if (hoursB < TARGET_HOURS && hoursA >= TARGET_HOURS) return 1;

        // Sort by least hours worked
        if (hoursA !== hoursB) return hoursA - hoursB;

        // Round-robin tie-breaker
        return (lastAssigned[a._id] || 0) - (lastAssigned[b._id] || 0);
    });
    return pool.slice(0, N);
}

// Calculate free time for workers
function calculateFreeTime(businessHours, finals) {
  // Subtract finals from business hours to get free time
  // Return an array of free intervals for each worker
}

// Balance hours across workers
function balanceHours(schedule, users, hoursWorked) {
  const underworkedUsers = users.filter(u => hoursWorked[u._id] < TARGET_HOURS);

  underworkedUsers.forEach(user => {
    let neededHours = TARGET_HOURS - hoursWorked[user._id];

    schedule.forEach(shift => {
      if (neededHours <= 0) return;
      if (shift.shiftType !== 'Remote' || shift.assignedTo.length >= 4) return;

      const duration = Math.min(4, TARGET_HOURS - hoursWorked[user._id]);
      if (hoursWorked[user._id] + duration > MAX_HOURS) return;

      const hasConflict = shift.assignedTo.some(w => w._id === user._id);
      if (hasConflict) return;

      shift.assignedTo.push({ _id: user._id, name: user.name });
      hoursWorked[user._id] += duration;
      neededHours -= duration;
    });
  });
}

// ================= MAIN =================
async function autoAssignFinals() {
    const users  = await User.find({ isActive: true });
    const finals = await Final.find();

    const core     = users.filter(u => !u.isFloater);
    const floaters = users.filter(u => u.isFloater);

    const schedule   = [];
    const violations = [];
    const hoursWorked = {};
    const lastAssignedWindow = {};
    const lastAssignedRemote = {};
    users.forEach(u => hoursWorked[u._id] = 0);

    // iterate each day/ block
    for (const [dateStr, [bs, be]] of Object.entries(businessHours)) {
        const blocks = generateTimeBlocksForDay(dateStr, bs, be);

        for (const block of blocks) {
            const dur = (toMinutes(block.endTime) - toMinutes(block.startTime)) / 60;

            // --- Find all eligible workers for this block ---
            let eligibleCore = findEligible(core, finals, block, hoursWorked, dur, 1);
            if (!eligibleCore.length) eligibleCore = findEligible(core, finals, block, hoursWorked, dur, 2);
            let eligibleFloaters = findEligible(floaters, finals, block, hoursWorked, dur, 2);
            const allEligible = [...eligibleCore, ...eligibleFloaters];

            console.log(`Assigning shift: ${block.startTime}–${block.endTime}`);
            console.log(`Eligible workers: ${allEligible.map(u => u.name).join(', ')}`);

            // --- Assign Window ---
            const currentWindowAssignments = schedule.filter(s =>
                s.shiftType === 'Window' &&
                s.date.toDateString() === block.date.toDateString() &&
                toMinutes(s.startTime) === toMinutes(block.startTime)
            ).length;

            const neededWindow = Math.max(0, WINDOW_MIN - currentWindowAssignments);
            const canAssignWindow = Math.min(WINDOW_MAX - currentWindowAssignments, allEligible.length);
            const numToAssignWindow = Math.min(canAssignWindow, neededWindow);

            const windowEligible = allEligible.filter(u => !schedule.some(s =>
                s.shiftType === 'Window' &&
                s.date.toDateString() === block.date.toDateString() &&
                toMinutes(s.startTime) === toMinutes(block.startTime) &&
                s.assignedTo.some(assignee => assignee._id.toString() === u._id.toString())
            ));

            const windowWorkers = pickWorkers(windowEligible, hoursWorked, numToAssignWindow, lastAssignedWindow);
            if (windowWorkers.length < neededWindow) {
                violations.push(`Window undercovered ${dateStr} ${block.startTime}`);
            }
            if (windowWorkers.length < WINDOW_MIN) {
                // Assign floaters to fill the gap
            }
            schedule.push({
                date: block.date, startTime: block.startTime, endTime: block.endTime,
                shiftType: 'Window',
                assignedTo: windowWorkers.map(u => ({ _id: u._id, name: u.name }))
            });
            windowWorkers.forEach(u => { hoursWorked[u._id] += dur; lastAssignedWindow[u._id] = Date.now(); });

            // --- Assign Remote ---
            const currentRemoteAssignments = schedule.filter(s =>
                s.shiftType === 'Remote' &&
                s.date.toDateString() === block.date.toDateString() &&
                toMinutes(s.startTime) === toMinutes(block.startTime)
            ).length;

            const neededRemote = Math.max(0, REMOTE_MIN - currentRemoteAssignments);
            const canAssignRemote = Math.min(REMOTE_MAX - currentRemoteAssignments, allEligible.length - windowWorkers.length);
            const numToAssignRemote = Math.min(canAssignRemote, neededRemote);

            const remoteEligible = allEligible.filter(u =>
                !windowWorkers.some(ww => ww._id.toString() === u._id.toString()) &&
                !schedule.some(s =>
                    s.shiftType === 'Remote' &&
                    s.date.toDateString() === block.date.toDateString() &&
                    toMinutes(s.startTime) === toMinutes(block.startTime) &&
                    s.assignedTo.some(assignee => assignee._id.toString() === u._id.toString())
                )
            );

            const remoteWorkers = pickWorkers(remoteEligible, hoursWorked, numToAssignRemote, lastAssignedRemote);
            if (remoteWorkers.length < neededRemote) {
                violations.push(`Remote undercovered ${dateStr} ${block.startTime}`);
            }
            if (remoteWorkers.length < REMOTE_MIN) {
                // Assign floaters to fill the gap
            }
            schedule.push({
                date: block.date, startTime: block.startTime, endTime: block.endTime,
                shiftType: 'Remote',
                assignedTo: remoteWorkers.map(u => ({ _id: u._id, name: u.name }))
            });
            remoteWorkers.forEach(u => { hoursWorked[u._id] += dur; lastAssignedRemote[u._id] = Date.now(); });
        }
    }

    // summary of under-target
    const under = users
        .filter(u => (hoursWorked[u._id] || 0) < TARGET_HOURS)
        .map(u => ({ name: u.name, hours: (hoursWorked[u._id] || 0).toFixed(2) }));

    // Log total hours for each worker
    console.log('=== Total Hours Worked (Monday through Friday) ===');
    users.forEach(u => {
        const hrs = (hoursWorked[u._id] || 0).toFixed(2);
        console.log(`User: ${u.name}, Total Hours: ${hrs}`);
    });

    return {
        summary: {
            totalBlocks: schedule.length,
            violations,
            underworked: under,
            allConstraintsMet: violations.length === 0
        },
        schedule
    };
}

module.exports = autoAssignFinals;