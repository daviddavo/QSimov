import numpy as np
from cmath import exp, pi

class FunctionalMatrix(object):
	def __init__(self, function, shape, decimals=20):
		self.f = function
		if (type(shape) != tuple):
			shape = (int(shape), int(shape))
		self.shape = shape
		self.size = shape[0] * shape[1]
		self.dec = decimals

	def __len__(self):
		return self.shape[0]

	def __getitem__(self, key):
		if (type(key) == int):
			if (key >= self.shape[0]):
				raise IndexError("index " + str(key) + " is out of bounds for axis 0 with shape " + str(self.shape[0]))
			if (key < 0):
				key = self.shape[0] + key
			return [np.around(self.f(key, i), decimals=self.dec) for i in range(self.shape[1])]
		elif (type(key) == slice):
			start = key.start if key.start != None else 0
			if (start < 0):
				start = self.shape[0] + start
			stop = key.stop if key.stop != None else self.shape[0]
			if (stop < 0):
				stop = self.shape[0] + stop
			step = key.step if key.step != None else 1
			return [self.__getitem__(i) for i in range(start, stop, step)]
		elif (type(key) == tuple):
			if (type(key[1]) == None):
				return self.__getitem__(key[0])
			elif (type(key[0]) == None):
				if (type(key[1]) == int):
					if (key[1] >= self.shape[1]):
						raise IndexError("index " + str(key[1]) + " is out of bounds for axis 1 with shape " + str(self.shape[1]))
					if (key[1] < 0):
						key = (key[0], self.shape[1] + key[1])
					return [np.around(self.f(i, key[1]), decimals=self.dec) for i in range(self.shape[0])]
				elif (type(key[1]) == slice):
					start = key[1].start if key[1].start != None else 0
					if (start < 0):
						start = self.shape[1] + start
					stop = key[1].stop if key[1].stop != None else self.shape[1]
					if (stop < 0):
						stop = self.shape[1] + stop
					step = key[1].step if key[1].step != None else 1
					return [self.__getitem__(None, i) for i in range(start, stop, step)]
			elif (type(key[0]) == int and type(key[1]) == int):
				if (key[0] >= self.shape[0]):
					raise IndexError("index " + str(key[0]) + " is out of bounds for axis 0 with shape " + str(self.shape[0]))
				if (key[1] >= self.shape[1]):
					raise IndexError("index " + str(key[1]) + " is out of bounds for axis 1 with shape " + str(self.shape[1]))
				if (key[0] < 0):
					key = (self.shape[0] + key[0], key[1])
				if (key[1] < 0):
					key = (key[0], self.shape[1] + key[1])
				return self.f(key[0], key[1])
			elif (type(key[0]) == slice and type(key[1]) == int):
				if (key[1] >= self.shape[1]):
					raise IndexError("index " + str(key[1]) + " is out of bounds for axis 1 with shape " + str(self.shape[1]))
				start = key[0].start if key[0].start != None else 0
				if (start < 0):
					start = self.shape[0] + start
				stop = key[0].stop if key[0].stop != None else self.shape[0]
				if (stop < 0):
					stop = self.shape[0] + stop
				step = key[0].step if key[0].step != None else 1
				if (key[1] < 0):
					key = (key[0], self.shape[1] + key[1])
				return [self.f(i, key[1]) for i in range(start, stop, step)]
			elif (type(key[0]) == int and type(key[1]) == slice):
				if (key[0] >= self.shape[0]):
					raise IndexError("index " + str(key[0]) + " is out of bounds for axis 0 with shape " + str(self.shape[0]))
				start = key[1].start if key[1].start != None else 0
				if (start < 0):
					start = self.shape[1] + start
				stop = key[1].stop if key[1].stop != None else self.shape[1]
				if (stop < 0):
					stop = self.shape[1] + stop
				step = key[1].step if key[1].step != None else 1
				if (key[0] < 0):
					key = (self.shape[0] + key[0], key[1])
				return [self.f(key[0], i) for i in range(start, stop, step)]
			elif (type(key[0]) == slice and type(key[1]) == slice):
				start0 = key[0].start if key[0].start != None else 0
				if (start0 < 0):
					start0 = self.shape[0] + start0
				stop0 = key[0].stop if key[0].stop != None else self.shape[0]
				if (stop0 < 0):
					stop0 = self.shape[0] + stop0
				step0 = key[0].step if key[0].step != None else 1
				start1 = key[1].start if key[1].start != None else 0
				if (start1 < 0):
					start1 = self.shape[1] + start1
				stop1 = key[1].stop if key[1].stop != None else self.shape[1]
				if (stop1 < 0):
					stop1 = self.shape[1] + stop1
				step1 = key[1].step if key[1].step != None else 1
				return [[self.f(i, j) for i in range(start0, stop0, step0)] for j in range(start1, stop1, step1)]

	def __mul__(self, other): # Element-wise multiplication
		return ewmul(self, other)

	def __imul__(self, other): # Element-wise multiplication
		return ewmul(self, other)

	def __rmul__(self, other): # Element-wise multiplication
		return ewmul(other, self)

	def __matmul__(self, other): # Matrix multiplication
		return matmul(self, other)

	def __imatmul__(self, other): # Matrix multiplication
		return matmul(self, other)

	def __rmatmul__(self, other): # Matrix multiplication
		return matmul(other, self)

	def transpose(self):
		return FunctionalMatrix(lambda i, j: self.f(j, i), (self.shape[1], self.shape[0]))

	def conjugate(self):
		return FunctionalMatrix(lambda i, j: np.conjugate(self.f(i, j)), self.shape)

	def dagger(self):
		return FunctionalMatrix(lambda i, j: np.conjugate(self.f(j, i)), (self.shape[1], self.shape[0]))

