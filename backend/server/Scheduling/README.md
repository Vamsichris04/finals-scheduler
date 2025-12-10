# IT Help Desk Scheduler - Core Implementation

## Overview

This is a scheduling system that uses AI algorithms (Genetic Algorithm, Simulated Annealing, CSP) to automatically generate work schedules for MSOE IT Help Desk student workers. It reads data directly from your MongoDB database.

## Files

```
scheduler-core/
├── main.py                    # Main entry point - run this!
├── mongodb_loader.py          # Loads data from MongoDB
├── scheduling_environment.py  # Problem definition & constraints
├── genetic_algorithm.py       # GA implementation
├── simulated_annealing.py     # SA implementation
├── csp_solver.py             # CSP implementation
├── requirements.txt          # Dependencies
├── README.md                 # This file
└── INDEX.md                  # Detailed documentation
```

## Quick Start

### 1. Install Dependencies

```bash
pip install pymongo numpy matplotlib
```

Or use requirements file:
```bash
pip install -r requirements.txt
```

### 2. Make Sure MongoDB is Running

Your MongoDB should have:
- Database: `finals_scheduler`
- Collections: `users`, `finals`

### 3. Run the Scheduler

**Recommended (fastest and best results):**
```bash
python main.py --algorithm SA --show-schedule
```

**Try Genetic Algorithm:**
```bash
python main.py --algorithm GA --show-schedule
```

**Compare All Three:**
```bash
python main.py --compare
```

## Command-Line Options

```bash
# Basic usage
python main.py --algorithm SA              # Run Simulated Annealing
python main.py --algorithm GA              # Run Genetic Algorithm
python main.py --algorithm CSP             # Run CSP solver

# Show full schedule
python main.py --algorithm SA --show-schedule

# Compare all algorithms
python main.py --compare

# Different schedule types
python main.py --algorithm SA --schedule-type finals    # Finals week
python main.py --algorithm SA --schedule-type regular   # Regular semester

# Custom MongoDB connection
python main.py --algorithm SA --db-host mongodb://localhost:27017/ --db-name finals_scheduler

# Quiet mode (less output)
python main.py --algorithm SA --quiet
```

## MongoDB Schema

### Users Collection

```javascript
{
  "_id": ObjectId,
  "name": "John Doe",
  "userId": 123456,                    // Unique employee ID
  "email": "doe@msoe.edu",
  "role": "user",                      // or "admin"
  "position": "Tier 2",                // Tier 1, 2, 3, or 4
  "isCommuter": false,                 // true if can't work before 9am
  "isActive": true,                    // Only active users scheduled
  "desiredHours": 15                   // Target hours per week
}
```

### Finals Collection

```javascript
{
  "_id": ObjectId,
  "userId": "123456",                  // String reference to user
  "date": "2024-12-18T00:00:00.000Z", // ISO date
  "startTime": "14:00",                // HH:MM format
  "endTime": "16:00"                   // HH:MM format
}
```

## Algorithm Comparison

| Algorithm | Speed | Quality | When to Use |
|-----------|-------|---------|-------------|
| **SA** (Simulated Annealing) | Fast (10-30s) | Best | **Recommended** - Best balance |
| **GA** (Genetic Algorithm) | Medium (20-40s) | Good | When SA gets stuck |
| **CSP** (Backtracking) | Slow (30-60s) | Variable | For verification |

**Recommendation:** Start with SA. It's fastest and usually finds the best schedules.

## Understanding Results

### Penalty Scores

The algorithm outputs a "penalty" score where lower is better:

- **0**: Perfect! All constraints satisfied
- **< 500**: Excellent schedule
- **500-1500**: Good schedule with minor issues
- **> 1500**: Has problems, try running again

### Common Violations

- `coverage_violations`: Not enough workers for some shifts
- `worker_conflicts`: Worker scheduled during finals/busy time
- `hour_violations`: Worker has more than 20 hours
- `fairness_violations`: Unbalanced hour distribution
- `morning_shift_violations`: Too many morning shifts for one worker

## Constraints Implemented

All constraints from your requirements are enforced:

✓ **Worker Constraints:**
- Max 20 hours per week
- Desired hours (10-18 typical)
- 4 tiers (1=entry, 2=experienced, 3=inventory tech, 4=manager)
- Commuters can't work before 9 AM
- Finals/busy times respected

