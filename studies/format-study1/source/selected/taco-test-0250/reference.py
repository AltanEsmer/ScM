def trailZero(x):
	x = str(x)
	count = 0
	for y in range(len(x) - 1, -1, -1):
		if x[y] != '0':
			return count
		count += 1
cases = int(input().strip())
nos = input().strip().split()
data = [4, 7]
curr = ['7', '4']
next = []
for x in range(9):
	for y in curr:
		next += [y + '4']
		next += [y + '7']
	data += [int(y) for y in next]
	curr = next
	next = []
data.sort()
for x in nos:
	y = int(x)
	while trailZero(y) < trailZero(4 * y):
		y *= 4
	print(y)
