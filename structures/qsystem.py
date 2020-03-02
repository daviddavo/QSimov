import numpy as np
import connectors.parser as prs
from structures.qregistry import QRegistry, superposition
from structures.qgate import QGate, getGateData
from collections.abc import Iterable

class QSystem:
    def __init__(self, nqbits):
        # nqbits -> number of QuBits in the registry.
        self.regs = [[QRegistry(1), [id]] for id in range(nqbits)]
        self.qubitMap = {id: id for id in range(nqbits)}
        self.nqubits = nqbits

    def __del__(self):
        for i in range(len(self.regs)):
            if self.regs[i] != None:
                del self.regs[i][0]
        del self.regs
        del self.qubitMap

    def getRegSize(self):
        return ((reg[0].getSize(), reg[1]) if type(reg[0]) == QRegistry else (1, reg[1]) for reg in self.regs)

    def getSize(self):
        total = 0
        for reg in self.regs:
            if type(reg[0]) == QRegistry:
                total += reg[0].getSize()
            else:
                total += 1
        return total

    def getRegNQubits(self):
        return (reg[0].getNQubits() if type(reg[0]) == QRegistry else 1 for reg in self.regs)

    def getNQubits(self):
        return self.nqubits

    def toString(self):
        return str([[reg[0].toString(), reg[1]] if type(reg[0]) == QRegistry else reg for reg in self.regs])

    def measure(self, msk, remove=False): # List of numbers with the QuBits that should be measured. 0 means not measuring that qubit, 1 otherwise. remove = True if you want to remove a QuBit from the registry after measuring
        nqubits = self.getNQubits()
        if (type(msk) != list or len(msk) != nqubits or \
            not all(type(num) == int and (num == 0 or num == 1) for num in msk)):
            raise ValueError('Not valid mask')
        result = []
        for qubit in range(self.nqubits):
            if msk[qubit] == 1:
                regid = self.qubitMap[qubit]
                if self.regs[regid][0].getNQubits() > 1:
                    result += self.regs[regid][0].measure([0 if self.regs[regid][1][i] != qubit else 1 for i in range(len(self.regs[regid][1]))], remove=True)
                    self.regs[regid][1].remove(qubit)
                    newid = self.regs.index(None)
                    self.regs[newid] = [QRegistry(1), [qubit]]
                    self.qubitMap[qubit] = newid
                    if result[-1] == 1:
                        self.regs[newid][0].applyGate("X")
                else:
                    if not remove:
                        result += self.regs[regid][0].measure([1], remove=False)
                    else:
                        if type(self.regs[regid][0]) == QRegistry:
                            result += self.regs[regid][0].measure([1], remove=False)
                            del self.regs[regid][0]
                            self.regs[regid] = [result[qubit], self.regs[regid][0][0]]
                        else:
                            result.append(self.regs[regid])
        return result

    def applyGate(self, *args, **kwargs): # gate, qubit=0, control=None, anticontrol=None):
        if len(args) == 1 or (len(args) == 2 and "qubit" not in kwargs):
            for key in kwargs:
                if key != "qubit" and key != "control" and key != "anticontrol":
                    raise ValueError('Apart from the gates, you can only specify "qubit", "control" and/or "anticontrol" (lowercase)')
            gate = args[0]
            if type(gate) == QGate:
                gate = (gate, gate.getNQubits())
            elif gate == "I" or gate is None:
                return
            else:
                gate = (gate, getGateData(gate)[0])
            qubit = kwargs.get("qubit", 0)
            if len(args) == 2:
                qubit = args[1]
            control = kwargs.get("control", [])
            if not isinstance(control, Iterable):
                control = [control]
            anticontrol = kwargs.get("anticontrol", [])
            if not isinstance(anticontrol, Iterable):
                anticontrol = [anticontrol]
            if isinstance(qubit, Iterable):
                for qid in qubit:
                    self.applyGate(gate[0], qubit=qid, control=control, anticontrol=anticontrol)
            else:
                name = ""
                if type(gate[0]) != QGate:
                    name, arg1, arg2, arg3, invert = prs.getGateData(gate[0])
                invstring = ""
                if invert:
                    invstring = "-1"
                qubits = set(control).union(anticontrol) # Todos los participantes
                if "SWAP" in name:
                    qubit = arg1
                    qubits.add(arg2)
                elif name == "XX" or name == "YY" or name == "ZZ":
                    qubit = arg2
                    qubits.add(arg3)
                else:
                    qubits.update([qubit + i for i in range(1, gate[1])])
                #print("Participants: " + str([qubit] + list(qubits)))
                rid = self.qubitMap[qubit]
                for qid in qubits:
                    self.superposition(rid, self.qubitMap[qid])
                reg, idlist = self.regs[rid]
                #print("RDATA: [" + str(reg.getNQubits()) + ", " + str(idlist) + "]")
                regmap = {idlist[i]: i for i in range(len(idlist))}
                newqubit = regmap[qubit]
                newcontrol = [regmap[qid] for qid in control]
                newanticontrol = [regmap[qid] for qid in anticontrol]
                if type(gate[0]) == QGate:
                    pass
                else:
                    if "SWAP" in name:
                        gate = (name + "(" + str(regmap[arg1]) + "," + str(regmap[arg2]) + ")" + invstring, gate[1])
                    if name == "XX" or name == "YY" or name == "ZZ":
                        gate = (name + "(" + str(arg1) + "," + str(regmap[arg2]) + "," + str(regmap[arg3]) + ")" + invstring, gate[1])
                    #print(gate[0])
                    reg.applyGate(gate[0], qubit=newqubit, control=newcontrol, anticontrol=newanticontrol)
        elif len(kwargs) == 0 and len(args) > 0:
            nq = 0
            gates = []
            for arg in args:
                if type(arg) == QGate:
                    gatenq = (arg, arg.getNQubits())
                elif arg == "I" or arg is None:
                    gatenq = (None, 1)
                else:
                    gatenq = (arg, getGateData(arg)[0])
                nq += gatenq[1]
                gates.append(gatenq)
            if nq == self.getNQubits():
                qid = 0
                for gate in gates:
                    if gate[0] != None:
                        self.applyGate(gate[0], qubit=qid)
                    qid += gate[1]
            else:
                print ("You have to specify a gate for each QuBit (or None if you don't want to operate with it)")
        elif len(args) == 0:
            print("You must specify at least one gate")
        else:
            print("You can't apply more than one gate when using " + '"qubit", "control" or "anticontrol"')

    def hopfCoords(self):
        return [self.regs[self.qubitMap[id]][0].hopfCoords() if type(self.regs[self.qubitMap[id]][0]) == QRegistry else None for id in range(self.nqubits)]

    def blochCoords(self):
        return [self.regs[self.qubitMap[id]][0].blochCoords() if type(self.regs[self.qubitMap[id]][0]) == QRegistry else None for id in range(self.nqubits)]

    def superposition(self, regid1, regid2):
        if regid1 != regid2:
            a = self.regs[regid1]
            b = self.regs[regid2]
            newregdata = joinRegs(a, b)
            self.regs[regid1] = newregdata
            self.regs[regid2] = None
            for id in b[1]:
                self.qubitMap[id] = regid1
            del a[0]
            del b[0]

    def getState(self):
        regs = list(filter(None, self.regs))
        if len(regs) == 1:
            return regs[0][0].getState()
        else:
            reg = joinRegs(regs[0], regs[1])
            for i in range(2, len(regs)):
                if regs[i] != None:
                    aux = reg
                    reg = joinRegs(aux, regs[i])
                    del aux[0]
            state = reg[0].getState()
            del reg[0]
            return state

