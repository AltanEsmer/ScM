def hopcroft_karp(graph, n, m):
	assert n == len(graph)
	match1 = [-1] * n
	match2 = [-1] * m
	for node in range(n):
		for nei in graph[node]:
			if match2[nei] == -1:
				match1[node] = nei
				match2[nei] = node
				break
	while 1:
		bfs = [node for node in range(n) if match1[node] == -1]
		depth = [-1] * n
		for node in bfs:
			depth[node] = 0
		for node in bfs:
			for nei in graph[node]:
				next_node = match2[nei]
				if next_node == -1:
					break
				if depth[next_node] == -1:
					depth[next_node] = depth[node] + 1
					bfs.append(next_node)
			else:
				continue
			break
		else:
			break
		pointer = [len(c) for c in graph]
		dfs = [node for node in range(n) if depth[node] == 0]
		while dfs:
			node = dfs[-1]
			while pointer[node]:
				pointer[node] -= 1
				nei = graph[node][pointer[node]]
				next_node = match2[nei]
				if next_node == -1:
					while nei != -1:
						node = dfs.pop()
						(match2[nei], match1[node], nei) = (node, nei, match1[node])
					break
				elif depth[node] + 1 == depth[next_node]:
					dfs.append(next_node)
					break
			else:
				dfs.pop()
	return (match1, match2)

def getMatchCounts(roads, days, n):
	adj = [[] for _ in range(n)]
	for (u, v, d) in roads:
		if d <= days:
			adj[u].append(v)
	matchCounts = n - hopcroft_karp(adj, n, n)[0].count(-1)
	return matchCounts

def main():
	(n, m) = readIntArr()
	roads = []
	for _ in range(m):
		(u, v, d) = readIntArr()
		u -= 1
		v -= 1
		roads.append([u, v, d])
	if getMatchCounts(roads, 1000000000.0 + 1, n) < n:
		print(-1)
	else:
		days = 0
		b = 1000000000
		while b > 0:
			while getMatchCounts(roads, days + b, n) < n:
				days += b
			b //= 2
		days += 1
		print(days)
	return
import sys
input = sys.stdin.buffer.readline

def oneLineArrayPrint(arr):
	print(' '.join([str(x) for x in arr]))

def multiLineArrayPrint(arr):
	print('\n'.join([str(x) for x in arr]))

def multiLineArrayOfArraysPrint(arr):
	print('\n'.join([' '.join([str(x) for x in y]) for y in arr]))

def readIntArr():
	return [int(x) for x in input().split()]

def makeArr(defaultValFactory, dimensionArr):
	dv = defaultValFactory
	da = dimensionArr
	if len(da) == 1:
		return [dv() for _ in range(da[0])]
	else:
		return [makeArr(dv, da[1:]) for _ in range(da[0])]

def queryInteractive(i, j):
	print('? {} {}'.format(i, j))
	sys.stdout.flush()
	return int(input())

def answerInteractive(ans):
	print('! {}'.format(' '.join([str(x) for x in ans])))
	sys.stdout.flush()
inf = float('inf')
MOD = 10 ** 9 + 7
for _abc in range(1):
	main()
