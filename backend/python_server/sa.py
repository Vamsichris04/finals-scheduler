"""Simulated Annealing wrapper exposing solve(users, slots, **opts)
Delegates to `scheduler.sa_solver`.
"""
from typing import List, Dict, Any
from . import scheduler


def solve(users: List[Dict[str, Any]], slots: List[Dict[str, Any]], **opts) -> Dict[str, Any]:
    iters = int(opts.get('iters', opts.get('sa_iters', 2000)))
    return scheduler.sa_solver(users, slots, iters=iters)
