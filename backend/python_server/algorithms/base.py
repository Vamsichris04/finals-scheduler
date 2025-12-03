from typing import List, Dict, Any


class Algorithm:
    """Base algorithm interface.

    Subclasses should implement `solve()` which returns a dict with
    keys: 'schedule' (list of assignments) and 'quality' (metrics dict).
    """

    def __init__(self, users: List[Dict[str, Any]], slots: List[Dict[str, Any]]):
        self.users = users
        self.slots = slots

    def configure(self, **opts):
        """Optional: apply options (population size, iterations, etc.)."""
        self.opts = opts

    def solve(self) -> Dict[str, Any]:
        raise NotImplementedError()
