"""Positive-resource grammar contracts with separate tree-enumeration goldens."""
import functools
import random
import textwrap

CHART = '''def _chart(data, counting=False):
    budget = data['budget']
    table = [[{} for _ in range(budget + 1)] for _ in range(data['n'])]
    for spent in range(1, budget + 1):
        for lhs, rhs, resource, cost in data['rules']:
            left = spent - resource
            if left < 0:
                continue
            possibilities = []
            if not rhs:
                if left == 0:
                    possibilities.append(('', 1 if counting else cost))
            elif type(rhs[0]) is str:
                if left == 0:
                    possibilities.append((rhs[0], 1 if counting else cost))
            elif len(rhs) == 1:
                for word, value in table[rhs[0]][left].items():
                    possibilities.append((word, value if counting else value + cost))
            else:
                for first in range(1, left):
                    for a, av in table[rhs[0]][first].items():
                        for b, bv in table[rhs[1]][left-first].items():
                            possibilities.append((a+b, av*bv if counting else av+bv+cost))
            dest = table[lhs][spent]
            for word, value in possibilities:
                if counting and word not in data['text']:
                    continue
                if counting:
                    dest[word] = (dest.get(word, 0) + value) % 1000000007
                elif word not in dest or value < dest[word]:
                    dest[word] = value
    return table[data['start']]
'''
PARSE = CHART + '''
def budget_parse_cost(data):
    values = [row[data['text']] for row in _chart(data) if data['text'] in row]
    return min(values) if values else None
'''
COUNT = CHART + '''
def bounded_derivation_count(data):
    return sum(row.get(data['text'], 0) for row in _chart(data, True)) % 1000000007
'''
EDIT = CHART + '''
def _distance(a, b):
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        nxt = [i]
        for j, y in enumerate(b, 1):
            nxt.append(min(nxt[-1]+1, row[j]+1, row[j-1]+(x != y)))
        row = nxt
    return row[-1]

def budget_grammar_edit_cost(data):
    words = {word for row in _chart(data) for word in row}
    return min((_distance(data['text'], word) for word in words), default=None)
'''


def tree_oracle(data):
    """Enumerate explicit ordered rule-identity trees rather than chart entries."""
    @functools.lru_cache(None)
    def trees(symbol, limit):
        found = []
        for identity, (lhs, rhs, resource, cost) in enumerate(data['rules']):
            if lhs != symbol or resource > limit:
                continue
            remaining = limit - resource
            if not rhs:
                found.append(('', cost, resource, (identity,)))
            elif type(rhs[0]) is str:
                found.append((rhs[0], cost, resource, (identity,)))
            elif len(rhs) == 1:
                for word, child_cost, used, tree in trees(rhs[0], remaining):
                    found.append((word, cost+child_cost, resource+used, (identity, tree)))
            else:
                for a, ac, au, at in trees(rhs[0], remaining):
                    for b, bc, bu, bt in trees(rhs[1], remaining-au):
                        found.append((a+b, cost+ac+bc, resource+au+bu, (identity, at, bt)))
        return tuple(found)
    return trees(data['start'], data['budget'])


def distance_oracle(a, b):
    @functools.lru_cache(None)
    def edit(i, j):
        if not i: return j
        if not j: return i
        return min(edit(i-1,j)+1,edit(i,j-1)+1,edit(i-1,j-1)+(a[i-1]!=b[j-1]))
    return edit(len(a),len(b))


def oracle(name, data):
    trees = tree_oracle(data)
    if name == 'budget_parse_cost':
        costs = [cost for word,cost,used,tree in trees if word == data['text']]
        return min(costs) if costs else None
    if name == 'bounded_derivation_count':
        return sum(word == data['text'] for word,cost,used,tree in trees) % 1000000007
    return min((distance_oracle(data['text'], word) for word,cost,used,tree in trees),default=None)


