"""
Algorithm Comparison Module
Runs all 3 algorithms (GA, SA, CSP) and generates comparison visualizations

Usage:
    python algorithm_comparison.py --db-host "mongodb+srv://..." --db-name "Scheduler"

Generates:
    1. Final Objective Score vs Algorithm (bar chart)
    2. Constraint Violation Count vs Algorithm (grouped bar)
    3. Runtime Performance vs Algorithm (bar chart)
    4. Fitness vs Iteration for GA & SA (line chart)
    5. Hours Distribution per Worker (grouped bar)
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
from datetime import datetime
import time
import argparse

from mongoDb_loader import MongoDBLoader
from scheduling_env import SchedulingEnvironment
from genetic_algorithm import GeneticAlgorithm
from simulated_annealing import SimulatedAnnealing
from csp_solver import CSPSolver


# ============================================================================
# HYPERPARAMETER CONFIGURATION - MODIFY THESE FOR LONGER/BETTER RUNS
# ============================================================================

# Genetic Algorithm Parameters
GA_CONFIG = {
    'population_size': 250,      # Number of individuals in population
    'generations': 5000,         # Number of generations to evolve
    'crossover_rate': 0.85,      # Probability of crossover
    'mutation_rate': 0.35,       # Probability of mutation
    'elitism_count': 15          # Best individuals to preserve
}

# Simulated Annealing Parameters
SA_CONFIG = {
    'initial_temp': 3500.0,      # Starting temperature (higher = more exploration)
    'final_temp': 0.001,         # Ending temperature (lower = finer tuning)
    'cooling_rate': 0.9985,      # Decay rate (closer to 1 = slower/longer)
    'iterations_per_temp': 300   # Iterations per temp (higher = more thorough)
}

# CSP Solver Parameters
CSP_CONFIG = {
    'max_time': 200.0,           # Max seconds to run
    'local_search_iterations': 15000  # Local search iterations
}


class AlgorithmComparison:
    """Run and compare all scheduling algorithms with visualizations"""

    def __init__(self, connection_string: str, database: str, schedule_type: str = 'finals'):
        self.connection_string = connection_string
        self.database = database
        self.schedule_type = schedule_type
        self.results = {}
        self.env = None
        self.workers = None
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    def load_data(self):
        """Load worker data from MongoDB"""
        print("=" * 80)
        print("LOADING DATA FROM MONGODB")
        print("=" * 80)

        loader = MongoDBLoader(self.connection_string, self.database)
        self.workers = loader.load_workers()
        loader.print_loaded_data(self.workers)
        loader.close()

        if not self.workers:
            raise ValueError("No active workers found in database!")

        print(f"\n✓ Loaded {len(self.workers)} workers")
        return self.workers

    def run_ga(self):
        """Run Genetic Algorithm with configured parameters"""
        print("\n" + "=" * 80)
        print("RUNNING GENETIC ALGORITHM (GA)")
        print("=" * 80)
        print(f"Config: {GA_CONFIG}")

        # Create fresh environment
        env = SchedulingEnvironment(self.workers, schedule_type=self.schedule_type)

        solver = GeneticAlgorithm(
            env,
            population_size=GA_CONFIG['population_size'],
            generations=GA_CONFIG['generations'],
            crossover_rate=GA_CONFIG['crossover_rate'],
            mutation_rate=GA_CONFIG['mutation_rate'],
            elitism_count=GA_CONFIG['elitism_count']
        )

        start_time = time.time()
        solution, penalty, history = solver.solve(verbose=True)
        runtime = time.time() - start_time

        _, details = env.evaluate_schedule(solution)

        # Calculate worker hours
        worker_hours = self._calculate_worker_hours(solution, env)

        self.results['GA'] = {
            'solution': solution,
            'penalty': penalty,
            'runtime': runtime,
            'history': history,
            'details': details,
            'worker_hours': worker_hours,
            'env': env
        }

        print(f"\n✓ GA Complete: Penalty={penalty:.2f}, Runtime={runtime:.1f}s")
        return solution, penalty

    def run_sa(self):
        """Run Simulated Annealing with configured parameters"""
        print("\n" + "=" * 80)
        print("RUNNING SIMULATED ANNEALING (SA)")
        print("=" * 80)
        print(f"Config: {SA_CONFIG}")

        # Create fresh environment
        env = SchedulingEnvironment(self.workers, schedule_type=self.schedule_type)

        solver = SimulatedAnnealing(
            env,
            initial_temp=SA_CONFIG['initial_temp'],
            final_temp=SA_CONFIG['final_temp'],
            cooling_rate=SA_CONFIG['cooling_rate'],
            iterations_per_temp=SA_CONFIG['iterations_per_temp']
        )

        start_time = time.time()
        solution, penalty, history = solver.solve(verbose=True)
        runtime = time.time() - start_time

        _, details = env.evaluate_schedule(solution)

        # Calculate worker hours
        worker_hours = self._calculate_worker_hours(solution, env)

        self.results['SA'] = {
            'solution': solution,
            'penalty': penalty,
            'runtime': runtime,
            'history': history,
            'details': details,
            'worker_hours': worker_hours,
            'env': env
        }

        print(f"\n✓ SA Complete: Penalty={penalty:.2f}, Runtime={runtime:.1f}s")
        return solution, penalty

    def run_csp(self):
        """Run CSP Solver with configured parameters"""
        print("\n" + "=" * 80)
        print("RUNNING CSP SOLVER")
        print("=" * 80)
        print(f"Config: {CSP_CONFIG}")

        # Create fresh environment
        env = SchedulingEnvironment(self.workers, schedule_type=self.schedule_type)

        solver = CSPSolver(
            env,
            max_time=CSP_CONFIG['max_time'],
            local_search_iterations=CSP_CONFIG['local_search_iterations']
        )

        start_time = time.time()
        solution, penalty, stats = solver.solve(verbose=True)
        runtime = time.time() - start_time

        _, details = env.evaluate_schedule(solution)

        # Calculate worker hours
        worker_hours = self._calculate_worker_hours(solution, env)

        self.results['CSP'] = {
            'solution': solution,
            'penalty': penalty,
            'runtime': runtime,
            'history': [],  # CSP doesn't track iteration history
            'details': details,
            'worker_hours': worker_hours,
            'env': env,
            'stats': stats
        }

        print(f"\n✓ CSP Complete: Penalty={penalty:.2f}, Runtime={runtime:.1f}s")
        return solution, penalty

    def _calculate_worker_hours(self, solution, env):
        """Calculate hours assigned to each worker"""
        worker_hours = {}
        for worker in env.workers:
            worker_hours[worker.name] = {
                'assigned': 0,
                'desired': worker.desired_hours,
                'id': worker.worker_id
            }

        for worker_id in solution:
            if worker_id != -1:
                worker = next((w for w in env.workers if w.worker_id == worker_id), None)
                if worker:
                    worker_hours[worker.name]['assigned'] += 1

        return worker_hours

    def run_all(self):
        """Run all three algorithms"""
        self.load_data()

        print("\n" + "=" * 80)
        print("STARTING FULL ALGORITHM COMPARISON")
        print("=" * 80)
        print(f"Schedule Type: {self.schedule_type}")
        print(f"This may take several minutes depending on hyperparameters...")

        self.run_ga()
        self.run_sa()
        self.run_csp()

        return self.results

    # ========================================================================
    # VISUALIZATION METHODS
    # ========================================================================

    def plot_1_final_objective_score(self, output_dir='outputs'):
        """Plot 1: Final Objective Score vs Algorithm"""
        os.makedirs(output_dir, exist_ok=True)

        algorithms = list(self.results.keys())
        penalties = [self.results[algo]['penalty'] for algo in algorithms]

        # Colors: green for best, others blue/red
        best_idx = penalties.index(min(penalties))
        colors = ['#e74c3c' if i != best_idx else '#27ae60' for i in range(len(algorithms))]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(algorithms, penalties, color=colors, edgecolor='black', linewidth=2)

        # Add value labels
        for bar, penalty in zip(bars, penalties):
            height = bar.get_height()
            ax.annotate(f'{penalty:.1f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 5),
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=14, fontweight='bold')

        ax.set_xlabel('Algorithm', fontsize=14, fontweight='bold')
        ax.set_ylabel('Final Penalty Score (Lower = Better)', fontsize=14, fontweight='bold')
        ax.set_title('1. Final Objective Score vs Algorithm', fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Mark best
        ax.annotate('★ BEST', xy=(best_idx, penalties[best_idx]),
                   xytext=(best_idx, penalties[best_idx] * 0.7),
                   fontsize=12, ha='center', color='green', fontweight='bold')

        plt.tight_layout()
        filename = f"{output_dir}/1_objective_score_{self.timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def plot_2_constraint_violations(self, output_dir='outputs'):
        """Plot 2: Constraint Violation Count vs Algorithm"""
        os.makedirs(output_dir, exist_ok=True)

        algorithms = list(self.results.keys())

        # Constraint categories
        constraints = [
            ('coverage_violations', 'Coverage'),
            ('worker_conflicts', 'Conflicts'),
            ('hour_violations', 'Hour Limit'),
            ('min_hour_violations', 'Min Hours'),
            ('shift_length_violations', 'Shift Length'),
            ('tier_mismatches', 'Tier Match'),
            ('fairness_violations', 'Fairness'),
            ('morning_shift_violations', 'Morning')
        ]

        x = np.arange(len(constraints))
        width = 0.25

        fig, ax = plt.subplots(figsize=(14, 7))

        colors = {'GA': '#2ecc71', 'SA': '#3498db', 'CSP': '#e74c3c'}

        for i, algo in enumerate(algorithms):
            values = [self.results[algo]['details'].get(c[0], 0) for c in constraints]
            bars = ax.bar(x + i * width, values, width, label=algo,
                         color=colors.get(algo, 'gray'), edgecolor='black')

            # Add value labels for non-zero values
            for bar, val in zip(bars, values):
                if val > 0:
                    ax.annotate(f'{int(val)}',
                               xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                               xytext=(0, 2),
                               textcoords="offset points",
                               ha='center', va='bottom', fontsize=9, fontweight='bold')

        ax.set_xlabel('Constraint Type', fontsize=14, fontweight='bold')
        ax.set_ylabel('Number of Violations', fontsize=14, fontweight='bold')
        ax.set_title('2. Constraint Violations by Algorithm', fontsize=16, fontweight='bold')
        ax.set_xticks(x + width)
        ax.set_xticklabels([c[1] for c in constraints], rotation=45, ha='right')
        ax.legend(fontsize=12, loc='upper right')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        filename = f"{output_dir}/2_constraint_violations_{self.timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def plot_3_runtime_performance(self, output_dir='outputs'):
        """Plot 3: Runtime Performance vs Algorithm"""
        os.makedirs(output_dir, exist_ok=True)

        algorithms = list(self.results.keys())
        runtimes = [self.results[algo]['runtime'] for algo in algorithms]

        # Colors based on speed
        fastest_idx = runtimes.index(min(runtimes))
        colors = ['#95a5a6' if i != fastest_idx else '#27ae60' for i in range(len(algorithms))]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(algorithms, runtimes, color=colors, edgecolor='black', linewidth=2)

        # Add value labels
        for bar, runtime in zip(bars, runtimes):
            height = bar.get_height()
            if runtime >= 60:
                label = f'{runtime/60:.1f} min'
            else:
                label = f'{runtime:.1f}s'
            ax.annotate(label,
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 5),
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=14, fontweight='bold')

        ax.set_xlabel('Algorithm', fontsize=14, fontweight='bold')
        ax.set_ylabel('Runtime (seconds)', fontsize=14, fontweight='bold')
        ax.set_title('3. Runtime Performance vs Algorithm', fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        plt.tight_layout()
        filename = f"{output_dir}/3_runtime_performance_{self.timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def plot_4_fitness_vs_iteration(self, output_dir='outputs'):
        """Plot 4: Fitness vs Iteration (GA & SA)"""
        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot GA history
        if 'GA' in self.results and self.results['GA']['history']:
            ga_history = self.results['GA']['history']
            generations = range(1, len(ga_history) + 1)
            ax.plot(generations, ga_history, 'g-', linewidth=2,
                   label=f'GA (Final: {ga_history[-1]:.1f})', alpha=0.8)

        # Plot SA history (downsample if needed)
        if 'SA' in self.results and self.results['SA']['history']:
            sa_history = self.results['SA']['history']
            # Downsample to ~1000 points for readability
            if len(sa_history) > 1000:
                step = len(sa_history) // 1000
                sa_history_plot = sa_history[::step]
            else:
                sa_history_plot = sa_history
            iterations = range(1, len(sa_history_plot) + 1)
            ax.plot(iterations, sa_history_plot, 'b-', linewidth=2,
                   label=f'SA (Final: {sa_history[-1]:.1f})', alpha=0.8)

        ax.set_xlabel('Iteration / Generation', fontsize=14, fontweight='bold')
        ax.set_ylabel('Fitness (Penalty Score)', fontsize=14, fontweight='bold')
        ax.set_title('4. Fitness Convergence: GA vs SA', fontsize=16, fontweight='bold')
        ax.legend(fontsize=12, loc='upper right')
        ax.grid(alpha=0.3, linestyle='--')

        # Add final value annotations
        if 'GA' in self.results:
            ax.axhline(y=self.results['GA']['penalty'], color='green',
                      linestyle='--', alpha=0.5, linewidth=1)
        if 'SA' in self.results:
            ax.axhline(y=self.results['SA']['penalty'], color='blue',
                      linestyle='--', alpha=0.5, linewidth=1)

        plt.tight_layout()
        filename = f"{output_dir}/4_fitness_convergence_{self.timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def plot_5_hours_distribution(self, output_dir='outputs'):
        """Plot 5: Hours Distribution per Worker"""
        os.makedirs(output_dir, exist_ok=True)

        # Get worker names (use first algorithm's data)
        first_algo = list(self.results.keys())[0]
        worker_names = list(self.results[first_algo]['worker_hours'].keys())

        # Sort by name for consistency
        worker_names = sorted(worker_names)

        x = np.arange(len(worker_names))
        width = 0.2

        fig, ax = plt.subplots(figsize=(16, 8))

        colors = {'GA': '#2ecc71', 'SA': '#3498db', 'CSP': '#e74c3c', 'Desired': '#f39c12'}

        # Plot desired hours first (as reference)
        desired_hours = [self.results[first_algo]['worker_hours'][name]['desired']
                        for name in worker_names]
        ax.bar(x - 1.5*width, desired_hours, width, label='Desired',
              color=colors['Desired'], edgecolor='black', alpha=0.7)

        # Plot each algorithm's assigned hours
        for i, algo in enumerate(self.results.keys()):
            assigned = [self.results[algo]['worker_hours'][name]['assigned']
                       for name in worker_names]
            ax.bar(x + (i - 0.5) * width, assigned, width, label=f'{algo} Assigned',
                  color=colors.get(algo, 'gray'), edgecolor='black')

        ax.set_xlabel('Worker', fontsize=14, fontweight='bold')
        ax.set_ylabel('Hours', fontsize=14, fontweight='bold')
        ax.set_title('5. Hours Distribution per Worker', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(worker_names, rotation=45, ha='right', fontsize=10)
        ax.legend(fontsize=10, loc='upper right')
        ax.grid(axis='y', alpha=0.3, linestyle='--')

        # Add reference lines
        ax.axhline(y=14, color='red', linestyle=':', alpha=0.5, label='Min 14h')
        ax.axhline(y=20, color='red', linestyle=':', alpha=0.5, label='Max 20h')

        plt.tight_layout()
        filename = f"{output_dir}/5_hours_distribution_{self.timestamp}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def generate_all_plots(self, output_dir='outputs'):
        """Generate all 5 comparison plots"""
        print("\n" + "=" * 80)
        print("GENERATING COMPARISON VISUALIZATIONS")
        print("=" * 80)

        plots = []
        plots.append(self.plot_1_final_objective_score(output_dir))
        plots.append(self.plot_2_constraint_violations(output_dir))
        plots.append(self.plot_3_runtime_performance(output_dir))
        plots.append(self.plot_4_fitness_vs_iteration(output_dir))
        plots.append(self.plot_5_hours_distribution(output_dir))

        return plots

    def generate_summary_report(self, output_dir='outputs'):
        """Generate comprehensive text summary report"""
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{output_dir}/comparison_report_{self.timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("ALGORITHM COMPARISON REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            # Configuration
            f.write("HYPERPARAMETERS USED\n")
            f.write("-" * 40 + "\n")
            f.write(f"GA: {GA_CONFIG}\n")
            f.write(f"SA: {SA_CONFIG}\n")
            f.write(f"CSP: {CSP_CONFIG}\n\n")

            # Results Summary
            f.write("RESULTS SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"{'Algorithm':<10} {'Penalty':<12} {'Runtime':<15} {'Status'}\n")
            f.write("-" * 50 + "\n")

            best_algo = min(self.results.keys(), key=lambda a: self.results[a]['penalty'])

            for algo in ['GA', 'SA', 'CSP']:
                if algo in self.results:
                    r = self.results[algo]
                    runtime_str = f"{r['runtime']:.1f}s" if r['runtime'] < 60 else f"{r['runtime']/60:.1f}min"
                    status = "★ BEST" if algo == best_algo else ""
                    f.write(f"{algo:<10} {r['penalty']:<12.2f} {runtime_str:<15} {status}\n")

            f.write("\n")

            # Constraint Details
            f.write("CONSTRAINT VIOLATIONS\n")
            f.write("-" * 40 + "\n")

            constraints = [
                'coverage_violations', 'worker_conflicts', 'hour_violations',
                'min_hour_violations', 'shift_length_violations', 'tier_mismatches',
                'fairness_violations', 'morning_shift_violations'
            ]

            header = f"{'Constraint':<25}"
            for algo in ['GA', 'SA', 'CSP']:
                header += f"{algo:<10}"
            f.write(header + "\n")
            f.write("-" * 55 + "\n")

            for constraint in constraints:
                row = f"{constraint:<25}"
                for algo in ['GA', 'SA', 'CSP']:
                    if algo in self.results:
                        val = self.results[algo]['details'].get(constraint, 0)
                        row += f"{int(val):<10}"
                f.write(row + "\n")

            f.write("\n")

            # Worker Hours
            f.write("WORKER HOURS SUMMARY\n")
            f.write("-" * 40 + "\n")

            first_algo = list(self.results.keys())[0]
            worker_names = sorted(self.results[first_algo]['worker_hours'].keys())

            f.write(f"{'Worker':<20} {'Desired':<10}")
            for algo in ['GA', 'SA', 'CSP']:
                f.write(f"{algo:<10}")
            f.write("\n")
            f.write("-" * 60 + "\n")

            for name in worker_names:
                desired = self.results[first_algo]['worker_hours'][name]['desired']
                row = f"{name:<20} {desired:<10.1f}"
                for algo in ['GA', 'SA', 'CSP']:
                    if algo in self.results:
                        assigned = self.results[algo]['worker_hours'][name]['assigned']
                        row += f"{assigned:<10}"
                f.write(row + "\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write(f"WINNER: {best_algo} with penalty {self.results[best_algo]['penalty']:.2f}\n")
            f.write("=" * 80 + "\n")

        print(f"  ✓ Saved: {filename}")
        return filename

    def export_best_schedule(self, output_dir='outputs'):
        """Export the best schedule found"""
        os.makedirs(output_dir, exist_ok=True)

        best_algo = min(self.results.keys(), key=lambda a: self.results[a]['penalty'])
        result = self.results[best_algo]
        env = result['env']

        filename = f"{output_dir}/BEST_{best_algo}_schedule_{self.timestamp}.json"

        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

        # Build schedule
        schedule_by_day = {day: [] for day in day_names}

        for i, worker_id in enumerate(result['solution']):
            if worker_id == -1:
                continue
            slot = env.shift_slots[i]
            worker = next((w for w in env.workers if w.worker_id == worker_id), None)
            if worker and slot.day < 6:
                schedule_by_day[day_names[slot.day]].append({
                    'time': f"{slot.hour:02d}:00-{slot.hour+1:02d}:00",
                    'type': slot.shift_type,
                    'worker': worker.name,
                    'tier': worker.tier
                })

        for day in schedule_by_day:
            schedule_by_day[day].sort(key=lambda x: x['time'])

        output = {
            'metadata': {
                'algorithm': best_algo,
                'penalty': result['penalty'],
                'runtime': result['runtime'],
                'timestamp': datetime.now().isoformat()
            },
            'constraints': {k: int(v) for k, v in result['details'].items()},
            'schedule': schedule_by_day,
            'worker_hours': {name: data['assigned'] for name, data in result['worker_hours'].items()}
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

        print(f"  ✓ Saved: {filename}")
        return filename


def run_full_comparison(connection_string: str, database: str, output_dir: str = 'outputs'):
    """Main function to run complete comparison"""

    print("\n" + "=" * 80)
    print("ALGORITHM COMPARISON - FULL RUN")
    print("=" * 80)
    print(f"\nHyperparameters:")
    print(f"  GA: generations={GA_CONFIG['generations']}, population={GA_CONFIG['population_size']}")
    print(f"  SA: cooling_rate={SA_CONFIG['cooling_rate']}, iterations_per_temp={SA_CONFIG['iterations_per_temp']}")
    print(f"  CSP: max_time={CSP_CONFIG['max_time']}s, local_search={CSP_CONFIG['local_search_iterations']}")
    print("\nThis may take 10-30 minutes depending on settings...")

    comparison = AlgorithmComparison(connection_string, database)

    # Run all algorithms
    comparison.run_all()

    # Generate all outputs
    print("\n" + "=" * 80)
    print("GENERATING OUTPUTS")
    print("=" * 80)

    comparison.generate_all_plots(output_dir)
    comparison.generate_summary_report(output_dir)
    comparison.export_best_schedule(output_dir)

    # Print final summary
    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)

    print("\n📊 Results Summary:")
    print("-" * 40)
    for algo in ['GA', 'SA', 'CSP']:
        if algo in comparison.results:
            r = comparison.results[algo]
            runtime = f"{r['runtime']:.1f}s" if r['runtime'] < 60 else f"{r['runtime']/60:.1f}min"
            print(f"  {algo}: Penalty={r['penalty']:.2f}, Runtime={runtime}")

    best = min(comparison.results.keys(), key=lambda a: comparison.results[a]['penalty'])
    print(f"\n★ WINNER: {best} with penalty {comparison.results[best]['penalty']:.2f}")

    print(f"\n📁 All outputs saved to: {output_dir}/")

    return comparison


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compare GA, SA, and CSP scheduling algorithms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python algorithm_comparison.py --db-host "mongodb+srv://user:pass@cluster.mongodb.net/" --db-name "Scheduler"

Outputs:
  1_objective_score_*.png     - Final penalty comparison
  2_constraint_violations_*.png - Violations breakdown
  3_runtime_performance_*.png  - Runtime comparison
  4_fitness_convergence_*.png  - GA/SA convergence curves
  5_hours_distribution_*.png   - Worker hours comparison
  comparison_report_*.txt      - Full text report
  BEST_*_schedule_*.json       - Best schedule found
        """
    )

    parser.add_argument('--db-host', type=str, required=True,
                       help='MongoDB connection string')
    parser.add_argument('--db-name', type=str, required=True,
                       help='Database name')
    parser.add_argument('--output-dir', type=str, default='outputs',
                       help='Output directory (default: outputs)')

    args = parser.parse_args()

    run_full_comparison(args.db_host, args.db_name, args.output_dir)
