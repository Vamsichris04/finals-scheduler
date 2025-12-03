"""
Scheduler implementations: CSP (greedy/backtracking-like), Simulated Annealing, Genetic Algorithm.
Solvers operate on simple Python dicts for users and slots.

Users expected shape (dict):
  {
    "_id": "<str>",
    "name": "Alice",
    "position": "Tier 1",         # Tier name or number
    "isCommuter": False,
    "isActive": True,
    "desiredHours": 15.0,
    "busy_times": { "Monday": [["09:00","11:00"]], ... },
    "exam_times": [["2025-05-12","09:00","11:00"], ...]
  }

Slots expected shape (dict):
  { "date":"2025-05-12", "day_name":"Monday", "start_time":"07:30", "end_time":"11:00", "shift_type":"Window" }

Returned schedule is a list of assignment dicts:
  { "date","start_time","end_time","shift_type","worker_id","worker_name","duration_hours" }

This module is intentionally self-contained and pragmatic.  It enforces the constraints described in the proposal.
"""
from typing import List, Dict, Any, Tuple
import math
import random
import copy

# Constants / constraints
TARGET_HOURS = 15.0
MAX_HOURS = 20.0
WINDOW_MIN, WINDOW_MAX = 1, 2
REMOTE_MIN, REMOTE_MAX = 1, 4
MAX_MORNING_SHIFTS = 2

# Helpers
def to_minutes(hm: str) -> int:
    h, m = map(int, hm.split(':'))
    return h * 60 + m

def duration_hours(start: str, end: str) -> float:
    return (to_minutes(end) - to_minutes(start)) / 60.0

# Constraint checks

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
        # each ex: [date, start, end]
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


# Evaluation / penalty

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


# CSP / greedy solver

def csp_solver(users: List[Dict[str, Any]], slots: List[Dict[str, Any]], hour_cap: float = TARGET_HOURS) -> Dict[str, Any]:
    hours = { str(u['_id']): 0.0 for u in users }
    assignments: List[Dict[str, Any]] = []

    slots_sorted = sorted(slots, key=lambda s: (s['date'], s['start_time'], s['shift_type']))

    for s in slots_sorted:
        dur = duration_hours(s['start_time'], s['end_time'])
        min_req = WINDOW_MIN if s['shift_type'] == 'Window' else REMOTE_MIN
        max_req = WINDOW_MAX if s['shift_type'] == 'Window' else REMOTE_MAX

        pool = [u for u in users if eligible(u, s, hours, hour_cap)]
        pool.sort(key=lambda u: (hours.get(str(u['_id']), 0.0) >= TARGET_HOURS, hours.get(str(u['_id']), 0.0)))

        assigned_count = 0
        for p in pool:
            if assigned_count >= max_req:
                break
            assignments.append({
                "date": s['date'],
                "start_time": s['start_time'],
                "end_time": s['end_time'],
                "shift_type": s['shift_type'],
                "worker_id": str(p['_id']),
                "worker_name": p.get('name',''),
                "duration_hours": dur
            })
            hours[str(p['_id'])] = hours.get(str(p['_id']), 0.0) + dur
            assigned_count += 1
            if assigned_count >= min_req:
                break

    quality = evaluate_schedule(assignments, users, slots)
    return { "schedule": assignments, "quality": quality }


# Simulated Annealing

def sa_solver(users: List[Dict[str, Any]], slots: List[Dict[str, Any]], iters: int = 2000) -> Dict[str, Any]:
    base = csp_solver(users, slots)
    current = base['schedule']
    current_q = evaluate_schedule(current, users, slots)
    best = copy.deepcopy(current)
    best_q = current_q

    for t in range(iters):
        T = max(0.0001, 1.0 * (0.001 ** (t / max(1, iters))))
        if not current:
            break
        idx = random.randrange(len(current))
        entry = current[idx]
        slot = { 'date': entry['date'], 'start_time': entry['start_time'], 'end_time': entry['end_time'], 'shift_type': entry['shift_type'] }

        pool = [u for u in users if str(u['_id']) != str(entry['worker_id']) and eligible(u, slot, { str(x['_id']):0.0 for x in users }, MAX_HOURS)]
        if not pool:
            continue
        new_user = random.choice(pool)
        neighbor = copy.deepcopy(current)
        neighbor[idx]['worker_id'] = str(new_user['_id'])
        neighbor[idx]['worker_name'] = new_user.get('name','')

        neighbor_q = evaluate_schedule(neighbor, users, slots)
        d = neighbor_q['total_penalty'] - current_q['total_penalty']
        if d < 0 or math.exp(-d / max(T,1e-9)) > random.random():
            current = neighbor
            current_q = neighbor_q
            if neighbor_q['total_penalty'] < best_q['total_penalty']:
                best = copy.deepcopy(neighbor)
                best_q = neighbor_q

    return { "schedule": best, "quality": best_q }


# Genetic Algorithm

def ga_solver(users: List[Dict[str, Any]], slots: List[Dict[str, Any]], pop: int = 30, gens: int = 200) -> Dict[str, Any]:
    def random_individual() -> List[Dict[str, Any]]:
        s: List[Dict[str, Any]] = []
        for slot in slots:
            dur = duration_hours(slot['start_time'], slot['end_time'])
            pool = [u for u in users if eligible(u, slot, { str(x['_id']):0.0 for x in users }, MAX_HOURS)]
            if not pool:
                continue
            min_req = WINDOW_MIN if slot['shift_type'] == 'Window' else REMOTE_MIN
            max_req = WINDOW_MAX if slot['shift_type'] == 'Window' else REMOTE_MAX
            cnt = random.randint(min_req, min(max_req, len(pool)))
            chosen = random.sample(pool, cnt)
            for c in chosen:
                s.append({
                    "date": slot['date'],
                    "start_time": slot['start_time'],
                    "end_time": slot['end_time'],
                    "shift_type": slot['shift_type'],
                    "worker_id": str(c['_id']),
                    "worker_name": c.get('name',''),
                    "duration_hours": dur
                })
        return s

    def fitness(ind: List[Dict[str, Any]]) -> float:
        q = evaluate_schedule(ind, users, slots)
        return -q['total_penalty']

    population = [ random_individual() for _ in range(pop) ]

    for g in range(gens):
        population.sort(key=fitness, reverse=True)
        next_pop = population[: max(1, pop // 10) ]
        while len(next_pop) < pop:
            a = random.choice(population)
            b = random.choice(population)
            cut = len(a) // 2
            child = copy.deepcopy(a[:cut] + b[cut:])
            if child and random.random() < 0.2:
                idx = random.randrange(len(child))
                slot = { 'date': child[idx]['date'], 'start_time': child[idx]['start_time'], 'end_time': child[idx]['end_time'], 'shift_type': child[idx]['shift_type'] }
                pool = [u for u in users if eligible(u, slot, { str(x['_id']):0.0 for x in users }, MAX_HOURS)]
                if pool:
                    new = random.choice(pool)
                    child[idx]['worker_id'] = str(new['_id'])
                    child[idx]['worker_name'] = new.get('name','')
            next_pop.append(child)
        population = next_pop

    population.sort(key=fitness, reverse=True)
    best = population[0] if population else []
    best_q = evaluate_schedule(best, users, slots)
    return { "schedule": best, "quality": best_q }
