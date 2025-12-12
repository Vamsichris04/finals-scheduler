# Map Coloring Algorithm Visualizer

An interactive visualization tool for solving the graph coloring problem using three different algorithms: **Constraint Satisfaction Problem (CSP) with Backtracking**, **Genetic Algorithm (GA)**, and **Simulated Annealing (SA)**.

## Overview

The Map Coloring problem is a classic constraint satisfaction problem where the goal is to assign colors to adjacent regions (states) such that no two adjacent regions have the same color. This project implements three different optimization algorithms to solve this problem and provides an interactive web-based visualizer.

## Algorithms

### 1. CSP with Backtracking and Forward Checking (`map_csp_algo.py`)

A complete search algorithm that uses:
- **Backtracking**: Systematically explores the solution space
- **MRV Heuristic**: Selects variables with the smallest remaining domain first
- **Forward Checking**: Prunes domain values to detect conflicts early

**Strengths:**
- Guarantees an optimal solution if one exists
- Efficient pruning reduces search space

**Best for:** Small to medium-sized problems (triangles, squares, hexagons, complex maps)

### 2. Genetic Algorithm (`map_ga_algo.py`)

An evolutionary optimization approach featuring:
- **Smart Initialization**: Prefers conflict-avoiding color assignments
- **Tournament Selection**: Selects fittest parents for reproduction
- **Two-Point Crossover**: Combines genetic material from two parents
- **Adaptive Mutation**: Increases mutation rate when population stagnates
- **Elitism**: Preserves top solutions across generations

**Strengths:**
- Good for large problems (e.g., USA map with 50 states)
- Scalable and parallelizable
- Adaptive parameter tuning

**Best for:** Large-scale problems where exact solutions are computationally expensive

### 3. Simulated Annealing (`map_sa_algo.py`)

A probabilistic algorithm inspired by metallurgical annealing:
- **Smart Initialization**: Starts with conflict-avoiding assignments
- **Neighborhood Exploration**: Makes small color changes to regions
- **Temperature-based Acceptance**: Probabilistically accepts worse solutions to escape local optima
- **Adaptive Cooling**: Reheats when stuck to explore new regions

**Strengths:**
- Good balance between exploration and exploitation
- Often finds near-optimal solutions quickly
- Adaptive cooling helps escape local minima

**Best for:** Large problems where quick near-optimal solutions are acceptable

## Project Structure

```
Map_Coloring/
├── map_csp_algo.py          # CSP backtracking implementation
├── map_ga_algo.py           # Genetic algorithm implementation
├── map_sa_algo.py           # Simulated annealing implementation
├── map_color_server.py      # Flask backend server
├── README.md                # This file
└── Frontend/
    └── map_color.html       # Interactive visualizer
```

## Setup and Installation

### Prerequisites
- Python 3.7+
- Flask
- Flask-CORS

### Installation

1. Install required dependencies:
```bash
pip install flask flask-cors
```

2. Navigate to the Map_Coloring directory:
```bash
cd backend/python_server/algorithms/Map_Coloring
```

3. Start the Flask server:
```bash
python map_color_server.py
```

The server will start on `http://localhost:5000`

4. Open the visualizer:
- Open `Frontend/map_color.html` in your web browser, or
- Use a local web server to serve the file

## Usage

### Web Interface

1. **Select a Map**: Choose from predefined maps:
   - **Triangle**: 3 regions (requires minimum 3 colors)
   - **Square**: 4 regions (requires minimum 2 colors)
   - **Hexagon**: 6 regions (requires minimum 3 colors)
   - **ComplexMap**: 8 regions (requires minimum 3 colors)
   - **USA**: 50 states (requires minimum 4 colors)

2. **Select an Algorithm**: Choose CSP, GA, or SA

3. **Run**: Click the "Run Algorithm" button

4. **View Results**: The visualization shows:
   - Colored map/graph
   - Number of conflicts
   - Algorithm-specific metrics (nodes explored, evaluations, steps)

