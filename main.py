#!/usr/bin/env python
import sys
from PyQt4 import QtGui,QtCore
from functools import partial

from imp import load_source


dROW = 4
aROW = 3


class Simulator(QtCore.QThread):
    def setDriver(self,driver):
        self.driver = driver
    
    def setSource(self,source):
        self.source = source
    
    def run(self):       
        try:
            source = load_source('source',self.source)
        except IOError:
            widget.error("Could not load source!")
            return -1
        
        source.A0,source.A1,source.A2,source.A3,source.A4,source.A5 = self.driver.aPins
        source.HIGH,source.OUT = (1,1)
        source.LOW,source.IN   = (0,0)

        self.pinValues  = {}
        self.pinModes   = {}
        
        for pin in self.driver.dPins+self.driver.aPins:
            self.pinModes[pin] = 0

        self.driver = self.driver.Driver(self)
        
        source.pinMode         = self.driver.pinMode
        source.digitalRead     = self.driver.digitalRead
        source.digitalWrite    = self.driver.digitalWrite
        source.analogRead      = self.driver.analogRead
        source.analogWrite     = self.driver.analogWrite
        source.serialPrint     = self.driver.serialPrint
        source.serialPrintln   = self.driver.serialPrintln
        source.error           = self.driver.error    

        try:
            app = source.Application()
        except AttributeError:
            widget.error("No Application object")
            return -1

        try:
            setup = app.setup
        except AttributeError:
            widget.error("No setup function")
            return -1

        try:
            loop = app.loop
        except AttributeError:
            widget.error("No loop function")
            return -1

        setup()
        while 1:
            loop()

        
