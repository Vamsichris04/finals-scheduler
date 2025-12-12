from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from map_ga_algo import genetic_algorithm
from map_sa_algo import simulated_annealing
from map_csp_algo import solve_csp

app = Flask(__name__)
CORS(app)

# VERIFIED US State Adjacency - Alphabetical Order (0-49)
# 0=AL, 1=AK, 2=AZ, 3=AR, 4=CA, 5=CO, 6=CT, 7=DE, 8=FL, 9=GA, 10=HI
# 11=ID, 12=IL, 13=IN, 14=IA, 15=KY, 16=KS, 17=LA, 18=ME, 19=MD, 20=MA
# 21=MI, 22=MN, 23=MS, 24=MO, 25=MT, 26=NE, 27=NV, 28=NH, 29=NJ, 30=NM
# 31=NY, 32=NC, 33=ND, 34=OH, 35=OK, 36=OR, 37=PA, 38=RI, 39=SC, 40=SD
# 41=TN, 42=TX, 43=UT, 44=VT, 45=VA, 46=WA, 47=WV, 48=WI, 49=WY

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

MAPS = {
    "Triangle": {
        "num_regions": 3,
        "adjacency": {0: [1, 2], 1: [0, 2], 2: [0, 1]}
    },
    "Square": {
        "num_regions": 4,
        "adjacency": {0: [1, 3], 1: [0, 2], 2: [1, 3], 3: [0, 2]}
    },
    "Hexagon": {
        "num_regions": 6,
        "adjacency": {0: [1, 5], 1: [0, 2], 2: [1, 3], 3: [2, 4], 4: [3, 5], 5: [4, 0]}
    },
    "ComplexMap": {
        "num_regions": 8,
        "adjacency": {0: [1, 2], 1: [0, 3, 4], 2: [0, 5], 3: [1, 6], 4: [1, 6, 7], 5: [2, 7], 6: [3, 4], 7: [4, 5]}
    },
    "USA": {
        "num_regions": 50,
        "adjacency": US_ADJACENCY
    }
}

COLORS = [0, 1, 2, 3]

@app.route('/api/run', methods=['POST'])
def run_algorithm():
    """
    Execute a map coloring algorithm on the selected map.
    
    Expected JSON request body:
        - map (str): Name of the map to solve (Triangle, Square, Hexagon, ComplexMap, USA)
        - algorithm (str): Algorithm to use (GA, SA, CSP)
    
    Returns:
        JSON response with solution array and algorithm-specific metrics
    """
    try:
        data = request.json
        map_name = data.get('map')
        algorithm = data.get('algorithm')
        
        # Validate map selection
        if map_name not in MAPS:
            return jsonify({'error': 'Invalid map'}), 400
        
        # Extract map configuration
        map_data = MAPS[map_name]
        adjacency = map_data['adjacency']
        num_regions = map_data['num_regions']
        
        # Use enhanced parameters for large USA map, standard parameters for smaller maps
        if map_name == 'USA':
            # Enhanced parameters for large-scale 50-state problem
            if algorithm == 'GA':
                # Genetic Algorithm: larger population and more generations for USA
                solution, penalty, evaluated, first_solution_at = genetic_algorithm(
                    adjacency, num_regions, COLORS,
                    pop_size=500,  # Large population for exploration
                    generations=2000,  # More generations for convergence
                    mutation_rate=0.15  # Higher mutation to maintain diversity
                )
            elif algorithm == 'SA':
                # Simulated Annealing: higher temperature and slower cooling for USA
                solution, penalty, steps = simulated_annealing(
                    adjacency, num_regions, COLORS,
                    initial_temp=5000,  # Higher starting temperature
                    cooling_rate=0.9998  # Slower cooling rate
                )
            elif algorithm == 'CSP':
                # Constraint Satisfaction Problem: may struggle with large graphs
                solution, nodes = solve_csp(adjacency, num_regions, COLORS)
        else:
            # Standard parameters for smaller maps (Triangle, Square, Hexagon, ComplexMap)
            if algorithm == 'GA':
                solution, penalty, evaluated, first_solution_at = genetic_algorithm(
                    adjacency, num_regions, COLORS
                )
            elif algorithm == 'SA':
                solution, penalty, steps = simulated_annealing(
                    adjacency, num_regions, COLORS
                )
            elif algorithm == 'CSP':
                solution, nodes = solve_csp(adjacency, num_regions, COLORS)
        
        # Format response based on algorithm used
        if algorithm == 'GA':
            # Return GA-specific metrics: penalty, evaluations count, first solution found
            return jsonify({
                'solution': solution,
                'penalty': penalty,
                'evaluated': evaluated,
                'firstSolutionAt': first_solution_at,
                'algoName': 'Genetic Algorithm'
            })
        elif algorithm == 'SA':
            # Return SA-specific metrics: penalty and number of steps taken
            return jsonify({
                'solution': solution,
                'penalty': penalty,
                'steps': steps,
                'algoName': 'Simulated Annealing'
            })
        elif algorithm == 'CSP':
            # Convert CSP solution from dict to list format for frontend
            if solution:
                solution_list = [solution[i] for i in range(num_regions)]
            else:
                solution_list = None
            # Return CSP-specific metrics: number of nodes explored
            return jsonify({
                'solution': solution_list,
                'nodes': nodes,
                'algoName': 'CSP Backtracking'
            })
        else:
            # Invalid algorithm selection
            return jsonify({'error': 'Invalid algorithm'}), 400
            
    except Exception as e:
        # Handle errors and return error response
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/maps', methods=['GET'])
def get_maps():
    """
    Retrieve all available maps and their configurations.
    
    Returns:
        JSON object containing all maps with their region counts and adjacency data
    """
    return jsonify(MAPS)

if __name__ == '__main__':
    # Start Flask development server on port 5000 with debug mode enabled
    app.run(debug=True, port=5000)