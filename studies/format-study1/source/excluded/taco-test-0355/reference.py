t = int(input())
for _ in range(t):
	N = int(input())
	B = list(map(int, input().split()))
	total = ones = 0
	flag = 0
	for i in B:
		if i > 0:
			ones += 1
			total += i
		if i > 100:
			flag = 1
	if total - ones < 100 and total >= 100:
		ans = 'YES'
	else:
		ans = 'NO'
	print(ans)