### API Endpoints

#### POST `/api/run`

Runs the selected algorithm on the selected map.

**Request:**
```json
{
  "map": "USA",
  "algorithm": "GA"
}
```

**Response (Genetic Algorithm):**
```json
{
  "solution": [0, 1, 0, 2, ...],
  "penalty": 0,
  "evaluated": 45000,
  "firstSolutionAt": 12345,
  "algoName": "Genetic Algorithm"
}
```

**Response (Simulated Annealing):**
```json
{
  "solution": [0, 1, 0, 2, ...],
  "penalty": 0,
  "steps": 15000,
  "algoName": "Simulated Annealing"
}
```

**Response (CSP):**
```json
{
  "solution": [0, 1, 0, 2, ...],
  "nodes": 1234,
  "algoName": "CSP Backtracking"
}
```

#### GET `/api/maps`

Returns available maps and their configurations.

## Algorithm Parameters

### Genetic Algorithm
- **Population Size**: 100 (500 for USA)
- **Generations**: 500 (2000 for USA)
- **Mutation Rate**: 0.05 (15% for USA)
- **Elitism**: Top 20% of population preserved

### Simulated Annealing
- **Initial Temperature**: 1000 (5000 for USA)
- **Cooling Rate**: 0.995 (0.9998 for USA)
- **Max Steps**: 100,000
- **Reheat Threshold**: 1000 steps without improvement

### CSP Backtracking
- **Variable Selection**: MRV (Minimum Remaining Values) heuristic
- **Constraint Propagation**: Forward checking

## Performance Considerations

- **CSP**: Best for small graphs; may struggle with 50-state USA map
- **GA**: Excellent for large problems; handles USA map efficiently
- **SA**: Good balance; faster than GA for small problems; competitive on large problems

## Color Scheme

The visualizer uses 4 colors by default:
- **Color 0**: Red (#FF6B6B)
- **Color 1**: Teal (#4ECDC4)
- **Color 2**: Blue (#45B7D1)
- **Color 3**: Orange (#FFA07A)

The Four Color Theorem guarantees that any planar graph (including maps) can be colored with at most 4 colors.

## Modifications and Extensions

### Adding New Maps

Edit `map_color_server.py` and add to the `MAPS` dictionary:

```python
MAPS = {
    "YourMap": {
        "num_regions": N,
        "adjacency": {
            0: [1, 2, ...],
            1: [0, 3, ...],
            ...
        }
    }
}
```

### Custom Algorithm Parameters

Modify the parameters in the `/api/run` endpoint handler in `map_color_server.py`:

```python
if map_name == 'YourMap':
    if algorithm == 'GA':
        solution, penalty, evaluated, first_solution_at = genetic_algorithm(
            adjacency, num_regions, COLORS,
            pop_size=150,      # Adjust as needed
            generations=1000,
            mutation_rate=0.1
        )
```

## Troubleshooting

**Flask server not running:**
- Ensure Python is installed and Flask/Flask-CORS are installed
- Check that port 5000 is not in use
- Run with debug mode for detailed error messages

**Visualizer not loading:**
- Ensure Flask server is running on `http://localhost:5000`
- Check browser console for CORS errors
- Verify all dependencies are installed

**USA map not rendering:**
- The app attempts to fetch TopoJSON data from CDN
- Check internet connection and browser console for network errors
- Falls back to grid layout if CDN is unavailable

## References

- **Four Color Theorem**: https://distributedmuseum.illinois.edu/exhibit/four-color-theorem/
- **Constraint Satisfaction**: https://www.geeksforgeeks.org/artificial-intelligence/constraint-satisfaction-problems-csp-in-artificial-intelligence/
- **Genetic Algorithms**: https://www.geeksforgeeks.org/dsa/genetic-algorithms/ 
- **Simulated Annealing**: https://www.geeksforgeeks.org/artificial-intelligence/what-is-simulated-annealing/

## Authors
Sukhbir S.
Vamsi S.
