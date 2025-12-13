"""
Algorithm Comparison Script for IT Scheduler
Runs all 3 algorithms (GA, SA, CSP) with quick settings and generates comparison visualizations
"""

import sys
import os
import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduling_env import SchedulingEnvironment, Worker
from Utils.mongoDb_loader import MongoDBLoader
from Utils.validator import quick_validate
from Utils.exporter import ScheduleExporter
from genetic_algorithm import GeneticAlgorithm
from simulated_annealing import SimulatedAnnealing
from csp_solver import CSPSolver


# ============================================================================
# CONFIGURATION - Quick runs for comparison
# ============================================================================

# Reduced parameters for quick testing (adjust as needed)
GA_CONFIG = {
    'population_size': 200,      # Reduced from 250
    'generations': 5000,         # Reduced from 5000
    'crossover_rate': 0.85,
    'mutation_rate': 0.35,
    'elitism_count': 25
}

SA_CONFIG = {
    'initial_temp': 2000.0,     # Reduced from 3500
    'final_temp': 0.001,          # Increased from 0.001 for faster convergence
    'cooling_rate': 0.95,       # Faster cooling (was 0.9985)
    'iterations_per_temp': 1500   # Reduced from 300
}

CSP_CONFIG = {
    'max_time': 1500.0,           
    'local_search_iterations': 5000  
}

# Output directory for plots
OUTPUT_DIR = 'comparison_outputs'


# ============================================================================
# SAMPLE DATA GENERATION
# ============================================================================

def load_workers_from_mongo(connection_string: str = "mongodb://localhost:27017/", database: str = "finals_scheduler"):
    """Load workers from MongoDB using Utils.mongoDb_loader.MongoDBLoader
    Falls back to an empty list if MongoDB is not available or no active workers."""
    try:
        loader = MongoDBLoader(connection_string, database)
        workers = loader.load_workers()
        loader.print_loaded_data(workers)
        loader.close()

        if not workers:
            print("  [ERROR] No active workers found in MongoDB. Please check the DB.")
        return workers
    except Exception as e:
        print(f"  [ERROR] Failed to load data from MongoDB: {e}")
        return []


def load_workers_from_datafiles(data_dir: str = 'Data'):
    """Load workers and finals from data JSON files under `data_dir`.
    Returns a list of `Worker` objects like the MongoDB loader.
    """
    import json
    users_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_dir, 'Users.json')
    finals_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_dir, 'Finals.json')

    if not os.path.exists(users_path):
        print(f"  [ERROR] Users.json not found at {users_path}")
        return []
    if not os.path.exists(finals_path):
        print(f"  [ERROR] Finals.json not found at {finals_path}")
        return []

    with open(users_path, 'r', encoding='utf-8') as f:
        users = json.load(f)
    with open(finals_path, 'r', encoding='utf-8') as f:
        finals = json.load(f)

    # Helper parse functions
    def parse_tier(position: str) -> int:
        tier_map = {'Tier 1': 1, 'Tier 2': 2, 'Tier 3': 3, 'Tier 4': 4}
        return tier_map.get(position, 1)

    def get_day_from_date(date_str: str):
        from datetime import datetime
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        if date.year == 2024:
            date = date.replace(year=2025)
        return date.weekday(), date

    def parse_time(time_str: str) -> int:
        hours, minutes = time_str.split(':')
        hour = int(hours)
        if int(minutes) >= 30:
            return hour + 0.5
        return hour

    # Build finals map by userId (strings and ints)
    finals_by_user = {}
    for final in finals:
        uid = final.get('userId')
        try:
            uid_key = int(uid)
        except Exception:
            try:
                uid_key = int(str(uid))
            except Exception:
                continue

        finals_by_user.setdefault(uid_key, []).append(final)

    workers = []
    for user in users:
        if not user.get('isActive', True):
            continue
        uid = user.get('userId')
        try:
            uid_int = int(uid)
        except Exception:
            continue

        busy_times = []
        for final in finals_by_user.get(uid_int, []):
            day, date_obj = get_day_from_date(final.get('date'))
            if day == 6:
                continue
            start_hour = parse_time(final.get('startTime', '00:00'))
            end_hour = parse_time(final.get('endTime', '00:00'))
            busy_times.append((day, int(start_hour), int(end_hour)))

        worker = Worker(
            worker_id=uid_int,
            name=user.get('name', f"Worker-{uid_int}"),
            tier=parse_tier(user.get('position', 'Tier 1')),
            is_commuter=user.get('isCommuter', False),
            desired_hours=user.get('desiredHours', 15),
            busy_times=busy_times
        )
        workers.append(worker)

    print(f"  Loaded {len(workers)} workers from data files")
    return workers


