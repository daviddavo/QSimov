import numpy as np
import ctypes as ct
import platform as plat
import qsimov.connectors.parser as prs
import os
from collections.abc import Iterable
from qsimov.structures.measure import Measure
from os.path import sep

# DLL Load
if plat.system() == "Windows":
    extension = ".dll"
else:
    extension = ".so"
__rootfolder__ = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
__libfolder__ = __rootfolder__ + sep + "lib"
__qsimovpath__ = __libfolder__ + sep + "libqsimov" + extension
if hasattr(os, "add_dll_directory"):
    __qsimovpath__ = "libqsimov" + extension
__qsimov__ = ct.CDLL(__qsimovpath__)

c_double_p = ct.POINTER(ct.c_double)


class QGate(object):
    def __init__(self, name="UNNAMED", size=None):
        self.empty = True
        self.lines = []
        self.oplines = []
        self.freeindexes = None
        self.lastindex = -1
        self.name = name
        self.size = size

    '''
    def __getitem__(self, key):
        return self.getMatrix()[key]
    '''

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def addLine(self, *args, **kwargs):
        add_line = True
        offset = 0
        if "add_line" in kwargs:
            add_line = kwargs["add_line"]
        if "offset" in kwargs:
            offset = kwargs["offset"]
        if "controls" in kwargs:
            controls = kwargs["controls"]
        if "anticontrols" in kwargs:
            anticontrols = kwargs["anticontrols"]
        args = [_rebuildGateName(gate) for gate in args]
        # size = sum([getGateSize(gate) for gate in args])
        parties = _getParties(args)
        size = len(parties)
        if size > 0:
            if (self.empty):
                self.size = size
                self.empty = False
                self.freeindexes = [0 for i in range(size)]
            if (self.size != size):
                raise ValueError("This gate requires a " + str(self.size) + " QuBit gate. Received " + str(size) + " QuBit gate.")

            if add_line:
                self.lines += [args]
            for i in range(len(args)):
                arg = args[i]
                if arg is not None:
                    if offset > 0:
                        arg[1] = controls.union({control + offset for control in arg[1]})
                        arg[2] = anticontrols.union({acontrol + offset for acontrol in arg[2]})
                    if isinstance(arg[0], QGate):
                        for line in arg[0].oplines:
                            self.addLine(*[None for j in range(i)],
                                         *line,
                                         *[None for j in range(self.size - arg[0].size - i)],
                                         add_line=False, offset=i,
                                         controls=arg[1],
                                         anticontrols=arg[2])
                    else:
                        # print(arg)
                        parties = _getParties([arg if j == i else None for j in range(len(args))], ignore_empty=True)
                        num_targets = len(parties) - len(arg[1]) - len(arg[2])
                        # print("Parties:", parties)
                        # print("Target:", i)
                        freeindex = max([self.freeindexes[party] for party in parties])
                        skip = False
                        if freeindex > 0:
                            previousGate = self.oplines[freeindex-1][i]
                            if previousGate is not None and \
                               arg[0] == _invertStrGate(previousGate[0]) and \
                               arg[1] == previousGate[1] and arg[2] == previousGate[2]:
                                self.oplines[freeindex-1] = self.oplines[freeindex-1][:i] + [None for j in range(num_targets)] + self.oplines[freeindex-1][i+1:]
                                if len(self.oplines[freeindex-1]) == 0 or \
                                   all([elem is None or elem == "I"
                                        for elem in self.oplines[freeindex-1]]):
                                    del self.oplines[freeindex-1]
                                self.recalculate_free()
                                skip = True
                        if not skip:
                            for party in parties:
                                self.freeindexes[party] = freeindex + 1
                            if freeindex > self.lastindex:
                                self.oplines.append([None for i in range(self.size)])
                                self.lastindex += 1
                            self.oplines[freeindex][i] = arg
                            while num_targets > 1:
                                del self.oplines[freeindex][i+1]
                                num_targets -= 1
        else:
            print("No gates. Just Monika.")

    def recalculate_free(self):
        for party in range(self.size):
            self.freeindexes[party] = 0
        self.lastindex = -1
        for i in range(len(self.oplines)):
            line = self.oplines[i]
            parties = _getParties(line)
            if len(parties) > 0:
                self.lastindex = i
            for party in parties:
                self.freeindexes[party] = i + 1

    def setName(self, name):
        self.name = name

    def dagger(self):  # Returns the Hermitian Conjugate or Conjugate Transpose of the given matrix
        invgate = QGate(self.name + "-1")
        for line in self.lines[::-1]:
            invgate.addLine(*[[_invertStrGate(gate[0]), gate[1], gate[2]] if isinstance(gate, Iterable) else gate.dagger() if isinstance(gate, Iterable) else gate for gate in line])
        return invgate

    def invert(self):
        return self.dagger()

    '''
    def _flatten(self, controls=set(), anticontrols=set()):
        flines = []
        for line in self.lines:
            newLines = [[]]
            qbs = 0
            for op in line:
                if op is None:
                    for i in range(len(newLines)):
                        newLines[i].append(None)
                    qbs += 1
                elif type(op) is Measure:
                    newLines[0].append(op)
                else:
                    gate, cons, acons = op
                    cons = cons.union(controls)
                    acons = acons.union(anticontrols)
                    if type(gate) is not QGate:
                        newLines[0].append(op)
                        for i in range(1, len(newLines)):
                            newLines[i].append(None)
                        qbs += 1 + len(cons) + len(acons)
                    else:
                        auxLines = gate._flatten(cons, acons)
                        if len(auxLines) > len(newLines):
                            newLines += [[None for j in range(qbs)] for i in range(len(auxLines) - len(newLines))]
                        for i in range(len(auxLines)):
                            auxLine = auxLines[i]
                            for j in range(len(auxLine)):
                                if auxLine[j] is not None:
                                    auxgate, auxcons, auxacons = auxLine[j]
                                    auxcons = set([c + qbs for c in auxcons])
                                    auxacons = set([ac + qbs for ac in auxacons])
                                    auxLine[j] = [auxgate, cons.union(auxcons), acons.union(auxacons)]
                            newLines[i] += auxLine
                        qbs += gate.size + len(cons) + len(acons)
            flines += newLines
        return flines
    '''

    def _applyGate(self, registry, qubit, controls, anticontrols, optimize=False):
        lines = self.lines
        if optimize:
            lines = self.oplines
        for line in lines:
            currbit = 0
            for i in range(len(line)):
                if line[i] is not None and line[i][0] is not None and (isinstance(line[i][0], QGate) or line[i][0].lower() != "i"):
                    if line[i][1] is not None:
                        if controls is None:
                            ctrls = set([qubit + c for c in line[i][1]])
                        else:
                            ctrls = set([qubit + c for c in line[i][1]]).union(controls)
                    if line[i][2] is not None:
                        if anticontrols is None:
                            actrls = set([qubit + ac for ac in line[i][2]])
                        else:
                            actrls = set([qubit + ac for ac in line[i][2]]).union(anticontrols)
                    if type(line[i][0]) == str:
                        registry.applyGate(_addQubitOffset(line[i][0], qubit), qubit=currbit+qubit, control=ctrls, anticontrol=actrls)
                    else:
                        line[i][0]._applyGate(registry, qubit+currbit, ctrls, actrls)
                    currbit += getGateSize(line[i][0])
                else:
                    currbit += 1


