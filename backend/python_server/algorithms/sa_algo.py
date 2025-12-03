from typing import List, Dict, Any
import copy
import random
import math
from .base import Algorithm
from .common import eligible, evaluate_schedule


class SAAlgorithm(Algorithm):
    """Simulated annealing implemented as a class."""

    def __init__(self, users: List[Dict[str, Any]], slots: List[Dict[str, Any]]):
        super().__init__(users, slots)
        self.iters = 2000

    def configure(self, **opts):
        self.iters = int(opts.get('sa_iters', opts.get('iters', self.iters)))

    def solve(self) -> Dict[str, Any]:
        # seed with CSP-like greedy assignment: reuse a simple greedy here
        from .csp_algo import CSPAlgorithm
        seed_alg = CSPAlgorithm(self.users, self.slots)
        seed_alg.configure()
        base = seed_alg.solve()
        current = base['schedule']
        current_q = evaluate_schedule(current, self.users, self.slots)
        best = copy.deepcopy(current)
        best_q = current_q

        for t in range(self.iters):
            T = max(0.0001, 1.0 * (0.001 ** (t / max(1, self.iters))))
            if not current:
                break
            idx = random.randrange(len(current))
            entry = current[idx]
            slot = { 'date': entry['date'], 'start_time': entry['start_time'], 'end_time': entry['end_time'], 'shift_type': entry['shift_type'] }

            pool = [u for u in self.users if str(u['_id']) != str(entry['worker_id']) and eligible(u, slot, { str(x['_id']):0.0 for x in self.users }, 20.0)]
            if not pool:
                continue
            new_user = random.choice(pool)
            neighbor = copy.deepcopy(current)
            neighbor[idx]['worker_id'] = str(new_user['_id'])
            neighbor[idx]['worker_name'] = new_user.get('name','')

            neighbor_q = evaluate_schedule(neighbor, self.users, self.slots)
            d = neighbor_q['total_penalty'] - current_q['total_penalty']
            if d < 0 or math.exp(-d / max(T,1e-9)) > random.random():
                current = neighbor
                current_q = neighbor_q
                if neighbor_q['total_penalty'] < best_q['total_penalty']:
                    best = copy.deepcopy(neighbor)
                    best_q = neighbor_q

        return { "schedule": best, "quality": best_q }