class Debug(QtGui.QMainWindow):
    def __init__(self):
        super(Debug, self).__init__()
        self.sim            = None
        self.inputDPins     = set()
        self.inputAPins     = set()
        self.outputDPins    = set()
        self.outputAPins    = set()

        self.settings       = {}
        self.runNumber      = 0

        self.createEditor()

        self.createActions()
        self.createMenus()

        self.createSerial()

        self.createDigitalInput()
        self.createDigitalOutput()
        self.createAnalogInput()
        self.createAnalogOutput()

        self.createCtrl()

        self.dSpinBoxes     = {}
        self.aSpinBoxes     = {}
        self.checkBoxes     = {}
        self.sliders        = {}
        self.pinGroupBoxes  = {}
        self.tmpLayouts     = []
        self.initUI()

    def newFile(self):
        if self.maybeSave():
            self.editor.clear()
            self.setCurrentFile('')

    def open(self):
        if self.maybeSave():
            fileName = QtGui.QFileDialog.getOpenFileName(self)
            if fileName:
                self.loadFile(fileName)

    def save(self):
        if self.curFile:
            return self.saveFile(self.curFile)

        return self.saveAs()

    def saveAs(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self)
        if fileName:
            return self.saveFile(fileName)

        return False

    def about(self):
        QtGui.QMessageBox.about(self, "About Application",
                "With <b>Embug</b> you can edit,emulate & debug your embedded programs")

    def documentWasModified(self):
        self.setWindowModified(self.editor.document().isModified())

    def setCurrentFile(self, fileName):
        self.curFile = fileName
        self.editor.document().setModified(False)
        self.setWindowModified(False)

        if self.curFile:
            shownName = self.strippedName(self.curFile)
        else:
            shownName = 'untitled.py'

        self.setWindowTitle("%s[*] - Embug" % shownName)

    def strippedName(self, fullFileName):
        return QtCore.QFileInfo(fullFileName).fileName()

    def maybeSave(self):
        if self.editor.document().isModified():
            ret = QtGui.QMessageBox.warning(self, "Application",
                    "The document has been modified.\nDo you want to save "
                    "your changes?",
                    QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard |
                    QtGui.QMessageBox.Cancel)
            if ret == QtGui.QMessageBox.Save:
                return self.save()
            elif ret == QtGui.QMessageBox.Cancel:
                return False
        return True

    def loadFile(self, fileName):
        file = QtCore.QFile(fileName)
        if not file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, "Application",
                    "Cannot read file %s:\n%s." % (fileName, file.errorString()))
            return

        inf = QtCore.QTextStream(file)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.editor.setPlainText(inf.readAll())
        QtGui.QApplication.restoreOverrideCursor()

        self.setCurrentFile(fileName)
        self.statusBar().showMessage("File loaded", 2000)

    def saveFile(self, fileName):
        file = QtCore.QFile(fileName)
        if not file.open(QtCore.QFile.WriteOnly | QtCore.QFile.Text):
            QtGui.QMessageBox.warning(self, "Application",
                    "Cannot write file %s:\n%s." % (fileName, file.errorString()))
            return False

        outf = QtCore.QTextStream(file)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        outf << self.editor.toPlainText()
        QtGui.QApplication.restoreOverrideCursor()

        self.setCurrentFile(fileName);
        self.statusBar().showMessage("File saved", 2000)
        return True

    def createEditor(self):
        self.editor = QtGui.QTextEdit()
        self.setCentralWidget(self.editor)

        self.editor.document().contentsChanged.connect(self.documentWasModified)
        self.setCurrentFile('')

    def createActions(self):
        self.newAct = QtGui.QAction(QtGui.QIcon(':/images/new.png'), "&New",
                self, shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file", triggered=self.newFile)

        self.openAct = QtGui.QAction(QtGui.QIcon('inputDPins:/images/open.png'),
                "&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.open)

        self.saveAct = QtGui.QAction(QtGui.QIcon(':/images/save.png'),
                "&Save", self, shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to disk", triggered=self.save)

        self.saveAsAct = QtGui.QAction("Save &As...", self,
                shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document under a new name",
                triggered=self.saveAs)

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.close)

        self.cutAct = QtGui.QAction(QtGui.QIcon(':/images/cut.png'), "Cu&t",
                self, shortcut=QtGui.QKeySequence.Cut,
                statusTip="Cut the current selection's contents to the clipboard",
                triggered=self.editor.cut)

        self.copyAct = QtGui.QAction(QtGui.QIcon(':/images/copy.png'),
                "&Copy", self, shortcut=QtGui.QKeySequence.Copy,
                statusTip="Copy the current selection's contents to the clipboard",
                triggered=self.editor.copy)

        self.pasteAct = QtGui.QAction(QtGui.QIcon(':/images/paste.png'),
                "&Paste", self, shortcut=QtGui.QKeySequence.Paste,
                statusTip="Paste the clipboard's contents into the current selection",
                triggered=self.editor.paste)

        self.aboutAct = QtGui.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

        self.aboutQtAct = QtGui.QAction("About &Qt", self,
                statusTip="Show the Qt library's About box",
                triggered=QtGui.qApp.aboutQt)

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())
    
    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addSeparator();
        self.fileMenu.addAction(self.exitAct)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.addAction(self.cutAct)
        self.editMenu.addAction(self.copyAct)
        self.editMenu.addAction(self.pasteAct)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

    def createSerial(self):
        dockWidget = QtGui.QDockWidget("Serial",self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)

        serialWidget = QtGui.QWidget(self)
        dockWidget.setWidget(serialWidget)

        serialLayout = QtGui.QVBoxLayout()
        serialWidget.setLayout(serialLayout)

        self.serialTextEdit = QtGui.QTextEdit(serialWidget)
        serialLayout.addWidget(self.serialTextEdit)

        clearButton = QtGui.QPushButton("Clear",self)
        clearButton.clicked.connect(self.clearSerial)
        serialLayout.addWidget(clearButton)

        autoScrollLayout = QtGui.QHBoxLayout()
        autoScrollWidget = QtGui.QWidget()
        autoScrollWidget.setLayout(autoScrollLayout)
        
        autoScrollLabel = QtGui.QLabel("Auto Scroll: ", autoScrollWidget)
        
        autoScrollCheckBox = QtGui.QCheckBox(autoScrollWidget)
        

    def createDigitalInput(self):
        dockWidget = QtGui.QDockWidget("Digital Input",self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dockWidget)

        digitalInputWidget = QtGui.QWidget(self)
        dockWidget.setWidget(digitalInputWidget)

        self.digitalInputLayout = QtGui.QHBoxLayout()
        digitalInputWidget.setLayout(self.digitalInputLayout)

    def createDigitalOutput(self):
        dockWidget = QtGui.QDockWidget("Digital Output",self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dockWidget)

        digitalOutputWidget = QtGui.QWidget(self)
        dockWidget.setWidget(digitalOutputWidget)

        self.digitalOutputLayout = QtGui.QHBoxLayout()
        digitalOutputWidget.setLayout(self.digitalOutputLayout)

    def createAnalogInput(self):
        dockWidget = QtGui.QDockWidget("Analog Input",self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dockWidget)
        
        analogInputWidget = QtGui.QWidget(self)
        dockWidget.setWidget(analogInputWidget)

        self.analogInputLayout = QtGui.QHBoxLayout()
        analogInputWidget.setLayout(self.analogInputLayout)

    def createAnalogOutput(self):
        dockWidget = QtGui.QDockWidget("Analog Output",self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dockWidget)

        analogOutputWidget = QtGui.QWidget(self)
        dockWidget.setWidget(analogOutputWidget)

        self.analogOutputLayout = QtGui.QHBoxLayout()
        analogOutputWidget.setLayout(self.analogOutputLayout)

    def createCtrl(self):
        dockWidget = QtGui.QDockWidget("Control",self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)

        ctrlWidget = QtGui.QWidget(self)
        dockWidget.setWidget(ctrlWidget)

        ctrlLayout = QtGui.QHBoxLayout()
        ctrlWidget.setLayout(ctrlLayout)
       
        self.startButton = QtGui.QPushButton("Start",self)
        self.startButton.clicked.connect(self.startSim)
        ctrlLayout.addWidget(self.startButton)

        terminateButton = QtGui.QPushButton("Terminate",self)
        terminateButton.clicked.connect(self.startSim)
        ctrlLayout.addWidget(terminateButton)

    def initUI(self):
        self.showMaximized()
        self.setWindowTitle('Embug')    
        self.show()

    def setupPins(self):
        
        self.clearLayout(self.digitalInputLayout)
        self.clearLayout(self.digitalOutputLayout)
        self.clearLayout(self.analogInputLayout)
        self.clearLayout(self.analogOutputLayout)
        
        for pin in self.inputDPins:           
            pinLayout    = QtGui.QVBoxLayout()
            pinGroupBox  = QtGui.QGroupBox("Pin "+str(pin),self)
            pinGroupBox.setLayout(pinLayout)

            pinSubLayout    = QtGui.QHBoxLayout()
            pinLayout.addLayout(pinSubLayout)
            
            pinCheckBox  = QtGui.QCheckBox(self)
            pinCheckBox.stateChanged.connect(partial(self.dWrite,pin))
            pinSubLayout.addWidget(pinCheckBox)
            self.checkBoxes[pin] = pinCheckBox
            
            pinSpinBox     = QtGui.QSpinBox(self)
            pinSpinBox.setMaximum(1)
            pinSpinBox.valueChanged.connect(partial(self.dWrite,pin))
            pinSubLayout.addWidget(pinSpinBox)
            self.dSpinBoxes[pin] = pinSpinBox

            spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
            pinLayout.addItem(spacerItem)
            
            self.pinGroupBoxes[pin] = pinGroupBox

        for pin in self.inputAPins:
            pinLayout    = QtGui.QVBoxLayout()
            pinGroupBox  = QtGui.QGroupBox("Pin A"+str(pin-self.driver.aPins[0]),self)
            pinGroupBox.setLayout(pinLayout)

            pinSpinBox     = QtGui.QSpinBox(self)
            pinSpinBox.setMaximum(255)
            pinSpinBox.valueChanged.connect(partial(self.aWrite,pin))
            pinLayout.addWidget(pinSpinBox)
            self.aSpinBoxes[pin] = pinSpinBox
            
            pinSlider  = QtGui.QSlider(1,self)
            pinSlider.setMaximum(255)
            pinSlider.valueChanged.connect(partial(self.aWrite,pin))
            pinLayout.addWidget(pinSlider)
            self.sliders[pin] = pinSlider
            
            spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
            pinLayout.addItem(spacerItem)
            
            self.pinGroupBoxes[pin] = pinGroupBox
    
    
    def updatePins(self):     
        inputDPinsList = list(self.inputDPins)
        for pin in inputDPinsList:
            self.pinGroupBoxes[pin].setDisabled(False)
            if pin==inputDPinsList[0] or inputDPinsList.index(pin)%dROW==0:
                currentLayout = QtGui.QVBoxLayout()
                self.tmpLayouts.append(currentLayout)
                self.digitalInputLayout.addLayout(currentLayout)
            
            currentLayout.addWidget(self.pinGroupBoxes[pin])

        outputDPinsList = list(self.outputDPins)
        for pin in outputDPinsList:
            self.pinGroupBoxes[pin].setDisabled(True)
            if pin==outputDPinsList[0] or outputDPinsList.index(pin)%dROW==0:
                currentLayout = QtGui.QVBoxLayout()
                self.tmpLayouts.append(currentLayout)
                self.digitalOutputLayout.addLayout(currentLayout)
            
            currentLayout.addWidget(self.pinGroupBoxes[pin])

        inputAPinsList = list(self.inputAPins)
        for pin in inputAPinsList:
            self.pinGroupBoxes[pin].setDisabled(False)
            if pin==inputAPinsList[0] or inputAPinsList.index(pin)%aROW==0:
                currentLayout = QtGui.QVBoxLayout()
                self.tmpLayouts.append(currentLayout)
                self.analogInputLayout.addLayout(currentLayout)
            
            currentLayout.addWidget(self.pinGroupBoxes[pin])

        outputAPinsList = list(self.outputAPins)
        for pin in outputAPinsList:
            self.pinGroupBoxes[pin].setDisabled(True)
            if pin==outputAPinsList[0] or outputAPinsList.index(pin)%aROW==0:
                currentLayout = QtGui.QVBoxLayout()
                self.tmpLayouts.append(currentLayout)
                self.analogOutputLayout.addLayout(currentLayout)
            
            currentLayout.addWidget(self.pinGroupBoxes[pin])
    
    def loadDriver(self):
        try:
            self.driver = load_source('driver',str(QtCore.QDir.currentPath())+'/drivers/firmata-dbg.py')
        except AttributeError:
            self.error("No driver")
            
        self.sim = Simulator()
        self.sim.setDriver(self.driver)
        
        self.inputDPins     = set(self.driver.dPins[:])
        self.inputAPins     = set(self.driver.aPins[:])
        
        self.setupPins()
        self.updatePins()
        
        self.connect(self.sim, QtCore.SIGNAL('sPinMode'), self.pinMode, QtCore.Qt.BlockingQueuedConnection)
        self.connect(self.sim, QtCore.SIGNAL('sDWrite'), self.dWrite, QtCore.Qt.BlockingQueuedConnection)
        self.connect(self.sim, QtCore.SIGNAL('sAWrite'), self.aWrite, QtCore.Qt.BlockingQueuedConnection)
        self.connect(self.sim, QtCore.SIGNAL('sEcho'), self.echo, QtCore.Qt.BlockingQueuedConnection)  
          
    
    def pinMode(self,pin,mode):
        self.sim.pinValues[pin] = 0
        self.sim.pinModes[pin]  = mode
        
        if pin in self.inputDPins and mode:
            self.inputDPins.remove(pin)
            self.outputDPins.add(pin)
        
        elif pin in self.outputDPins and not mode:
            self.outputDPins.remove(pin)
            self.inputDPins.add(pin)

        elif pin in self.inputAPins and mode:
            self.inputAPins.remove(pin)
            self.outputAPins.add(pin)
        
        elif pin in self.outputDPins and not mode:
            self.outputAPins.remove(pin)
            self.inputAPins.add(pin)  
        
        self.updatePins()
    
    def dWrite(self,pin,value):
        if value:
            self.checkBoxes[pin].setCheckState(2)
            self.dSpinBoxes[pin].setValue(1)
            self.sim.pinValues[pin]   = 1
        else:
            self.checkBoxes[pin].setCheckState(0)
            self.dSpinBoxes[pin].setValue(0)
            self.sim.pinValues[pin]   = 0

    def aWrite(self,pin,value):
        self.sliders[pin].setValue(value)
        self.aSpinBoxes[pin].setValue(value)
        self.sim.pinValues[pin]   = value

    def echo(self,msg,newline=True,color="black"):
        self.serialTextEdit.setTextColor(QtGui.QColor(color))
        if newline:
            self.serialTextEdit.append(msg)
        else:
            self.serialTextEdit.addText(msg)
        self.serialTextEdit.verticalScrollBar().setValue(self.serialTextEdit.verticalScrollBar().maximum())

    def info(self,msg):
        self.echo("INFO: "+msg,True,"green")

    def error(self,msg):
        self.echo("ERROR: "+msg,True,"red")

    def clearSerial(self):
        self.serialTextEdit.clear()

    def startSim(self):
        self.maybeSave()
        
        if not self.sim:
            self.runNumber += 1
            self.info("Start run #"+str(self.runNumber))
            self.loadDriver()
            self.sim.setSource(str(self.curFile))
            self.sim.start()
            self.startButton.setText("Stop")
        else:
            self.info("Stop run #"+str(self.runNumber))
            self.sim.terminate()
            self.sim = None
            self.startButton.setText("Start")

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    widget = Debug()
    app.exec_()
    