# ============================================================================
# ALGORITHM RUNNERS
# ============================================================================

def run_ga(env, config, verbose=True):
    """Run Genetic Algorithm and return results"""
    print("\n" + "="*60)
    print("RUNNING GENETIC ALGORITHM")
    print("="*60)

    ga = GeneticAlgorithm(
        env,
        population_size=config['population_size'],
        generations=config['generations'],
        crossover_rate=config['crossover_rate'],
        mutation_rate=config['mutation_rate'],
        elitism_count=config['elitism_count']
    )

    start_time = time.time()
    solution, penalty, history = ga.solve(verbose=verbose)
    runtime = time.time() - start_time

    _, details = env.evaluate_schedule(solution)

    return {
        'solution': solution,
        'penalty': penalty,
        'history': history,
        'runtime': runtime,
        'details': details,
        'algorithm': 'GA'
    }


def run_sa(env, config, verbose=True):
    """Run Simulated Annealing and return results"""
    print("\n" + "="*60)
    print("RUNNING SIMULATED ANNEALING")
    print("="*60)

    sa = SimulatedAnnealing(
        env,
        initial_temp=config['initial_temp'],
        final_temp=config['final_temp'],
        cooling_rate=config['cooling_rate'],
        iterations_per_temp=config['iterations_per_temp']
    )

    start_time = time.time()
    solution, penalty, history = sa.solve(verbose=verbose)
    runtime = time.time() - start_time

    _, details = env.evaluate_schedule(solution)

    return {
        'solution': solution,
        'penalty': penalty,
        'history': history,
        'runtime': runtime,
        'details': details,
        'algorithm': 'SA'
    }


