"""
Genetic Algorithm for IT Scheduling
"""

import numpy as np
from typing import List, Tuple
from scheduling_env import SchedulingEnvironment, Worker
import random

class GeneticAlgorithm:
    """Genetic Algorithm solver for IT scheduling"""

    def __init__(self, environment: SchedulingEnvironment,
                 population_size: int = 250,
                 generations: int = 5000,
                 crossover_rate: float = 0.85,
                 mutation_rate: float = 0.35,
                 elitism_count: int = 15):
        """
        Initialize GA solver
        
        Args:
            environment: SchedulingEnvironment instance
            population_size: Number of individuals in population
            generations: Number of generations to evolve
            crossover_rate: Probability of crossover
            mutation_rate: Probability of mutation
            elitism_count: Number of best individuals to preserve
        """
        self.env = environment
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count
        
        self.chromosome_length = self.env.num_slots
        self.worker_ids = [w.worker_id for w in self.env.workers]
        
        # Track best solution
        self.best_solution = None
        self.best_fitness = float('inf')
        self.fitness_history = []
        
    def initialize_population(self) -> List[np.ndarray]:
        """Create initial population assigning workers in continuous blocks (2-6 hours)"""
        population = []
        min_hours = getattr(self.env, 'MIN_HOURS_PER_WORKER', 14)
        min_shift = 2  # Minimum 2 hours (~1.5h requirement)
        max_shift = 6  # Maximum 6 hours

        for _ in range(self.population_size):
            chromosome = np.full(self.chromosome_length, -1, dtype=int)
            worker_hours = {w.worker_id: 0 for w in self.env.workers}

            # Group slots by day, hour, and shift_type for block assignment
            slot_groups = {}
            for i, slot in enumerate(self.env.shift_slots):
                key = (slot.day, slot.shift_type)
                if key not in slot_groups:
                    slot_groups[key] = []
                slot_groups[key].append((i, slot.hour))

            # Sort each group by hour
            for key in slot_groups:
                slot_groups[key].sort(key=lambda x: x[1])

            # Shuffle keys for variety
            keys = list(slot_groups.keys())
            random.shuffle(keys)

            # Assign workers in blocks
            for key in keys:
                slots = slot_groups[key]
                day, shift_type = key
                i = 0

                while i < len(slots):
                    slot_idx, hour = slots[i]

                    # Find available workers for this hour
                    available = self.env.get_available_workers(day, hour)
                    if not available:
                        i += 1
                        continue

                    # Prefer workers under minimum hours
                    under_min = [w for w in available if worker_hours[w] < min_hours]
                    if under_min and random.random() < 0.85:
                        candidates = under_min
                    else:
                        candidates = available

                    chosen = random.choice(candidates)

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
                                chromosome[next_idx] = chosen
                                assigned += 1
                            else:
                                break
                        else:
                            break

                    if assigned > 0:
                        worker_hours[chosen] += assigned

                    i += max(1, assigned)

            population.append(chromosome)

        return population
    
    def calculate_fitness(self, chromosome: np.ndarray) -> float:
        """Calculate fitness (lower is better - using penalty)"""
        penalty, _ = self.env.evaluate_schedule(chromosome)
        return penalty
    
    def select_parents(self, population: List[np.ndarray], 
                      fitnesses: List[float]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Select two parents using tournament selection
        
        Args:
            population: Current population
            fitnesses: Fitness scores for population
            
        Returns:
            Two parent chromosomes
        """
        def tournament_select(k=3):
            # Select k random individuals and return the best
            indices = random.sample(range(len(population)), k)
            best_idx = min(indices, key=lambda i: fitnesses[i])
            return population[best_idx].copy()
        
        parent1 = tournament_select()
        parent2 = tournament_select()
        return parent1, parent2
    
    def crossover(self, parent1: np.ndarray, parent2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform two-point crossover
        
        Args:
            parent1, parent2: Parent chromosomes
            
        Returns:
            Two offspring chromosomes
        """
        if random.random() > self.crossover_rate:
            return parent1.copy(), parent2.copy()
        
        # Two-point crossover
        point1 = random.randint(0, self.chromosome_length - 1)
        point2 = random.randint(point1, self.chromosome_length)
        
        offspring1 = np.concatenate([
            parent1[:point1],
            parent2[point1:point2],
            parent1[point2:]
        ])
        
        offspring2 = np.concatenate([
            parent2[:point1],
            parent1[point1:point2],
            parent2[point2:]
        ])
        
        return offspring1, offspring2
    
    def mutate(self, chromosome: np.ndarray) -> np.ndarray:
        """
        Perform mutation using block-aware operations

        Args:
            chromosome: Chromosome to mutate

        Returns:
            Mutated chromosome
        """
        if random.random() > self.mutation_rate:
            return chromosome

        min_shift = 2
        max_shift = 6
        min_hours = getattr(self.env, 'MIN_HOURS_PER_WORKER', 14)

        # Choose mutation type
        mutation_type = random.choice(['extend_block', 'swap_blocks', 'fill_gap', 'reassign'])

        if mutation_type == 'extend_block':
            # Extend an existing worker's shift
            assigned = [i for i, w in enumerate(chromosome) if w != -1]
            if assigned:
                idx = random.choice(assigned)
                slot = self.env.shift_slots[idx]
                worker_id = chromosome[idx]

                # Find adjacent empty slots
                for i, s in enumerate(self.env.shift_slots):
                    if (s.day == slot.day and s.shift_type == slot.shift_type and
                        abs(s.hour - slot.hour) == 1 and chromosome[i] == -1):
                        worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)
                        if worker and worker.is_available(s.day, s.hour):
                            hours = sum(1 for w in chromosome if w == worker_id)
                            if hours < 20:
                                chromosome[i] = worker_id
                                break

        elif mutation_type == 'swap_blocks':
            # Swap two workers
            assigned = [i for i, w in enumerate(chromosome) if w != -1]
            if len(assigned) >= 2:
                idx1, idx2 = random.sample(assigned, 2)
                slot1, slot2 = self.env.shift_slots[idx1], self.env.shift_slots[idx2]
                w1, w2 = chromosome[idx1], chromosome[idx2]

                worker1 = next((w for w in self.env.workers if w.worker_id == w1), None)
                worker2 = next((w for w in self.env.workers if w.worker_id == w2), None)

                if (worker1 and worker2 and
                    worker1.is_available(slot2.day, slot2.hour) and
                    worker2.is_available(slot1.day, slot1.hour)):
                    chromosome[idx1], chromosome[idx2] = w2, w1

        elif mutation_type == 'fill_gap':
            # Fill empty slots with a block
            empty = [i for i, w in enumerate(chromosome) if w == -1]
            if empty:
                idx = random.choice(empty)
                slot = self.env.shift_slots[idx]
                available = self.env.get_available_workers(slot.day, slot.hour)

                if available:
                    # Prefer workers under minimum hours
                    worker_hours = {w.worker_id: sum(1 for x in chromosome if x == w.worker_id)
                                   for w in self.env.workers}
                    under_min = [w for w in available if worker_hours.get(w, 0) < min_hours]
                    chosen = random.choice(under_min) if under_min else random.choice(available)

                    # Assign block of 2-4 hours
                    block_size = random.randint(min_shift, 4)
                    for i, s in enumerate(self.env.shift_slots):
                        if (s.day == slot.day and s.shift_type == slot.shift_type and
                            slot.hour <= s.hour < slot.hour + block_size and
                            chromosome[i] == -1):
                            worker = next((w for w in self.env.workers if w.worker_id == chosen), None)
                            if worker and worker.is_available(s.day, s.hour):
                                hours = sum(1 for w in chromosome if w == chosen)
                                if hours < 20:
                                    chromosome[i] = chosen

        elif mutation_type == 'reassign':
            # Reassign a slot to a different worker
            idx = random.randint(0, self.chromosome_length - 1)
            slot = self.env.shift_slots[idx]
            available = self.env.get_available_workers(slot.day, slot.hour)

            if available:
                current = chromosome[idx]
                if current in available and len(available) > 1:
                    available = [w for w in available if w != current]
                chromosome[idx] = random.choice(available)

        return chromosome
    
    def repair_chromosome(self, chromosome: np.ndarray) -> np.ndarray:
        """
        Repair chromosome to fix critical violations
        
        Args:
            chromosome: Chromosome to repair
            
        Returns:
            Repaired chromosome
        """
        # Fix availability violations
        for i, worker_id in enumerate(chromosome):
            if worker_id == -1:
                continue
                
            slot = self.env.shift_slots[i]
            worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)
            
            if worker and not worker.is_available(slot.day, slot.hour):
                # Replace with available worker or -1
                available = self.env.get_available_workers(slot.day, slot.hour)
                if available:
                    chromosome[i] = random.choice(available)
                else:
                    chromosome[i] = -1
        
        return chromosome
    
    def solve(self, verbose: bool = True) -> Tuple[np.ndarray, float, List[float]]:
        """
        Run genetic algorithm
        
        Args:
            verbose: Print progress
            
        Returns:
            best_solution: Best schedule found
            best_fitness: Fitness of best solution
            fitness_history: Fitness over generations
        """
        # Initialize population
        population = self.initialize_population()
        
        for generation in range(self.generations):
            # Evaluate fitness
            fitnesses = [self.calculate_fitness(ind) for ind in population]
            
            # Track best solution
            min_fitness_idx = np.argmin(fitnesses)
            if fitnesses[min_fitness_idx] < self.best_fitness:
                self.best_fitness = fitnesses[min_fitness_idx]
                self.best_solution = population[min_fitness_idx].copy()
            
            self.fitness_history.append(self.best_fitness)
            
            if verbose and generation % 50 == 0:
                avg_fitness = np.mean(fitnesses)
                print(f"Generation {generation}: Best={self.best_fitness:.2f}, Avg={avg_fitness:.2f}")
            
            # Early stopping if perfect solution found
            if self.best_fitness == 0:
                if verbose:
                    print(f"Perfect solution found at generation {generation}!")
                break
            
            # Create new population
            new_population = []
            
            # Elitism
            elite_indices = np.argsort(fitnesses)[:self.elitism_count]
            for idx in elite_indices:
                new_population.append(population[idx].copy())
            
            # Generate offspring
            while len(new_population) < self.population_size:
                # Select parents
                parent1, parent2 = self.select_parents(population, fitnesses)
                
                # Crossover
                offspring1, offspring2 = self.crossover(parent1, parent2)
                
                # Mutation
                offspring1 = self.mutate(offspring1)
                offspring2 = self.mutate(offspring2)
                
                # Repair
                offspring1 = self.repair_chromosome(offspring1)
                offspring2 = self.repair_chromosome(offspring2)
                
                new_population.append(offspring1)
                if len(new_population) < self.population_size:
                    new_population.append(offspring2)
            
            population = new_population
        
        if verbose:
            print(f"\nGA completed. Best fitness: {self.best_fitness:.2f}")
            penalty, details = self.env.evaluate_schedule(self.best_solution)
            print(f"Violation details: {details}")
        
        return self.best_solution, self.best_fitness, self.fitness_history