from typing import List, Dict, Any, Tuple

# Shared helpers and constraint/evaluation functions used by algorithms
TARGET_HOURS = 15.0
MAX_HOURS = 20.0
WINDOW_MIN, WINDOW_MAX = 1, 2
REMOTE_MIN, REMOTE_MAX = 1, 4
MAX_MORNING_SHIFTS = 2


def to_minutes(hm: str) -> int:
    h, m = map(int, hm.split(':'))
    return h * 60 + m


def duration_hours(start: str, end: str) -> float:
    return (to_minutes(end) - to_minutes(start)) / 60.0


def commuter_blocked(user: Dict[str, Any], slot: Dict[str, Any]) -> bool:
    if not user.get('isCommuter'):
        return False
    return to_minutes(slot['start_time']) < 9 * 60


def busy_conflict(user: Dict[str, Any], slot: Dict[str, Any]) -> bool:
    day = slot.get('day_name')
    if not day:
        return False
    busy = user.get('busy_times', {}).get(day, [])
    s = to_minutes(slot['start_time']); e = to_minutes(slot['end_time'])
    for b in busy:
        if isinstance(b, str) and '-' in b:
            bs, be = b.split('-', 1)
        elif isinstance(b, (list, tuple)) and len(b) >= 2:
            bs, be = b[0], b[1]
        else:
            continue
        if s < to_minutes(be) and e > to_minutes(bs):
            return True
    return False


def exam_conflict(user: Dict[str, Any], slot: Dict[str, Any]) -> bool:
    exams = user.get('exam_times', [])
    s = to_minutes(slot['start_time']); e = to_minutes(slot['end_time'])
    for ex in exams:
        if len(ex) < 3:
            continue
        ex_date, ex_s, ex_e = ex[0], ex[1], ex[2]
        if ex_date != slot['date']:
            continue
        if s < to_minutes(ex_e) and e > to_minutes(ex_s):
            return True
    return False


def eligible(user: Dict[str, Any], slot: Dict[str, Any], hours_by_user: Dict[str, float], hour_cap: float) -> bool:
    if not user.get('isActive', True):
        return False
    if commuter_blocked(user, slot):
        return False
    if busy_conflict(user, slot):
        return False
    if exam_conflict(user, slot):
        return False
    dur = duration_hours(slot['start_time'], slot['end_time'])
    if hours_by_user.get(str(user['_id']), 0.0) + dur > hour_cap:
        return False
    return True


def evaluate_schedule(assignments: List[Dict[str, Any]], users: List[Dict[str, Any]], slots: List[Dict[str, Any]]) -> Dict[str, Any]:
    penalty = 0.0
    hours_by_user: Dict[str, float] = { str(u['_id']): 0.0 for u in users }
    morning_counts: Dict[str, int] = { str(u['_id']): 0 for u in users }

    slot_map: Dict[Tuple[str,str,str,str], List[str]] = {}
    for a in assignments:
        key = (a['date'], a['start_time'], a['end_time'], a['shift_type'])
        slot_map.setdefault(key, []).append(str(a['worker_id']))
        dur = duration_hours(a['start_time'], a['end_time'])
        hours_by_user[str(a['worker_id'])] = hours_by_user.get(str(a['worker_id']), 0.0) + dur
        if to_minutes(a['start_time']) < 12 * 60:
            morning_counts[str(a['worker_id'])] = morning_counts.get(str(a['worker_id']), 0) + 1

    for s in slots:
        key = (s['date'], s['start_time'], s['end_time'], s['shift_type'])
        assigned = slot_map.get(key, [])
        min_req = WINDOW_MIN if s['shift_type'] == 'Window' else REMOTE_MIN
        max_req = WINDOW_MAX if s['shift_type'] == 'Window' else REMOTE_MAX
        if len(assigned) < min_req:
            penalty += (min_req - len(assigned)) * 100.0
        if len(assigned) > max_req:
            penalty += (len(assigned) - max_req) * 20.0

    for uid, hrs in hours_by_user.items():
        if hrs > MAX_HOURS:
            penalty += (hrs - MAX_HOURS) * 50.0
        else:
            if hrs < TARGET_HOURS:
                penalty += (TARGET_HOURS - hrs) * 1.0

    for uid, m in morning_counts.items():
        if m > MAX_MORNING_SHIFTS:
            penalty += (m - MAX_MORNING_SHIFTS) * 20.0

    return {
        "total_penalty": penalty,
        "hours_by_user": hours_by_user,
        "morning_counts": morning_counts
    }
