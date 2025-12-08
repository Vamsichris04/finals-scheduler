def solve_csp(adjacency, num_regions, colors):
    """
    Solve map coloring using CSP with backtracking and forward checking
    Returns: (solution_dict or None, nodes_explored_count)
    """
    domains = {r: colors.copy() for r in range(num_regions)}
    assignment = {}
    nodes = 0
    
    def is_consistent(region, color):
        """Check if assigning color to region violates any constraints"""
        for neighbor in adjacency[region]:
            if neighbor in assignment and assignment[neighbor] == color:
                return False
        return True
    
    def select_unassigned_variable():
        """MRV heuristic: choose variable with smallest domain"""
        unassigned = [r for r in range(num_regions) if r not in assignment]
        if not unassigned:
            return None
        # Choose region with fewest legal values (MRV)
        return min(unassigned, key=lambda r: len(domains[r]))
    
    def forward_check(region, color):
        """
        Remove color from domains of all neighbors
        Returns new domains or None if any domain becomes empty
        """
        new_domains = {r: domains[r].copy() for r in domains}
        
        for neighbor in adjacency[region]:
            if neighbor not in assignment:  # Only prune unassigned neighbors
                if color in new_domains[neighbor]:
                    new_domains[neighbor].remove(color)
                    if len(new_domains[neighbor]) == 0:
                        return None  # Domain wipeout - backtrack
        
        return new_domains
    
    def backtrack():
        nonlocal nodes, domains
        nodes += 1
        
        # If all regions assigned, we found a solution
        if len(assignment) == num_regions:
            return assignment
        
        # Select next region to color
        region = select_unassigned_variable()
        if region is None:
            return assignment if len(assignment) == num_regions else None
        
        # Try each color in the domain
        for color in domains[region][:]:  # Use slice to avoid modification issues
            if is_consistent(region, color):
                # Make assignment
                assignment[region] = color
                
                # Save old domains for backtracking
                old_domains = domains
                
                # Forward check
                new_domains = forward_check(region, color)
                
                if new_domains is not None:
                    domains = new_domains
                    result = backtrack()
                    
                    if result is not None:
                        return result
                    
                    # Restore domains if backtracking
                    domains = old_domains
                
                # Remove assignment if failed
                del assignment[region]
        
        return None
    
    solution = backtrack()
    return solution, nodes


# Test the algorithm
if __name__ == "__main__":
    # Test with triangle (should be easy)
    test_adjacency = {
        0: [1, 2],
        1: [0, 2],
        2: [0, 1]
    }
    
    solution, nodes = solve_csp(test_adjacency, 3, [0, 1, 2, 3])
    print(f"Solution: {solution}")
    print(f"Nodes explored: {nodes}")
    
    # Verify
    if solution:
        valid = True
        for region in test_adjacency:
            for neighbor in test_adjacency[region]:
                if solution[region] == solution[neighbor]:
                    print(f"VIOLATION: {region} and {neighbor}")
                    valid = False
        print(f"Valid: {valid}")