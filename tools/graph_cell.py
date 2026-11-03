from collections import deque
from itertools import count
import heapq
import math


def _graph_parts(problem):
    """Build an undirected adjacency list without changing the input."""
    nodes = {node['id']: node for node in problem['nodes']}
    adjacency = {name: [] for name in nodes}
    for edge in problem['edges']:
        u, v, cost = edge['u'], edge['v'], edge['cost']
        adjacency[u].append((v, cost))
        adjacency[v].append((u, cost))
    for neighbours in adjacency.values():
        neighbours.sort(key=lambda item: item[0])
    return nodes, adjacency


def _graph_search(problem, algorithm, trace=None):
    """The optional trace records frontier choices for written explanations."""
    expanded = []
    generated = 0
    peak = 1

    def result(status, path=(), cost=None, message=None):
        answer = dict(status=status, path=list(path), cost=cost,
                      expanded_order=expanded, expanded_count=len(expanded),
                      generated_count=generated, frontier_peak=peak)
        if message is not None:
            answer['message'] = message
        return answer

    if algorithm not in ('dfs', 'bfs', 'ucs', 'astar'):
        peak = 0
        return result('error', message='Use dfs, bfs, ucs, or astar.')

    nodes, adjacency = _graph_parts(problem)
    start, goal = problem['start'], problem['goal']

    def h(node):
        # UCS does not access coordinates in its priority calculation.
        if algorithm != 'astar':
            return 0
        return math.hypot(nodes[node]['x'] - nodes[goal]['x'],
                          nodes[node]['y'] - nodes[goal]['y'])

    priority_search = algorithm in ('ucs', 'astar')
    serial = count()
    if priority_search:
        # Fields enforce priority, complete path, then insertion order.
        frontier = [(h(start), (start,), next(serial), 0)]
        best = {start: (0, (start,))}
    else:
        frontier = deque([((start,), 0)])
        discovered = {start}

    def snapshot():
        if priority_search:
            return [dict(path=list(path), g=g, priority=priority,
                         stale=(g, path) != best[path[-1]])
                    for priority, path, _, g in sorted(frontier)]
        entries = list(frontier)
        if algorithm == 'dfs':
            entries.reverse()
        return [dict(path=list(path), g=g, stale=False) for path, g in entries]

    while frontier:
        before = snapshot() if trace is not None else None
        if priority_search:
            _, path, _, g = heapq.heappop(frontier)
            if (g, path) != best[path[-1]]:
                continue  # Stale entries do not count as expansions.
        elif algorithm == 'dfs':
            path, g = frontier.pop()
        else:
            path, g = frontier.popleft()

        node = path[-1]
        expanded.append(node)
        if node == goal:
            if trace is not None:
                trace.append(dict(node=node, before=before, after=snapshot()))
            return result('found', path, g)

        # Candidates are counted before discovery or best-path filtering.
        neighbours = adjacency[node]
        generated += len(neighbours)
        if algorithm == 'dfs':
            neighbours = reversed(neighbours)
        for neighbour, edge_cost in neighbours:
            new_path = path + (neighbour,)
            new_g = g + edge_cost
            if priority_search:
                pair = (new_g, new_path)
                if neighbour not in best or pair < best[neighbour]:
                    best[neighbour] = pair
                    heapq.heappush(frontier, (new_g + h(neighbour), new_path,
                                             next(serial), new_g))
            elif neighbour not in discovered:
                discovered.add(neighbour)
                frontier.append((new_path, new_g))
            peak = max(peak, len(frontier))
        if trace is not None:
            trace.append(dict(node=node, before=before, after=snapshot()))

    return result('not_found')


def solve_graph(problem: dict, algorithm: str) -> dict:
    """Return a deterministic DFS, BFS, UCS, or A* graph-search result."""
    return _graph_search(problem, algorithm)
