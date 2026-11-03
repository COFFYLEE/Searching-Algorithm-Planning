def solve_planning(problem: dict) -> dict:
    """Forward BFS on fact sets, using only the supplied action records."""
    initial = frozenset(problem['initial'])
    goal = frozenset(problem['goal'])
    actions = [(action['name'], frozenset(action['preconditions']),
                frozenset(action['add']), frozenset(action['delete']))
               for action in sorted(problem['actions'], key=lambda a: a['name'])]
    frontier = deque([(initial, ())])
    discovered = {initial}
    expanded = []
    generated = 0
    peak = 1

    def result(status, plan=(), cost=None):
        return dict(status=status, plan=list(plan), cost=cost,
                    expanded_order=expanded, expanded_count=len(expanded),
                    generated_count=generated, frontier_peak=peak)

    while frontier:
        state, plan = frontier.popleft()
        expanded.append(sorted(state))
        if goal <= state:
            return result('found', plan, len(plan))
        for name, preconditions, add, delete in actions:
            if preconditions <= state:
                generated += 1
                successor = (state - delete) | add
                if successor not in discovered:
                    discovered.add(successor)
                    frontier.append((successor, plan + (name,)))
                    peak = max(peak, len(frontier))
    return result('not_found')
