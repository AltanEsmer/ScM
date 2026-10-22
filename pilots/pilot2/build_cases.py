"""Rebuild pilot 2 fixtures deterministically, without model calls."""
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def jobs_oracle(data):
    best = (0, 0, [])
    for mask in range(1 << len(data)):
        indices = [i for i in range(len(data)) if mask >> i & 1]
        if all(data[i][1] <= data[j][0] or data[j][1] <= data[i][0]
               for i, j in itertools.combinations(indices, 2)):
            key = (-sum(data[i][2] for i in indices), len(indices), indices)
            best = min(best, key)
    return best[2]


def glob_oracle(data):
    pattern, text = data['pattern'], data['text']
    tokens = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == '\\':
            i += 1
            tokens.append(('literal', pattern[i] if i < len(pattern) else '\\'))
        elif char == '*':
            end = i + 1
            while end < len(pattern) and pattern[end] == '*':
                end += 1
            tokens.append(('globstar' if end - i >= 2 else 'star', ''))
            i = end - 1
        elif char == '?':
            tokens.append(('one', ''))
        else:
            tokens.append(('literal', char))
        i += 1
    reachable = {0}
    for kind, value in tokens:
        following = set()
        for pos in reachable:
            if kind in ('star', 'globstar'):
                following.add(pos)
                end = pos
                while end < len(text) and (kind == 'globstar' or text[end] != '/'):
                    end += 1
                    following.add(end)
            elif pos < len(text) and ((kind == 'one' and text[pos] != '/') or
                                     (kind == 'literal' and text[pos] == value)):
                following.add(pos + 1)
        reachable = following
    return len(text) in reachable


def flights_oracle(data):
    if data['start'] == data['goal']:
        return []
    flights = data['flights']
    best = None
    # Every feasible subset has unique chronological order because dep < arr.
    for size in range(1, len(flights) + 1):
        for subset in itertools.combinations(range(len(flights)), size):
            route = sorted(subset, key=lambda i: (flights[i][2], i))
            city, time = data['start'], data['time']
            for i in route:
                origin, dest, departure, arrival = flights[i]
                if origin != city or departure < time:
                    break
                city, time = dest, arrival
            else:
                if city == data['goal']:
                    key = (time, size, route)
                    best = key if best is None else min(best, key)
    return None if best is None else best[2]


ORACLES = {'select_jobs': jobs_oracle, 'match_path': glob_oracle, 'best_itinerary': flights_oracle}


def flight_case(flights, expected, start='A', goal='C', time=0):
    return ({'flights': flights, 'start': start, 'goal': goal, 'time': time}, expected)


