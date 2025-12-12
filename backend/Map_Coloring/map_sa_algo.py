import random
import math

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
            # Create normalized edge representation to prevent duplicates
            edge = (min(region, n), max(region, n))
            if edge not in seen:
                seen.add(edge)
                # Increment penalty if adjacent regions have same color
                if state[region] == state[n]:
                    penalty += 1
    return penalty


def simulated_annealing(adjacency, num_regions, colors,
                        initial_temp=1000, cooling_rate=0.995):
    """
    Solve map coloring using Simulated Annealing (SA) algorithm.
    
    Inspired by metallurgical annealing process, SA probabilistically accepts
    worse solutions to escape local optima, gradually reducing this probability
    through a "cooling" schedule.
    
    Algorithm overview:
    1. Start with a random solution and high temperature
    2. Repeatedly generate neighbor solutions by small modifications
    3. Accept better solutions always, worse solutions probabilistically
    4. Gradually lower temperature, reducing acceptance of worse solutions
    5. If stuck too long, reheat to explore new regions
    
    Key concepts:
    - Temperature (T): Controls acceptance probability of worse solutions
    - Metropolis Criterion: Accept move if delta < 0 or random() < exp(-delta/T)
    - Cooling Schedule: Temperature decreases each step
    - Adaptive Reheating: Reheat if no improvement for too long
    
    Args:
        adjacency (dict): Graph adjacency list (region -> list of neighbors)
        num_regions (int): Total number of regions to color
        colors (list): Available colors to assign
        initial_temp (float): Starting temperature (default 1000)
        cooling_rate (float): Multiplicative cooling factor per step (default 0.995)
    
    Returns:
        tuple: (best_solution, penalty, steps_taken)
               - best_solution: List of colors assigned to each region
               - penalty: Number of conflicts in best solution
               - steps_taken: Number of iterations performed
    """
    
    # Smart initialization: greedy coloring to avoid obvious conflicts
    state = [None] * num_regions
    for region in range(num_regions):
        # Collect colors already used by assigned neighbors
        used_colors = set()
        for neighbor in adjacency[region]:
            if state[neighbor] is not None:
                used_colors.add(state[neighbor])
        
        # Pick a color not used by neighbors if possible
        available = [c for c in colors if c not in used_colors]
        if available:
            state[region] = random.choice(available)
        else:
            # All colors used by neighbors, pick any random color
            state[region] = random.choice(colors)
    
    # Calculate initial penalty
    penalty = compute_penalty(state, adjacency)
    
    # Track best solution found during search
    best_state = state[:]
    best_penalty = penalty
    
    # Initialize temperature and iteration counters
    T = initial_temp
    steps = 0  # Total steps taken
    steps_since_improvement = 0  # Steps without finding better solution
    
    # Main simulated annealing loop
    # Continue while temperature is above threshold AND haven't exceeded max steps
    while T > 0.001 and steps < 100000:
        steps += 1
        
        # Generate neighbor solution: make a copy and change one region's color
        neighbor = state[:]
        region = random.randint(0, num_regions - 1)
        
        # Smart color selection: 70% prefer non-conflicting colors, 30% random
        neighbor_colors = [state[n] for n in adjacency[region]]
        # Find colors not used by neighbors and different from current color
        available = [c for c in colors if c not in neighbor_colors and c != state[region]]
        
        if available and random.random() < 0.7:
            # 70% of the time: pick a color that doesn't conflict with neighbors
            neighbor[region] = random.choice(available)
        else:
            # 30% of the time: pick a random color (allows worse moves, helps exploration)
            new_color = random.choice(colors)
            while new_color == state[region] and len(colors) > 1:
                new_color = random.choice(colors)
            neighbor[region] = new_color
        
        # Evaluate neighbor solution
        new_penalty = compute_penalty(neighbor, adjacency)
        delta = new_penalty - penalty  # Difference in penalty (negative = improvement)
        
        # Metropolis Criterion: Accept move if better, or probabilistically if worse
        # At high temperature: more likely to accept worse solutions
        # At low temperature: rarely accept worse solutions
        if delta < 0 or random.random() < math.exp(-delta / T):
            # Accept the move
            state = neighbor
            penalty = new_penalty
            steps_since_improvement = 0  # Reset stagnation counter
            
            # Track best solution found so far
            if penalty < best_penalty:
                best_state = state[:]
                best_penalty = penalty
        else:
            # Reject the move, stay with current solution
            steps_since_improvement += 1
        
        # Early exit: if perfect solution found, return immediately
        if penalty == 0:
            return state, 0, steps
        
        # Adaptive cooling: reheat if stuck in local optimum too long
        if steps_since_improvement > 1000:
            # No improvement for 1000 steps, reheat to explore new regions
            T = min(T * 1.5, initial_temp)  # Increase temperature (up to initial)
            steps_since_improvement = 0  # Reset counter
        else:
            # Continue normal cooling
            T *= cooling_rate
    
    # Return best solution found across all iterations
    return best_state, best_penalty, steps