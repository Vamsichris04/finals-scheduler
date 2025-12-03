from typing import List, Dict, Any
import random
import copy
from .base import Algorithm
from .common import eligible, evaluate_schedule, duration_hours


class GAAlgorithm(Algorithm):
    """Genetic algorithm implemented as a class."""

    def __init__(self, users: List[Dict[str, Any]], slots: List[Dict[str, Any]]):
        super().__init__(users, slots)
        self.pop = 30
        self.gens = 200

    def configure(self, **opts):
        self.pop = int(opts.get('ga_pop', opts.get('pop', self.pop)))
        self.gens = int(opts.get('ga_gens', opts.get('gens', self.gens)))

    def solve(self) -> Dict[str, Any]:
        def random_individual() -> List[Dict[str, Any]]:
            s: List[Dict[str, Any]] = []
            for slot in self.slots:
                dur = duration_hours(slot['start_time'], slot['end_time'])
                pool = [u for u in self.users if eligible(u, slot, { str(x['_id']):0.0 for x in self.users }, 20.0)]
                if not pool:
                    continue
                min_req = 1 if slot['shift_type']=='Window' else 1
                max_req = 2 if slot['shift_type']=='Window' else 4
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
            q = evaluate_schedule(ind, self.users, self.slots)
            return -q['total_penalty']

        population = [ random_individual() for _ in range(self.pop) ]

        for g in range(self.gens):
            population.sort(key=fitness, reverse=True)
            next_pop = population[: max(1, self.pop // 10) ]
            while len(next_pop) < self.pop:
                a = random.choice(population)
                b = random.choice(population)
                cut = len(a) // 2
                child = copy.deepcopy(a[:cut] + b[cut:])
                if child and random.random() < 0.2:
                    idx = random.randrange(len(child))
                    slot = { 'date': child[idx]['date'], 'start_time': child[idx]['start_time'], 'end_time': child[idx]['end_time'], 'shift_type': child[idx]['shift_type'] }
                    pool = [u for u in self.users if eligible(u, slot, { str(x['_id']):0.0 for x in self.users }, 20.0)]
                    if pool:
                        new = random.choice(pool)
                        child[idx]['worker_id'] = str(new['_id'])
                        child[idx]['worker_name'] = new.get('name','')
                next_pop.append(child)
            population = next_pop

        population.sort(key=fitness, reverse=True)
        best = population[0] if population else []
        best_q = evaluate_schedule(best, self.users, self.slots)
        return { "schedule": best, "quality": best_q }
