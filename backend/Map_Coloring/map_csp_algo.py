"""
Map Coloring Constraint Satisfaction Problem (CSP) Solver

This module implements a complete Constraint Satisfaction Problem solver for the map coloring
problem using backtracking search with advanced heuristics and constraint propagation techniques.

The CSP approach models map coloring as a constraint satisfaction problem where:
- Variables: Regions to be colored
- Domains: Available colors for each region
- Constraints: Adjacent regions must have different colors

Key Features:
- Backtracking search with systematic exploration of solution space
- Minimum Remaining Values (MRV) heuristic for variable selection
- Forward checking for constraint propagation and domain pruning
- Conflict detection and early termination for infeasible branches
- Comprehensive performance tracking (nodes explored)

The algorithm guarantees finding a solution if one exists with the given color constraints,
making it ideal for exact solving of map coloring problems. It performs particularly well
on structured problems like planar graphs and can handle the full USA 50-state map.

This implementation serves as one of three algorithm options in the Map Coloring application,
providing guaranteed correctness and detailed search statistics.
"""

def solve_csp(adjacency, num_regions, colors):
    """
    Solve map coloring using CSP with backtracking and forward checking
    
    This function uses constraint satisfaction problem techniques with:
    - Backtracking: systematically explores solution space
    - MRV heuristic: selects variables with smallest remaining domain
    - Forward checking: prunes domains to detect conflicts early
    
    Args:
        adjacency (dict): Graph adjacency list where keys are regions (0 to num_regions-1)
                         and values are lists of adjacent region indices
        num_regions (int): Total number of regions to color
        colors (list): Available colors to assign (typically [0, 1, 2, 3] for maps)
    
    Returns:
        tuple: (solution_dict or None, nodes_explored_count)
               - solution_dict: dict mapping region index to color (if found)
               - nodes_explored_count: number of nodes explored during search
    """
    # Initialize domains: each region can initially be assigned any color
    domains = {r: colors.copy() for r in range(num_regions)}
    
    # Track current partial assignment (region -> color mapping)
    assignment = {}
    
    # Count nodes explored for performance analysis
    nodes = 0
    
    def is_consistent(region, color):
        """
        Check if assigning color to region violates any constraints.
        
        A color assignment is consistent if no adjacent region already 
        has the same color assigned.
        
        Args:
            region (int): Region to potentially assign color to
            color (int): Color to check for consistency
            
        Returns:
            bool: True if assignment is consistent, False otherwise
        """
        # Check all neighbors of this region
        for neighbor in adjacency[region]:
            # If neighbor already has an assignment and it matches this color, conflict!
            if neighbor in assignment and assignment[neighbor] == color:
                return False
        return True
    
    def select_unassigned_variable():
        """
        Select the next variable to assign using MRV (Minimum Remaining Values) heuristic.
        
        MRV: Choose the unassigned variable with the smallest domain (fewest legal colors).
        This heuristic reduces branching factor and detects failures early.
        
        Returns:
            int: Index of region with smallest domain, or None if all regions assigned
        """
        # Find all unassigned regions
        unassigned = [r for r in range(num_regions) if r not in assignment]
        if not unassigned:
            return None
        # Choose region with fewest legal values (MRV heuristic)
        return min(unassigned, key=lambda r: len(domains[r]))
    
    def forward_check(region, color):
        """
        Apply forward checking: remove assigned color from domains of unassigned neighbors.
        
        This constraint propagation technique prunes the search space by detecting
        domain wipeouts early (when a region has no legal colors left).
        
        Args:
            region (int): Region that was just assigned a color
            color (int): The color that was assigned
            
        Returns:
            dict: New domains with color removed from neighbors' domains, or
                  None if any domain becomes empty (pruning opportunity)
        """
        # Create copies of all domains to avoid modifying original
        new_domains = {r: domains[r].copy() for r in domains}
        
        # Process each neighbor of the assigned region
        for neighbor in adjacency[region]:
            if neighbor not in assignment:  # Only prune unassigned neighbors
                if color in new_domains[neighbor]:
                    # Remove the assigned color from neighbor's domain
                    new_domains[neighbor].remove(color)
                    # If any domain becomes empty, backtrack immediately
                    if len(new_domains[neighbor]) == 0:
                        return None  # Domain wipeout - backtrack
        
        return new_domains
    
    def backtrack():
        """
        Recursively search for a valid coloring using backtracking with forward checking.
        
        Algorithm:
        1. If all regions assigned, return solution
        2. Select unassigned region using MRV heuristic
        3. Try each color in region's domain:
           - Check consistency with already-assigned neighbors
           - Apply forward checking to prune domains
           - Recursively continue search
           - If successful, return solution
           - If failed, backtrack and restore domains
        4. If no color works, backtrack further
        
        Returns:
            dict: Complete assignment if solution found, None if no solution exists
        """
        nonlocal nodes, domains
        nodes += 1  # Increment node counter for each search node visited
        
        # Base case: all regions assigned - we have a solution!
        if len(assignment) == num_regions:
            return assignment
        
        # Select next region to color using MRV heuristic
        region = select_unassigned_variable()
        if region is None:
            # All regions should be assigned at this point
            return assignment if len(assignment) == num_regions else None
        
        # Try each color in this region's domain
        for color in domains[region][:]:  # Use slice to avoid modification issues
            if is_consistent(region, color):
                # Make assignment
                assignment[region] = color
                
                # Save old domains for backtracking
                old_domains = domains
                
                # Apply forward checking to prune domains
                new_domains = forward_check(region, color)
                
                if new_domains is not None:
                    # No domain wipeout, continue search with new domains
                    domains = new_domains
                    result = backtrack()
                    
                    if result is not None:
                        # Solution found!
                        return result
                    
                    # Restore domains if backtracking
                    domains = old_domains
                
                # Remove assignment and try next color
                del assignment[region]
        
        # No color worked, backtrack further
        return None
    
    # Execute backtracking search and return solution and node count
    solution = backtrack()
    return solution, nodes


# Test the algorithm
if __name__ == "__main__":
    # A triangle graph requires 3 colors minimum (complete graph K3)
    test_adjacency = {
        0: [1, 2],  # Region 0 adjacent to regions 1 and 2
        1: [0, 2],  # Region 1 adjacent to regions 0 and 2
        2: [0, 1]   # Region 2 adjacent to regions 0 and 1
    }
    
    # Solve using CSP with 4 available colors
    solution, nodes = solve_csp(test_adjacency, 3, [0, 1, 2, 3])
    print(f"Solution: {solution}")
    print(f"Nodes explored: {nodes}")
    
    # Verify the solution is valid
    if solution:
        valid = True
        for region in test_adjacency:
            for neighbor in test_adjacency[region]:
                # Check if any adjacent regions have the same color
                if solution[region] == solution[neighbor]:
                    print(f"VIOLATION: {region} and {neighbor}")
                    valid = False
        print(f"Valid: {valid}")