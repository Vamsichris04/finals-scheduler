import random
import math

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


def simulated_annealing(adjacency, num_regions, colors,
                        initial_temp=1000, cooling_rate=0.995):
    
    # Smart initialization - try to avoid conflicts
    state = [None] * num_regions
    for region in range(num_regions):
        used_colors = set()
        for neighbor in adjacency[region]:
            if state[neighbor] is not None:
                used_colors.add(state[neighbor])
        
        available = [c for c in colors if c not in used_colors]
        if available:
            state[region] = random.choice(available)
        else:
            state[region] = random.choice(colors)
    
    penalty = compute_penalty(state, adjacency)
    best_state = state[:]
    best_penalty = penalty
    
    T = initial_temp
    steps = 0
    steps_since_improvement = 0
    
    while T > 0.001 and steps < 100000:  # Add max steps limit
        steps += 1
        
        # Generate neighbor - flip a random region's color
        neighbor = state[:]
        region = random.randint(0, num_regions - 1)
        
        # Smart color selection - prefer colors that reduce conflicts
        neighbor_colors = [state[n] for n in adjacency[region]]
        available = [c for c in colors if c not in neighbor_colors and c != state[region]]
        
        if available and random.random() < 0.7:  # 70% smart, 30% random
            neighbor[region] = random.choice(available)
        else:
            new_color = random.choice(colors)
            while new_color == state[region] and len(colors) > 1:
                new_color = random.choice(colors)
            neighbor[region] = new_color
        
        new_penalty = compute_penalty(neighbor, adjacency)
        delta = new_penalty - penalty
        
        # Accept if better, or with probability based on temperature
        if delta < 0 or random.random() < math.exp(-delta / T):
            state = neighbor
            penalty = new_penalty
            steps_since_improvement = 0
            
            # Track best solution
            if penalty < best_penalty:
                best_state = state[:]
                best_penalty = penalty
        else:
            steps_since_improvement += 1
        
        # Found solution
        if penalty == 0:
            return state, 0, steps
        
        # Adaptive cooling - reheat if stuck
        if steps_since_improvement > 1000:
            T = min(T * 1.5, initial_temp)  # Reheat
            steps_since_improvement = 0
        else:
            T *= cooling_rate
    
    # Return best found
    return best_state, best_penalty, steps