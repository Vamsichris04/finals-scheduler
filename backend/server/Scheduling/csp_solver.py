"""
Constraint Satisfaction Problem (CSP) Solver with Optimization
Uses greedy construction + local search for better solutions
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from scheduling_env import SchedulingEnvironment
import time
import random


class CSPSolver:
    """CSP solver with greedy construction and local search for IT scheduling"""

    def __init__(self, environment: SchedulingEnvironment,
                 max_time: float = 120.0,
                 local_search_iterations: int = 5000):
        """
        Initialize CSP solver

        Args:
            environment: SchedulingEnvironment instance
            max_time: Maximum time to search (seconds)
            local_search_iterations: Number of local search iterations
        """
        self.env = environment
        self.max_time = max_time
        self.local_search_iterations = local_search_iterations

        self.worker_ids = [w.worker_id for w in self.env.workers]

        # Track statistics
        self.nodes_explored = 0
        self.improvements = 0
        self.start_time = None

        # Best solution found
        self.best_solution = None
        self.best_penalty = float('inf')

        # Constraints
        self.min_shift = 2  # Minimum 2 hours per shift
        self.max_shift = 6  # Maximum 6 hours per shift
        self.min_hours_per_worker = getattr(environment, 'MIN_HOURS_PER_WORKER', 14)

    def _get_worker_hours(self, assignment: np.ndarray) -> Dict[int, int]:
        """Count hours assigned to each worker"""
        worker_hours = {w.worker_id: 0 for w in self.env.workers}
        for worker_id in assignment:
            if worker_id != -1 and worker_id in worker_hours:
                worker_hours[worker_id] += 1
        return worker_hours

    def _get_coverage_at_slot(self, assignment: np.ndarray, day: int, hour: int, shift_type: str) -> int:
        """Count how many workers are assigned to a specific time/type"""
        count = 0
        for i, worker_id in enumerate(assignment):
            if worker_id != -1:
                slot = self.env.shift_slots[i]
                if slot.day == day and slot.hour == hour and slot.shift_type == shift_type:
                    count += 1
        return count

    def _build_greedy_solution(self) -> np.ndarray:
        """Build initial solution using greedy construction with block assignments"""
        solution = np.full(self.env.num_slots, -1, dtype=int)
        worker_hours = {w.worker_id: 0 for w in self.env.workers}

        # Group slots by (day, shift_type) for block assignment
        slot_groups = {}
        for i, slot in enumerate(self.env.shift_slots):
            key = (slot.day, slot.shift_type)
            if key not in slot_groups:
                slot_groups[key] = []
            slot_groups[key].append((i, slot.hour))

        # Sort each group by hour
        for key in slot_groups:
            slot_groups[key].sort(key=lambda x: x[1])

        # Process each day/shift_type combination
        for (day, shift_type), slots in slot_groups.items():
            i = 0
            while i < len(slots):
                slot_idx, hour = slots[i]

                # Find available workers for this slot
                available = self.env.get_available_workers(day, hour)
                if not available:
                    i += 1
                    continue

                # Score workers: prefer those under minimum hours
                def worker_score(w_id):
                    hours = worker_hours[w_id]
                    worker = next((w for w in self.env.workers if w.worker_id == w_id), None)

                    # Primary: workers under minimum hours get priority
                    if hours < self.min_hours_per_worker:
                        base = 0
                    else:
                        base = 1000

                    # Secondary: prefer workers with fewer hours (fairness)
                    return base + hours

                available_sorted = sorted(available, key=worker_score)

                # Try to assign best worker in a block
                for chosen in available_sorted:
                    if worker_hours[chosen] >= 20:
                        continue

                    # Determine block length (2-6 hours)
                    max_block = min(self.max_shift, 20 - worker_hours[chosen])
                    if max_block < self.min_shift:
                        continue

                    # Find how many consecutive hours this worker can work
                    block_length = 0
                    for j in range(i, len(slots)):
                        next_idx, next_hour = slots[j]
                        if next_hour != hour + (j - i):
                            break
                        worker = next((w for w in self.env.workers if w.worker_id == chosen), None)
                        if worker and worker.is_available(day, next_hour):
                            block_length += 1
                            if block_length >= max_block:
                                break
                        else:
                            break

                    # Only assign if we can get at least min_shift hours
                    if block_length >= self.min_shift:
                        for j in range(block_length):
                            next_idx, _ = slots[i + j]
                            solution[next_idx] = chosen
                        worker_hours[chosen] += block_length
                        i += block_length
                        break
                else:
                    # No worker could be assigned in a valid block
                    i += 1

        return solution

    def _local_search(self, solution: np.ndarray, verbose: bool = True) -> np.ndarray:
        """Improve solution using local search"""
        current = solution.copy()
        current_penalty, _ = self.env.evaluate_schedule(current)

        best = current.copy()
        best_penalty = current_penalty

        no_improvement_count = 0
        max_no_improvement = 500

        for iteration in range(self.local_search_iterations):
            if time.time() - self.start_time > self.max_time:
                break

            # Choose a random move
            move_type = random.choice(['swap', 'reassign_block', 'extend', 'fill_gap'])

            neighbor = current.copy()

            if move_type == 'swap':
                # Swap two workers between slots
                assigned = [i for i, w in enumerate(current) if w != -1]
                if len(assigned) >= 2:
                    idx1, idx2 = random.sample(assigned, 2)
                    slot1, slot2 = self.env.shift_slots[idx1], self.env.shift_slots[idx2]
                    w1, w2 = neighbor[idx1], neighbor[idx2]

                    # Check if swap is valid
                    worker1 = next((w for w in self.env.workers if w.worker_id == w1), None)
                    worker2 = next((w for w in self.env.workers if w.worker_id == w2), None)

                    if (worker1 and worker2 and
                        worker1.is_available(slot2.day, slot2.hour) and
                        worker2.is_available(slot1.day, slot1.hour)):
                        neighbor[idx1], neighbor[idx2] = w2, w1

            elif move_type == 'reassign_block':
                # Reassign a block of hours to a different worker
                assigned = [i for i, w in enumerate(current) if w != -1]
                if assigned:
                    idx = random.choice(assigned)
                    slot = self.env.shift_slots[idx]
                    old_worker = neighbor[idx]

                    # Find another available worker
                    available = self.env.get_available_workers(slot.day, slot.hour)
                    available = [w for w in available if w != old_worker]

                    if available:
                        new_worker = random.choice(available)
                        # Reassign entire block for this worker on this day
                        for i, s in enumerate(self.env.shift_slots):
                            if (s.day == slot.day and s.shift_type == slot.shift_type and
                                neighbor[i] == old_worker):
                                worker = next((w for w in self.env.workers if w.worker_id == new_worker), None)
                                if worker and worker.is_available(s.day, s.hour):
                                    neighbor[i] = new_worker

            elif move_type == 'extend':
                # Extend a worker's shift by 1 hour
                assigned = [i for i, w in enumerate(current) if w != -1]
                if assigned:
                    idx = random.choice(assigned)
                    slot = self.env.shift_slots[idx]
                    worker_id = neighbor[idx]

                    # Find adjacent empty slot
                    for i, s in enumerate(self.env.shift_slots):
                        if (s.day == slot.day and s.shift_type == slot.shift_type and
                            abs(s.hour - slot.hour) == 1 and neighbor[i] == -1):
                            worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)
                            if worker and worker.is_available(s.day, s.hour):
                                # Check hour limit
                                hours = sum(1 for w in neighbor if w == worker_id)
                                if hours < 20:
                                    neighbor[i] = worker_id
                                    break

            elif move_type == 'fill_gap':
                # Fill an empty slot with a new block
                empty = [i for i, w in enumerate(current) if w == -1]
                if empty:
                    idx = random.choice(empty)
                    slot = self.env.shift_slots[idx]
                    available = self.env.get_available_workers(slot.day, slot.hour)

                    # Prefer workers under minimum hours
                    worker_hours = self._get_worker_hours(neighbor)
                    under_min = [w for w in available if worker_hours[w] < self.min_hours_per_worker]

                    if under_min:
                        chosen = random.choice(under_min)
                    elif available:
                        chosen = random.choice(available)
                    else:
                        continue

                    # Assign block of 2-4 hours
                    block_size = random.randint(2, 4)
                    assigned = 0
                    for i, s in enumerate(self.env.shift_slots):
                        if (s.day == slot.day and s.shift_type == slot.shift_type and
                            slot.hour <= s.hour < slot.hour + block_size and
                            neighbor[i] == -1):
                            worker = next((w for w in self.env.workers if w.worker_id == chosen), None)
                            if worker and worker.is_available(s.day, s.hour):
                                hours = sum(1 for w in neighbor if w == chosen)
                                if hours < 20:
                                    neighbor[i] = chosen
                                    assigned += 1

            # Evaluate neighbor
            neighbor_penalty, _ = self.env.evaluate_schedule(neighbor)
            self.nodes_explored += 1

            # Accept if better, or with small probability if worse (simulated annealing style)
            if neighbor_penalty < current_penalty:
                current = neighbor
                current_penalty = neighbor_penalty
                no_improvement_count = 0

                if current_penalty < best_penalty:
                    best = current.copy()
                    best_penalty = current_penalty
                    self.improvements += 1

                    if verbose and self.improvements % 50 == 0:
                        print(f"  Iteration {iteration}: New best penalty = {best_penalty:.2f}")
            else:
                no_improvement_count += 1
                # Occasionally accept worse solutions to escape local minima
                if random.random() < 0.01:
                    current = neighbor
                    current_penalty = neighbor_penalty

            # Restart if stuck
            if no_improvement_count > max_no_improvement:
                current = self._build_greedy_solution()
                current_penalty, _ = self.env.evaluate_schedule(current)
                no_improvement_count = 0
                if verbose:
                    print(f"  Restarting search at iteration {iteration}")

        return best

    def solve(self, verbose: bool = True) -> Tuple[Optional[np.ndarray], float, Dict]:
        """
        Solve scheduling problem using greedy construction + local search

        Args:
            verbose: Print progress

        Returns:
            solution: Best schedule found
            penalty: Penalty of best solution
            stats: Statistics about search
        """
        self.start_time = time.time()
        self.nodes_explored = 0
        self.improvements = 0

        if verbose:
            print("Starting CSP solver with local search...")
            print(f"Number of slots: {self.env.num_slots}")
            print(f"Number of workers: {len(self.env.workers)}")
            print(f"Max time: {self.max_time}s")
            print(f"Local search iterations: {self.local_search_iterations}")

        # Phase 1: Build greedy solution
        if verbose:
            print("\nPhase 1: Building initial greedy solution...")

        initial_solution = self._build_greedy_solution()
        initial_penalty, details = self.env.evaluate_schedule(initial_solution)

        if verbose:
            print(f"  Initial penalty: {initial_penalty:.2f}")
            print(f"  Initial violations: {details}")

        # Phase 2: Local search improvement
        if verbose:
            print("\nPhase 2: Local search optimization...")

        best_solution = self._local_search(initial_solution, verbose)
        best_penalty, final_details = self.env.evaluate_schedule(best_solution)

        elapsed_time = time.time() - self.start_time

        stats = {
            'nodes_explored': self.nodes_explored,
            'improvements': self.improvements,
            'time': elapsed_time,
            'success': True
        }

        if verbose:
            print(f"\nCSP Search completed:")
            print(f"  Time: {elapsed_time:.2f}s")
            print(f"  Nodes explored: {self.nodes_explored}")
            print(f"  Improvements found: {self.improvements}")
            print(f"  Best penalty: {best_penalty:.2f}")
            print(f"  Violation details: {final_details}")

        self.best_solution = best_solution
        self.best_penalty = best_penalty

        return best_solution, best_penalty, stats
