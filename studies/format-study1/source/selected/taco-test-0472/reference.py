import sys

def solve(io):
	N = io.readInt()
	boards = [None] * 4
	for i in range(0, 4):
		boards[i] = io.readStringArray(N)
	best = 1234567890
	for v in [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]:
		best = min(best, delta(boards[v[0][0]], '0') + delta(boards[v[0][1]], '0') + delta(boards[v[1][0]], '1') + delta(boards[v[1][1]], '1'), delta(boards[v[0][0]], '1') + delta(boards[v[0][1]], '1') + delta(boards[v[1][0]], '0') + delta(boards[v[1][1]], '0'))
	io.println(+best)

def delta(b, tl):
	cnt = 0
	for i in range(0, len(b)):
		for j in range(0, len(b[i])):
			if ((i + j) % 2 == 0) != (b[i][j] == tl):
				cnt += 1
	return cnt

class IO:
	input = None
	output = None
	raw = ''
	buf = []
	pos = 0

	def __init__(self, inputStream, outputStream):
		self.input = inputStream
		self.output = outputStream

	def readToBuffer(self):
		self.raw = self.input.readline().rstrip('\n')
		self.buf = self.raw.split()
		self.pos = 0

	def readString(self):
		while self.pos == len(self.buf):
			self.readToBuffer()
		ans = self.buf[self.pos]
		self.pos += 1
		return ans

	def readInt(self):
		return int(self.readString())

	def readFloat(self):
		return float(self.readString())

	def readStringArray(self, N, offset=0):
		arr = [None] * offset
		for _ in range(0, N):
			arr.append(self.readString())
		return arr

	def readIntArray(self, N, offset=0):
		arr = [None] * offset
		for _ in range(0, N):
			arr.append(self.readInt())
		return arr

	def readFloatArray(self, N, offset=0):
		arr = [None] * offset
		for _ in range(0, N):
			arr.append(self.readFloat())
		return arr

	def readLine(self):
		while self.pos == len(self.buf):
			self.readToBuffer()
		if self.pos > 0:
			raise ValueError('Cannot call readline in the middle of a line.')
		return self.raw

	def prints(self, s):
		self.output.write(str(s))

	def println(self, s):
		self.prints(s)
		self.prints('\n')

	def flushOutput(self):
		self.output.flush()
pythonIO = IO(sys.stdin, sys.stdout)
solve(pythonIO)
pythonIO.flushOutput()
