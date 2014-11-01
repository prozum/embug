from PyQt4 import QtCore

dPins = range(14)
aPins = range(18,24)

A0,A1,A2,A3,A4,A5 = aPins
HIGH,OUT = (1,1)
LOW,IN   = (0,0)

class Driver():
    def __init__(self,sim):
        self.sim = sim

    def pinMode(self,pin,mode):
        self.sim.emit(QtCore.SIGNAL("sPinMode"),pin,mode)

    def digitalRead(self,pin):
        if pin in dPins:
            if not self.sim.pinModes[pin]:
                return self.sim.pinValues[pin]
            else:
                self.error("Pin {0} is not IN!".format(pin))
        else:
            self.error("Pin {0} is not digital!".format(pin))

    def digitalWrite(self,pin,state):
        if pin in dPins:
            if self.sim.pinModes[pin]:
                self.sim.emit(QtCore.SIGNAL("sDWrite"),pin,state)
            else:
                self.error("Pin {0} is not OUT!".format(pin))
        else:
            self.error("Pin {0} is not digital!".format(pin))

    def analogRead(self,pin):
        if pin in aPins:
            if not self.sim.pinModes[pin]:
                return self.sim.pinValues[pin]
            else:
                self.error("Pin {0} is not IN!".format(pin))
        else:
            self.error("Pin {0} is not analog!".format(pin))

    def analogWrite(self,pin,state):
        if pin in aPins:
            if self.sim.pinModes[pin]:
                self.sim.emit(QtCore.SIGNAL("sAWrite"),pin,state)
            else:
                self.error("Pin {0} is not OUT!".format(pin))
        else:
            self.error("Pin {0} is not analog!".format(pin))

    def serialPrint(self,msg):
        self.sim.emit(QtCore.SIGNAL("sEcho"),str(msg),False)

    def serialPrintln(self,msg):
        self.sim.emit(QtCore.SIGNAL("sEcho"),str(msg),True)

    def error(self,msg):
        self.sim.emit(QtCore.SIGNAL("sEcho"),"ERROR: "+str(msg),True,"red")

