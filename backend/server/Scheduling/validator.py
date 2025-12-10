"""
Quick Schedule Validator
Run this after generating a schedule to validate it
"""

def quick_validate(schedule, env):
    """
    Quick validation check - prints easy-to-read report
    
    Args:
        schedule: Generated schedule array
        env: SchedulingEnvironment object
    """
    
    print("\n" + "="*80)
    print("QUICK VALIDATION CHECK")
    print("="*80)
    
    # Get penalty and details
    penalty, details = env.evaluate_schedule(schedule)
    
    # Overall status
    print("\n Overall Score:")
    print(f"   Penalty: {penalty:.2f}")
    
    if penalty == 0:
        print("   Status: ✓ PERFECT!")
    elif penalty < 500:
        print("   Status: ✓ EXCELLENT - Ready to use")
    elif penalty < 1500:
        print("   Status: ✓ GOOD - Minor issues")
    else:
        print("   Status: ⚠ NEEDS REVIEW - Has issues")
    
    # Critical constraints
    print("\nCritical Constraints:")
    critical = ['coverage_violations', 'worker_conflicts', 'hour_violations', 'min_hour_violations']
    all_good = True

    for constraint in critical:
        count = details.get(constraint, 0)
        if count == 0:
            print(f"   ✓ {constraint}: None")
        else:
            print(f"   ✗ {constraint}: {count}")
            all_good = False

    if all_good:
        print("\n   ✓ All critical constraints satisfied!")
    
    # Warnings
    print("\n Warnings (Not Critical):")
    warnings = ['fairness_violations', 'morning_shift_violations', 'tier_mismatches', 'shift_length_violations']
    
    for constraint in warnings:
        count = details.get(constraint, 0)
        if count > 0:
            print(f"  {constraint}: {count}")
    
    # Worker hour summary
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
    
    # Quick checks
    print("\nQuick Checks:")
    
    # Check for over-scheduled workers
    over_scheduled = [(w.name, worker_hours[w.worker_id]) 
                     for w in env.workers 
                     if worker_hours[w.worker_id] > 20]
    if over_scheduled:
        print(f"    Workers over 20 hours: {len(over_scheduled)}")
        for name, hours in over_scheduled[:3]:  # Show first 3
            print(f"      - {name}: {hours} hours")
    else:
        print(f"   No workers over 20 hours")
    
    # Check for conflicts
    conflicts = 0
    for i, worker_id in enumerate(schedule):
        if worker_id == -1:
            continue
        slot = env.shift_slots[i]
        worker = next((w for w in env.workers if w.worker_id == worker_id), None)
        if worker:
            for busy_day, busy_start, busy_end in worker.busy_times:
                if slot.day == busy_day and busy_start <= slot.hour < busy_end:
                    conflicts += 1
    
    if conflicts == 0:
        print(f"   No scheduling conflicts with finals")
    else:
        print(f"   {conflicts} conflicts with finals/busy times")
    
    # Coverage check
    coverage_map = {}
    for i, slot in enumerate(env.shift_slots):
        key = (slot.day, slot.hour)
        if key not in coverage_map:
            coverage_map[key] = {'Window': 0, 'Remote': 0}
        if schedule[i] != -1:
            coverage_map[key][slot.shift_type] += 1
    
    gaps = sum(1 for shifts in coverage_map.values() 
              if shifts['Window'] < 1 or shifts['Remote'] < 1)
    
    if gaps == 0:
        print(f"   All shifts have adequate coverage")
    else:
        print(f"   {gaps} time slots with inadequate coverage")
    
    # Final verdict
    print("\n" + "="*80)
    
    if penalty < 500 and all_good:
        print("VERDICT: Schedule is APPROVED for use")
        print("  → Safe to export and implement")
    elif penalty < 1500:
        print("VERDICT: Schedule is USABLE with minor issues")
        print("  → Review warnings but generally okay")
    else:
        print("VERDICT: Schedule needs IMPROVEMENT")
        print("  → Try running algorithm again or use different algorithm")
    
    print("="*80)
    
    return penalty < 1500  # Returns True if acceptable


if __name__ == "__main__":
    print("Import this module and call quick_validate(schedule, env)")
    print("\nExample:")
    print("  from quick_validator import quick_validate")
    print("  ")
    print("  solution, penalty, env = run_scheduler('SA')")
    print("  is_valid = quick_validate(solution, env)")