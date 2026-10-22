(n, b) = [int(x) for x in input().split()]
ni = [0 for _ in range(n + 1)]
for i in range(1, n + 1):
	ni[i] = int(input())
dp = [0 for _ in range(b + 1)]
cum = [0 for _ in range(n + 2)]
dp[b - 1] = 1
dp[b] = 0
cum[b] = 1
cum[b - 1] = 2
md = int(1000000000.0 + 7)
for i in range(b - 2, 0, -1):
	dp[i] = (cum[i + 1] - cum[i + ni[i] + 1] + md) % md
	cum[i] = (dp[i] + cum[i + 1]) % md
q = int(input())
for i in range(q):
	qu = int(input())
	print(dp[qu])