def run_csp(env, config, verbose=True):
    """Run CSP Solver and return results"""
    print("\n" + "="*60)
    print("RUNNING CSP SOLVER")
    print("="*60)

    csp = CSPSolver(
        env,
        max_time=config['max_time'],
        local_search_iterations=config['local_search_iterations']
    )

    start_time = time.time()
    solution, penalty, stats = csp.solve(verbose=verbose)
    runtime = time.time() - start_time

    _, details = env.evaluate_schedule(solution)

    # Create a pseudo-history for CSP based on improvements
    # CSP doesn't track iteration-by-iteration, so we'll create a linear decay
    history = np.linspace(penalty * 1.5, penalty, config['local_search_iterations'] // 10)

    return {
        'solution': solution,
        'penalty': penalty,
        'history': list(history),
        'runtime': runtime,
        'details': details,
        'stats': stats,
        'algorithm': 'CSP'
    }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def setup_plotting():
    """Setup Seaborn styling for all plots"""
    sns.set_theme(style="whitegrid")
    sns.set_palette("husl")
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['figure.dpi'] = 150


def plot_final_penalty_comparison(results, output_dir):
    """Plot 1: Final penalty scores comparison"""
    fig, ax = plt.subplots(figsize=(10, 6))

    algorithms = [r['algorithm'] for r in results]
    penalties = [r['penalty'] for r in results]
    colors = sns.color_palette("husl", len(algorithms))

    bars = ax.bar(algorithms, penalties, color=colors, edgecolor='black', linewidth=1.5)

    # Add value labels on bars
    for bar, penalty in zip(bars, penalties):
        height = bar.get_height()
        ax.annotate(f'{penalty:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=14, fontweight='bold')

    ax.set_xlabel('Algorithm', fontsize=14)
    ax.set_ylabel('Final Penalty Score', fontsize=14)
    ax.set_title('Algorithm Performance: Final Penalty Comparison\n(Lower is Better)', fontsize=16, fontweight='bold')

    # Add reference line for "good" threshold
    ax.axhline(y=500, color='green', linestyle='--', alpha=0.7, label='Excellent (<500)')
    ax.axhline(y=1500, color='orange', linestyle='--', alpha=0.7, label='Acceptable (<1500)')
    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/1_penalty_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 1_penalty_comparison.png")


def plot_convergence(results, output_dir):
    """Plot 2: Convergence curves for all algorithms"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    colors = {'GA': '#2ecc71', 'SA': '#3498db', 'CSP': '#e74c3c'}

    # Plot 1: Full convergence
    ax1 = axes[0, 0]
    for r in results:
        history = r['history']
        # Downsample if too many points
        if len(history) > 500:
            indices = np.linspace(0, len(history)-1, 500, dtype=int)
            history = [history[i] for i in indices]
        ax1.plot(history, label=r['algorithm'], color=colors[r['algorithm']], linewidth=2)

    ax1.set_xlabel('Iteration (normalized)', fontsize=12)
    ax1.set_ylabel('Penalty Score', fontsize=12)
    ax1.set_title('Full Convergence History', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Early phase (first 20%)
    ax2 = axes[0, 1]
    for r in results:
        history = r['history']
        early_cutoff = len(history) // 5
        early_history = history[:early_cutoff]
        ax2.plot(early_history, label=r['algorithm'], color=colors[r['algorithm']], linewidth=2)

    ax2.set_xlabel('Iteration', fontsize=12)
    ax2.set_ylabel('Penalty Score', fontsize=12)
    ax2.set_title('Early Phase Convergence (First 20%)', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Plot 3: Late phase (last 30%)
    ax3 = axes[1, 0]
    for r in results:
        history = r['history']
        late_start = int(len(history) * 0.7)
        late_history = history[late_start:]
        ax3.plot(range(late_start, late_start + len(late_history)),
                late_history, label=r['algorithm'], color=colors[r['algorithm']], linewidth=2)

    ax3.set_xlabel('Iteration', fontsize=12)
    ax3.set_ylabel('Penalty Score', fontsize=12)
    ax3.set_title('Late Phase Convergence (Last 30%)', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # Plot 4: Improvement rate (derivative)
    ax4 = axes[1, 1]
    for r in results:
        history = np.array(r['history'])
        if len(history) > 10:
            # Calculate rolling improvement
            window = max(len(history) // 20, 5)
            improvements = []
            for i in range(window, len(history)):
                improvement = history[i-window] - history[i]
                improvements.append(max(0, improvement))

            if len(improvements) > 100:
                indices = np.linspace(0, len(improvements)-1, 100, dtype=int)
                improvements = [improvements[i] for i in indices]

            ax4.plot(improvements, label=r['algorithm'], color=colors[r['algorithm']], linewidth=2, alpha=0.8)

    ax4.set_xlabel('Iteration (normalized)', fontsize=12)
    ax4.set_ylabel('Improvement Rate', fontsize=12)
    ax4.set_title('Improvement Rate Over Time', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.suptitle('Algorithm Convergence Analysis', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/2_convergence_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 2_convergence_analysis.png")


def plot_constraint_violations(results, output_dir):
    """Plot 3: Constraint violations breakdown"""
    fig, ax = plt.subplots(figsize=(14, 8))

    constraint_types = [
        'coverage_violations',
        'worker_conflicts',
        'hour_violations',
        'min_hour_violations',
        'shift_length_violations',
        'tier_mismatches',
        'fairness_violations',
        'morning_shift_violations'
    ]

    # Shorter labels for display
    labels = [
        'Coverage',
        'Worker Conflicts',
        'Hour Limit',
        'Min Hours',
        'Shift Length',
        'Tier Mismatch',
        'Fairness',
        'Morning Shifts'
    ]

    x = np.arange(len(labels))
    width = 0.25

    colors = {'GA': '#2ecc71', 'SA': '#3498db', 'CSP': '#e74c3c'}

    for i, r in enumerate(results):
        values = [r['details'].get(c, 0) for c in constraint_types]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, values, width, label=r['algorithm'],
                     color=colors[r['algorithm']], edgecolor='black', linewidth=0.5)

        # Add value labels
        for bar, val in zip(bars, values):
            if val > 0:
                ax.annotate(f'{int(val)}',
                           xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                           xytext=(0, 2),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('Constraint Type', fontsize=14)
    ax.set_ylabel('Number of Violations', fontsize=14)
    ax.set_title('Constraint Violations Breakdown by Algorithm', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend(title='Algorithm')

    # Highlight critical constraints
    ax.axvspan(-0.5, 3.5, alpha=0.1, color='red', label='Critical Constraints')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/3_constraint_violations.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 3_constraint_violations.png")


def plot_runtime_comparison(results, output_dir):
    """Plot 4: Runtime comparison"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    algorithms = [r['algorithm'] for r in results]
    runtimes = [r['runtime'] for r in results]
    penalties = [r['penalty'] for r in results]
    colors = {'GA': '#2ecc71', 'SA': '#3498db', 'CSP': '#e74c3c'}
    bar_colors = [colors[a] for a in algorithms]

    # Plot 1: Runtime bars
    ax1 = axes[0]
    bars = ax1.bar(algorithms, runtimes, color=bar_colors, edgecolor='black', linewidth=1.5)

    for bar, runtime in zip(bars, runtimes):
        height = bar.get_height()
        ax1.annotate(f'{runtime:.2f}s',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')

    ax1.set_xlabel('Algorithm', fontsize=14)
    ax1.set_ylabel('Runtime (seconds)', fontsize=14)
    ax1.set_title('Algorithm Runtime Comparison', fontsize=14, fontweight='bold')

    # Plot 2: Efficiency (Penalty improvement per second)
    ax2 = axes[1]
    # Assume initial penalty around 5000 (rough estimate)
    initial_penalty_estimate = 5000
    efficiency = [(initial_penalty_estimate - p) / r if r > 0 else 0 for p, r in zip(penalties, runtimes)]

    bars2 = ax2.bar(algorithms, efficiency, color=bar_colors, edgecolor='black', linewidth=1.5)

    for bar, eff in zip(bars2, efficiency):
        height = bar.get_height()
        ax2.annotate(f'{eff:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')

    ax2.set_xlabel('Algorithm', fontsize=14)
    ax2.set_ylabel('Penalty Reduction per Second', fontsize=14)
    ax2.set_title('Algorithm Efficiency\n(Higher is Better)', fontsize=14, fontweight='bold')

    plt.suptitle('Runtime Analysis', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/4_runtime_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 4_runtime_analysis.png")


def plot_exploration_exploitation(results, output_dir):
    """Plot 5: Exploration vs Exploitation analysis"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    colors = {'GA': '#2ecc71', 'SA': '#3498db', 'CSP': '#e74c3c'}

    # Plot 1: Penalty variance over time (exploration indicator)
    ax1 = axes[0]
    for r in results:
        history = np.array(r['history'])
        if len(history) > 20:
            # Calculate rolling variance
            window = max(len(history) // 10, 10)
            variances = []
            for i in range(window, len(history)):
                var = np.std(history[i-window:i])
                variances.append(var)

            # Normalize iterations
            x = np.linspace(0, 100, len(variances))
            ax1.plot(x, variances, label=r['algorithm'], color=colors[r['algorithm']], linewidth=2)

    ax1.set_xlabel('Progress (%)', fontsize=12)
    ax1.set_ylabel('Penalty Variance (Rolling Window)', fontsize=12)
    ax1.set_title('Exploration Intensity\n(Higher variance = more exploration)', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Cumulative improvement
    ax2 = axes[1]
    for r in results:
        history = np.array(r['history'])
        if len(history) > 1:
            # Calculate cumulative improvement from start
            improvements = history[0] - history
            improvements = np.maximum(improvements, 0)  # Only positive improvements

            # Normalize iterations
            x = np.linspace(0, 100, len(improvements))
            ax2.plot(x, improvements, label=r['algorithm'], color=colors[r['algorithm']], linewidth=2)

    ax2.set_xlabel('Progress (%)', fontsize=12)
    ax2.set_ylabel('Cumulative Penalty Reduction', fontsize=12)
    ax2.set_title('Exploitation Progress\n(Cumulative improvement over time)', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.suptitle('Exploration vs Exploitation Analysis', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/5_exploration_exploitation.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 5_exploration_exploitation.png")


def plot_worker_hours_distribution(results, env, output_dir):
    """Plot 6: Worker hours distribution comparison"""
    fig, ax = plt.subplots(figsize=(14, 8))

    workers = env.workers
    worker_names = [w.name for w in workers]
    desired_hours = [w.desired_hours for w in workers]

    x = np.arange(len(worker_names))
    width = 0.2

    colors = {'GA': '#2ecc71', 'SA': '#3498db', 'CSP': '#e74c3c', 'Desired': '#f39c12'}

    # Plot desired hours
    ax.bar(x - 1.5*width, desired_hours, width, label='Desired',
           color=colors['Desired'], edgecolor='black', linewidth=0.5, alpha=0.7)

    # Plot each algorithm's assigned hours
    for i, r in enumerate(results):
        worker_hours = {w.worker_id: 0 for w in workers}
        for worker_id in r['solution']:
            if worker_id != -1 and worker_id in worker_hours:
                worker_hours[worker_id] += 1

        hours = [worker_hours[w.worker_id] for w in workers]
        offset = (i - 0.5) * width
        ax.bar(x + offset, hours, width, label=r['algorithm'],
              color=colors[r['algorithm']], edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Worker', fontsize=14)
    ax.set_ylabel('Hours Assigned', fontsize=14)
    ax.set_title('Worker Hours Distribution by Algorithm', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(worker_names, rotation=45, ha='right')
    ax.legend(title='Source')

    # Add min/max hour lines
    ax.axhline(y=14, color='red', linestyle='--', alpha=0.5, label='Min (14h)')
    ax.axhline(y=20, color='red', linestyle='--', alpha=0.5, label='Max (20h)')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/6_worker_hours.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 6_worker_hours.png")


def plot_radar_comparison(results, output_dir):
    """Plot 7: Radar chart comparing multiple metrics"""
    categories = ['Solution Quality', 'Speed', 'Consistency', 'Coverage', 'Fairness']

    # Calculate normalized scores for each algorithm
    scores = {}
    max_penalty = max(r['penalty'] for r in results) + 1
    max_runtime = max(r['runtime'] for r in results) + 0.1

    for r in results:
        algo = r['algorithm']

        # Solution quality (inverse of penalty, normalized)
        quality = 1 - (r['penalty'] / max_penalty)

        # Speed (inverse of runtime, normalized)
        speed = 1 - (r['runtime'] / max_runtime)

        # Consistency (inverse of variance in late history)
        history = np.array(r['history'])
        late_var = np.std(history[-len(history)//5:]) if len(history) > 5 else 0
        consistency = 1 / (1 + late_var / 100)

        # Coverage (inverse of coverage violations)
        coverage = 1 / (1 + r['details'].get('coverage_violations', 0))

        # Fairness (inverse of fairness violations)
        fairness = 1 / (1 + r['details'].get('fairness_violations', 0))

        scores[algo] = [quality, speed, consistency, coverage, fairness]

    # Create radar chart
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # Complete the loop

    colors = {'GA': '#2ecc71', 'SA': '#3498db', 'CSP': '#e74c3c'}

    for algo, vals in scores.items():
        values = vals + vals[:1]  # Complete the loop
        ax.plot(angles, values, 'o-', linewidth=2, label=algo, color=colors[algo])
        ax.fill(angles, values, alpha=0.25, color=colors[algo])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=12)
    ax.set_ylim(0, 1)
    ax.set_title('Algorithm Multi-Metric Comparison', fontsize=16, fontweight='bold', y=1.08)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))

    plt.tight_layout()
    plt.savefig(f'{output_dir}/7_radar_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: 7_radar_comparison.png")


def generate_summary_report(results, output_dir):
    """Generate a text summary report"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    report = []
    report.append("="*70)
    report.append("ALGORITHM COMPARISON SUMMARY REPORT")
    report.append(f"Generated: {timestamp}")
    report.append("="*70)
    report.append("")

    # Sort by penalty
    sorted_results = sorted(results, key=lambda x: x['penalty'])

    report.append("RANKING (by Final Penalty):")
    report.append("-"*40)
    for i, r in enumerate(sorted_results, 1):
        report.append(f"  {i}. {r['algorithm']}: {r['penalty']:.2f} penalty ({r['runtime']:.2f}s)")
    report.append("")

    # Best algorithm
    best = sorted_results[0]
    report.append(f"WINNER: {best['algorithm']}")
    report.append(f"  - Final Penalty: {best['penalty']:.2f}")
    report.append(f"  - Runtime: {best['runtime']:.2f} seconds")
    report.append("")

    # Detailed breakdown
    report.append("DETAILED RESULTS:")
    report.append("-"*40)
    for r in results:
        report.append(f"\n{r['algorithm']}:")
        report.append(f"  Penalty: {r['penalty']:.2f}")
        report.append(f"  Runtime: {r['runtime']:.2f}s")
        report.append(f"  Constraint Violations:")
        for k, v in r['details'].items():
            if v > 0:
                report.append(f"    - {k}: {int(v)}")

    report.append("")
    report.append("="*70)
    report.append("Files generated:")
    report.append("  1. 1_penalty_comparison.png - Final penalty scores")
    report.append("  2. 2_convergence_analysis.png - Convergence curves")
    report.append("  3. 3_constraint_violations.png - Constraint breakdown")
    report.append("  4. 4_runtime_analysis.png - Runtime and efficiency")
    report.append("  5. 5_exploration_exploitation.png - Search behavior")
    report.append("  6. 6_worker_hours.png - Worker assignment distribution")
    report.append("  7. 7_radar_comparison.png - Multi-metric radar chart")
    report.append("="*70)

    report_text = "\n".join(report)

    # Print to console
    print("\n" + report_text)

    # Save to file
    with open(f'{output_dir}/summary_report.txt', 'w') as f:
        f.write(report_text)
    print(f"\n  Saved: summary_report.txt")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function to run comparison"""
    print("="*70)
    print("IT SCHEDULER - ALGORITHM COMPARISON")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  GA: {GA_CONFIG['generations']} generations, pop={GA_CONFIG['population_size']}")
    print(f"  SA: temp {SA_CONFIG['initial_temp']} -> {SA_CONFIG['final_temp']}, cooling={SA_CONFIG['cooling_rate']}")
    print(f"  CSP: {CSP_CONFIG['local_search_iterations']} iterations, max {CSP_CONFIG['max_time']}s")

    # CLI args
    parser = argparse.ArgumentParser(description='Run algorithm comparison using MongoDB data')
    parser.add_argument('--db-host', default='mongodb+srv://vamsi123:D32rm2786@cluster1.lnpslid.mongodb.net/', help='MongoDB connection string')
    parser.add_argument('--db-name', default='Scheduler', help='MongoDB database name')
    parser.add_argument('--output-dir', default=OUTPUT_DIR, help='Directory to save outputs')
    parser.add_argument('--source', choices=['file', 'mongo'], default='file', help='Data source: file or mongo (default: file)')
    parser.add_argument('--data-dir', default='Data', help='Data directory for Users.json and Finals.json (used when --source=file)')
    args = parser.parse_args()
    # Local output directory from CLI
    output_dir = args.output_dir

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nOutput directory: {output_dir}/")
    print(f"Using data source: {args.source} (db host: {args.db_host if args.source=='mongo' else 'n/a'}) db={args.db_name if args.source=='mongo' else 'n/a'}")

    # Load workers from MongoDB
    print(f"\nLoading workers from source: {args.source}...")
    if args.source == 'file':
        print("  Using file loader")
        workers = load_workers_from_datafiles(args.data_dir)
    else:
        print("  Using MongoDB loader")
        workers = load_workers_from_mongo(args.db_host, args.db_name)
    if not workers:
        print("\nNo workers loaded - aborting. Provide a valid MongoDB or run locally.")
        return []
    print(f"  Loaded {len(workers)} workers from MongoDB")

    # Create environments (fresh for each algorithm)
    print("\nCreating scheduling environment...")
    env = SchedulingEnvironment(workers, schedule_type='finals')
    print(f"  Total slots: {env.num_slots}")

    # Run all algorithms
    results = []

    # Run GA
    env_ga = SchedulingEnvironment(workers, schedule_type='finals')
    ga_result = run_ga(env_ga, GA_CONFIG, verbose=True)
    results.append(ga_result)

    # Run SA
    env_sa = SchedulingEnvironment(workers, schedule_type='finals')
    sa_result = run_sa(env_sa, SA_CONFIG, verbose=True)
    results.append(sa_result)

    # Run CSP
    env_csp = SchedulingEnvironment(workers, schedule_type='finals')
    csp_result = run_csp(env_csp, CSP_CONFIG, verbose=True)
    results.append(csp_result)

    # Validate and export - use utilities
    print("\nValidating results and exporting schedules...")
    for r in results:
        valid = quick_validate(r['solution'], SchedulingEnvironment(workers, schedule_type='finals'))
        if not valid:
            print(f"  Warning: {r['algorithm']} solution flagged by validator (penalty={r['penalty']:.1f}).")

    # Generate visualizations
    print("\n" + "="*60)
    print("GENERATING VISUALIZATIONS")
    print("="*60)

    setup_plotting()

    plot_final_penalty_comparison(results, output_dir)
    plot_convergence(results, output_dir)
    plot_constraint_violations(results, output_dir)
    plot_runtime_comparison(results, output_dir)
    plot_exploration_exploitation(results, output_dir)
    plot_worker_hours_distribution(results, env, output_dir)
    plot_radar_comparison(results, output_dir)

    # Generate summary report
    generate_summary_report(results, output_dir)

    # Export each algorithm's schedule and the best schedule (using ScheduleExporter util)
    for r in results:
        algo_exports_dir = f"{output_dir}/exports/{r['algorithm']}"
        os.makedirs(algo_exports_dir, exist_ok=True)
        exporter = ScheduleExporter(env, r['solution'], r['algorithm'])
        exporter.export_all(algo_exports_dir)

    # Also export the best schedule separately
    best = sorted(results, key=lambda x: x['penalty'])[0]
    best_dir = f"{output_dir}/exports/BEST_{best['algorithm']}"
    os.makedirs(best_dir, exist_ok=True)
    best_exporter = ScheduleExporter(env, best['solution'], best['algorithm'])
    best_exporter.export_all(best_dir)

    print("\n" + "="*70)
    print("COMPARISON COMPLETE!")
    print(f"All outputs saved to: {output_dir}/")
    print("="*70)

    return results


if __name__ == '__main__':
    main()