__cGetQGate__ = __qsimov__.getQGate
__cGetQGate__.argtypes = [ct.c_char_p, ct.c_double, ct.c_double, ct.c_double, ct.c_int]
__cGetQGate__.restype = ct.c_void_p

__cGetQGateQubits__ = __qsimov__.getQGateQubits
__cGetQGateQubits__.argtypes = [ct.c_void_p]
__cGetQGateQubits__.restype = ct.c_int

__cGetQGateSize__ = __qsimov__.getQGateSize
__cGetQGateSize__.argtypes = [ct.c_void_p]
__cGetQGateSize__.restype = ct.c_uint

__cGet2dGate__ = __qsimov__.get2dGate
__cGet2dGate__.argtypes = [ct.c_void_p]
__cGet2dGate__.restype = c_double_p


def getGate(gatename):
    name, arg1, arg2, arg3, invert = prs.getGateData(gatename)
    if arg1 is None:
        arg1 = 0
    if arg2 is None:
        arg2 = 0
    if arg3 is None:
        arg3 = 0
    qgate = ct.c_void_p(__cGetQGate__(ct.c_char_p(name.encode()), ct.c_double(arg1), ct.c_double(arg2), ct.c_double(arg3), ct.c_int(int(invert))))
    if (qgate or False) == qgate:  # NOTNULLPTR and True returns True, NOTNULLPTR or False returns NOTNULLPTR
        # nqubits = int(__cGetQGateQubits__(qgate))
        size = int(__cGetQGateSize__(qgate))
        plainmatrix2d = __cGet2dGate__(qgate)[:size*size*2]
        rematrix2d = plainmatrix2d[:size*size]
        immatrix2d = plainmatrix2d[size*size:size*size*2]
        matrix = np.array([complex(rematrix2d[i], immatrix2d[i]) for i in range(size*size)])
        matrix = matrix.reshape(size, size)
        # print("Gate for " + str(nqubits) + " qubits with size " + str(size))
    else:
        matrix = None
        print("Error while getting the specified gate!")

    return matrix


