import heapq as hp

def solve(heap, k):
	li = heap.copy()
	s = 0
	while k >= 2 and len(li) > 0:
		s += hp.heappop(li)
		k -= 2
	return -s
for _ in range(int(input())):
	(n, k) = map(int, input().strip().split())
	s = input()
	zeros = 0
	for ch in s:
		if ch == '0':
			zeros += 1
	if k < 1:
		print(zeros)
		continue
	l = 0
	while l < n and s[l] == '0':
		l += 1
	r = n - 1
	while r >= 0 and s[r] == '0':
		r -= 1
	if k < 2:
		print(zeros - max(l, n - r - 1))
		continue
	heap = []
	cnt = 0
	for i in range(l, r + 1):
		if s[i] == '0':
			cnt -= 1
		if s[i] == '1' and cnt < 0:
			hp.heappush(heap, cnt)
			cnt = 0
	x = solve(heap, k)
	y = solve(heap, k - 1)
	z = solve(heap, k - 2)
	ans = max(x, l + y, n - r - 1 + y, l + n - r - 1 + z)
	print(zeros - ans)
