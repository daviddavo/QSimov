import numpy as np
import structures.funmatrix as fm
from structures.qgate import _getMatrix
import ctypes as ct

c_double_p = ct.POINTER(ct.c_double)

# Lib C functions
_libc = ct.cdll.msvcrt
free = _libc.free
free.argtypes = [ct.c_void_p]
free.restype = ct.c_void_p

__qsimov__ = ct.CDLL("libqsimov.dll")
__new_QRegistry__ = __qsimov__.new_QRegistry
__new_QRegistry__.argtypes = [ct.c_uint]
__new_QRegistry__.restype = ct.c_void_p

__cToString__ = __qsimov__.QR_toString
__cToString__.argtypes = [ct.c_void_p]
__cToString__.restype = ct.c_char_p

__cApplyGate__ = __qsimov__.applyGate
__cApplyGate__.argtypes = [ct.c_void_p, ct.c_void_p]
__cApplyGate__.restype = ct.c_int

__cBlochCoords__ = __qsimov__.blochCoords
__cBlochCoords__.argtypes = [ct.c_void_p]
__cBlochCoords__.restype = c_double_p

__cHopfCoords__ = __qsimov__.hopfCoords
__cHopfCoords__.argtypes = [ct.c_void_p]
__cHopfCoords__.restype = c_double_p

__cMeasure__ = __qsimov__.measure
__cMeasure__.argtypes = [ct.c_void_p, ct.POINTER(ct.c_int), ct.c_int, ct.POINTER(ct.c_int), ct.c_int]
__cMeasure__.restype = ct.c_int

__cGetState__ = __qsimov__.getState
__cGetState__.argtypes = [ct.c_void_p]
__cGetState__.restype = c_double_p

__cSetState__ = __qsimov__.setState
__cSetState__.argtypes = [ct.c_void_p, c_double_p, ct.c_int]
__cSetState__.restype = ct.c_int

__cGetNQubits__ = __qsimov__.getNQubits
__cGetNQubits__.argtypes = [ct.c_void_p]
__cGetNQubits__.restype = ct.c_int

__cGetSize__ = __qsimov__.getSize
__cGetSize__.argtypes = [ct.c_void_p]
__cGetSize__.restype = ct.c_int

class QRegistry:
    def __init__(self, nqbits, **kwargs):
        # nqbits -> number of QuBits in the registry.
        # Seed for the Pseudo Random Number Generation can be specified with seed = <seed> as an argument.
        self.reg = __new_QRegistry__(nqbits)

    def getSize(self):
        return int(__cGetSize__(self.reg))

    def getNQubits(self):
        return int(__cGetNQubits__(self.reg))

    def toString(self):
        return __cToString__(self.reg)

    def measure(self, msk, remove = False): # List of numbers with the QuBits that should be measured. 0 means not measuring that qubit, 1 otherwise. remove = True if you want to remove a QuBit from the registry after measuring
        nqubits = self.getNQubits()
        if (type(msk) != list or len(msk) != nqubits or \
            not all(type(num) == int and (num == 0 or num == 1) for num in msk)):
            raise ValueError('Not valid mask')
        mask = []
        for i in range(nqubits):
            if msk[i] == 1:
                mask.append(i)
        if (not all(num < nqubits and num > -1 for num in mask)):
            raise ValueError('Out of range')

        nq = len(mask)
        int_array = ct.c_int * nq
        result = int_array(*[0 for i in mask])
        rem = 0
        if (remove):
            rem = 1
        if int(__cMeasure__(self.reg, int_array(*mask), ct.c_int(nq), result, ct.c_int(rem))) == 0:
            print("Error measuring!")
        else:
            return list(result)

    def applyGate(self, *gates): # Applies a quantum gate to the registry.
        gate = _getMatrix(gates[0])
        for g in list(gates)[1:]:
            gate = fm.kron(gate, _getMatrix(g))

        if int(__cApplyGate__(self.reg, gate)) == 0:
            print("Error applying gate!")

    def getState(self):
        rawState = __cGetState__(self.reg)
        size = self.getSize()
        state = np.array([complex(rawState[i], rawState[i + size]) for i in range(size)])
        free(rawState)
        return state

    def setState(self, newState, nqubits):
        size = 2 << (nqubits - 1) # 2^n_qubits
        statetype = ct.c_double * (size * 2)
        cstate = statetype(*[newState[i].real if i < size else newState[i - size].imag for i in range(size * 2)])
        result = __cSetState__(self.reg, cstate, ct.c_int(nqubits)) == 1

        return result

    def densityMatrix(self):
        return np.dot(ket(self.state), bra(self.state))

    def vnEntropy(self, **kwargs):
        base = kwargs.get('base', "e")
        #dm = self.densityMatrix()
        #evalues, m = np.linalg.eig(dm)
        entropy = 0
        #for e in evalues:
        #    if e != 0:
        #        entropy += e * np.log(e)
        for amp in self.state[0]:
            p = cm.polar(amp)[0]**2
            if p > 0:
                if base == "e":
                    entropy += p * np.log(p)
                elif type(base) == int or type(base) == float:
                    entropy += p * np.log(p)/np.log(base)
        return -entropy

def _calculateState(tnum, cnum, size, fun):
    indexes = [i for i in range(cnum, size, tnum)]
    return [(index, fun(index, 0)) for index in indexes]

def prob(q, x): # Devuelve la probabilidad de obtener x al medir el qbit q
    p = 0
    if (x < q.size):
        p = cm.polar(q[0,x])[0]**2
    return p

def bra(v): # Devuelve el vector pasado como parametro en forma de fila conjugado. <v|
    b = v[:]
    s = v.shape
    if s[0] != 1:
        b = np.matrix.getH(b)
    else:
        b = np.conjugate(b)
    return b

def ket(v): # Devuelve el vector pasado como parametro en forma de columna. |v>
    k = v[:]
    s = v.shape
    if s[1] != 1:
        k = np.transpose(k)
    return k

def superposition(x, y): # Devuelve el estado compuesto por los dos QuBits.
    z = np.kron(x, y)
    normalize(z)
    return z

def normalize(state): # Funcion que asegura que se cumpla la propiedad que dice que |a|^2 + |b|^2 = 1 para cualquier QuBit. Si no se cumple, modifica el QuBit para que la cumpla si se puede.
    sqs = 0
    for i in range(0, state.size):
        sqs += cm.polar(state[0, i])[0]**2
    sqs = np.sqrt(sqs)
    if (sqs == 0):
        raise ValueError('Impossible QuBit')
    if (sqs != 1):
        for bs in state:
            bs /= sqs

def QBit(a,b): # Devuelve un QuBit con a y b. q = a|0> + b|1>, con a y b complejos
    q = np.array([a,b], dtype=complex)
    q.shape = (1,2)
    normalize(q)
    return q

def QZero(): # Devuelve un QuBit en el estado 0
    q = np.array([complex(1,0),complex(0,0)])
    q.shape = (1,2)
    return q

def QOne(): # Devuelve un QuBit en el estado 1
    q = np.array([complex(0,0),complex(1,0)])
    q.shape = (1,2)
    return q
