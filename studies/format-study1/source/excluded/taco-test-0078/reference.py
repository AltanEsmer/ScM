from collections import Counter
for _ in range(int(input())):
	n = int(input())
	a = Counter([int(x) for x in input().strip().split()])
	a = [(x, y) for (x, y) in a.items()]
	a.sort(key=lambda x: x[0], reverse=True)
	(ans, i) = (0, 0)
	while ans < n / 2 and i < len(a):
		ans += a[i][1]
		i += 1
	print(ans)
