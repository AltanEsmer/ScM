def solve():
	input()
	(n, k) = map(int, input().split())
	f = list(enumerate(list(map(lambda x: int(x) - 1, input().split()))))
	g = {i: [] for i in range(n)}
	for i in range(n - 1):
		(a, b) = map(int, input().split())
		a -= 1
		b -= 1
		g[a].append(b)
		g[b].append(a)
	needed = {}
	vlad = [0]
	visited = [False] * n
	friends = [-1] * n
	while len(vlad):
		nf = []
		for (i, f1) in f:
			if friends[f1] != -1:
				continue
			friends[f1] = i
			for e in g[f1]:
				nf.append((i, e))
		f = nf
		new_vlad = []
		for v in vlad:
			if friends[v] != -1:
				needed[friends[v]] = True
				continue
			if visited[v] == True:
				continue
			visited[v] = True
			if len(g[v]) == 1 and v != 0:
				return -1
			for e in g[v]:
				new_vlad.append(e)
		vlad = new_vlad
	return len(needed)
n = int(input())
for i in range(n):
	print(solve())
