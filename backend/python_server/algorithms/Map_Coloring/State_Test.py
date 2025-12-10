"""
Run this to test your actual algorithm outputs
Usage: python verify_real_solutions.py
"""

from map_ga_algo import genetic_algorithm
from map_sa_algo import simulated_annealing
from map_csp_algo import solve_csp

# State names for debugging
STATE_NAMES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KY", "KS", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

US_ADJACENCY = {
    0: [8, 9, 23, 41],  # AL: FL, GA, MS, TN
    1: [],  # AK: island
    2: [4, 5, 27, 30, 43],  # AZ: CA, CO, NV, NM, UT  
    3: [17, 23, 24, 35, 41, 42],  # AR: LA, MS, MO, OK, TN, TX
    4: [2, 27, 36],  # CA: AZ, NV, OR
    5: [2, 16, 26, 30, 35, 43, 49],  # CO: AZ, KS, NE, NM, OK, UT, WY
    6: [20, 31, 38],  # CT: MA, NY, RI
    7: [19, 29, 37],  # DE: MD, NJ, PA
    8: [0, 9],  # FL: AL, GA
    9: [0, 8, 32, 39, 41],  # GA: AL, FL, NC, SC, TN
    10: [],  # HI: island
    11: [25, 27, 36, 43, 46, 49],  # ID: MT, NV, OR, UT, WA, WY
    12: [13, 14, 15, 24, 48],  # IL: IN, IA, KY, MO, WI
    13: [12, 15, 21, 34],  # IN: IL, KY, MI, OH
    14: [12, 22, 24, 26, 40, 48],  # IA: IL, MN, MO, NE, SD, WI
    15: [12, 13, 24, 34, 41, 47],  # KY: IL, IN, MO, OH, TN, WV
    16: [5, 24, 26, 35],  # KS: CO, MO, NE, OK
    17: [3, 23, 42],  # LA: AR, MS, TX
    18: [28],  # ME: NH
    19: [7, 37, 45, 47],  # MD: DE, PA, VA, WV
    20: [6, 28, 31, 38, 44],  # MA: CT, NH, NY, RI, VT
    21: [13, 34, 48],  # MI: IN, OH, WI
    22: [14, 33, 40, 48],  # MN: IA, ND, SD, WI
    23: [0, 3, 17, 41],  # MS: AL, AR, LA, TN
    24: [3, 12, 14, 15, 16, 26, 35, 41],  # MO: AR, IL, IA, KY, KS, NE, OK, TN
    25: [11, 33, 40, 49],  # MT: ID, ND, SD, WY
    26: [5, 14, 16, 24, 40, 49],  # NE: CO, IA, KS, MO, SD, WY
    27: [2, 4, 11, 36, 43],  # NV: AZ, CA, ID, OR, UT
    28: [18, 20, 44],  # NH: ME, MA, VT
    29: [7, 31, 37],  # NJ: DE, NY, PA
    30: [2, 5, 35, 42],  # NM: AZ, CO, OK, TX
    31: [6, 20, 29, 37, 44],  # NY: CT, MA, NJ, PA, VT
    32: [9, 39, 41, 45],  # NC: GA, SC, TN, VA
    33: [22, 25, 40],  # ND: MN, MT, SD
    34: [13, 15, 21, 37, 47],  # OH: IN, KY, MI, PA, WV
    35: [3, 5, 16, 24, 30, 42],  # OK: AR, CO, KS, MO, NM, TX
    36: [4, 11, 27, 46],  # OR: CA, ID, NV, WA
    37: [7, 19, 29, 31, 34, 47],  # PA: DE, MD, NJ, NY, OH, WV
    38: [6, 20],  # RI: CT, MA
    39: [9, 32],  # SC: GA, NC
    40: [14, 22, 25, 26, 33, 49],  # SD: IA, MN, MT, NE, ND, WY
    41: [0, 3, 9, 15, 23, 24, 32, 45],  # TN: AL, AR, GA, KY, MS, MO, NC, VA
    42: [3, 17, 30, 35],  # TX: AR, LA, NM, OK
    43: [2, 5, 11, 27, 49],  # UT: AZ, CO, ID, NV, WY
    44: [20, 28, 31],  # VT: MA, NH, NY
    45: [15, 19, 32, 41, 47],  # VA: KY, MD, NC, TN, WV
    46: [11, 36],  # WA: ID, OR
    47: [15, 19, 34, 37, 45],  # WV: KY, MD, OH, PA, VA
    48: [12, 14, 21, 22],  # WI: IL, IA, MI, MN
    49: [5, 11, 25, 26, 40, 43]  # WY: CO, ID, MT, NE, SD, UT
}

COLORS = [0, 1, 2, 3]

def verify_solution(solution, adjacency):
    """Verify if solution is valid"""
    violations = []
    
    for region in adjacency:
        for neighbor in adjacency[region]:
            if region < neighbor:  # Check each edge once
                if solution[region] == solution[neighbor]:
                    violations.append((region, neighbor, solution[region]))
    
    return len(violations) == 0, violations


def test_algorithm(name, algo_func, *args):
    """Test an algorithm and verify its solution"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print('='*60)
    
    try:
        result = algo_func(*args)
        
        if name == "CSP":
            solution_dict, nodes = result
            if solution_dict:
                solution = [solution_dict[i] for i in range(50)]
            else:
                print("❌ No solution found!")
                return
            print(f"Nodes explored: {nodes:,}")
        elif name == "SA":
            solution, penalty, steps = result
            print(f"Steps: {steps:,}")
            print(f"Reported penalty: {penalty}")
        else:  # GA
            solution, penalty, evals, first = result
            print(f"Evaluations: {evals:,}")
            print(f"First solution at: {first if first else 'N/A'}")
            print(f"Reported penalty: {penalty}")
        
        # Verify the solution
        is_valid, violations = verify_solution(solution, US_ADJACENCY)
        
        print(f"\n{'✅ VALID' if is_valid else '❌ INVALID'} - Actual violations: {len(violations)}")
        
        if not is_valid:
            print(f"\nFirst 10 violations:")
            for i, (s1, s2, color) in enumerate(violations[:10], 1):
                print(f"  {i}. {STATE_NAMES[s1]} ({s1}) and {STATE_NAMES[s2]} ({s2}) both have color {color}")
            
            if len(violations) > 10:
                print(f"  ... and {len(violations) - 10} more violations")
        
        # Print solution
        print(f"\nSolution: {solution[:20]}... (showing first 20 states)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Testing Map Coloring Algorithms on USA Map (50 states)")
    print("This will verify if solutions are truly valid\n")
    
    # Test CSP
    test_algorithm("CSP", solve_csp, US_ADJACENCY, 50, COLORS)
    
    # Test SA
    test_algorithm("SA", simulated_annealing, US_ADJACENCY, 50, COLORS,
                   5000, 0.9998)
    
    # Test GA
    test_algorithm("GA", genetic_algorithm, US_ADJACENCY, 50, COLORS,
                   500, 2000, 0.15)
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)