def _rebuildGateName(gate):
    cons = set()
    acons = set()
    gatename = gate
    if not isinstance(gate, str) and isinstance(gate, Iterable):
        gatename = gate[0]
        if (len(gate) > 1):
            if gate[1] is not None:
                if isinstance(gate[1], Iterable) and len(gate[1]) > 0:
                    cons = set(gate[1])
                elif not isinstance(gate[1], Iterable):
                    cons = set([gate[1]])
        if (len(gate) > 2):
            if gate[2] is not None:
                if isinstance(gate[2], Iterable) and len(gate[2]) > 0:
                    acons = set(gate[2])
                elif not isinstance(gate[2], Iterable):
                    acons = set([gate[2]])
    if not isinstance(gatename, QGate):
        if gatename is not None and gatename.lower() != "i":
            name, arg1, arg2, arg3, invert = prs.getGateData(gatename)
            if arg1 is not None:
                name += "(" + str(arg1)
            if arg2 is not None:
                name += "," + str(arg2)
            if arg3 is not None:
                name += "," + str(arg3) + ")"
            elif arg1 is not None:
                name += ")"
            if invert:
                name += "-1"
        else:
            name = None
    else:
        name = gatename
    return [name, cons, acons] if name is not None else None


def _getQuBitArg(gatename):
    args = None
    if isinstance(gatename, str):
        qubitargs = ["XX", "YY", "ZZ"]
        name, arg1, arg2, arg3, invert = prs.getGateData(gatename)
        if name in qubitargs or "SWAP" in name:
            if name in qubitargs:
                args = set([arg2, arg3])
            else:
                args = set([arg1, arg2])
    return args


def _addQubitOffset(gatename, offset):
    qubitargs = ["XX", "YY", "ZZ"]
    name, arg1, arg2, arg3, invert = prs.getGateData(gatename)
    if name in qubitargs or "SWAP" in name:
        arg2 += offset
        if name in qubitargs:
            arg3 += offset
        else:
            arg1 += offset
        if arg1 is not None:
            name += "(" + str(arg1)
        if arg2 is not None:
            name += str(arg2)
        if arg3 is not None:
            name += str(arg3) + ")"
        if invert:
            name += "-1"
        gatename = name
    return gatename