LITERALS = {
    'select_jobs': [
        ([], []), ([[0, 1, -1]], []), ([[0, 1, 0]], []),
        ([[0, 2, 5], [2, 3, 4]], [0, 1]),
        ([[0, 3, 9], [0, 2, 5], [2, 3, 4]], [0]),
        ([[0, 2, 5], [0, 2, 5]], [0]),
        ([[4, 5, 3], [0, 1, 3], [1, 4, 3]], [0, 1, 2]),
        ([[0, 3, 8], [0, 1, 4], [1, 3, 4], [3, 4, 0]], [0]),
        ([[-3, -1, 2], [-1, 0, 2], [-2, 1, 5]], [2]),
        ([[0, 1, 1], [1, 2, -2], [2, 3, 1]], [0, 2]),
        ([[2, 4, 2], [0, 2, 2], [0, 1, 2], [1, 4, 2]], [0, 1]),
        ([[0, 5, 100], [1, 2, 60], [2, 3, 60]], [1, 2]),
        ([[i, i + 1, 1] for i in reversed(range(12))], list(range(12))),
    ],
    'match_path': [({'pattern': p, 'text': t}, expected) for p, t, expected in [
        ('', '', True), ('', 'a', False), ('*', '', True), ('*', 'a/b', False),
        ('**', 'a/b', True), ('**', '\n', True), ('?', '\n', True),
        ('***', '/a//b/', True), ('?', '/', False),
        ('?', 'a', True), ('a', 'ba', False), ('a/*/b', 'a//b', True),
        ('a/**/b', 'a/b', False), ('a/**/b', 'a/x/y/b', True),
        ('\\*', '*', True), ('\\*', 'x', False), ('\\?', '?', True),
        ('\\**', '*abc', True), ('*\\**', 'a*b/c', False),
        ('\\***', '*a/b', True), ('a\\', 'a\\', True),
        ('\\\\', '\\', True), ('[a].', '[a].', True), ('[a]', 'a', False),
        ('a\\/b', 'a/b', True), ('a?b', 'a/b', False),
        ('**?**', '/', False), ('**?**', '/a/', True),
        ('*', 'x' * 30, True), ('a' * 30, 'a' * 30, True),
    ]],
    'best_itinerary': [
        flight_case([], None), flight_case([], [], goal='A'),
        flight_case([['A', 'C', 0, 3]], [0]),
        flight_case([['A', 'C', 0, 3]], None, time=1),
        flight_case([['A', 'B', 0, 2], ['B', 'C', 2, 4]], [0, 1]),
        flight_case([['A', 'C', 0, 8], ['A', 'B', 1, 2], ['B', 'C', 3, 4]], [1, 2]),
        flight_case([['A', 'B', 0, 1], ['B', 'D', 1, 2], ['A', 'D', 0, 3], ['D', 'C', 4, 5]], [2, 3]),
        flight_case([['B', 'C', 2, 3], ['A', 'B', 0, 1]], [1, 0]),
        flight_case([['A', 'C', 1, 4], ['A', 'C', 0, 4]], [0]),
        flight_case([['A', 'B', 0, 1], ['B', 'A', 1, 2], ['A', 'C', 3, 4]], [2]),
        flight_case([['A', 'B', 0, 1], ['B', 'C', 0, 2]], None),
        flight_case([['A', 'C', -3, -1]], [0], time=-3),
        flight_case([['A', 'C', 0, 2]], [], goal='A'),
        flight_case([['A', 'B', 0, 1], ['B', 'C', 1, 3], ['A', 'D', 0, 1], ['D', 'C', 1, 3]], [0, 1]),
        flight_case([['A', 'B', 0, 1], ['B', 'C', 1, 3], ['A', 'C', 0, 3]], [2]),
        flight_case([['', 'C', 0, 1]], [0], start=''),
    ],
}

REFERENCES = {
'select_jobs': '''def select_jobs(data):
    states = [(0, ())]
    for i in sorted(range(len(data)), key=lambda i: (data[i][1], data[i][0], i)):
        start, end, profit = data[i]
        options = [(0, ())]
        for score, chosen in states:
            if all(data[j][1] <= start or end <= data[j][0] for j in chosen):
                options.append((score + profit, tuple(sorted(chosen + (i,)))))
        states.extend(options[1:])
    return list(min(states, key=lambda state: (-state[0], len(state[1]), state[1]))[1])
''',
'match_path': '''def match_path(data):
    import re
    pattern = data['pattern']
    pieces = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == chr(92):
            i += 1
            pieces.append(re.escape(pattern[i] if i < len(pattern) else chr(92)))
        elif c == '*':
            j = i + 1
            while j < len(pattern) and pattern[j] == '*':
                j += 1
            pieces.append(r'[\\s\\S]*' if j - i >= 2 else '[^/]*')
            i = j - 1
        elif c == '?':
            pieces.append('[^/]')
        else:
            pieces.append(re.escape(c))
        i += 1
    return re.fullmatch(''.join(pieces), data['text']) is not None
''',
'best_itinerary': '''def best_itinerary(data):
    if data['start'] == data['goal']:
        return []
    best = None
    pending = [(data['start'], data['time'], ())]
    while pending:
        city, now, path = pending.pop()
        for i, (origin, destination, departure, arrival) in enumerate(data['flights']):
            if origin != city or departure < now:
                continue
            route = path + (i,)
            if destination == data['goal']:
                candidate = (arrival, len(route), route)
                if best is None or candidate < best:
                    best = candidate
            else:
                pending.append((destination, arrival, route))
    return None if best is None else list(best[2])
''',
}


