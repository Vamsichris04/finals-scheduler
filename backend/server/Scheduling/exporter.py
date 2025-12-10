"""
Schedule Export Module - Save schedules in various formats
"""

import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict
import os


class ScheduleExporter:
    """Export schedules to various formats"""
    
    def __init__(self, env, solution, algorithm_name="Unknown"):
        """
        Initialize exporter
        
        Args:
            env: SchedulingEnvironment object
            solution: Schedule array
            algorithm_name: Name of algorithm used
        """
        self.env = env
        self.solution = solution
        self.algorithm_name = algorithm_name
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
    def export_to_json(self, filename=None):
        """
        Export schedule to JSON format
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"schedule_{self.algorithm_name}_{self.timestamp}.json"
        
        # Calculate penalty
        penalty, details = self.env.evaluate_schedule(self.solution)
        
        # Build schedule data
        shifts = []
        worker_summaries = {}
        
        for i, worker_id in enumerate(self.solution):
            if worker_id == -1:
                continue
                
            slot = self.env.shift_slots[i]
            worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)
            
            if not worker:
                continue
            
            shift = {
                'day': slot.day,
                'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][slot.day],
                'hour': slot.hour,
                'time_range': f"{slot.hour:02d}:00-{slot.hour+1:02d}:00",
                'shift_type': slot.shift_type,
                'worker_id': worker.worker_id,
                'worker_name': worker.name,
                'worker_tier': worker.tier
            }
            shifts.append(shift)
            
            # Track worker hours
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
        
        # Build final output
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
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Schedule exported to JSON: {filename}")
        return filename
    
    def export_to_csv(self, filename=None):
        """
        Export schedule to CSV format
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"schedule_{self.algorithm_name}_{self.timestamp}.csv"
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(['Day', 'Date', 'Time', 'Shift Type', 'Worker ID', 'Worker Name', 'Tier'])
            
            # Shifts
            for i, worker_id in enumerate(self.solution):
                if worker_id == -1:
                    continue
                    
                slot = self.env.shift_slots[i]
                worker = next((w for w in self.env.workers if w.worker_id == worker_id), None)
                
                if not worker:
                    continue
                
                writer.writerow([
                    day_names[slot.day],
                    '',  # Date would go here if you have start date
                    f"{slot.hour:02d}:00-{slot.hour+1:02d}:00",
                    slot.shift_type,
                    worker.worker_id,
                    worker.name,
                    worker.tier
                ])
        
        print(f"✓ Schedule exported to CSV: {filename}")
        return filename
    
    def export_worker_summary(self, filename=None):
        """
        Export worker hour summary
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"worker_summary_{self.algorithm_name}_{self.timestamp}.csv"
        
        # Calculate worker hours
        worker_hours = {w.worker_id: 0 for w in self.env.workers}
        for worker_id in self.solution:
            if worker_id != -1:
                worker_hours[worker_id] += 1
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Worker ID', 'Name', 'Tier', 'Desired Hours', 'Assigned Hours', 'Difference'])
            
            for worker in self.env.workers:
                assigned = worker_hours[worker.worker_id]
                diff = assigned - worker.desired_hours
                
                writer.writerow([
                    worker.worker_id,
                    worker.name,
                    worker.tier,
                    worker.desired_hours,
                    assigned,
                    f"{diff:+d}"  # +/- prefix
                ])
        
        print(f"✓ Worker summary exported: {filename}")
        return filename
    
    def export_to_mongodb_format(self, filename=None):
        """
        Export in format ready for MongoDB Shifts collection
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"mongodb_shifts_{self.algorithm_name}_{self.timestamp}.json"
        
        # You'll need to provide a start date for finals week
        # For now, using placeholder
        start_date = datetime(2024, 12, 16)  # Adjust this!
        
        shifts = []
        for i, worker_id in enumerate(self.solution):
            if worker_id == -1:
                continue
                
            slot = self.env.shift_slots[i]
            
            # Calculate actual date
            shift_date = start_date + timedelta(days=slot.day)
            
            shift = {
                'date': shift_date.isoformat(),
                'startTime': f"{slot.hour:02d}:00",
                'endTime': f"{slot.hour+1:02d}:00",
                'assignedTo': str(worker_id),  # MongoDB uses string for userId
                'shiftType': slot.shift_type,
                'notes': f"Auto-assigned by {self.algorithm_name}"
            }
            shifts.append(shift)
        
        with open(filename, 'w') as f:
            json.dump(shifts, f, indent=2)
        
        print(f"✓ MongoDB format exported: {filename}")
        return filename
    
    def export_all(self, output_dir='outputs'):
        """
        Export to all formats
        
        Args:
            output_dir: Directory to save files
            
        Returns:
            Dictionary of saved files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        files = {}
        files['json'] = self.export_to_json(f"{output_dir}/schedule_{self.algorithm_name}_{self.timestamp}.json")
        files['csv'] = self.export_to_csv(f"{output_dir}/schedule_{self.algorithm_name}_{self.timestamp}.csv")
        files['worker_summary'] = self.export_worker_summary(f"{output_dir}/workers_{self.algorithm_name}_{self.timestamp}.csv")
        files['mongodb'] = self.export_to_mongodb_format(f"{output_dir}/mongodb_{self.algorithm_name}_{self.timestamp}.json")
        
        print(f"\n✓ All exports saved to: {output_dir}/")
        return files


if __name__ == "__main__":
    print("This module is meant to be imported, not run directly.")
    print("\nUsage:")
    print("  from schedule_exporter import ScheduleExporter")
    print("  exporter = ScheduleExporter(env, solution, 'GA')")
    print("  exporter.export_all()")