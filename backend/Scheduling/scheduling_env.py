"""
IT Help Desk Scheduling Environment
Handles the problem formulation, constraints, and fitness evaluation
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np

class Worker:
    """Represents a student worker with their attributes"""
    def __init__(self, worker_id: int, name: str, tier: int, is_commuter: bool, 
                 desired_hours: float, busy_times: List[Tuple[int, int, int]]):
        self.worker_id = worker_id
        self.name = name
        self.tier = tier  # 1-4 (4 = manager, 3 = inventory tech)
        self.is_commuter = is_commuter
        self.desired_hours = desired_hours  # Target hours per week (< 20)
        self.busy_times = busy_times  # List of (day, start_hour, end_hour) when unavailable
        
    def is_available(self, day: int, hour: int) -> bool:
        """Check if worker is available at given day and hour"""
        # Check commuter constraint (can't work before 9 AM)
        if self.is_commuter and hour < 9:
            return False
            
        # Check busy times
        for busy_day, busy_start, busy_end in self.busy_times:
            if day == busy_day and busy_start <= hour < busy_end:
                return False
        return True


class ShiftSlot:
    """Represents a time slot that needs coverage"""
    def __init__(self, day: int, hour: int, shift_type: str):
        self.day = day  # 0=Monday, 1=Tuesday, etc.
        self.hour = hour  # Hour of day (7-20 for most days)
        self.shift_type = shift_type  # 'Window' or 'Remote'
        self.assigned_worker = None  # Worker ID or None


class SchedulingEnvironment:
    """Main environment for IT scheduling problem"""
    
    SHIFT_TYPES = ['Window', 'Remote']
    
    # Working hours for different days
    HOURS_CONFIG = {
        'finals': {
            0: (7.5, 20),   # Monday: 7:30am - 8pm
            1: (7.5, 20),   # Tuesday
            2: (7.5, 20),   # Wednesday
            3: (7.5, 20),   # Thursday
            4: (7.5, 17),   # Friday: 7:30am - 5pm
            5: (10, 18),    # Saturday: 10am - 6pm
        },
        'regular': {
            0: (7.5, 20),   # Monday
            1: (7.5, 20),   # Tuesday
            2: (7.5, 20),   # Wednesday
            3: (7.5, 20),   # Thursday
            4: (7.5, 17),   # Friday
            5: (10, 18),    # Saturday: 10am - 6pm
        }
    }

    # Minimum hours per worker per week
    MIN_HOURS_PER_WORKER = 14

    # Coverage requirements per time slot
    COVERAGE_REQUIREMENTS = {
        'Window': {'min': 2, 'max': 2},   # Exactly 2 Window workers per slot
        'Remote': {'min': 2, 'max': 4}    # 2-4 Remote workers per slot
    }
    
    def __init__(self, workers: List[Worker], schedule_type: str = 'finals'):
        """
        Initialize scheduling environment
        
        Args:
            workers: List of Worker objects
            schedule_type: 'finals' or 'regular'
        """
        self.workers = workers
        self.schedule_type = schedule_type
        self.hours_config = self.HOURS_CONFIG[schedule_type]
        
        # Generate all shift slots
        self.shift_slots = self._generate_shift_slots()
        self.num_slots = len(self.shift_slots)
        
    def _generate_shift_slots(self) -> List[ShiftSlot]:
        """Generate all shift slots based on working hours and shift types"""
        slots = []

        for day, (start_hour, end_hour) in self.hours_config.items():
            # Convert hours to integer slots (e.g., 7.5 -> 7, 8, ... for each hour)
            start_int = int(np.ceil(start_hour))
            end_int = int(end_hour)

            for hour in range(start_int, end_int):
                # Create multiple Window slots (2 workers needed)
                for _ in range(self.COVERAGE_REQUIREMENTS['Window']['max']):
                    slots.append(ShiftSlot(day, hour, 'Window'))
                # Create multiple Remote slots (up to 4 workers)
                for _ in range(self.COVERAGE_REQUIREMENTS['Remote']['max']):
                    slots.append(ShiftSlot(day, hour, 'Remote'))

        return slots
    
    def evaluate_schedule(self, schedule: np.ndarray) -> Tuple[float, Dict]:
        """
        Evaluate a schedule and return penalty score
        
        Args:
            schedule: Array where schedule[i] = worker_id assigned to slot i
                     -1 means no worker assigned
        
        Returns:
            penalty: Total penalty score (lower is better, 0 is perfect)
            details: Dictionary with breakdown of violations
        """
        penalty = 0
        details = {
            'coverage_violations': 0,
            'tier_mismatches': 0,
            'worker_conflicts': 0,
            'hour_violations': 0,
            'min_hour_violations': 0,
            'fairness_violations': 0,
            'morning_shift_violations': 0,
            'shift_length_violations': 0
        }

        # Group slots by day and hour for coverage checking
        coverage_map = {}
        for i, slot in enumerate(self.shift_slots):
            key = (slot.day, slot.hour)
            if key not in coverage_map:
                coverage_map[key] = {'Window': [], 'Remote': []}
            coverage_map[key][slot.shift_type].append((i, schedule[i]))

        # Check coverage constraints using configurable requirements
        for key, shifts in coverage_map.items():
            window_workers = [w for w in shifts['Window'] if w[1] != -1]
            remote_workers = [w for w in shifts['Remote'] if w[1] != -1]

            # Window coverage check
            window_req = self.COVERAGE_REQUIREMENTS['Window']
            if len(window_workers) < window_req['min']:
                penalty += 100 * (window_req['min'] - len(window_workers))  # Critical
                details['coverage_violations'] += 1
            elif len(window_workers) > window_req['max']:
                penalty += 50
                details['coverage_violations'] += 1

            # Remote coverage check
            remote_req = self.COVERAGE_REQUIREMENTS['Remote']
            if len(remote_workers) < remote_req['min']:
                penalty += 100 * (remote_req['min'] - len(remote_workers))  # Critical
                details['coverage_violations'] += 1
            elif len(remote_workers) > remote_req['max']:
                penalty += 50
                details['coverage_violations'] += 1
        
        # Calculate worker statistics
        worker_hours = {w.worker_id: 0 for w in self.workers}
        worker_morning_shifts = {w.worker_id: 0 for w in self.workers}
        worker_assignments = {w.worker_id: [] for w in self.workers}
        
        for i, worker_id in enumerate(schedule):
            if worker_id == -1:
                continue
                
            slot = self.shift_slots[i]
            worker_hours[worker_id] += 1  # Each slot is 1 hour
            worker_assignments[worker_id].append(i)
            
            if slot.hour < 12:
                worker_morning_shifts[worker_id] += 1
            
            # Check worker availability
            worker = next((w for w in self.workers if w.worker_id == worker_id), None)
            if worker and not worker.is_available(slot.day, slot.hour):
                penalty += 200  # Critical violation
                details['worker_conflicts'] += 1
            
            # Check tier constraints (Tier 3-4 should prefer Remote)
            if worker and worker.tier >= 3 and slot.shift_type == 'Window':
                # Only minor penalty - they CAN work Window if needed
                penalty += 10
                details['tier_mismatches'] += 1
        
        # Check hour constraints and fairness
        total_hours = []
        for worker in self.workers:
            hours = worker_hours[worker.worker_id]
            total_hours.append(hours)

            # MINIMUM hours per week (critical constraint)
            if hours < self.MIN_HOURS_PER_WORKER:
                shortfall = self.MIN_HOURS_PER_WORKER - hours
                penalty += shortfall * 75  # Heavy penalty for under-hours
                details['min_hour_violations'] += 1

            # Max 20 hours per week
            if hours > 20:
                penalty += (hours - 20) * 50
                details['hour_violations'] += 1

            # Prefer close to desired hours (but less critical than min hours)
            hour_diff = abs(hours - worker.desired_hours)
            if hour_diff > 3:
                penalty += hour_diff * 3  # Reduced penalty
                details['fairness_violations'] += 1

            # Morning shift constraints (max 1, ideally; max 2 absolute)
            morning_count = worker_morning_shifts[worker.worker_id]
            if morning_count > 2:
                penalty += (morning_count - 2) * 30
                details['morning_shift_violations'] += 1
            elif morning_count > 1:
                penalty += 10
                details['morning_shift_violations'] += 1
        
        # Fairness: minimize variance in hours
        if total_hours:
            hours_std = np.std(total_hours)
            penalty += hours_std * 2
        
        # Check shift length constraints (shifts should be continuous blocks)
        # Group by worker and check unique hours per day
        for worker_id, assignments in worker_assignments.items():
            if not assignments:
                continue

            # Get unique (day, hour) combinations for this worker
            day_hours = {}
            for idx in assignments:
                slot = self.shift_slots[idx]
                if slot.day not in day_hours:
                    day_hours[slot.day] = set()
                day_hours[slot.day].add(slot.hour)

            # Check each day's continuous blocks
            for day, hours in day_hours.items():
                sorted_hours = sorted(hours)

                # Group into continuous blocks of hours
                blocks = []
                current_block = [sorted_hours[0]]

                for i in range(1, len(sorted_hours)):
                    if sorted_hours[i] == sorted_hours[i-1] + 1:
                        current_block.append(sorted_hours[i])
                    else:
                        blocks.append(current_block)
                        current_block = [sorted_hours[i]]
                blocks.append(current_block)

                # Check block lengths (min 2 hours for ~1.5h minimum, max 6 hours)
                # CRITICAL: 1-hour shifts are NOT allowed - very high penalty
                for block in blocks:
                    block_length = len(block)
                    if block_length < 2:
                        penalty += 500  # CRITICAL penalty - 1hr shifts not allowed
                        details['shift_length_violations'] += 1
                    elif block_length > 6:
                        penalty += (block_length - 6) * 100  # Heavy penalty for long shifts
                        details['shift_length_violations'] += 1
        
        return penalty, details
    
    def get_available_workers(self, day: int, hour: int) -> List[int]:
        """Get list of worker IDs available for a given day and hour"""
        available = []
        for worker in self.workers:
            if worker.is_available(day, hour):
                available.append(worker.worker_id)
        return available
    
    def schedule_to_matrix(self, schedule: np.ndarray) -> np.ndarray:
        """Convert schedule array to a readable matrix format"""
        days = max(slot.day for slot in self.shift_slots) + 1
        hours = 24  # Max hours in a day
        shift_types = 2  # Window and Remote
        
        matrix = np.zeros((days, hours, shift_types), dtype=int) - 1
        
        for i, worker_id in enumerate(schedule):
            slot = self.shift_slots[i]
            type_idx = 0 if slot.shift_type == 'Window' else 1
            matrix[slot.day, slot.hour, type_idx] = worker_id
            
        return matrix
    
    def print_schedule(self, schedule: np.ndarray):
        """Print a human-readable schedule"""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        matrix = self.schedule_to_matrix(schedule)
        
        print("\n" + "="*80)
        print("SCHEDULE")
        print("="*80)
        
        for day in range(matrix.shape[0]):
            print(f"\n{day_names[day]}:")
            print("-" * 80)
            
            for hour in range(matrix.shape[1]):
                window_worker = matrix[day, hour, 0]
                remote_worker = matrix[day, hour, 1]
                
                if window_worker != -1 or remote_worker != -1:
                    time_str = f"{hour:02d}:00-{hour+1:02d}:00"
                    
                    window_str = f"Window: {self._get_worker_name(window_worker)}" if window_worker != -1 else "Window: ---"
                    remote_str = f"Remote: {self._get_worker_name(remote_worker)}" if remote_worker != -1 else "Remote: ---"
                    
                    print(f"  {time_str} | {window_str:30s} | {remote_str}")
    
    def _get_worker_name(self, worker_id: int) -> str:
        """Get worker name by ID"""
        if worker_id == -1:
            return "---"
        for worker in self.workers:
            if worker.worker_id == worker_id:
                return f"{worker.name} (T{worker.tier})"
        return f"Worker-{worker_id}"