def isNumber(n):
	types = [int, float, complex, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64, np.float16, np.float32, np.float64, np.complex64, np.complex128]
	return (type(n) in types)

def ewmul(a, b):
	anum = isNumber(a)
	bnum = isNumber(b)
	if (type(a) == FunctionalMatrix):
		asi = a.shape
		af = a.f
	elif (type(a) == np.ndarray):
		if (len(a.shape) == 1):
			a.shape = (1, a.shape[0])
		asi = a.shape
		af = lambda i, j: a[i][j]
	elif (type(a) == list):
		asi = (len(a), len(a[0]))
		af = lambda i, j: a[i][j]
	elif (not anum):
		return NotImplemented

	if (type(b) == FunctionalMatrix):
		bsi = b.shape
		bf = b.f
	elif (type(b) == np.ndarray):
		if (len(b.shape) == 1):
			b.shape = (1, b.shape[0])
		bsi = b.shape
		bf = lambda i, j: b[i][j]
	elif (type(b) == list):
		bsi = (len(b), len(b[0]))
		bf = lambda i, j: b[i][j]
	elif (not bnum):
		return NotImplemented

	if (anum and bnum):
		return a*b
	elif (anum and not bnum):
		return FunctionalMatrix(lambda i, j: a * bf(i, j), bsi)
	elif (not anum and bnum):
		return FunctionalMatrix(lambda i, j: af(i, j) * b, asi)

	if (asi == bsi):
		return FunctionalMatrix(lambda i, j: af(i, j) * bf(i, j), asi)
	elif (asi[0] == 1 and bsi[1] == 1):
		return matmul(b, a)
	elif (asi[1] == 1 and bsi[0] == 1):
		return matmul(a, b)
	else:
		raise ValueError("operands could not be broadcast together with shapes " + str(asi) + " " + str(bsi))

