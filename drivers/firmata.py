import pyfirmata

dPins = range(14)
aPins = range(18,24)

A0,A1,A2,A3,A4,A5 = aPins

HIGH,OUT = (1,1)

LOW,IN   = (0,0)

class Driver():
    def __init__(self,device):
        self.board = pyfirmata.Arduino(device)
        
        # Setup Analog Pins
        it = pyfirmata.util.Iterator(self.board)
        it.start()
        
        for pin in aPins:
            self.board.analog[pin-aPins[0]].enable_reporting()
            
        # Delay 1 sec
        self.board.pass_time(1)
    
    def analogRead(self):
        pass

    def analogWrite(self):
        pass

    def digitalRead(self):
        pass

    def digitalWrite(self,pin,state):
        self.board.digital[pin].write(state)

    def pinMode(self):
        pass

    def serialPrintln(self,msg):
        print msg
    
    def exit(self):
        self.board.exit()