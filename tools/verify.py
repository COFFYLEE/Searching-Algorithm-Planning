"""Independent checks against the solver code embedded in the notebook."""
import ast
import contextlib
import copy
import io
import json
import math
from pathlib import Path
import random
import zipfile

ROOT = Path(__file__).resolve().parents[1]
notebook = json.loads((ROOT / 'z5615327_assignment1.ipynb').read_text())
namespace = {}
code_cells = [''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code']
exec(code_cells[0], namespace)
for source in code_cells[1:]:
    if 'def solve_graph(' in source or 'def solve_planning(' in source:
        exec(source, namespace)
    else:
        # Load helper definitions, not earlier experiments or plotting imports.
        module = ast.parse(source)
        definitions = [node for node in module.body if isinstance(node, ast.FunctionDef)]
        exec(compile(ast.Module(body=definitions, type_ignores=[]), '<helpers>', 'exec'), namespace)
solve_graph = namespace['solve_graph']
solve_planning = namespace['solve_planning']
algorithms = ('dfs', 'bfs', 'ucs', 'astar')
checks = 0


def require(condition, message):
    global checks
    assert condition, message
    checks += 1


def exhaustive_routes(problem):
    """Enumerate simple paths, independently of a frontier search."""
    adjacency = {n['id']: [] for n in problem['nodes']}
    for e in problem['edges']:
        adjacency[e['u']].append((e['v'], e['cost']))
        adjacency[e['v']].append((e['u'], e['cost']))
    answers = []

    def walk(path, cost):
        if path[-1] == problem['goal']:
            answers.append((cost, tuple(path)))
            return
        for neighbour, weight in adjacency[path[-1]]:
            if neighbour not in path:
                walk(path + [neighbour], cost + weight)

    walk([problem['start']], 0)
    return answers


def check_graph(problem, algorithm):
    original = copy.deepcopy(problem)
    result = solve_graph(problem, algorithm)
    require(problem == original, 'Graph input mutated')
    require(result['expanded_count'] == len(result['expanded_order']), 'Expansion count')
    require(result['frontier_peak'] >= 1, 'Peak includes initial entry')
    neighbours = {n['id']: {} for n in problem['nodes']}
    for edge in problem['edges']:
        neighbours[edge['u']][edge['v']] = edge['cost']
        neighbours[edge['v']][edge['u']] = edge['cost']
    generated = sum(len(neighbours[n]) for n in result['expanded_order'] if n != problem['goal'])
    require(result['generated_count'] == generated, 'Count candidates before filtering')
    solutions = exhaustive_routes(problem)
    require((result['status'] == 'found') == bool(solutions), 'Reachability')
    if solutions:
        path = result['path']
        require(path[0] == problem['start'] and path[-1] == problem['goal'], 'Path endpoints')
        require(all(v in neighbours[u] for u, v in zip(path, path[1:])), 'Path edges exist')
        require(result['cost'] == sum(neighbours[u][v] for u, v in zip(path, path[1:])), 'Path cost')
        if algorithm in ('ucs', 'astar'):
            require(result['cost'] == min(cost for cost, _ in solutions), 'Optimal weighted cost')
        if algorithm == 'bfs':
            require(len(path) == min(len(p) for _, p in solutions), 'Fewest BFS edges')
        require(result['expanded_order'][-1] == problem['goal'], 'Popped goal counted')
    else:
        require(result['path'] == [] and result['cost'] is None, 'Unreachable fields')
    json.dumps(result, allow_nan=False)
    return result


def planning_layers(problem):
    """Unordered whole-depth layers provide an independent minimum length."""
    layer = {frozenset(problem['initial'])}
    visited = set(layer)
    goal = set(problem['goal'])
    depth = 0
    while layer:
        if any(goal <= state for state in layer):
            return depth
        following = set()
        for state in layer:
            for action in problem['actions']:
                if set(action['preconditions']) <= state:
                    successor = frozenset((state - set(action['delete'])) | set(action['add']))
                    if successor not in visited:
                        following.add(successor)
        visited.update(following)
        layer = following
        depth += 1
    return None


def check_planning(problem):
    original = copy.deepcopy(problem)
    result = solve_planning(problem)
    require(problem == original, 'Planning input mutated')
    require(result['cost'] == planning_layers(problem), 'Minimum planning depth / no solution')
    require(result['expanded_count'] == len(result['expanded_order']), 'Planning expanded count')
    require(all(s == sorted(set(s)) for s in result['expanded_order']), 'Sorted unique output facts')
    require(len({tuple(s) for s in result['expanded_order']}) == result['expanded_count'],
            'No duplicate planning expansions')
    generated = sum(sum(set(a['preconditions']) <= set(state) for a in problem['actions'])
                    for state in result['expanded_order'] if not set(problem['goal']) <= set(state))
    require(result['generated_count'] == generated, 'Applicable candidates before filtering')
    state = set(problem['initial'])
    actions = {a['name']: a for a in problem['actions']}
    for name in result['plan']:
        action = actions[name]
        require(set(action['preconditions']) <= state, 'Returned action is applicable')
        state = (state - set(action['delete'])) | set(action['add'])
    if result['status'] == 'found':
        require(set(problem['goal']) <= state, 'Returned plan satisfies all goals')
        require(result['cost'] == len(result['plan']), 'Unit action cost')
    else:
        require(result['plan'] == [] and result['cost'] is None, 'No plan fields')
    return result


inputs = namespace['load_inputs']()
for problem in inputs['graphs'].values():
    for algorithm in algorithms:
        check_graph(problem, algorithm)
for problem in inputs['planning'].values():
    check_planning(problem)
for case, problem in namespace['derived_graphs'](inputs['graphs']).items():
    for algorithm in (('astar',) if case == 'zero_coordinates' else algorithms):
        check_graph(problem, algorithm)

# Deterministic small, cyclic and disconnected graphs. Edge costs are positive
# and at least straight-line distance, making the A* cost oracle appropriate.
rng = random.Random(9414)
for trial in range(80):
    size = rng.randint(2, 8)
    nodes = [{'id': chr(65 + i), 'x': rng.randrange(5), 'y': rng.randrange(5)}
             for i in range(size)]
    edges = []
    for i, u in enumerate(nodes):
        for v in nodes[i + 1:]:
            if rng.random() < 0.35:
                cost = max(1, math.ceil(math.hypot(u['x'] - v['x'], u['y'] - v['y'])))
                edges.append(dict(u=u['id'], v=v['id'], cost=cost + rng.randrange(3)))
    problem = dict(nodes=nodes, edges=edges, start=nodes[0]['id'], goal=nodes[-1]['id'])
    for algorithm in algorithms:
        check_graph(problem, algorithm)
    shuffled = copy.deepcopy(problem)
    rng.shuffle(shuffled['nodes'])
    rng.shuffle(shuffled['edges'])
    for algorithm in algorithms:
        require(solve_graph(problem, algorithm) == solve_graph(shuffled, algorithm),
                'Graph ordering must not depend on JSON ordering')

# Equal-cost replacement must use the complete path, not the final node.
def small_graph(names, edges, start='S', goal='T'):
    return dict(nodes=[dict(id=n, x=0, y=0) for n in names],
                edges=[dict(u=u, v=v, cost=c) for u, v, c in edges], start=start, goal=goal)


tie = small_graph('SAZXT', [('S', 'Z', 1), ('S', 'A', 2), ('Z', 'X', 2), ('A', 'X', 1)])
for algorithm in ('ucs', 'astar'):
    require(solve_graph({**tie, 'goal': 'X'}, algorithm)['path'] == ['S', 'A', 'X'],
            'Equal-cost lexicographic replacement')
    r = solve_graph(tie, algorithm)
    require(r['expanded_order'] == ['S', 'Z', 'A', 'X'], 'Skip stale tied entry')
    require(r['generated_count'] == 8 and r['frontier_peak'] == 2, 'Stale-entry metrics')
path_tie = small_graph('SABZCT', [('S', 'A', 1), ('S', 'B', 1), ('A', 'Z', 1), ('B', 'C', 1)])
require(solve_graph(path_tie, 'ucs')['expanded_order'] == ['S', 'A', 'B', 'Z', 'C'],
        'Complete path tie-break, not endpoint tie-break')

# Deliberately inconsistent geometric heuristic tests reopening, not the
# supplied graphs' edge-distance guarantee. The optimal result here is known.
reopen = small_graph('SABG', [('S', 'A', 5), ('S', 'B', 1), ('B', 'A', 1), ('A', 'G', 20)], goal='G')
reopen['nodes'][2]['x'] = 10
r = solve_graph(reopen, 'astar')
require(r['expanded_order'] == ['S', 'A', 'B', 'A', 'G'] and r['cost'] == 22,
        'Improved path reopens an expanded node')
no_coordinates = copy.deepcopy(inputs['graphs']['workshop'])
no_coordinates['nodes'] = [{'id': n['id']} for n in no_coordinates['nodes']]
require(solve_graph(no_coordinates, 'ucs') == solve_graph(inputs['graphs']['workshop'], 'ucs'),
        'UCS does not use coordinates')

# Verify the hand frontiers independently against explicitly written entries.
workshop = inputs['graphs']['workshop']
for algorithm, orders in {
    'dfs': ['depot', 'aisle', 'ramp', 'lift', 'test_bay'],
    'bfs': ['depot', 'aisle', 'stores', 'ramp', 'workshop', 'lift', 'test_bay'],
    'ucs': ['depot', 'aisle', 'stores', 'ramp', 'lift', 'workshop', 'test_bay'],
}.items():
    require(solve_graph(workshop, algorithm)['expanded_order'] == orders, 'Written expansion order')
events = []
namespace['_graph_search'](workshop, 'ucs', events)
require([(e['path'], e['g'], e['stale']) for e in events[2]['after']] == [
    (['depot', 'stores', 'ramp'], 3, False),
    (['depot', 'aisle', 'ramp'], 5, True),
    (['depot', 'aisle', 'workshop'], 8, False)], 'Written stale UCS frontier')

# A small generic fact model includes equivalent successors, no-op actions,
# delete effects and shuffled facts/actions. No equipment-specific symbols.
generic = dict(initial=['a'], goal=['c'], actions=[
    dict(name='z_noop', preconditions=['a'], add=[], delete=[]),
    dict(name='b_duplicate', preconditions=['a'], add=['b'], delete=['a']),
    dict(name='a_step', preconditions=['a'], add=['b'], delete=['a']),
    dict(name='c_finish', preconditions=['b'], add=['c'], delete=['b']),
])
r = check_planning(generic)
require(r['plan'] == ['a_step', 'c_finish'] and r['generated_count'] == 4,
        'Action ordering, duplicates, and no-op counting')
require(check_planning({**generic, 'goal': ['a']}) == dict(
    status='found', plan=[], cost=0, expanded_order=[['a']], expanded_count=1,
    generated_count=0, frontier_peak=1), 'Planning initial goal')
check_planning({**generic, 'goal': ['absent']})
for problem in inputs['planning'].values():
    shuffled = copy.deepcopy(problem)
    rng.shuffle(shuffled['initial'])
    rng.shuffle(shuffled['actions'])
    for action in shuffled['actions']:
        for field in ('preconditions', 'add', 'delete'):
            rng.shuffle(action[field])
    require(solve_planning(shuffled) == solve_planning(problem), 'Fact/action order independence')

# Reusable evaluation runs with definitions only, without earlier experiment
# variables. Compare generated results to the already executed notebook's JSON.
saved = json.loads((ROOT / 'z5615327_results.json').read_text())
evaluation_source = next(s for s in code_cells if s.startswith('# REUSABLE EVALUATION CELL'))
with contextlib.redirect_stdout(io.StringIO()):
    exec(evaluation_source, namespace)
require(saved == namespace['results'], 'Fresh evaluation cell reproduces all 24 saved results')

archive = Path('/Users/macbookm4/Documents/UNSW/COMP9414/assignment1_data_t3.zip')
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        require((ROOT / name).read_bytes() == z.read(name), 'Supplied file changed: ' + name)

print(f'PASS: {checks} assertions, 80 independently checked random graphs, '
      'tie/stale/reopening checks, generic planner checks, and all 24 saved results.')
