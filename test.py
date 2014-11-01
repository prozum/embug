from time import sleep

class Application:
    
    def setup(self):
        pinMode(0,IN) 
        pinMode(A0,IN)

        pinMode(1,OUT)
        pinMode(A1,OUT)

    def loop(self):
        sleep(0.5)

        if analogRead(A0)==255:
            digitalWrite(1,HIGH)
            serialPrintln("Pin 1 is set to HIGH!")
        else:
            digitalWrite(1,LOW)
            serialPrintln("Pin 1 is set to LOW!!")

if __name__ == '__main__':
    app = Application()
    app.setup()
    while 1:
        app.loop()
