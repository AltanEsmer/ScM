import sys
from math import gcd
sys.setrecursionlimit(10 ** 9)
for _ in range(int(input())):
	n = int(input())
	adj = [[] for i in range(n)]
	for i in range(n - 1):
		(a, b) = map(int, input().split())
		adj[a - 1].append(b - 1)
		adj[b - 1].append(a - 1)
	v = list(map(int, input().split()))

	def solve(i, p):
		g[i] = v[i]
		for j in adj[i]:
			if j != p:
				solve(j, i)
				g[i] = gcd(g[i], g[j])
	g = [0] * n
	solve(0, -1)

	def dfs(i, p, gp):
		d = gp
		a = []
		b = []
		child = []
		for j in adj[i]:
			if j != p:
				d += g[j]
				a.append(g[j])
				b.append(g[j])
				child.append(j)
		ans[0] = max(ans[0], d)
		t = len(a)
		for j in range(1, t):
			a[j] = gcd(a[j], a[j - 1])
		for j in reversed(range(t - 1)):
			b[j] = gcd(b[j], b[j + 1])
		for k in range(t):
			ngp = gcd(gp, v[i])
			if k > 0:
				ngp = gcd(ngp, a[k - 1])
			if k < t - 1:
				ngp = gcd(ngp, b[k + 1])
			dfs(child[k], i, ngp)
	ans = [0]
	dfs(0, -1, 0)
	print(ans[0])
