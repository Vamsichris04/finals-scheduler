# IT Help Desk Scheduler

Scheduling system using AI algorithms (GA, SA, CSP) to generate work schedules for IT Help Desk student workers.

## How to Run

### 1. Install Dependencies
```bash
pip install pymongo numpy matplotlib
```

### 2. Run the Scheduler
```bash
# Simulated Annealing (recommended - fastest)
python main.py --algorithm SA --show-schedule

# Genetic Algorithm
python main.py --algorithm GA --show-schedule

# CSP Solver
python main.py --algorithm CSP --show-schedule

# Compare all algorithms
python main.py --compare

# Export schedule
python main.py --algorithm SA --export simple
```

### Command-Line Arguments
- `--algorithm` - GA, SA, or CSP (default: SA)
- `--compare` - Run and compare all three algorithms
- `--validate` - Run validation checks
- `--export` - Export format: simple, json, csv, mongodb, all
- `--show-schedule` - Print full schedule
- `--output-dir` - Output directory for exports

---

## File Descriptions

### main.py
Main entry point for running the scheduler.

**Classes:**
- `ScheduleExporter` - Exports schedules to JSON, CSV, MongoDB formats
  - `export_to_json()` - JSON with metadata and constraints
  - `export_to_csv()` - CSV for spreadsheets
  - `export_worker_summary()` - Worker hours and fairness metrics
  - `export_to_mongodb_format()` - MongoDB Shifts collection format
  - `export_all()` - All formats
- `ScheduleValidator` - Validates generated schedules
  - `quick_validate()` - Fast validation with penalty report

**Functions:**
- `run_scheduler()` - Runs a single algorithm with MongoDB data
- `compare_algorithms()` - Runs all three and compares results
- `main()` - CLI interface

---

### scheduling_env.py
Problem definition with constraints and fitness evaluation.

**Classes:**
- `Worker` - Represents a student worker
  - `is_available(day, hour)` - Checks availability based on busy times and commuter status
- `ShiftSlot` - Represents a time slot needing coverage
- `SchedulingEnvironment` - Main scheduling problem
  - `evaluate_schedule()` - Returns penalty score and constraint violations
  - `get_available_workers()` - Finds available workers for a slot
  - `schedule_to_matrix()` - Converts schedule to readable matrix
  - `print_schedule()` - Displays human-readable schedule

**Constraints Evaluated:** Coverage violations, worker conflicts, hour violations (max 20), min hours (14), shift length (2-6 hrs), tier mismatches, fairness, morning shifts

---

### genetic_algorithm.py
Genetic Algorithm implementation - evolves population of schedules.

**Methods:**
- `initialize_population()` - Creates initial population with valid block assignments
- `calculate_fitness()` - Evaluates penalty (lower = better)
- `select_parents()` - Tournament selection
- `crossover()` - Two-point crossover
- `mutate()` - 4 strategies: extend block, swap blocks, fill gaps, reassign slots
- `repair_chromosome()` - Fixes availability violations
- `solve()` - Main GA loop with elitism

---

### simulated_annealing.py
Simulated Annealing - temperature-based optimization.

**Methods:**
- `generate_initial_solution()` - Creates initial solution with block assignments
- `calculate_cost()` - Evaluates penalty
- `generate_neighbor()` - 5 strategies: swap, extend, shrink, reassign, fill empty
- `acceptance_probability()` - Metropolis criterion for accepting worse solutions
- `solve()` - Main SA loop with temperature cooling

---

### csp_solver.py
CSP Solver - two-phase greedy + local search approach.

**Methods:**
- `_build_greedy_solution()` - Phase 1: Greedy construction prioritizing workers under min hours
- `_local_search()` - Phase 2: Improves via swap, reassign, extend, fill gap moves
- `solve()` - Orchestrates both phases

---

### run_comparison.py
Algorithm comparison with visualizations.

**Functions:**
- `load_workers_from_mongo()` - Loads from MongoDB
- `load_workers_from_datafiles()` - Loads from local JSON files
- `run_ga()`, `run_sa()`, `run_csp()` - Run individual algorithms
- `plot_final_penalty_comparison()` - Bar chart of penalties
- `plot_convergence()` - Convergence analysis
- `plot_constraint_violations()` - Constraint breakdown
- `plot_runtime_comparison()` - Runtime metrics
- `plot_worker_hours_distribution()` - Worker hours vs desired
- `generate_summary_report()` - Text summary

---

### Utils/mongoDb_loader.py
MongoDB data integration.

**Methods:**
- `load_workers()` - Fetches active users and finals, returns Worker objects
- `parse_tier()` - Converts position string to tier integer
- `get_day_from_date()` - Parses ISO date to day of week
- `parse_time()` - Converts HH:MM to hour integer
- `print_loaded_data()` - Displays loaded workers
- `close()` - Closes MongoDB connection

---

### Utils/validator.py
Schedule validation utility.

**Functions:**
- `quick_validate()` - Validates schedule, classifies quality (Perfect/Excellent/Good/Needs Review), checks critical constraints, reports coverage gaps

---

### Utils/exporter.py
Export utilities (same as ScheduleExporter in main.py).

**Methods:**
- `export_to_json()`, `export_to_csv()`, `export_worker_summary()`, `export_to_mongodb_format()`, `export_all()`

---

### Data/
Contains sample data files:
- `Users.json` - Sample worker data
- `Finals.json` - Sample finals schedule data
