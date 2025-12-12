import random

def compute_penalty(state, adjacency):
    """Count violations (each edge counted once)"""
    penalty = 0
    seen = set()
    for region, neighbors in adjacency.items():
        for n in neighbors:
            edge = (min(region, n), max(region, n))
            if edge not in seen:
                seen.add(edge)
                if state[region] == state[n]:
                    penalty += 1
    return penalty


def genetic_algorithm(adjacency, num_regions, colors,
                      pop_size=100, generations=500, mutation_rate=0.05):
    
    class Counter:
        def __init__(self):
            self.count = 0
            self.first_solution_at = None
        
        def compute_penalty_tracked(self, state):
            self.count += 1
            penalty = compute_penalty(state, adjacency)
            
            if penalty == 0 and self.first_solution_at is None:
                self.first_solution_at = self.count
            
            return penalty
    
    counter = Counter()
    
    # Initialize with smart random (try to avoid conflicts)
    def smart_init():
        state = [None] * num_regions
        for region in range(num_regions):
            # Get colors used by already-assigned neighbors
            used_colors = set()
            for neighbor in adjacency[region]:
                if state[neighbor] is not None:
                    used_colors.add(state[neighbor])
            
            # Pick a random color not used by neighbors if possible
            available = [c for c in colors if c not in used_colors]
            if available:
                state[region] = random.choice(available)
            else:
                state[region] = random.choice(colors)
        return state
    
    # Initialize population with mix of smart and random
    population = []
    for i in range(pop_size):
        if i < pop_size // 2:
            population.append(smart_init())
        else:
            population.append([random.choice(colors) for _ in range(num_regions)])
    
    best_ever = None
    best_penalty = float('inf')
    stagnant_count = 0
    
    for gen in range(generations):
        # Evaluate and sort
        population.sort(key=lambda c: counter.compute_penalty_tracked(c))
        
        current_best_penalty = compute_penalty(population[0], adjacency)
        
        # Track best solution
        if current_best_penalty < best_penalty:
            best_penalty = current_best_penalty
            best_ever = population[0][:]
            stagnant_count = 0
        else:
            stagnant_count += 1
        
        # Found solution
        if counter.first_solution_at is not None:
            return population[0], 0, counter.count, counter.first_solution_at
        
        # Increase mutation if stagnant
        current_mutation = mutation_rate * (1 + stagnant_count / 50)
        
        # Elitism - keep top 20%
        elite_size = pop_size // 5
        new_population = population[:elite_size]
        
        # Generate new population
        while len(new_population) < pop_size:
            # Tournament selection
            tournament_size = 5
            parent1 = min(random.sample(population[:pop_size//2], tournament_size), 
                         key=lambda c: compute_penalty(c, adjacency))
            parent2 = min(random.sample(population[:pop_size//2], tournament_size),
                         key=lambda c: compute_penalty(c, adjacency))
            
            # Two-point crossover
            cp1 = random.randint(1, num_regions - 2)
            cp2 = random.randint(cp1 + 1, num_regions - 1)
            child = parent1[:cp1] + parent2[cp1:cp2] + parent1[cp2:]
            
            # Mutation with repair
            for i in range(num_regions):
                if random.random() < current_mutation:
                    # Try to pick color that reduces conflicts
                    neighbor_colors = [child[n] for n in adjacency[i]]
                    available = [c for c in colors if c not in neighbor_colors]
                    if available:
                        child[i] = random.choice(available)
                    else:
                        child[i] = random.choice(colors)
            
            new_population.append(child)
        
        population = new_population
    
    # Return best found
    best = best_ever if best_ever else population[0]
    final_penalty = compute_penalty(best, adjacency)
    
    return best, final_penalty, counter.count, counter.first_solution_at