gstart = [0 for i in range(1000)]
gend = [0 for i in range(1000)]
gxor = [0 for i in range(1000)]
gid = [0 for i in range(10 ** 6 + 100)]
gcnt = [{} for j in range(1000)]
ps = [0 for i in range(10 ** 5 + 10)]

def buildSqrtDecomp(n):
	gsize = 1
	while gsize * gsize < n:
		gsize += 1
	ng = 0
	for i in range(0, n, gsize):
		gstart[ng] = i
		gend[ng] = i + gsize - 1
		ng += 1
	gend[ng - 1] = n - 1
	for g in range(ng):
		gxor[g] = 0
		for i in range(gstart[g], gend[g] + 1):
			if ps[i] in gcnt[g]:
				gcnt[g][ps[i]] += 1
			else:
				gcnt[g][ps[i]] = 1
			gid[i] = g
	return gsize
(n, q) = [int(c) for c in input().split()]
arr = [int(i) for i in input().split()]
currXor = 0
for i in range(len(arr)):
	currXor ^= arr[i]
	ps[i] = currXor
gsize = buildSqrtDecomp(n)
for _ in range(q):
	(op, i, x) = [int(c) for c in input().split()]
	if op == 1:
		i -= 1
		block_number = gid[i]
		c = arr[i] ^ x
		arr[i] = x
		for j in range(i, gend[block_number] + 1):
			gcnt[block_number][ps[j]] -= 1
			ps[j] ^= c
			if ps[j] in gcnt[block_number]:
				gcnt[block_number][ps[j]] += 1
			else:
				gcnt[block_number][ps[j]] = 1
		for j in range(gid[i] + 1, gsize + 1):
			gxor[j] ^= c
	else:
		i -= 1
		block_number = gid[i]
		ans = 0
		for j in range(gstart[block_number], i + 1):
			if ps[j] ^ gxor[block_number] == x:
				ans += 1
		for j in range(0, block_number):
			if x ^ gxor[j] in gcnt[j]:
				ans += gcnt[j][x ^ gxor[j]]
		print(ans)
