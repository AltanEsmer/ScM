cases = int(input())
for _ in range(cases):
	(n, k, q) = list(map(int, input().split()))
	s = input().strip()
	far = [0] * n
	sumfar = [0] * (n + 1)
	count0 = count1 = 0
	j = -1
	for i in range(n):
		while j < n and count0 <= k and (count1 <= k):
			j += 1
			if j == n:
				break
			if s[j] == '0':
				count0 += 1
			else:
				count1 += 1
		far[i] = j
		if s[i] == '0':
			count0 -= 1
		else:
			count1 -= 1
	for i in range(1, n + 1):
		sumfar[i] = sumfar[i - 1] + far[i - 1]
	for i in range(q):
		(l, r) = tuple(map(int, input().split()))
		l -= 1
		r -= 1
		(lo, hi) = (l, r)
		while lo < hi:
			mid = (lo + hi) // 2
			if far[mid] <= r:
				lo = mid + 1
			else:
				hi = mid
		k = lo - 1
		ans = sumfar[k + 1] - sumfar[l] + (r + 1) * (r - k) - (r * (r + 1) // 2 - l * (l - 1) // 2)
		print(ans)
