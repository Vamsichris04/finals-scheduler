"""
MongoDB Data Loader
Loads worker and finals data from MongoDB
"""

from pymongo import MongoClient
from datetime import datetime
from scheduling_env import Worker
from typing import List


class MongoDBLoader:
    """Load scheduling data from MongoDB"""
    
    def __init__(self, connection_string: str = "mongodb://localhost:27017/", 
                 database: str = "finals_scheduler"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string
            database: Database name
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[database]
        self.users_collection = self.db['Users']
        self.finals_collection = self.db['Finals']
    
    def parse_tier(self, position: str) -> int:
        """Convert position string to tier number"""
        tier_map = {
            'Tier 1': 1,
            'Tier 2': 2,
            'Tier 3': 3,
            'Tier 4': 4
        }
        return tier_map.get(position, 1)
    
    def get_day_from_date(self, date_str: str) -> tuple:
        """
        Convert date string to day of week (0=Monday, 1=Tuesday, etc.)

        Args:
            date_str: ISO format date string

        Returns:
            Tuple of (day_of_week, date_object) where day_of_week is 0-6
        """
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

        # Check if year is 2024 - likely needs to be 2025 for finals
        if date.year == 2024:
            # Correct the year to 2025
            date = date.replace(year=2025)
            print(f"  [WARNING] Corrected date from 2024 to 2025: {date.strftime('%Y-%m-%d %A')}")

        return date.weekday(), date
    
    def parse_time(self, time_str: str) -> int:
        """
        Convert time string (HH:MM) to hour integer
        
        Args:
            time_str: Time in HH:MM format
            
        Returns:
            Hour as integer
        """
        hours, minutes = time_str.split(':')
        hour = int(hours)
        
        # If minutes >= 30, consider it as the next half hour block
        if int(minutes) >= 30:
            return hour + 0.5
        return hour
    
    def load_workers(self) -> List[Worker]:
        """
        Load all active workers from MongoDB
        
        Returns:
            List of Worker objects
        """
        # Fetch all active users
        users = list(self.users_collection.find({'isActive': True}))
        
        workers = []
        
        for user in users:
            user_id = user['userId']
            
            # Fetch finals for this user
            finals = list(self.finals_collection.find({'userId': str(user_id)}))
            
            # Convert finals to busy times
            busy_times = []
            for final in finals:
                day, date_obj = self.get_day_from_date(final['date'])
                start_hour = self.parse_time(final['startTime'])
                end_hour = self.parse_time(final['endTime'])

                # Skip Sunday finals (day 6) - helpdesk is closed
                if day == 6:
                    print(f"  [WARNING] Skipping Sunday final for {user['name']}: {date_obj.strftime('%Y-%m-%d')}")
                    continue

                busy_times.append((day, int(start_hour), int(end_hour)))
            
            # Create Worker object
            worker = Worker(
                worker_id=user_id,
                name=user['name'],
                tier=self.parse_tier(user.get('position', 'Tier 1')),
                is_commuter=user.get('isCommuter', False),
                desired_hours=user.get('desiredHours', 15),
                busy_times=busy_times
            )
            
            workers.append(worker)
        
        return workers
    
    def print_loaded_data(self, workers: List[Worker]):
        """Print summary of loaded data"""
        print("\n" + "="*80)
        print(f"LOADED {len(workers)} WORKERS FROM MONGODB")
        print("="*80)

        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for worker in workers:
            print(f"\n{worker.name} (ID: {worker.worker_id})")
            print(f"  Tier: {worker.tier}")
            print(f"  Commuter: {'Yes' if worker.is_commuter else 'No'}")
            print(f"  Desired Hours: {worker.desired_hours}")
            print(f"  Busy Times: {len(worker.busy_times)} finals/conflicts")

            if worker.busy_times:
                for day, start, end in worker.busy_times:
                    print(f"    {day_names[day]} {start:02d}:00-{end:02d}:00")
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()


if __name__ == "__main__":
    # Test loading data
    print("Testing MongoDB connection...")
    
    try:
        loader = MongoDBLoader()
        workers = loader.load_workers()
        loader.print_loaded_data(workers)
        loader.close()
        
        print("\n✓ Successfully loaded data from MongoDB!")
        
    except Exception as e:
        print(f"\n✗ Error loading data: {e}")
        print("\nMake sure:")
        print("  1. MongoDB is running")
        print("  2. Database 'finals_scheduler' exists")
        print("  3. Collections 'users' and 'finals' have data")