t = int(input())
for _ in range(t):
	r = input()
	c = input()
	m = len(r) + 1
	n = len(c) + 1
	a = {}
	if r[0] == '0' or c[0] == '0':
		a[1 * 1000000 + 1] = '1'
	else:
		a[1 * 1000000 + 1] = '0'
	for i in range(2, m):
		if r[i - 1] == '0' or a[1 * 1000000 + i - 1] == '0':
			a[1 * 1000000 + i] = '1'
		else:
			a[1 * 1000000 + i] = '0'
	for i in range(2, n):
		if c[i - 1] == '0' or a[(i - 1) * 1000000 + 1] == '0':
			a[i * 1000000 + 1] = '1'
		else:
			a[i * 1000000 + 1] = '0'
	for i in range(2, min(n, 5)):
		for j in range(2, m):
			if a[(i - 1) * 1000000 + j] == '0' or a[i * 1000000 + j - 1] == '0':
				a[i * 1000000 + j] = '1'
			else:
				a[i * 1000000 + j] = '0'
	for i in range(2, n):
		for j in range(2, min(m, 5)):
			if a[(i - 1) * 1000000 + j] == '0' or a[i * 1000000 + j - 1] == '0':
				a[i * 1000000 + j] = '1'
			else:
				a[i * 1000000 + j] = '0'
	q = int(input())
	s = ''
	for i in range(q):
		(x, y) = map(int, input().split())
		if x < 5 or y < 5:
			s = s + a[x * 1000000 + y]
		elif x == y:
			s = s + a[4 * 1000000 + 4]
		elif x > y:
			s = s + a[(x - (y - 4)) * 1000000 + 4]
		else:
			s = s + a[4 * 1000000 + y - (x - 4)]
	print(s)