def _invertStrGate(gatename):
    selfinvert = ["X", "Y", "Z", "H", "SWAP"]
    name, arg1, arg2, arg3, invert = prs.getGateData(gatename)
    if name not in selfinvert:
        if invert:
            gatename = gatename[:-2]
        else:
            gatename += "-1"
    return gatename


def _getParties(args, ignore_empty=False):
    parties = set()
    empties = set()
    currbit = 0
    for i in range(len(args)):
        if args[i] is not None:
            myparty = _getQuBitArg(args[i][0])
            if myparty is None:
                gateSize = getGateSize(args[i][0])
                if gateSize is None:
                    continue
                myparty = set([currbit + j for j in range(gateSize)])
            if args[i][0] is not None:
                if len(myparty.intersection(args[i][1])) == 0:
                    myparty = myparty.union(args[i][1])
                else:
                    raise ValueError("You can't apply a gate to a qubit and use it as a control: " + str(myparty.intersection(args[i][1])))
                if len(myparty.intersection(args[i][2])) == 0:
                    myparty = myparty.union(args[i][2])
                else:
                    raise ValueError("You can't apply a gate to a qubit and use it as a control, or use it as control and anticontrol at the same time: " + str(myparty.intersection(args[i][2])))
            if len(parties.intersection(myparty)) == 0:
                parties = parties.union(myparty)
            else:
                raise ValueError("You can't apply two or more gates to the same qubit in the same line: " + str(parties.intersection(myparty)))
            currbit += getGateSize(args[i][0])
        else:
            empties.add(currbit)
            currbit += 1
    if ignore_empty:
        return parties
    return parties.union(empties)


def getGateData(gatename):
    if isinstance(gatename, QGate):
        shape = (gatename.size, 2**gatename.size)
    else:
        name, arg1, arg2, arg3, invert = prs.getGateData(gatename)
        if arg1 is None:
            arg1 = 0
        if arg2 is None:
            arg2 = 0
        if arg3 is None:
            arg3 = 0
        if "SWAP" in name or name == "XX" or name == "YY" or name == "ZZ":
            shape = (2, 4)
        else:
            qgate = ct.c_void_p(__cGetQGate__(ct.c_char_p(name.encode()), ct.c_double(arg1), ct.c_double(arg2), ct.c_double(arg3), ct.c_int(int(invert))))
            if (qgate or False) == qgate:  # NOTNULLPTR and True returns True, NOTNULLPTR or False returns NOTNULLPTR
                nqubits = int(__cGetQGateQubits__(qgate))
                size = int(__cGetQGateSize__(qgate))
                shape = (nqubits, size)
            else:
                shape = None
                print("Error while getting the specified gate!")

    return shape


def joinGates(gates):
    maxgatelen = max(map(getLines, gates))
    newlines = []
    for i in range(maxgatelen):
        newline = []
        for gate in gates:
            if type(gate) != Measure:
                if i < len(gate.lines):
                    newline += gate.lines[i]
                else:
                    newline += [None for i in range(gate.size)]
            else:
                if i < 1:
                    newline += [gate]
                else:
                    newline += [None for i in range(getGateSize(gate))]
        newlines += [newline]
    return newlines


def getGateSize(gate):
    size = 0
    if isinstance(gate, str):
        size = getGateData(gate)[0]
    elif isinstance(gate, Iterable):
        cacs = 0
        if len(gate) > 1:
            if gate[1] is not None:
                cacs += len(gate[1])
        if len(gate) > 2:
            if gate[2] is not None:
                cacs += len(gate[2])
        size = getGateData(gate[0])[0] + cacs
    elif isinstance(gate, Measure):
        size = len(gate.mask)
    elif isinstance(gate, QGate):
        size = gate.size
    elif gate is None:
        size = 1
    else:
        raise ValueError(str(gate) + " is not a gate!")
    return size


def getLines(gate):
    if type(gate) == Measure:
        return 1
    return len(gate.lines)