def make_case_sets():
    cases = {name: list(values) for name, values in LITERALS.items()}
    rng = random.Random(20261022)
    while len(cases['select_jobs']) < 36:
        data = []
        for _ in range(rng.randrange(3, 13)):
            start = rng.randrange(-3, 9)
            data.append([start, start + rng.randrange(1, 6), rng.randrange(-4, 12)])
        cases['select_jobs'].append((data, jobs_oracle(data)))
    while len(cases['match_path']) < 36:
        pattern = ''.join(rng.choice(['a', '/', '?', '*', '**', '***', '\\*', '\\?', '\\\\', '.'])
                          for _ in range(rng.randrange(1, 8)))
        text = ''.join(rng.choice('a/*?.\\\n') for _ in range(rng.randrange(9)))
        data = {'pattern': pattern, 'text': text}
        cases['match_path'].append((data, glob_oracle(data)))
    while len(cases['best_itinerary']) < 36:
        flights = []
        for _ in range(rng.randrange(5, 13)):
            departure = rng.randrange(-2, 12)
            flights.append([rng.choice('ABCD'), rng.choice('ABCD'), departure,
                            departure + rng.randrange(1, 5)])
        data = {'flights': flights, 'start': 'A', 'goal': 'C', 'time': rng.randrange(-2, 3)}
        cases['best_itinerary'].append((data, flights_oracle(data)))
    return cases


def make_tasks():
    cases = make_case_sets()
    return [{'id': name, 'function': name, 'spec': SPECS[name],
             'cases': [[arg, expected] for arg, expected in cases[name]],
             'reference': REFERENCES[name]} for name in ORACLES]


SPECS = {
'select_jobs': 'Define select_jobs(data). Input data is a list of at most 12 jobs, each [start, end, profit] with integer values and start < end. Select a subset whose half-open intervals [start, end) do not overlap; touching endpoints are allowed. The empty subset is allowed. Maximize total profit, then minimize selected job count, then choose the lexicographically smallest ascending list of original zero-based job indices. Return that ascending list. Do not modify the input.',
'match_path': 'Define match_path(data). Input data is a dictionary with pattern and text, both ASCII strings of at most 30 characters. Return a bool indicating whether the entire text matches the entire pattern. Slash / is the path separator. An unescaped ? matches exactly one non-slash character. An unescaped * matches zero or more non-slash characters. Each maximal consecutive unescaped run of at least two stars matches zero or more characters, including slash. Backslash escapes the next character, making it literal; a final backslash is literal. Every other character, including brackets and dot, is literal. Do not modify the input.',
'best_itinerary': 'Define best_itinerary(data). Input data is a dictionary with flights, start, goal, and time. flights is a list of at most 12 flights [origin, destination, departure, arrival]; origin and destination, start, and goal are ASCII city strings, and departure, arrival, and time are integers with departure < arrival for every flight. A route starts in start with its first departure >= time; each subsequent flight has origin equal to the previous destination and departure >= the previous arrival. The last destination must equal goal. Waiting and repeated cities are allowed. Rank routes by earliest final arrival, then fewest flights, then lexicographically smallest sequence of original zero-based flight indices in travel order. If start == goal return []; otherwise return the best route as a list of original zero-based flight indices in travel order, or None if no route exists. Do not modify the input.',
}

if __name__ == '__main__':
    (ROOT / 'tasks.json').write_text(json.dumps(make_tasks(), indent=2) + '\n')
