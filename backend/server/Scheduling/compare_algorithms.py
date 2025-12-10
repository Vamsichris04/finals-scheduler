"""
Algorithm Comparison and Visualization Module
Compares GA, SA, and CSP algorithms with graphs and metrics
"""

import matplotlib.pyplot as plt
import numpy as np
import json
import os
from datetime import datetime
import time

from mongoDb_loader import MongoDBLoader
from scheduling_env import SchedulingEnvironment
from genetic_algorithm import GeneticAlgorithm
from simulated_annealing import SimulatedAnnealing
from csp_solver import CSPSolver


class AlgorithmComparison:
    """Run and compare all scheduling algorithms"""

    def __init__(self, connection_string: str, database: str, schedule_type: str = 'finals'):
        self.connection_string = connection_string
        self.database = database
        self.schedule_type = schedule_type
        self.results = {}
        self.env = None
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    def load_data(self):
        """Load worker data from MongoDB"""
        print("=" * 80)
        print("LOADING DATA FROM MONGODB")
        print("=" * 80)

        loader = MongoDBLoader(self.connection_string, self.database)
        workers = loader.load_workers()
        loader.print_loaded_data(workers)
        loader.close()

        if not workers:
            raise ValueError("No active workers found in database!")

        self.env = SchedulingEnvironment(workers, schedule_type=self.schedule_type)
        print(f"\nSchedule Type: {self.schedule_type}")
        print(f"Total Shift Slots: {self.env.num_slots}")
        print(f"Number of Workers: {len(workers)}")

        return workers

    def run_ga(self, verbose=True):
        """Run Genetic Algorithm"""
        print("\n" + "=" * 80)
        print("RUNNING GENETIC ALGORITHM (GA)")
        print("=" * 80)

        solver = GeneticAlgorithm(self.env)
        start_time = time.time()
        solution, penalty, history = solver.solve(verbose=verbose)
        runtime = time.time() - start_time

        _, details = self.env.evaluate_schedule(solution)

        self.results['GA'] = {
            'solution': solution,
            'penalty': penalty,
            'runtime': runtime,
            'history': history,  # Fitness over generations
            'details': details
        }

        return solution, penalty

    def run_sa(self, verbose=True):
        """Run Simulated Annealing"""
        print("\n" + "=" * 80)
        print("RUNNING SIMULATED ANNEALING (SA)")
        print("=" * 80)

        solver = SimulatedAnnealing(self.env)
        start_time = time.time()
        solution, penalty, history = solver.solve(verbose=verbose)
        runtime = time.time() - start_time

        _, details = self.env.evaluate_schedule(solution)

        self.results['SA'] = {
            'solution': solution,
            'penalty': penalty,
            'runtime': runtime,
            'history': history,  # Cost over iterations
            'details': details
        }

        return solution, penalty

    def run_csp(self, verbose=True):
        """Run CSP Solver"""
        print("\n" + "=" * 80)
        print("RUNNING CSP SOLVER")
        print("=" * 80)

        solver = CSPSolver(self.env)
        start_time = time.time()
        solution, penalty, stats = solver.solve(verbose=verbose)
        runtime = time.time() - start_time

        _, details = self.env.evaluate_schedule(solution)

        self.results['CSP'] = {
            'solution': solution,
            'penalty': penalty,
            'runtime': runtime,
            'history': [],  # CSP doesn't have iteration history
            'details': details,
            'stats': stats
        }

        return solution, penalty

    def run_all(self, verbose=False):
        """Run all three algorithms"""
        self.load_data()

        print("\n" + "=" * 80)
        print("RUNNING ALL ALGORITHMS FOR COMPARISON")
        print("=" * 80)

        self.run_ga(verbose=verbose)
        self.run_sa(verbose=verbose)
        self.run_csp(verbose=verbose)

        return self.results

    def plot_final_fitness(self, output_dir='outputs'):
        """Plot: Final Fitness vs Algorithm"""
        os.makedirs(output_dir, exist_ok=True)

        algorithms = list(self.results.keys())
        penalties = [self.results[algo]['penalty'] for algo in algorithms]

        colors = ['#2ecc71', '#3498db', '#e74c3c']

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(algorithms, penalties, color=colors, edgecolor='black', linewidth=1.5)

        # Add value labels on bars
        for bar, penalty in zip(bars, penalties):
            height = bar.get_height()
            ax.annotate(f'{penalty:.1f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=12, fontweight='bold')

        ax.set_xlabel('Algorithm', fontsize=14)
        ax.set_ylabel('Final Penalty Score (Lower is Better)', fontsize=14)
        ax.set_title('Final Fitness vs Algorithm', fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        # Add best indicator
        best_algo = min(algorithms, key=lambda a: self.results[a]['penalty'])
        best_idx = algorithms.index(best_algo)
        bars[best_idx].set_color('#27ae60')
        bars[best_idx].set_edgecolor('#1e8449')
        bars[best_idx].set_linewidth(3)

        plt.tight_layout()
        filename = f"{output_dir}/comparison_fitness_{self.timestamp}.png"
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def plot_constraint_violations(self, output_dir='outputs'):
        """Plot: Constraint Violations vs Algorithm"""
        os.makedirs(output_dir, exist_ok=True)

        algorithms = list(self.results.keys())

        # Define constraint categories
        constraints = [
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
            'Conflicts',
            'Hour Limit',
            'Min Hours',
            'Shift Length',
            'Tier Match',
            'Fairness',
            'Morning'
        ]

        x = np.arange(len(constraints))
        width = 0.25

        fig, ax = plt.subplots(figsize=(14, 7))

        colors = ['#2ecc71', '#3498db', '#e74c3c']

        for i, algo in enumerate(algorithms):
            values = [self.results[algo]['details'].get(c, 0) for c in constraints]
            bars = ax.bar(x + i * width, values, width, label=algo, color=colors[i], edgecolor='black')

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
        ax.set_title('Constraint Violations by Algorithm', fontsize=16, fontweight='bold')
        ax.set_xticks(x + width)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.legend(fontsize=12)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        filename = f"{output_dir}/comparison_violations_{self.timestamp}.png"
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def plot_runtime(self, output_dir='outputs'):
        """Plot: Runtime vs Algorithm"""
        os.makedirs(output_dir, exist_ok=True)

        algorithms = list(self.results.keys())
        runtimes = [self.results[algo]['runtime'] for algo in algorithms]

        colors = ['#2ecc71', '#3498db', '#e74c3c']

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(algorithms, runtimes, color=colors, edgecolor='black', linewidth=1.5)

        # Add value labels
        for bar, runtime in zip(bars, runtimes):
            height = bar.get_height()
            ax.annotate(f'{runtime:.1f}s',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=12, fontweight='bold')

        ax.set_xlabel('Algorithm', fontsize=14)
        ax.set_ylabel('Runtime (seconds)', fontsize=14)
        ax.set_title('Runtime vs Algorithm', fontsize=16, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        filename = f"{output_dir}/comparison_runtime_{self.timestamp}.png"
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def plot_fitness_over_iterations(self, output_dir='outputs'):
        """Plot: Fitness vs Iteration (GA + SA)"""
        os.makedirs(output_dir, exist_ok=True)

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot GA history (fitness per generation)
        if 'GA' in self.results and self.results['GA']['history']:
            ga_history = self.results['GA']['history']
            generations = range(1, len(ga_history) + 1)
            ax.plot(generations, ga_history, 'g-', linewidth=2, label='GA (Generations)', alpha=0.8)

        # Plot SA history (cost per temperature step)
        if 'SA' in self.results and self.results['SA']['history']:
            sa_history = self.results['SA']['history']
            # Downsample if too many points
            if len(sa_history) > 1000:
                step = len(sa_history) // 1000
                sa_history = sa_history[::step]
            iterations = range(1, len(sa_history) + 1)
            ax.plot(iterations, sa_history, 'b-', linewidth=2, label='SA (Iterations)', alpha=0.8)

        ax.set_xlabel('Iteration / Generation', fontsize=14)
        ax.set_ylabel('Fitness (Penalty Score)', fontsize=14)
        ax.set_title('Fitness Convergence: GA vs SA', fontsize=16, fontweight='bold')
        ax.legend(fontsize=12)
        ax.grid(alpha=0.3)

        # Add final values as horizontal lines
        if 'GA' in self.results:
            ax.axhline(y=self.results['GA']['penalty'], color='green', linestyle='--', alpha=0.5)
        if 'SA' in self.results:
            ax.axhline(y=self.results['SA']['penalty'], color='blue', linestyle='--', alpha=0.5)

        plt.tight_layout()
        filename = f"{output_dir}/comparison_convergence_{self.timestamp}.png"
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"  ✓ Saved: {filename}")
        return filename

    def generate_all_plots(self, output_dir='outputs'):
        """Generate all comparison plots"""
        print("\n" + "=" * 80)
        print("GENERATING COMPARISON GRAPHS")
        print("=" * 80)

        plots = []
        plots.append(self.plot_final_fitness(output_dir))
        plots.append(self.plot_constraint_violations(output_dir))
        plots.append(self.plot_runtime(output_dir))
        plots.append(self.plot_fitness_over_iterations(output_dir))

        return plots

    def generate_summary_report(self, output_dir='outputs'):
        """Generate comprehensive summary report"""
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{output_dir}/comparison_summary_{self.timestamp}.txt"

        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ALGORITHM COMPARISON SUMMARY REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            # Overview
            f.write("OVERVIEW\n")
            f.write("-" * 40 + "\n")
            f.write(f"Schedule Type: {self.schedule_type}\n")
            f.write(f"Total Shift Slots: {self.env.num_slots}\n")
            f.write(f"Number of Workers: {len(self.env.workers)}\n\n")

            # Results table
            f.write("RESULTS COMPARISON\n")
            f.write("-" * 40 + "\n")
            f.write(f"{'Algorithm':<10} {'Penalty':<12} {'Runtime':<12} {'Status'}\n")
            f.write("-" * 50 + "\n")

            best_algo = min(self.results.keys(), key=lambda a: self.results[a]['penalty'])

            for algo in ['GA', 'SA', 'CSP']:
                if algo in self.results:
                    penalty = self.results[algo]['penalty']
                    runtime = self.results[algo]['runtime']
                    status = "★ BEST" if algo == best_algo else ""
                    f.write(f"{algo:<10} {penalty:<12.2f} {runtime:<12.2f}s {status}\n")

            f.write("\n")

            # Detailed violations
            f.write("CONSTRAINT VIOLATIONS BY ALGORITHM\n")
            f.write("-" * 40 + "\n")

            constraints = [
                ('coverage_violations', 'Coverage'),
                ('worker_conflicts', 'Worker Conflicts'),
                ('hour_violations', 'Hour Limit'),
                ('min_hour_violations', 'Min Hours'),
                ('shift_length_violations', 'Shift Length'),
                ('tier_mismatches', 'Tier Mismatches'),
                ('fairness_violations', 'Fairness'),
                ('morning_shift_violations', 'Morning Shifts')
            ]

            header = f"{'Constraint':<20}"
            for algo in ['GA', 'SA', 'CSP']:
                header += f"{algo:<10}"
            f.write(header + "\n")
            f.write("-" * 50 + "\n")

            for key, name in constraints:
                row = f"{name:<20}"
                for algo in ['GA', 'SA', 'CSP']:
                    if algo in self.results:
                        val = self.results[algo]['details'].get(key, 0)
                        row += f"{int(val):<10}"
                    else:
                        row += f"{'N/A':<10}"
                f.write(row + "\n")

            f.write("\n")

            # Winner analysis
            f.write("WINNER ANALYSIS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Best Algorithm: {best_algo}\n")
            f.write(f"Best Penalty: {self.results[best_algo]['penalty']:.2f}\n")
            f.write(f"Runtime: {self.results[best_algo]['runtime']:.2f}s\n\n")

            # Critical constraints check
            critical = ['coverage_violations', 'worker_conflicts', 'hour_violations', 'min_hour_violations']
            best_details = self.results[best_algo]['details']
            all_critical_pass = all(best_details.get(c, 0) == 0 for c in critical)

            f.write("Critical Constraints Status:\n")
            for c in critical:
                val = best_details.get(c, 0)
                status = "✓ PASS" if val == 0 else f"✗ FAIL ({int(val)})"
                f.write(f"  {c}: {status}\n")

            f.write("\n")
            if all_critical_pass:
                f.write("✓ ALL CRITICAL CONSTRAINTS SATISFIED\n")
            else:
                f.write("⚠ SOME CRITICAL CONSTRAINTS NOT MET\n")

            f.write("\n" + "=" * 80 + "\n")

        print(f"  ✓ Saved: {filename}")
        return filename

    def export_best_schedule(self, output_dir='outputs'):
        """Export the best schedule found"""
        os.makedirs(output_dir, exist_ok=True)

        best_algo = min(self.results.keys(), key=lambda a: self.results[a]['penalty'])
        solution = self.results[best_algo]['solution']
        penalty = self.results[best_algo]['penalty']
        details = self.results[best_algo]['details']
        runtime = self.results[best_algo]['runtime']

        filename = f"{output_dir}/BEST_schedule_{best_algo}_{self.timestamp}.json"

        # Build schedule data
        shifts = []
        worker_hours = {w.worker_id: 0 for w in self.env.workers}

        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for i, worker_id in enumerate(solution):
            if worker_id == -1:
                continue

            slot = self.env.shift_slots[i]
            worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)

            if worker:
                worker_hours[worker_id] += 1
                shifts.append({
                    'day': day_names[slot.day],
                    'hour': slot.hour,
                    'time': f"{slot.hour:02d}:00-{slot.hour+1:02d}:00",
                    'type': slot.shift_type,
                    'worker_id': worker.worker_id,
                    'worker_name': worker.name,
                    'tier': worker.tier
                })

        # Worker summary
        worker_summary = []
        for worker in self.env.workers:
            assigned = worker_hours[worker.worker_id]
            worker_summary.append({
                'worker_id': worker.worker_id,
                'name': worker.name,
                'tier': worker.tier,
                'desired_hours': worker.desired_hours,
                'assigned_hours': assigned,
                'difference': assigned - worker.desired_hours
            })

        output = {
            'metadata': {
                'algorithm': best_algo,
                'generated_at': datetime.now().isoformat(),
                'penalty_score': penalty,
                'runtime_seconds': runtime,
                'schedule_type': self.schedule_type,
                'total_workers': len(self.env.workers),
                'total_shifts_assigned': len(shifts)
            },
            'constraint_violations': {k: int(v) for k, v in details.items()},
            'schedule': sorted(shifts, key=lambda x: (day_names.index(x['day']), x['hour'])),
            'worker_summary': sorted(worker_summary, key=lambda x: x['name'])
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"  ✓ Saved: {filename}")
        return filename


def run_comparison(connection_string: str, database: str, output_dir: str = 'outputs'):
    """Main function to run full comparison"""

    comparison = AlgorithmComparison(connection_string, database)

    # Run all algorithms
    comparison.run_all(verbose=True)

    # Generate outputs
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

    print("\nResults Summary:")
    print("-" * 40)
    for algo in ['GA', 'SA', 'CSP']:
        if algo in comparison.results:
            r = comparison.results[algo]
            print(f"{algo}: Penalty={r['penalty']:.2f}, Runtime={r['runtime']:.1f}s")

    best_algo = min(comparison.results.keys(), key=lambda a: comparison.results[a]['penalty'])
    print(f"\n★ Best Algorithm: {best_algo}")
    print(f"★ Best Penalty: {comparison.results[best_algo]['penalty']:.2f}")

    return comparison


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Compare scheduling algorithms')
    parser.add_argument('--db-host', type=str, required=True, help='MongoDB connection string')
    parser.add_argument('--db-name', type=str, required=True, help='Database name')
    parser.add_argument('--output-dir', type=str, default='outputs', help='Output directory')

    args = parser.parse_args()

    run_comparison(args.db_host, args.db_name, args.output_dir)