BASE_CLAUSES = [
    'The argument is a dictionary with exactly n, start, rules, budget, and text; all numeric fields are integers, not booleans.',
    'There are n nonterminal symbols numbered 0 through n-1, where 1 <= n <= 3, and start is one of those symbols.',
    'Rules is a list of zero through six lists [lhs, rhs, resource, cost], where lhs is a nonterminal, resource is 1 through 3, and cost is -5 through 5.',
    'Each rhs is either an empty list, a one-element list containing the terminal string "a" or "b", a one-element list containing a nonterminal integer, or a two-element list of nonterminal integers.',
    'Budget is between 0 and 7 inclusive; text is a string of zero through seven characters, all from "ab".',
    'A derivation is a finite ordered tree rooted at start; every nonterminal occurrence chooses one rule with that lhs, and the rhs gives its ordered children, with an empty rhs producing the empty string.',
    'A tree yield is its terminal leaves read left to right; its resource and cost are the respective sums of resource and cost over all rule occurrences, including empty and unary rules.',
    'A permitted tree has total resource at most budget; a nonterminal root always needs a rule occurrence, so budget zero permits no tree.',
    'Recursive rules, nullable cycles, unused nonterminals, and duplicate rule entries are allowed; positions in rules distinguish rule identities.',
]


def make_tasks():
    def case(rules, budget, text='', n=1, start=0):
        return dict(n=n,start=start,rules=rules,budget=budget,text=text)
    inputs = [
        case([], 7),
        case([[0,[],1,2]],0),
        case([[0,[],1,2]],1),
        case([[0,['a'],2,-3]],1,'a'),
        case([[0,['a'],2,-3]],2,'a'),
        case([[0,[0],1,-2],[0,[],1,3]],7),
        case([[0,[0,0],1,-1],[0,[],1,2],[0,['a'],1,4]],7,'a'),
        case([[0,['a'],1,2],[0,['a'],1,-3]],2,'a'),
        case([[0,[1],1,0],[1,[0],1,-2],[1,[],1,1]],7,'',2),
        case([[0,[1,2],1,0],[1,[],2,-1],[2,['b'],2,3]],5,'b',3),
        case([[0,[1,2],1,0],[1,['a'],1,0],[2,['b'],1,0]],3,'ba',3),
        case([[0,[0,0],1,0],[0,['a'],1,0],[0,['b'],1,0]],7,'abba'),
        case([[0,[0],1,-5],[0,['b'],1,5]],7,'a'),
        case([[0,[1],3,1],[1,['a'],3,-4]],6,'a',2),
    ]
    rng = random.Random(22021)
    for _ in range(6):
        n = rng.randint(1,3)
        rules = []
        for j in range(rng.randint(2,6)):
            rhs = rng.choice([[],['a'],['b'],[rng.randrange(n)],[rng.randrange(n),rng.randrange(n)]])
            rules.append([rng.randrange(n),rhs,rng.randint(1,3),rng.randint(-5,5)])
        inputs.append(case(rules,rng.randint(1,7),''.join(rng.choice('ab') for j in range(rng.randint(0,4))),n,rng.randrange(n)))
    specs = [
        ('budget_parse_cost','development',PARSE,[
            'Return the minimum total rule cost over permitted trees whose yield equals text exactly, as an integer, or None if there is no such tree.',
            'Different resources may yield the same text, and signed rule costs do not change the positive resource restriction.']),
        ('bounded_derivation_count','heldout',COUNT,[
            'Return as an integer the number of permitted trees whose yield equals text exactly, reduced modulo 1000000007; return zero if there is no such tree.',
            'Two trees are distinct if their ordered tree structures or the rule identity at any corresponding occurrence differ; identical duplicate entries still give distinct choices, and costs have no effect on counting.']),
        ('budget_grammar_edit_cost','heldout',EDIT,[
            'For each permitted tree yield, measure the unit Levenshtein distance from text to that yield: insertion of one character, deletion of one character, and substitution of one character each cost one, while retaining an equal character costs zero.',
            'Return the minimum such distance as an integer, or None if no permitted tree exists; rule costs and the number of distinct trees have no effect on this result, and transposition is not an operation.'])]
    tasks = []
    for name, role, source, extra in specs:
        clauses = BASE_CLAUSES[:]
        cases = [[data, oracle(name, data)] for data in inputs]
        if name == 'bounded_derivation_count':
            clauses[4] = 'Budget is between 0 and 16 inclusive; text is a string of zero through seven characters, all from "ab".'
            data = case([[0,[0],1,0]] * 5 + [[0,[],1,0]], 16)
            cases.append([data, sum(5**depth for depth in range(16)) % 1000000007])
        tasks.append(dict(id=name, function=name, family='F2', role=role,
                          clauses=clauses+extra+['Do not modify the argument or any nested object.'],
                          cases=cases, reference=textwrap.dedent(source)))
    return tasks
