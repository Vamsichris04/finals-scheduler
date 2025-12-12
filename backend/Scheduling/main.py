"""
Main Scheduler - Run scheduling algorithms with MongoDB data
Enhanced with export and validation features
"""

import sys
import argparse
from mongoDb_loader import MongoDBLoader
from scheduling_env import SchedulingEnvironment
from genetic_algorithm import GeneticAlgorithm
from simulated_annealing import SimulatedAnnealing
from csp_solver import CSPSolver
import time
import json
import csv
from datetime import datetime, timedelta
import os


class ScheduleExporter:
    """Export schedules to various formats"""

    def __init__(self, env, solution, algorithm_name="Unknown", penalty=0, runtime=0):
        self.env = env
        self.solution = solution
        self.algorithm_name = algorithm_name
        self.penalty = penalty
        self.runtime = runtime
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def export_to_json(self, filename=None, output_dir='outputs'):
        """Export schedule to JSON format"""
        os.makedirs(output_dir, exist_ok=True)
        
        if filename is None:
            filename = f"{output_dir}/schedule_{self.algorithm_name}_{self.timestamp}.json"
        
        penalty, details = self.env.evaluate_schedule(self.solution)
        
        shifts = []
        worker_summaries = {}
        
        for i, worker_id in enumerate(self.solution):
            if worker_id == -1:
                continue
                
            slot = self.env.shift_slots[i]
            worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)
            
            if not worker:
                continue
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            shift = {
                'day': slot.day,
                'day_name': day_names[slot.day],
                'hour': slot.hour,
                'time_range': f"{slot.hour:02d}:00-{slot.hour+1:02d}:00",
                'shift_type': slot.shift_type,
                'worker_id': worker.worker_id,
                'worker_name': worker.name,
                'worker_tier': worker.tier
            }
            shifts.append(shift)
            
            if worker.worker_id not in worker_summaries:
                worker_summaries[worker.worker_id] = {
                    'worker_id': worker.worker_id,
                    'name': worker.name,
                    'tier': worker.tier,
                    'desired_hours': worker.desired_hours,
                    'assigned_hours': 0,
                    'shifts': []
                }
            
            worker_summaries[worker.worker_id]['assigned_hours'] += 1
            worker_summaries[worker.worker_id]['shifts'].append({
                'day': shift['day_name'],
                'time': shift['time_range'],
                'type': shift['shift_type']
            })
        
        output = {
            'metadata': {
                'algorithm': self.algorithm_name,
                'generated_at': datetime.now().isoformat(),
                'penalty_score': float(penalty),
                'schedule_type': self.env.schedule_type,
                'total_workers': len(self.env.workers),
                'total_shifts': len([s for s in self.solution if s != -1])
            },
            'constraint_violations': {k: int(v) for k, v in details.items()},
            'shifts': sorted(shifts, key=lambda x: (x['day'], x['hour'])),
            'worker_summaries': list(worker_summaries.values())
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f" JSON: {filename}")
        return filename
    
    def export_to_csv(self, filename=None, output_dir='outputs'):
        """Export schedule to CSV format"""
        os.makedirs(output_dir, exist_ok=True)
        
        if filename is None:
            filename = f"{output_dir}/schedule_{self.algorithm_name}_{self.timestamp}.csv"
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Day', 'Time', 'Shift Type', 'Worker ID', 'Worker Name', 'Tier'])
            
            for i, worker_id in enumerate(self.solution):
                if worker_id == -1:
                    continue
                    
                slot = self.env.shift_slots[i]
                worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)
                
                if not worker:
                    continue
                
                writer.writerow([
                    day_names[slot.day],
                    f"{slot.hour:02d}:00-{slot.hour+1:02d}:00",
                    slot.shift_type,
                    worker.worker_id,
                    worker.name,
                    worker.tier
                ])
        
        print(f"  ✓ CSV: {filename}")
        return filename
    
    def export_worker_summary(self, filename=None, output_dir='outputs'):
        """Export worker hour summary"""
        os.makedirs(output_dir, exist_ok=True)
        
        if filename is None:
            filename = f"{output_dir}/worker_summary_{self.algorithm_name}_{self.timestamp}.csv"
        
        worker_hours = {w.worker_id: 0 for w in self.env.workers}
        for worker_id in self.solution:
            if worker_id != -1:
                worker_hours[worker_id] += 1
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Worker ID', 'Name', 'Tier', 'Desired Hours', 'Assigned Hours', 'Difference'])
            
            for worker in self.env.workers:
                assigned = worker_hours[worker.worker_id]
                diff = int(assigned - worker.desired_hours)

                writer.writerow([
                    worker.worker_id,
                    worker.name,
                    worker.tier,
                    worker.desired_hours,
                    assigned,
                    f"{diff:+d}"
                ])
        
        print(f"  ✓ Worker Summary: {filename}")
        return filename
    
    def export_to_mongodb_format(self, filename=None, output_dir='outputs', start_date=None):
        """Export in format ready for MongoDB Shifts collection"""
        os.makedirs(output_dir, exist_ok=True)
        
        if filename is None:
            filename = f"{output_dir}/mongodb_shifts_{self.algorithm_name}_{self.timestamp}.json"
        
        if start_date is None:
            # Default to next Monday
            today = datetime.now()
            days_ahead = 0 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            start_date = today + timedelta(days=days_ahead)
        
        shifts = []
        for i, worker_id in enumerate(self.solution):
            if worker_id == -1:
                continue
                
            slot = self.env.shift_slots[i]
            shift_date = start_date + timedelta(days=slot.day)
            
            shift = {
                'date': shift_date.isoformat(),
                'startTime': f"{slot.hour:02d}:00",
                'endTime': f"{slot.hour+1:02d}:00",
                'assignedTo': str(worker_id),
                'shiftType': slot.shift_type,
                'notes': f"Auto-assigned by {self.algorithm_name}"
            }
            shifts.append(shift)
        
        with open(filename, 'w') as f:
            json.dump(shifts, f, indent=2)
        
        print(f"  ✓ MongoDB Format: {filename}")
        return filename
    
    def export_all(self, output_dir='outputs', start_date=None):
        """Export to all formats"""
        print(f"\nExporting to: {output_dir}/")

        files = {}
        files['json'] = self.export_to_json(output_dir=output_dir)
        files['csv'] = self.export_to_csv(output_dir=output_dir)
        files['worker_summary'] = self.export_worker_summary(output_dir=output_dir)
        files['mongodb'] = self.export_to_mongodb_format(output_dir=output_dir, start_date=start_date)

        print(f"\n✓ All exports complete!")
        return files

    def export_simple(self, output_dir='outputs'):
        """Export simplified output: just schedule + summary with clear naming"""
        os.makedirs(output_dir, exist_ok=True)

        penalty, details = self.env.evaluate_schedule(self.solution)

        # Clear naming convention: ALGO_PENALTY_TIMESTAMP
        base_name = f"{self.algorithm_name}_penalty{int(penalty)}_{self.timestamp}"

        # 1. Schedule JSON
        schedule_file = f"{output_dir}/{base_name}_schedule.json"
        self._export_schedule_json(schedule_file, penalty, details)

        # 2. Summary TXT
        summary_file = f"{output_dir}/{base_name}_summary.txt"
        self._export_summary_txt(summary_file, penalty, details)

        print(f"\nOutputs saved to: {output_dir}/")
        print(f"  ✓ Schedule: {base_name}_schedule.json")
        print(f"  ✓ Summary:  {base_name}_summary.txt")

        return {'schedule': schedule_file, 'summary': summary_file}

    def _export_schedule_json(self, filename, penalty, details):
        """Export schedule to JSON with clear structure"""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Build shifts grouped by day
        schedule_by_day = {day: [] for day in day_names[:6]}  # Mon-Sat

        worker_hours = {w.worker_id: 0 for w in self.env.workers}

        for i, worker_id in enumerate(self.solution):
            if worker_id == -1:
                continue

            slot = self.env.shift_slots[i]
            worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)

            if worker:
                worker_hours[worker_id] += 1
                day_name = day_names[slot.day]
                if day_name in schedule_by_day:
                    schedule_by_day[day_name].append({
                        'time': f"{slot.hour:02d}:00-{slot.hour+1:02d}:00",
                        'type': slot.shift_type,
                        'worker': worker.name,
                        'worker_id': worker.worker_id,
                        'tier': worker.tier
                    })

        # Sort shifts by time within each day
        for day in schedule_by_day:
            schedule_by_day[day].sort(key=lambda x: x['time'])

        # Worker summary
        worker_summary = []
        for worker in sorted(self.env.workers, key=lambda w: w.name):
            assigned = worker_hours[worker.worker_id]
            worker_summary.append({
                'name': worker.name,
                'id': worker.worker_id,
                'tier': worker.tier,
                'desired': worker.desired_hours,
                'assigned': assigned,
                'diff': assigned - worker.desired_hours
            })

        output = {
            'run_info': {
                'algorithm': self.algorithm_name,
                'timestamp': datetime.now().isoformat(),
                'penalty': penalty,
                'runtime_seconds': self.runtime
            },
            'constraints': {k: int(v) for k, v in details.items()},
            'schedule': schedule_by_day,
            'workers': worker_summary
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

    def _export_summary_txt(self, filename, penalty, details):
        """Export human-readable summary"""
        with open(filename, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("SCHEDULE RUN SUMMARY\n")
            f.write("=" * 60 + "\n\n")

            # Run info
            f.write(f"Algorithm:  {self.algorithm_name}\n")
            f.write(f"Timestamp:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Runtime:    {self.runtime:.2f} seconds\n")
            f.write(f"Penalty:    {penalty:.2f}\n\n")

            # Status
            if penalty < 500:
                f.write("Status: EXCELLENT - Ready to use\n\n")
            elif penalty < 1500:
                f.write("Status: GOOD \n\n")
            else:
                f.write("Status: BAD\n\n")

            # Constraints
            f.write("-" * 40 + "\n")
            f.write("CONSTRAINT VIOLATIONS\n")
            f.write("-" * 40 + "\n")

            critical = ['coverage_violations', 'worker_conflicts', 'hour_violations', 'min_hour_violations']
            warnings = ['shift_length_violations', 'tier_mismatches', 'fairness_violations', 'morning_shift_violations']

            f.write("\nCritical (must be 0):\n")
            all_critical_pass = True
            for c in critical:
                val = details.get(c, 0)
                status = "✓" if val == 0 else "✗"
                if val > 0:
                    all_critical_pass = False
                f.write(f"  {status} {c}: {int(val)}\n")

            f.write("\nWarnings:\n")
            for w in warnings:
                val = details.get(w, 0)
                f.write(f"  • {w}: {int(val)}\n")

            # Worker hours
            f.write("\n" + "-" * 40 + "\n")
            f.write("WORKER HOURS\n")
            f.write("-" * 40 + "\n\n")

            worker_hours = {w.worker_id: 0 for w in self.env.workers}
            for worker_id in self.solution:
                if worker_id != -1:
                    worker_hours[worker_id] += 1

            f.write(f"{'Name':<25} {'Desired':>8} {'Assigned':>9} {'Diff':>6}\n")
            f.write("-" * 50 + "\n")

            for worker in sorted(self.env.workers, key=lambda w: w.name):
                assigned = worker_hours[worker.worker_id]
                diff = int(assigned - worker.desired_hours)
                f.write(f"{worker.name:<25} {worker.desired_hours:>8.1f} {assigned:>9} {diff:>+6}\n")

            hours_list = [h for h in worker_hours.values() if h > 0]
            if hours_list:
                f.write("\n")
                f.write(f"Min: {min(hours_list)}h | Max: {max(hours_list)}h | Avg: {sum(hours_list)/len(hours_list):.1f}h\n")

            # Final verdict
            f.write("\n" + "=" * 60 + "\n")
            if all_critical_pass and penalty < 1500:
                f.write("✓ SCHEDULE APPROVED FOR USE\n")
            else:
                f.write("⚠ SCHEDULE NEEDS IMPROVEMENT\n")
            f.write("=" * 60 + "\n")


class ScheduleValidator:
    """Validate generated schedules"""
    
    @staticmethod
    def quick_validate(schedule, env, verbose=True):
        """Quick validation with easy-to-read report"""
        
        if verbose:
            print("\n" + "="*80)
            print("SCHEDULE VALIDATION")
            print("="*80)
        
        penalty, details = env.evaluate_schedule(schedule)
        
        if verbose:
            print("\nOverall Score:")
            print(f"   Penalty: {penalty:.2f}")
            
            if penalty == 0:
                print("   Status: PERFECT!")
            elif penalty < 500:
                print("   Status: EXCELLENT - Ready to use")
            elif penalty < 1500:
                print("   Status: GOOD - Minor issues")
            else:
                print("   Status: BAD - Has issues")
        
        # Critical constraints
        critical = ['coverage_violations', 'worker_conflicts', 'hour_violations', 'min_hour_violations']
        all_critical_pass = all(details.get(c, 0) == 0 for c in critical)

        if verbose:
            print("\nCritical Constraints:")
            for constraint in critical:
                count = details.get(constraint, 0)
                if count == 0:
                    print(f"    {constraint}: None")
                else:
                    print(f"    {constraint}: {count}")

        # Warnings
        if verbose:
            warnings = ['fairness_violations', 'morning_shift_violations',
                       'tier_mismatches', 'shift_length_violations']
            
            warning_count = sum(details.get(w, 0) for w in warnings)
            if warning_count > 0:
                print("\n⚠ Warnings (Not Critical):")
                for constraint in warnings:
                    count = details.get(constraint, 0)
                    if count > 0:
                        print(f"    {constraint}: {count}")
        
        # Worker hour summary
        if verbose:
            print("\n Worker Hours:")
            worker_hours = {w.worker_id: 0 for w in env.workers}
            for worker_id in schedule:
                if worker_id != -1:
                    worker_hours[worker_id] += 1
            
            hours_list = [h for h in worker_hours.values() if h > 0]
            if hours_list:
                print(f"   Min: {min(hours_list)} hours")
                print(f"   Max: {max(hours_list)} hours")
                print(f"   Avg: {sum(hours_list)/len(hours_list):.1f} hours")
        
        # Final verdict
        if verbose:
            print("\n" + "="*80)
            
            if penalty < 500 and all_critical_pass:
                print(" VERDICT: Schedule is APPROVED for use")
                print("  → Safe to export and implement")
            elif penalty < 1500:
                print(" VERDICT: Schedule is USABLE with minor issues")
                print("  → Review warnings but generally okay")
            else:
                print(" VERDICT: Schedule needs IMPROVEMENT")
                print("  → Try running algorithm again or use different algorithm")
            
            print("="*80 + "\n")
        
        return {
            'is_acceptable': penalty < 1500,
            'is_excellent': penalty < 500 and all_critical_pass,
            'penalty': penalty,
            'details': details,
            'all_critical_pass': all_critical_pass
        }


def run_scheduler(algorithm: str = 'SA', 
                 schedule_type: str = 'finals',
                 connection_string: str = 'mongodb://localhost:27017/',
                 database: str = 'finals_scheduler',
                 verbose: bool = True):
    """Run scheduling algorithm with MongoDB data"""
    
    if verbose:
        print("="*80)
        print("LOADING DATA FROM MONGODB")
        print("="*80)
    
    loader = MongoDBLoader(connection_string, database)
    workers = loader.load_workers()
    
    if verbose:
        loader.print_loaded_data(workers)
    
    loader.close()
    
    if not workers:
        print("\n No active workers found in database!")
        return None, None, None
    
    if verbose:
        print("\n" + "="*80)
        print("CREATING SCHEDULING ENVIRONMENT")
        print("="*80)
        print(f"Schedule Type: {schedule_type}")
        print(f"Total Shift Slots: ", end="")
    
    env = SchedulingEnvironment(workers, schedule_type=schedule_type)
    
    if verbose:
        print(f"{env.num_slots}")
        print(f"Number of Workers: {len(workers)}")
    
    if verbose:
        print("\n" + "="*80)
        print(f"RUNNING {algorithm.upper()} ALGORITHM")
        print("="*80)
    
    start_time = time.time()
    
    if algorithm.upper() == 'GA':
        solver = GeneticAlgorithm(env, population_size=100, generations=300)
        solution, penalty, history = solver.solve(verbose=verbose)
        
    elif algorithm.upper() == 'SA':
        solver = SimulatedAnnealing(env, initial_temp=1000.0, cooling_rate=0.995)
        solution, penalty, history = solver.solve(verbose=verbose)
        
    elif algorithm.upper() == 'CSP':
        solver = CSPSolver(env, max_time=60.0)
        solution, penalty, stats = solver.solve(verbose=verbose)
        
    else:
        print(f"Unknown algorithm: {algorithm}")
        return None, None, None
    
    elapsed = time.time() - start_time
    
    if solution is None:
        print("\n✗ No solution found!")
        return None, None, None, 0

    if verbose:
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"Algorithm: {algorithm.upper()}")
        print(f"Runtime: {elapsed:.2f} seconds")
        print(f"Final Penalty: {penalty:.2f}")

    return solution, penalty, env, elapsed


def compare_algorithms(schedule_type: str = 'finals',
                      connection_string: str = 'mongodb://localhost:27017/',
                      database: str = 'finals_scheduler'):
    """Run all three algorithms and compare results"""
    
    print("\n" + "="*80)
    print("COMPARING ALL THREE ALGORITHMS")
    print("="*80)
    
    algorithms = ['GA', 'SA', 'CSP']
    results = {}
    
    for algo in algorithms:
        print(f"\n{'='*80}")
        print(f"Testing {algo}...")
        print(f"{'='*80}")
        
        solution, penalty, env = run_scheduler(
            algorithm=algo,
            schedule_type=schedule_type,
            connection_string=connection_string,
            database=database,
            verbose=False
        )
        
        if solution is not None:
            results[algo] = {
                'penalty': penalty,
                'solution': solution,
                'env': env
            }
            print(f"✓ {algo}: Penalty = {penalty:.2f}")
        else:
            print(f"✗ {algo}: Failed to find solution")
    
    if results:
        print("\n" + "="*80)
        print("COMPARISON SUMMARY")
        print("="*80)
        
        for algo, data in sorted(results.items(), key=lambda x: x[1]['penalty']):
            print(f"{algo}: {data['penalty']:.2f}")
        
        best_algo = min(results.keys(), key=lambda k: results[k]['penalty'])
        best_solution = results[best_algo]['solution']
        best_env = results[best_algo]['env']
        
        print(f"\n✓ Best Algorithm: {best_algo}")
        print(f"✓ Best Penalty: {results[best_algo]['penalty']:.2f}")
        
        # Validate best
        ScheduleValidator.quick_validate(best_solution, best_env)
        
        return results
    
    return None


def main():
    """Main entry point with command-line interface"""
    
    parser = argparse.ArgumentParser(
        description='IT Help Desk Scheduler - Generate schedules using AI algorithms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Simulated Annealing (fastest, recommended)
  python main.py --algorithm SA
  
  # Run with validation and export
  python main.py --algorithm SA --validate --export all
  
  # Compare all algorithms
  python main.py --compare
  
  # Show full schedule
  python main.py --algorithm SA --show-schedule
  
  # Export to specific directory
  python main.py --algorithm GA --export all --output-dir my_schedules
        """
    )
    
    parser.add_argument('--algorithm', '-a', 
                       type=str, 
                       default='SA',
                       choices=['GA', 'SA', 'CSP'],
                       help='Algorithm to use (default: SA)')
    
    parser.add_argument('--schedule-type', '-t',
                       type=str,
                       default='finals',
                       choices=['finals', 'regular'],
                       help='Type of schedule (default: finals)')
    
    parser.add_argument('--compare', '-c',
                       action='store_true',
                       help='Compare all three algorithms')
    
    parser.add_argument('--db-host',
                       type=str,
                       default='mongodb://localhost:27017/',
                       help='MongoDB connection string')
    
    parser.add_argument('--db-name',
                       type=str,
                       default='finals_scheduler',
                       help='Database name')
    
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='Suppress detailed output')
    
    parser.add_argument('--show-schedule', '-s',
                       action='store_true',
                       help='Print full schedule')
    
    parser.add_argument('--validate', '-v',
                       action='store_true',
                       help='Run validation checks')
    
    parser.add_argument('--export', '-e',
                       type=str,
                       choices=['simple', 'json', 'csv', 'mongodb', 'all'],
                       help='Export schedule: simple (recommended), json, csv, mongodb, or all')
    
    parser.add_argument('--output-dir', '-o',
                       type=str,
                       default='outputs',
                       help='Directory for output files (default: outputs)')
    
    args = parser.parse_args()
    
    try:
        if args.compare:
            results = compare_algorithms(
                schedule_type=args.schedule_type,
                connection_string=args.db_host,
                database=args.db_name
            )
            
            if results and args.export:
                best_algo = min(results.keys(), key=lambda k: results[k]['penalty'])
                best_solution = results[best_algo]['solution']
                best_env = results[best_algo]['env']
                
                exporter = ScheduleExporter(best_env, best_solution, best_algo)
                
                if args.export == 'all':
                    exporter.export_all(args.output_dir)
                elif args.export == 'json':
                    exporter.export_to_json(output_dir=args.output_dir)
                elif args.export == 'csv':
                    exporter.export_to_csv(output_dir=args.output_dir)
                elif args.export == 'mongodb':
                    exporter.export_to_mongodb_format(output_dir=args.output_dir)
        
        else:
            solution, penalty, env, runtime = run_scheduler(
                algorithm=args.algorithm,
                schedule_type=args.schedule_type,
                connection_string=args.db_host,
                database=args.db_name,
                verbose=not args.quiet
            )

            if solution is not None:
                # Validate
                if args.validate:
                    ScheduleValidator.quick_validate(solution, env)

                # Export
                if args.export:
                    exporter = ScheduleExporter(env, solution, args.algorithm, penalty, runtime)

                    if args.export == 'simple':
                        # New simplified output: just schedule + summary
                        exporter.export_simple(args.output_dir)
                    elif args.export == 'all':
                        exporter.export_all(args.output_dir)
                    elif args.export == 'json':
                        exporter.export_to_json(output_dir=args.output_dir)
                    elif args.export == 'csv':
                        exporter.export_to_csv(output_dir=args.output_dir)
                    elif args.export == 'mongodb':
                        exporter.export_to_mongodb_format(output_dir=args.output_dir)

                # Show schedule
                if args.show_schedule:
                    print("\n" + "="*80)
                    print("FULL SCHEDULE")
                    print("="*80)
                    env.print_schedule(solution)

                    print("\n" + "="*80)
                    print("WORKER SUMMARY")
                    print("="*80)

                    worker_hours = {w.worker_id: 0 for w in env.workers}
                    for worker_id in solution:
                        if worker_id != -1:
                            worker_hours[worker_id] += 1

                    for worker in env.workers:
                        hours = worker_hours[worker.worker_id]
                        if hours > 0:
                            diff = hours - worker.desired_hours
                            print(f"{worker.name:30s} {hours:2d}h (desired: {worker.desired_hours}h, diff: {diff:+d})")
        
        print("\n✓ Scheduling complete!")
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())