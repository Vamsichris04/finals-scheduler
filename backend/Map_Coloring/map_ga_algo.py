"""
Map Coloring Genetic Algorithm Solver

This module implements a Genetic Algorithm (GA) for solving the map coloring problem,
an NP-hard constraint satisfaction problem. The GA uses evolutionary principles to
search for valid colorings through iterative improvement of a population of candidate solutions.

The algorithm employs several advanced techniques:
- Smart initialization: Greedy coloring to create diverse starting population
- Tournament selection: Probabilistic selection favoring fitter individuals
- Two-point crossover: Genetic recombination between parent solutions
- Adaptive mutation: Conflict-reducing color changes with dynamic mutation rates
- Elitism: Preservation of best solutions across generations
- Stagnation detection: Automatic mutation rate increases when progress stalls

Key Features:
- Population-based search exploring multiple solution candidates simultaneously
- Adaptive parameters based on problem size (standard vs. USA map)
- Comprehensive performance tracking (evaluations, first solution generation)
- Early termination upon finding perfect solutions
- Robust handling of local optima through mutation and diversity

This GA implementation provides probabilistic approximate solutions, often finding
optimal or near-optimal colorings efficiently, especially for large complex maps
like the 50-state USA map where exact methods may be computationally expensive.
"""

import random

def compute_penalty(state, adjacency):
    """
    Calculate the number of constraint violations in a coloring.
    
    A violation occurs when two adjacent regions have the same color.
    Each edge is counted only once to avoid double-counting.
    
    Args:
        state (list): Color assignment for each region (index = region, value = color)
        adjacency (dict): Graph adjacency list (region -> list of neighbors)
        
    Returns:
        int: Number of edge violations (0 means valid solution)
    """
    penalty = 0
    seen = set()  # Track edges to avoid counting twice
    for region, neighbors in adjacency.items():
        for n in neighbors:
            # Create normalized edge representation (min, max) to prevent duplicates
            edge = (min(region, n), max(region, n))
            if edge not in seen:
                seen.add(edge)
                # Increment penalty if adjacent regions have same color
                if state[region] == state[n]:
                    penalty += 1
    return penalty


