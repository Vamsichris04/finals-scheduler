"""Genetic Algorithm wrapper exposing solve(users, slots, **opts)
Delegates to `scheduler.ga_solver`.
"""
from typing import List, Dict, Any
from . import scheduler


def solve(users: List[Dict[str, Any]], slots: List[Dict[str, Any]], **opts) -> Dict[str, Any]:
    pop = int(opts.get('pop', opts.get('ga_pop', 30)))
    gens = int(opts.get('gens', opts.get('ga_gens', 200)))
    return scheduler.ga_solver(users, slots, pop=pop, gens=gens)
