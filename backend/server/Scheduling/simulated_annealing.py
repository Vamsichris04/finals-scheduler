"""
Simulated Annealing for IT Scheduling
"""

import numpy as np
from typing import Tuple, List
from scheduling_env import SchedulingEnvironment
import random
import math

class SimulatedAnnealing:
    """Simulated Annealing solver for IT scheduling"""
    
    def __init__(self, environment: SchedulingEnvironment,
                 initial_temp: float = 2000.0,
                 final_temp: float = 0.01,
                 cooling_rate: float = 0.997,
                 iterations_per_temp: int = 200):
        """
        Initialize SA solver

        Args:
            environment: SchedulingEnvironment instance
            initial_temp: Starting temperature (higher = more exploration)
            final_temp: Ending temperature
            cooling_rate: Temperature decay rate (closer to 1 = slower cooling)
            iterations_per_temp: Number of iterations at each temperature
        """
        self.env = environment
        self.initial_temp = initial_temp
        self.final_temp = final_temp
        self.cooling_rate = cooling_rate
        self.iterations_per_temp = iterations_per_temp
        
        self.worker_ids = [w.worker_id for w in self.env.workers]
        
        # Track best solution
        self.best_solution = None
        self.best_cost = float('inf')
        self.cost_history = []
        
    def generate_initial_solution(self) -> np.ndarray:
        """Generate initial feasible solution assigning workers in continuous blocks (2-6 hours)"""
        solution = np.full(self.env.num_slots, -1, dtype=int)

        # Track hours assigned to each worker
        worker_hours = {w.worker_id: 0 for w in self.env.workers}
        min_hours = getattr(self.env, 'MIN_HOURS_PER_WORKER', 14)
        min_shift = 2  # Minimum 2 hours (~1.5h requirement)
        max_shift = 6  # Maximum 6 hours

        # Group slots by day and shift_type for block assignment
        slot_groups = {}
        for i, slot in enumerate(self.env.shift_slots):
            key = (slot.day, slot.shift_type)
            if key not in slot_groups:
                slot_groups[key] = []
            slot_groups[key].append((i, slot.hour))

        # Sort each group by hour
        for key in slot_groups:
            slot_groups[key].sort(key=lambda x: x[1])

        # Assign workers in blocks for each day/shift_type combo
        for key in slot_groups:
            slots = slot_groups[key]
            day, _ = key
            i = 0

            while i < len(slots):
                slot_idx, hour = slots[i]

                # Find available workers for this hour
                available = self.env.get_available_workers(day, hour)
                if not available:
                    i += 1
                    continue

                # Sort by hours (prefer workers under minimum)
                def priority(w_id):
                    hours = worker_hours[w_id]
                    if hours < min_hours:
                        return (0, hours)
                    return (1, hours)

                available_sorted = sorted(available, key=priority)
                chosen = available_sorted[0]

                # Determine block length (2-6 hours)
                block_length = random.randint(min_shift, max_shift)

                # Assign worker to consecutive slots if available
                assigned = 0
                for j in range(i, min(i + block_length, len(slots))):
                    next_idx, next_hour = slots[j]
                    # Check if consecutive hour and worker is available
                    if next_hour == hour + (j - i):
                        worker = next((w for w in self.env.workers if w.worker_id == chosen), None)
                        if worker and worker.is_available(day, next_hour):
                            solution[next_idx] = chosen
                            assigned += 1
                        else:
                            break
                    else:
                        break

                if assigned > 0:
                    worker_hours[chosen] += assigned

                i += max(1, assigned)

        return solution
    
    def calculate_cost(self, solution: np.ndarray) -> float:
        """Calculate cost (penalty) of solution"""
        penalty, _ = self.env.evaluate_schedule(solution)
        return penalty
    
    def generate_neighbor(self, solution: np.ndarray) -> np.ndarray:
        """
        Generate neighbor solution by making block-aware modifications

        Neighbor generation strategies:
        1. Swap two blocks of assignments
        2. Extend a block by adding adjacent hours
        3. Shrink a block by removing hours (but keep min 2)
        4. Reassign a block to a different worker
        5. Fill an empty block with a new worker
        """
        neighbor = solution.copy()
        min_shift = 2
        max_shift = 6

        strategy = random.choice(['swap_blocks', 'extend_block', 'shrink_block',
                                  'reassign_block', 'fill_block'])

        if strategy == 'swap_blocks':
            # Swap two random assignments (keeping block structure)
            assigned_indices = [i for i, w in enumerate(solution) if w != -1]
            if len(assigned_indices) >= 2:
                idx1, idx2 = random.sample(assigned_indices, 2)
                slot1 = self.env.shift_slots[idx1]
                slot2 = self.env.shift_slots[idx2]

                # Only swap if both workers are available at swapped locations
                w1, w2 = neighbor[idx1], neighbor[idx2]
                worker1 = next((w for w in self.env.workers if w.worker_id == w1), None)
                worker2 = next((w for w in self.env.workers if w.worker_id == w2), None)

                if (worker1 and worker2 and
                    worker1.is_available(slot2.day, slot2.hour) and
                    worker2.is_available(slot1.day, slot1.hour)):
                    neighbor[idx1], neighbor[idx2] = w2, w1

        elif strategy == 'extend_block':
            # Find a block and try to extend it by 1-2 hours
            assigned_indices = [i for i, w in enumerate(solution) if w != -1]
            if assigned_indices:
                idx = random.choice(assigned_indices)
                slot = self.env.shift_slots[idx]
                worker_id = neighbor[idx]

                # Find adjacent empty slot to extend into
                for i, s in enumerate(self.env.shift_slots):
                    if (s.day == slot.day and s.shift_type == slot.shift_type and
                        abs(s.hour - slot.hour) == 1 and neighbor[i] == -1):
                        worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)
                        if worker and worker.is_available(s.day, s.hour):
                            neighbor[i] = worker_id
                            break

        elif strategy == 'shrink_block':
            # Find a block and remove edge hours (but keep min 2 hours)
            assigned_indices = [i for i, w in enumerate(solution) if w != -1]
            if assigned_indices:
                idx = random.choice(assigned_indices)
                slot = self.env.shift_slots[idx]
                worker_id = neighbor[idx]

                # Count block size for this worker on this day/type
                block_size = sum(1 for i, s in enumerate(self.env.shift_slots)
                               if s.day == slot.day and s.shift_type == slot.shift_type
                               and neighbor[i] == worker_id)

                # Only shrink if block > min_shift
                if block_size > min_shift:
                    neighbor[idx] = -1

        elif strategy == 'reassign_block':
            # Reassign a slot to a different available worker
            idx = random.randint(0, len(solution) - 1)
            slot = self.env.shift_slots[idx]
            available = self.env.get_available_workers(slot.day, slot.hour)

            if available:
                current = neighbor[idx]
                if current in available and len(available) > 1:
                    available = [w for w in available if w != current]
                neighbor[idx] = random.choice(available)
            else:
                neighbor[idx] = -1

        elif strategy == 'fill_block':
            # Fill empty slots with a block assignment (2-6 consecutive hours)
            empty_indices = [i for i, w in enumerate(solution) if w == -1]
            if empty_indices:
                idx = random.choice(empty_indices)
                slot = self.env.shift_slots[idx]
                available = self.env.get_available_workers(slot.day, slot.hour)

                if available:
                    chosen = random.choice(available)
                    block_length = random.randint(min_shift, max_shift)

                    # Find consecutive empty slots
                    assigned = 0
                    for i, s in enumerate(self.env.shift_slots):
                        if (s.day == slot.day and s.shift_type == slot.shift_type and
                            slot.hour <= s.hour < slot.hour + block_length and
                            neighbor[i] == -1):
                            worker = next((w for w in self.env.workers if w.worker_id == chosen), None)
                            if worker and worker.is_available(s.day, s.hour):
                                neighbor[i] = chosen
                                assigned += 1
                            else:
                                break

        return neighbor
    
    def acceptance_probability(self, current_cost: float, new_cost: float, 
                              temperature: float) -> float:
        """
        Calculate probability of accepting worse solution
        
        Args:
            current_cost: Cost of current solution
            new_cost: Cost of new solution
            temperature: Current temperature
            
        Returns:
            Acceptance probability
        """
        if new_cost < current_cost:
            return 1.0
        
        if temperature == 0:
            return 0.0
        
        delta = new_cost - current_cost
        return math.exp(-delta / temperature)
    
    def solve(self, verbose: bool = True) -> Tuple[np.ndarray, float, List[float]]:
        """
        Run simulated annealing
        
        Args:
            verbose: Print progress
            
        Returns:
            best_solution: Best schedule found
            best_cost: Cost of best solution
            cost_history: Cost over iterations
        """
        # Generate initial solution
        current_solution = self.generate_initial_solution()
        current_cost = self.calculate_cost(current_solution)
        
        self.best_solution = current_solution.copy()
        self.best_cost = current_cost
        
        temperature = self.initial_temp
        iteration = 0
        
        if verbose:
            print(f"Initial solution cost: {current_cost:.2f}")
        
        while temperature > self.final_temp:
            for _ in range(self.iterations_per_temp):
                iteration += 1
                
                # Generate neighbor
                new_solution = self.generate_neighbor(current_solution)
                new_cost = self.calculate_cost(new_solution)
                
                # Decide whether to accept new solution
                accept_prob = self.acceptance_probability(current_cost, new_cost, temperature)
                
                if random.random() < accept_prob:
                    current_solution = new_solution
                    current_cost = new_cost
                    
                    # Update best solution
                    if current_cost < self.best_cost:
                        self.best_solution = current_solution.copy()
                        self.best_cost = current_cost
                
                self.cost_history.append(self.best_cost)
                
                # Early stopping if perfect solution found
                if self.best_cost == 0:
                    if verbose:
                        print(f"Perfect solution found at iteration {iteration}!")
                    return self.best_solution, self.best_cost, self.cost_history
            
            # Cool down
            temperature *= self.cooling_rate
            
            if verbose and iteration % 1000 == 0:
                print(f"Iteration {iteration}, Temp={temperature:.2f}, Best Cost={self.best_cost:.2f}, Current Cost={current_cost:.2f}")
        
        if verbose:
            print(f"\nSA completed. Best cost: {self.best_cost:.2f}")
            penalty, details = self.env.evaluate_schedule(self.best_solution)
            print(f"Violation details: {details}")
        
        return self.best_solution, self.best_cost, self.cost_history