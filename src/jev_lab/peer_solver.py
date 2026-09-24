"""Opt-in bounded exact solvers. No model confidence, labels, or authority changes.
Only explicitly supported structured atoms are accepted. Not general language understanding.
"""
from fractions import Fraction
from itertools import product
import hashlib, json, math

def _validate_packet(atoms):
    if type(atoms) is not dict:
        raise ValueError('Atoms must be an exact dictionary')
    stack = [(atoms, 0)]
    visited = 0
    while stack:
        value, depth = stack.pop()
        visited += 1
        if visited > 1024 or depth > 8:
            raise ValueError('Atom count/depth bound exceeded')
        kind = type(value)
        if kind is dict:
            if len(value) > 64 or any((type(k) is not str or len(k) > 128 for k in value)):
                raise ValueError('Invalid dictionary shape')
            stack.extend(((v, depth + 1) for v in value.values()))
        elif kind is list:
            if len(value) > 256:
                raise ValueError('Array bound exceeded')
            stack.extend(((v, depth + 1) for v in value))
        elif kind is str:
            if len(value) > 256:
                raise ValueError('String bound exceeded')
        elif kind is int:
            if value.bit_length() > 63:
                raise ValueError('Integer bound exceeded')
        elif kind is bool or value is None:
            pass
        else:
            raise ValueError('Unsupported atom type')

def solve(atoms):
    _validate_packet(atoms)
    k = atoms['kind']
    if k == 'sat':
        n = atoms['variables']
        if not (type(n) == int and 1 <= n <= 12):
            raise ValueError('Invalid or out-of-bounds atom packet')
        clauses = atoms['clauses']
        if not (len(clauses) <= 64 and all((c and all((type(v) == int and 1 <= abs(v) <= n for v in c)) for c in clauses))):
            raise ValueError('Invalid or out-of-bounds atom packet')
        q = atoms['query_variable']
        if not (type(q) is int and 1 <= q <= n):
            raise ValueError('Invalid or out-of-bounds atom packet')
        worlds = []
        for bits in product([False, True], repeat=n):
            if all((any((bits[abs(v) - 1] if v > 0 else not bits[abs(v) - 1] for v in c)) for c in clauses)):
                worlds.append(bits)
        if not worlds:
            raise ValueError('Inconsistent premises: no truth verdict from explosion')
        vals = {w[q - 1] for w in worlds}
        return (vals, {'compatible_worlds': len(worlds)})
    if k == 'shortest_path':
        n = atoms['nodes']
        edges = atoms['edges']
        if not (2 <= n <= 32 and len(edges) <= 256 and all((type(a) is int and type(b) is int and 0 <= a < n and 0 <= b < n and (type(w) == int) and (0 <= w <= 100) for a, b, w in edges))):
            raise ValueError('Invalid or out-of-bounds atom packet')
        dist = [math.inf] * n
        dist[0] = 0
        for _ in range(n - 1):
            changed = False
            for a, b, w in edges:
                if dist[a] + w < dist[b]:
                    dist[b] = dist[a] + w
                    changed = True
            if not changed:
                break
        if not math.isfinite(dist[-1]):
            raise ValueError('Destination unreachable')
        return ({dist[-1]}, {'shortest_distance': dist[-1]})
    if k == 'knapsack':
        items = atoms['items']
        cap = atoms['capacity']
        if not (len(items) <= 20 and type(cap) == int and (0 <= cap <= 200) and all((type(w) == type(v) == int and 1 <= w <= 100 and (0 <= v <= 10000) for w, v in items))):
            raise ValueError('Invalid or out-of-bounds atom packet')
        dp = [0] * (cap + 1)
        for w, v in items:
            for c in range(cap, w - 1, -1):
                dp[c] = max(dp[c], dp[c - w] + v)
        return ({max(dp)}, {'best_value': max(dp), 'capacity': cap})
    if k == 'critical_path':
        durations = atoms['durations']
        parents = atoms['parents']
        if not (1 <= len(durations) <= 32 and len(parents) == len(durations)):
            raise ValueError('Invalid or out-of-bounds atom packet')
        finish = []
        for i, (d, ps) in enumerate(zip(durations, parents)):
            if not (type(d) == int and 0 <= d <= 100 and all((type(p) == int and 0 <= p < i for p in ps))):
                raise ValueError('Require explicit acyclic topological order')
            finish.append(d + max((finish[p] for p in ps), default=0))
        return ({max(finish)}, {'earliest_finish': finish})
    if k == 'idempotent_effects':
        events = atoms['events']
        if not (len(events) <= 24 and all((set(e) == {'key', 'applied'} and type(e['key']) == str and (type(e['applied']) is bool or e['applied'] is None) for e in events))):
            raise ValueError('Invalid or out-of-bounds atom packet')
        known = {e['key'] for e in events if e['applied'] is True}
        possible = {e['key'] for e in events if e['applied'] is not False}
        return (set(range(len(known), len(possible) + 1)), {'minimum_unique_effects': len(known), 'maximum_unique_effects': len(possible)})
    if k == 'bayes_counts':
        counts = atoms['positive_counts']
        q = atoms['category']
        if not (2 <= len(counts) <= 8 and all((type(x) == int and 0 <= x <= 10000 for x in counts)) and (sum(counts) > 0) and type(q) is int and (0 <= q < len(counts))):
            raise ValueError('Invalid or out-of-bounds atom packet')
        value = Fraction(counts[q], sum(counts))
        return ({value}, {'posterior_numerator': value.numerator, 'posterior_denominator': value.denominator})
    if k == 'expected_value':
        weights = atoms['state_weights']
        payoffs = atoms['future_net_payoffs']
        if not (1 <= len(weights) <= 8 and 1 <= len(payoffs) <= 8 and all((type(w) == int and w > 0 for w in weights))):
            raise ValueError('Invalid or out-of-bounds atom packet')
        if not all((len(row) == len(weights) and all((type(x) == int and abs(x) <= 1000000 for x in row)) for row in payoffs)):
            raise ValueError('Invalid or out-of-bounds atom packet')
        values = [sum((w * x for w, x in zip(weights, row))) for row in payoffs]
        winners = {i for i, v in enumerate(values) if v == max(values)}
        if len(winners) != 1:
            raise ValueError('No unique optimum; do not invent tie-break preference')
        return (winners, {'weighted_future_values': values, 'ignored_sunk_cost': True})
    if k == 'evidence_conjunction':
        states = atoms['underlying_truth']
        if not (1 <= len(states) <= 20 and all((type(v) == bool or v is None for v in states))):
            raise ValueError('Invalid or out-of-bounds atom packet')
        vals = {False} if False in states else {False, True} if None in states else {True}
        return (vals, {'known_false': sum((x is False for x in states)), 'unknown': sum((x is None for x in states))})
    raise ValueError('Unsupported atom type: no silent generic inference')