def matmul(a, b, spec=False):
	if (type(a) == FunctionalMatrix):
		asi = a.shape
		af = a.f
	elif (type(a) == np.ndarray):
		if (len(a.shape) == 1):
			a.shape = (1, a.shape[0])
		asi = a.shape
		af = lambda i, j: a[i][j]
	elif (type(a) == list):
		asi = (len(a), len(a[0]))
		af = lambda i, j: a[i][j]
	elif (isNumber(a)):
		return a*b
	else:
		return NotImplemented

	if (type(b) == FunctionalMatrix):
		bsi = b.shape
		bf = b.f
	elif (type(b) == np.ndarray):
		if (len(b.shape) == 1):
			b.shape = (1, b.shape[0])
		bsi = b.shape
		bf = lambda i, j: b[i][j]
	elif (type(b) == list):
		bsi = (len(b), len(b[0]))
		bf = lambda i, j: b[i][j]
	elif (isNumber(b)):
		return a*b
	else:
		return NotImplemented

	if (asi[1] != bsi[0]):
		raise ValueError("shapes " + str(asi) + " and " + str(bsi) + " not aligned: " + str(asi[1]) + " (dim 1) != " + str(bsi[0]) + " (dim 0)")

	if (spec and asi[0] == asi[1] and bsi[0] == bsi[1] and asi[0] > 4 and 2**int(np.log(asi[0])/np.log(2)) == asi[0]):
		halv = asi[0]/2
		
		a11 = FunctionalMatrix(af, halv)
		a12 = FunctionalMatrix(lambda i, j: af(i, j+halv), halv)
		a21 = FunctionalMatrix(lambda i, j: af(i+halv, j), halv)
		a22 = FunctionalMatrix(lambda i, j: af(i+halv, j+halv), halv)

		b11 = FunctionalMatrix(bf, halv)
		b12 = FunctionalMatrix(lambda i, j: bf(i, j+halv), halv)
		b21 = FunctionalMatrix(lambda i, j: bf(i+halv, j), halv)
		b22 = FunctionalMatrix(lambda i, j: bf(i+halv, j+halv), halv)

		a1122 = FunctionalMatrix(lambda i, j: af(i, j) + af(i+halv, j+halv), halv)
		b1122 = FunctionalMatrix(lambda i, j: bf(i, j) + bf(i+halv, j+halv), halv)
		a2111 = FunctionalMatrix(lambda i, j: af(i+halv, j) - af(i, j), halv)
		b1112 = FunctionalMatrix(lambda i, j: bf(i, j) + bf(i, j+halv), halv)
		a1222 = FunctionalMatrix(lambda i, j: af(i, j+halv) - af(i+halv, j+halv), halv)
		b2122 = FunctionalMatrix(lambda i, j: bf(i+halv, j) + bf(i+halv, j+halv), halv)

		M1 = matmul(a1122, b1122, spec=True)
		M2 = matmul(FunctionalMatrix(lambda i, j: af(i+halv, j) + af(i+halv, j+halv), halv), b11, spec=True)
		M3 = matmul(a11, FunctionalMatrix(lambda i, j: bf(i, j+halv) - bf(i+halv, j+halv), halv), spec=True)
		M4 = matmul(a22, FunctionalMatrix(lambda i, j: bf(i+halv, j) - bf(i, j), halv), spec=True)
		M5 = matmul(FunctionalMatrix(lambda i, j: af(i, j) + af(i, j+halv), halv), b22, spec=True)
		M6 = matmul(a2111, b1112, spec=True)
		M7 = matmul(a1222, b2122, spec=True)
		def muuu(i, j):
			if i < halv and j < halv:
				return M1.f(i, j) + M4.f(i, j) - M5.f(i, j) + M7.f(i, j)
			elif i < halv:
				return M3.f(i, j) + M5.f(i, j)
			elif j < halv:
				return M2.f(i, j) + M4.f(i, j)
			else:
				return M1.f(i, j) - M2.f(i, j) + M3.f(i, j) + M6.f(i, j)
		return FunctionalMatrix(muuu, asi)
	else:
		return FunctionalMatrix(lambda i, j: sum(af(i, k) * bf(k, j) for k in range(asi[1])), (asi[0], bsi[1]))

def kron(a, b): # Kronecker Product
	if (type(a) == FunctionalMatrix):
		asi = a.shape
		af = a.f
	elif (type(a) == np.ndarray):
		if (len(a.shape) == 1):
			a.shape = (1, a.shape[0])
		asi = a.shape
		af = lambda i, j: a[i][j]
	elif (type(a) == list):
		asi = (len(a), len(a[0]))
		af = lambda i, j: a[i][j]
	elif (isNumber(a)):
		return a*b
	else:
		return NotImplemented

	if (type(b) == FunctionalMatrix):
		bsi = b.shape
		bf = b.f
	elif (type(b) == np.ndarray):
		if (len(b.shape) == 1):
			b.shape = (1, b.shape[0])
		bsi = b.shape
		bf = lambda i, j: b[i][j]
	elif (type(b) == list):
		bsi = (len(b), len(b[0]))
		bf = lambda i, j: b[i][j]
	elif (isNumber(b)):
		return a*b
	else:
		return NotImplemented

	return FunctionalMatrix(lambda i, j: af(i//bsi[0], j//bsi[1]) * bf(i%bsi[0], j%bsi[1]), (asi[0] * bsi[0], asi[1] * bsi[1]))