✓ **Shift Requirements:**
- Window shifts: 1-2 workers required
- Remote shifts: 1-4 workers required
- Tier 3-4 prefer Remote (but can do Window if needed)

✓ **Operating Hours:**
- **Finals:** Mon-Thu 7:30am-8pm, Fri 7:30am-5pm
- **Regular:** Mon-Thu 7:30am-8pm, Fri 7:30am-5pm, Sat 10am-6pm

✓ **Fairness:**
- Balanced hours across workers
- Limited morning shifts (max 2 per worker)
- Shift lengths 1.5-6 hours
- No gaps in coverage

## Customizing Parameters

Edit `main.py` to tune algorithm parameters:

### Genetic Algorithm
```python
solver = GeneticAlgorithm(
    env,
    population_size=100,    # More = better exploration (slower)
    generations=300,        # More = better convergence (slower)
    crossover_rate=0.8,     # 0.7-0.9 typical
    mutation_rate=0.2,      # 0.1-0.3 typical
    elitism_count=5         # Best individuals to preserve
)
```

### Simulated Annealing
```python
solver = SimulatedAnnealing(
    env,
    initial_temp=1000.0,        # Higher = more exploration
    final_temp=0.1,             # When to stop
    cooling_rate=0.995,         # Slower = more thorough (0.99-0.999)
    iterations_per_temp=50      # More = better quality
)
```

### CSP Solver
```python
solver = CSPSolver(
    env,
    max_time=60.0,              # Time limit in seconds
    use_forward_checking=True,  # Enable constraint propagation
    use_mrv=True                # Use MRV heuristic
)
```

## Troubleshooting

### "ModuleNotFoundError: pymongo"
```bash
pip install pymongo
```

### "Connection refused" or "MongoDB not found"
Make sure MongoDB is running:
```bash
# Check if MongoDB is running
mongosh
```

### "No active workers found"
Check your database:
```javascript
// In mongosh
use finals_scheduler
db.users.find({isActive: true}).count()
```

### Results seem poor (high penalty)
Try:
1. Run SA multiple times (it's fast)
2. Check if workers have too many conflicts
3. Verify operating hours match your needs
4. Try GA for different approach

## Testing Without MongoDB

To test algorithms without MongoDB, you can modify `main.py` to use sample data:

```python
# Add at top of main.py
from sample_data import generate_sample_workers

# Replace MongoDB loading with:
workers = generate_sample_workers(15)
```

Then create a simple `sample_data.py` with test workers.

## Output Example

```
================================================================================
RUNNING SA ALGORITHM
================================================================================
Initial solution cost: 1245.50
Iteration 1000, Temp=606.53, Best Cost=456.20, Current Cost=523.10
...
SA completed. Best cost: 234.50

================================================================================
RESULTS
================================================================================
Algorithm: SA
Runtime: 12.34 seconds
Final Penalty: 234.50

Constraint Violations:
  fairness_violations: 3
  morning_shift_violations: 1

✓ EXCELLENT SCHEDULE - Minor violations only
```

## Next Steps

1. **Test it works:** `python main.py --algorithm SA`
2. **View schedule:** `python main.py --algorithm SA --show-schedule`
3. **Compare algorithms:** `python main.py --compare`
4. **Integrate:** Use generated schedule in your application

## Integration with Your App

The schedule can be converted to MongoDB Shifts format. See `main.py` for the schedule structure - each slot in the solution array corresponds to a shift that can be saved to your Shifts collection.

## For Your Project Report

This implementation demonstrates:
- ✓ Three different AI algorithms (GA, SA, CSP)
- ✓ Real-world constraint satisfaction problem
- ✓ Direct integration with existing database
- ✓ Comparative analysis of algorithms
- ✓ Practical scheduling solution

## Need Help?

1. Read `INDEX.md` for detailed documentation
2. Check code comments in each `.py` file
3. Try `python main.py --help` for all options
4. Run with `--compare` to see which algorithm works best

---

**Quick Commands:**
```bash
# Most common usage
python main.py --algorithm SA --show-schedule

# Quick comparison
python main.py --compare

# Full output
python main.py --algorithm SA --show-schedule > schedule.txt
```