def genetic_algorithm(adjacency, num_regions, colors,
                      pop_size=100, generations=500, mutation_rate=0.05):
    """
    Solve map coloring using a Genetic Algorithm with adaptive evolution.
    
    This evolutionary algorithm creates a population of candidate colorings and
    iteratively improves them through selection, crossover, and mutation until
    a valid solution is found or generation limit is reached.
    
    Key features:
    - Smart initialization: Initial solutions avoid obvious conflicts
    - Tournament selection: Select fittest parents for reproduction
    - Two-point crossover: Combine genetic material from two parents
    - Smart mutation: Prefer conflict-reducing color changes
    - Elitism: Preserve top solutions across generations
    - Adaptive mutation: Increase mutation rate if population stagnates
    
    Args:
        adjacency (dict): Graph adjacency list (region -> list of neighbors)
        num_regions (int): Total number of regions to color
        colors (list): Available colors to assign
        pop_size (int): Population size (default 100)
        generations (int): Number of generations to evolve (default 500)
        mutation_rate (float): Base mutation probability per region (default 0.05)
    
    Returns:
        tuple: (best_solution, penalty, evaluations_count, first_solution_generation)
               - best_solution: List of colors assigned to each region
               - penalty: Number of conflicts in best solution
               - evaluations_count: Total fitness evaluations performed
               - first_solution_generation: When first valid solution found (or None)
    """
    
    # Counter class to track evaluations and first solution found
    class Counter:
        """Track the number of fitness evaluations and when first solution is found"""
        def __init__(self):
            self.count = 0  # Total number of fitness evaluations
            self.first_solution_at = None  # Generation when first valid solution found
        
        def compute_penalty_tracked(self, state):
            """
            Compute penalty while tracking evaluations and first solution.
            
            Args:
                state: Color assignment to evaluate
                
            Returns:
                int: Penalty score (0 = valid solution)
            """
            self.count += 1  # Increment evaluation counter
            penalty = compute_penalty(state, adjacency)
            
            # Record when first perfect solution (penalty=0) is found
            if penalty == 0 and self.first_solution_at is None:
                self.first_solution_at = self.count
            
            return penalty
    
    counter = Counter()
    
    # Initialize population with smart and random individuals
    def smart_init():
        """
        Create a smart initial coloring that avoids obvious conflicts.
        
        Greedy approach: For each region, assign a color that is not used
        by any already-assigned neighbor (if possible).
        
        Returns:
            list: A partial or complete coloring avoiding conflicts
        """
        state = [None] * num_regions
        for region in range(num_regions):
            # Collect colors already used by assigned neighbors
            used_colors = set()
            for neighbor in adjacency[region]:
                if state[neighbor] is not None:
                    used_colors.add(state[neighbor])
            
            # Pick a random color not used by neighbors if possible
            available = [c for c in colors if c not in used_colors]
            if available:
                state[region] = random.choice(available)
            else:
                # All colors used by neighbors, pick any random color
                state[region] = random.choice(colors)
        return state
    
    # Initialize population: 50% smart, 50% random for diversity
    population = []
    for i in range(pop_size):
        if i < pop_size // 2:
            # First half: use smart initialization
            population.append(smart_init())
        else:
            # Second half: purely random for genetic diversity
            population.append([random.choice(colors) for _ in range(num_regions)])
    
    # Track best solution found so far
    best_ever = None
    best_penalty = float('inf')
    stagnant_count = 0  # Count generations without improvement
    
    # Main evolutionary loop
    for gen in range(generations):
        # Evaluate all individuals and sort by fitness (lower penalty = better)
        population.sort(key=lambda c: counter.compute_penalty_tracked(c))
        
        # Get best individual in current generation
        current_best_penalty = compute_penalty(population[0], adjacency)
        
        # Update all-time best if improved
        if current_best_penalty < best_penalty:
            best_penalty = current_best_penalty
            best_ever = population[0][:]  # Save a copy
            stagnant_count = 0  # Reset stagnation counter
        else:
            stagnant_count += 1  # Increment stagnation
        
        # Early exit: if perfect solution found, return immediately
        if counter.first_solution_at is not None:
            return population[0], 0, counter.count, counter.first_solution_at
        
        # Adaptive mutation: increase rate if population stagnates
        # This helps escape local optima
        current_mutation = mutation_rate * (1 + stagnant_count / 50)
        
        # Elitism: preserve the top 20% best individuals unchanged
        elite_size = pop_size // 5
        new_population = population[:elite_size]
        
        # Generate offspring to fill rest of population
        while len(new_population) < pop_size:
            # Tournament selection: select 2 parents from top half
            tournament_size = 5
            # Parent 1: best of random sample from top half
            parent1 = min(random.sample(population[:pop_size//2], tournament_size), 
                         key=lambda c: compute_penalty(c, adjacency))
            # Parent 2: best of different random sample from top half
            parent2 = min(random.sample(population[:pop_size//2], tournament_size),
                         key=lambda c: compute_penalty(c, adjacency))
            
            # Two-point crossover: combine genetic material from both parents
            # Creates child with segments from: parent1 | parent2 | parent1
            cp1 = random.randint(1, num_regions - 2)
            cp2 = random.randint(cp1 + 1, num_regions - 1)
            child = parent1[:cp1] + parent2[cp1:cp2] + parent1[cp2:]
            
            # Mutation with intelligent repair
            # Smart mutation tries to reduce conflicts when possible
            for i in range(num_regions):
                if random.random() < current_mutation:
                    # Collect colors used by this region's neighbors
                    neighbor_colors = [child[n] for n in adjacency[i]]
                    # Prefer colors that aren't used by neighbors
                    available = [c for c in colors if c not in neighbor_colors]
                    if available:
                        # Smart choice: pick from non-conflicting colors
                        child[i] = random.choice(available)
                    else:
                        # All colors conflict, pick any random color
                        child[i] = random.choice(colors)
            
            new_population.append(child)
        
        # Replace population with new generation
        population = new_population
    
    # Return best solution found across all generations
    best = best_ever if best_ever else population[0]
    final_penalty = compute_penalty(best, adjacency)
    
    return best, final_penalty, counter.count, counter.first_solution_at