def joinSystems(a, b): # Este metodo une dos QSystems
    pass

def joinRegs(a, b): # Este metodo une dos registros en uno solo y deja los qubits ordenados SIEMPRE
    newregdata = []
    # Como a y b estan ordenados
    if b[1][0] > a[1][-1]: # Si el ultimo qubit de a es menor que el primero de b
        newregdata = [superposition(b[0], a[0]), a[1] + b[1]] # Hacemos el producto tensorial de b y a (recordemos que en los registros los qubits van en orden decreciente)
    elif a[1][0] > b[1][-1]: # Si el ultimo qubit de b es menor que el primero de a
        newregdata = [superposition(a[0], b[0]), b[1] + a[1]] # Hacemos el producto tensorial de a y b
    else: # En caso contrario
        newregdata = [superposition(b[0], a[0]), a[1] + b[1]] # Hacemos el producto tensorial sin importar el orden de a y b
        newregdata = sortRegdata(newregdata) # Y los reordenamos porque estan desordenados
    return newregdata

def sortRegdata(regdata): # regdata[1] = [1,3,2,4] -> el qubit 0 del registro es el 1 del sistema
    relen = len(regdata[1]) # Qubits almacenados en el registro
    for i in range(relen-1): # Si hay n elementos, no será necesaria la iteracion en la que colocamos el ultimo en su misma posicion
        aux = regdata[1][i:] # Elementos todavia no ordenados del registro
        minid = min(aux) # Obtenemos el elemento con menor identificador
        minindex = aux.index(minid) + i # Vemos a que id del registro corresponde
        if aux[0] != minid: # Si no esta en la primera posicion todavia
            regdata[0].applyGate("SWAP(" + str(i) + "," + str(minindex) + ")") # Lo intercambiamos con el qubit en dicha posicion
            regdata[1][i], regdata[1][minindex] = minid, regdata[1][i] # Y actualizamos la lista de qubits de forma acorde al intercambio
    return regdata
