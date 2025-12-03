"""CSP solver wrapper exposing solve(users, slots, **opts)
Delegates to `scheduler.csp_solver`.
"""
from typing import List, Dict, Any
from . import scheduler


def solve(users: List[Dict[str, Any]], slots: List[Dict[str, Any]], **opts) -> Dict[str, Any]:
    """Run CSP solver. Accepts same args as scheduler.csp_solver.
    Returns dict { 'schedule': ..., 'quality': ... }
    """
    hour_cap = opts.get('hour_cap', scheduler.TARGET_HOURS)
    return scheduler.csp_solver(users, slots, hour_cap=hour_cap)
