"""Statement-derived shape/domain checks; never execute reference solutions."""

class Tokens:
    def __init__(self, text):
        self.tokens = text.split()
        self.position = 0

    def take(self):
        if self.position == len(self.tokens):
            raise ValueError('Input truncated')
        value = self.tokens[self.position]
        self.position += 1
        return value

    def integer(self, low, high):
        raw = self.take()
        try:
            value = int(raw)
        except ValueError:
            raise ValueError(f'Expected integer, got {raw!r}') from None
        if not low <= value <= high:
            raise ValueError(f'Integer {value} outside [{low}, {high}]')
        return value

    def binary(self, length=None):
        value = self.take()
        if not value or set(value) - set('01') or (length is not None and len(value) != length):
            raise ValueError('Invalid binary string or length')
        return value

    def done(self):
        if self.position != len(self.tokens):
            raise ValueError('Unexpected trailing tokens')


def integers_output(text, bounds):
    output = Tokens(text)
    for low, high in bounds:
        output.integer(low, high)
    output.done()


def tree(tokens, size):
    parents = list(range(size))
    def find(vertex):
        while parents[vertex] != vertex:
            parents[vertex] = parents[parents[vertex]]
            vertex = parents[vertex]
        return vertex
    for _ in range(size - 1):
        left = tokens.integer(1, size) - 1
        right = tokens.integer(1, size) - 1
        a, b = find(left), find(right)
        if a == b:
            raise ValueError('Graph contains cycle, self-loop, or duplicate edge')
        parents[a] = b


def validate(row_index, input_text, expected_text):
    tokens = Tokens(input_text)
    bounds = []
    if row_index == 152:
        size = tokens.integer(1, 10**4)
        count = tokens.integer(1, 10**5)
        durations = set()
        for _ in range(count):
            tokens.integer(1, size)
            tokens.integer(1, size)
            durations.add(tokens.integer(1, 10**9))
        output = Tokens(expected_text)
        value = output.integer(-1, 10**9)
        if value != -1 and value not in durations:
            raise ValueError('Matching completion time must be a supplied road duration or -1')
        output.done()
    elif row_index == 339:
        size = tokens.integer(1, 5 * 10**5)
        values = [tokens.integer(1, 10**9) for _ in range(size)]
        if len(set(values)) != size:
            raise ValueError('Array values must be pairwise distinct')
        bounds = [(0, 10**9 + 6)]
    elif row_index == 466:
        size = tokens.integer(1, 10**5)
        count = tokens.integer(1, 10**5)
        for _ in range(size):
            tokens.integer(1, 10**6)
        for _ in range(count):
            kind = tokens.integer(1, 2)
            index = tokens.integer(1, size)
            tokens.integer(1, 10**6)
            if kind == 2:
                bounds.append((0, index))
    elif row_index == 581:
        count = tokens.integer(1, 1000)
        total = 0
        for _ in range(count):
            size = tokens.integer(2, 10**5)
            total += size
            tree(tokens, size)
            values = [tokens.integer(1, 10**9) for _ in range(size)]
            bounds.append((1, sum(values) - min(values)))
        if total > 5 * 10**5:
            raise ValueError('Sum of N exceeds 500000')
    elif row_index == 778:
        count = tokens.integer(1, 10**6)
        total = 0
        lengths = []
        for _ in range(count):
            horizontal = tokens.binary()
            vertical = tokens.binary()
            if not 1 <= len(horizontal) <= 10**5 or not 1 <= len(vertical) <= 10**5:
                raise ValueError('Terminal row/column length outside bounds')
            queries = tokens.integer(1, 10**5)
            total += len(horizontal) + len(vertical) + queries
            lengths.append(queries)
            for _ in range(queries):
                tokens.integer(1, len(vertical))
                tokens.integer(1, len(horizontal))
        if total > 10**6:
            raise ValueError('Sum of N+M+Q exceeds 1000000')
        output = Tokens(expected_text)
        for length in lengths:
            output.binary(length)
        output.done()
    elif row_index == 979:
        count = tokens.integer(1, 10**5)
        total_size = total_queries = 0
        for _ in range(count):
            size = tokens.integer(1, 10**5)
            tokens.integer(1, size)
            queries = tokens.integer(1, 10**5)
            total_size += size
            total_queries += queries
            tokens.binary(size)
            for _ in range(queries):
                left = tokens.integer(1, size)
                right = tokens.integer(left, size)
                length = right - left + 1
                bounds.append((length, length * (length + 1) // 2))
        if total_size > 10**5 or total_queries > 10**5:
            raise ValueError('Sum of N or Q exceeds 100000')
    else:
        raise ValueError(f'No statement validator for HARD row {row_index}')
    tokens.done()
    if row_index not in (152, 778):
        integers_output(expected_text, bounds)
