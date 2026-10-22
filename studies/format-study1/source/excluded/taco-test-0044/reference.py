for _ in range(int(input())):
	n = int(input())
	d = list(map(int, input().split()))
	d = sorted(d)
	if n == 1:
		print(d[n - 1])
		continue
	l = [0]
	for i in range(n - 2, -1, -1):
		l.append(d[i] - d[n - 1])
	c = n - 1
	S = sum(l)
	ans = S
	for i in range(n - 2, 0, -1):
		dis = (d[i] - d[i + 1]) * c
		S -= dis
		ans += S
		c -= 1
	for i in range(1, n):
		ans += d[i] - d[i - 1]
	print(ans)
