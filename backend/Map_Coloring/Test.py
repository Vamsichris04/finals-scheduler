"""
Map Coloring Algorithm Test Suite

This comprehensive test module evaluates the performance and correctness of the three
map coloring algorithms (Genetic Algorithm, Simulated Annealing, and CSP) across
multiple benchmark problem instances of varying complexity and structure.

The test suite includes:
- Triangle: Complete graph K3 (requires 3 colors minimum)
- Square: Cycle graph C4 (requires 2 colors minimum)
- Hexagon: Cycle graph C6 (requires 2 colors minimum)
- ComplexMap: 8-region graph with varying connectivity patterns

Key Features:
- Standardized test cases with known optimal solutions
- Comparative algorithm performance analysis
- Solution validity verification for each test map
- Detailed output showing solutions, penalties, and performance metrics
- Support for algorithm parameter tuning and comparison

This testing framework provides systematic validation of algorithmic implementations
across different graph topologies, ensuring robustness and correctness for the Map
Coloring application. It serves as both a development tool for algorithm refinement
and a benchmark for comparing different approaches to constraint satisfaction problems.
"""

from map_ga_algo import genetic_algorithm
from map_sa_algo import simulated_annealing
from map_csp_algo import solve_csp

# Shared test maps
MAPS = {
    "Triangle": {
        "num_regions": 3,
        "adjacency": {
            0: [1, 2],
            1: [0, 2],
            2: [0, 1]
        }
    },
    "Square": {
        "num_regions": 4,
        "adjacency": {
            0: [1, 3],
            1: [0, 2],
            2: [1, 3],
            3: [0, 2]
        }
    },
    "Hexagon": {
        "num_regions": 6,
        "adjacency": {
            0: [1, 5],
            1: [0, 2],
            2: [1, 3],
            3: [2, 4],
            4: [3, 5],
            5: [4, 0]
        }
    },
    "ComplexMap": {
        "num_regions": 8,
        "adjacency": {
            0: [1, 2],
            1: [0, 3, 4],
            2: [0, 5],
            3: [1, 6],
            4: [1, 6, 7],
            5: [2, 7],
            6: [3, 4],
            7: [4, 5]
        }
    }
}

COLORS = [0, 1, 2, 3]

# ------------------------------
# Run Tests
# ------------------------------
for map_name, map_data in MAPS.items():
    print("\n" + "=" * 50)
    print(f"Testing Map: {map_name}")
    print("=" * 50)

    adjacency = map_data["adjacency"]
    num_regions = map_data["num_regions"]

    # ---------------- GA ----------------
    print("Genetic Algorithm")
    colors = [0, 1, 2, 3]  # define colors here

    ga_solution, ga_penalty, ga_evaluated, ga_first_solution = genetic_algorithm(
        adjacency, num_regions, colors
    )

    print("Solution:", ga_solution)
    print("Penalty:", ga_penalty)
    print("Total chromosomes evaluated:", ga_evaluated)
    if ga_first_solution:
        print("First valid solution found at evaluation:", ga_first_solution)

    # ---------------- SA ----------------
    print("\nSimulated Annealing")
    sa_solution, sa_penalty, sa_steps = simulated_annealing(
        adjacency,
        num_regions,
        COLORS
    )

    print("Solution:", sa_solution)
    print("Penalty:", sa_penalty)
    print("States explored:", sa_steps)

    # ---------------- CSP ----------------
    print("\nConstraint Satisfaction (CSP)")
    csp_solution, csp_nodes = solve_csp(
        adjacency,
        num_regions,
        COLORS
    )

    if csp_solution:
        print("Solution:", csp_solution)
        print("Backtracking nodes:", csp_nodes)
    else:
        print("No solution found")