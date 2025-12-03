from typing import List, Dict, Any
from .base import Algorithm
from .common import eligible, duration_hours, evaluate_schedule


class CSPAlgorithm(Algorithm):
    """CSP / greedy algorithm implemented as a class."""

    def __init__(self, users: List[Dict[str, Any]], slots: List[Dict[str, Any]]):
        super().__init__(users, slots)

    def configure(self, **opts):
        # hour_cap can be provided; default to TARGET_HOURS inside common if needed
        self.hour_cap = opts.get('hour_cap', None)

    def solve(self) -> Dict[str, Any]:
        hour_cap = self.hour_cap if self.hour_cap is not None else 15.0
        hours = { str(u['_id']): 0.0 for u in self.users }
        assignments: List[Dict[str, Any]] = []

        slots_sorted = sorted(self.slots, key=lambda s: (s['date'], s['start_time'], s['shift_type']))

        for s in slots_sorted:
            dur = duration_hours(s['start_time'], s['end_time'])
            min_req = 1 if s['shift_type'] == 'Window' else 1
            max_req = 2 if s['shift_type'] == 'Window' else 4

            pool = [u for u in self.users if eligible(u, s, hours, hour_cap)]
            pool.sort(key=lambda u: (hours.get(str(u['_id']), 0.0) >= 15.0, hours.get(str(u['_id']), 0.0)))

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

        quality = evaluate_schedule(assignments, self.users, self.slots)
        return { "schedule": assignments, "quality": quality }
