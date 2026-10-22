import sys
(n, m) = map(int, input().split())
adj = [[] for i in range(n)]
a = list(map(int, input().split()))
for i in range(n - 1):
	(u, v) = map(int, input().split())
	adj[v - 1].append(u - 1)
	adj[u - 1].append(v - 1)

def dfs(v, c):
	st = [[v, c, -1]]
	ans = 0
	while len(st):
		(v, c, f) = st.pop()
		if c > m:
			continue
		if len(adj[v]) == 1 and v != 0:
			ans += 1
		for u in adj[v]:
			if u != f:
				st.append([u, (c + 1) * a[u], v])
	return ans
print(dfs(0, a[0]))
