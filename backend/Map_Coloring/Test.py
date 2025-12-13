"""
Test class for Map Coloring algorithms on various test maps
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