def review(atoms, claimed_value):
    _validate_packet(atoms)
    k = atoms.get('kind')
    if k in ('sat', 'evidence_conjunction'):
        if type(claimed_value) is not bool:
            raise ValueError('Boolean claim required')
    elif k == 'bayes_counts':
        if type(claimed_value) is not list or len(claimed_value) != 2 or any((type(v) is not int or v.bit_length() > 63 for v in claimed_value)):
            raise ValueError('Bounded numerator/denominator claim required')
        n, d = claimed_value
        if d <= 0 or n < 0 or n > d:
            raise ValueError('Invalid probability claim')
        claimed_value = Fraction(n, d)
    elif k in ('shortest_path', 'knapsack', 'critical_path', 'idempotent_effects', 'expected_value'):
        if type(claimed_value) is not int or claimed_value < 0 or claimed_value.bit_length() > 63:
            raise ValueError('Nonnegative bounded integer claim required')
    else:
        raise ValueError('Unsupported schema')
    values, witness = solve(atoms)
    matches = [v == claimed_value for v in values]
    verdict = 'supported' if all(matches) else 'contradicted' if not any(matches) else 'underdetermined'
    return {'verdict': verdict, 'witness': witness, 'input_sha256': hashlib.sha256(json.dumps({'atoms': atoms, 'claimed_value': str(claimed_value)}, sort_keys=True).encode()).hexdigest(), 'source': 'bounded deterministic tool, not a model judgment', 'permission_granted': False}

def concise_review(atoms, claimed_value, model_verdict=None):
    r = review(atoms, claimed_value)
    disagreement = model_verdict is not None and model_verdict != r['verdict']
    return {'verdict': r['verdict'], 'challenge': 'Model answer conflicts with the checked atoms.' if disagreement else 'No verified counterexample to the tool verdict.', 'evidence': r['witness'], 'next': 'Obtain the missing evidence.' if r['verdict'] == 'underdetermined' else 'Use the checked result within this atom schema; do not generalize beyond it.', 'model_disagreement': disagreement, 'permission_granted': False}
