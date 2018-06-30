#!/usr/local/bin/python

"""
When this is launched:
    - Open the UI
    - Open a command port
    - launch bg Maya process
        - Send the master command port to the bg process
        - open a command port
        - open specified Maya file
        - send the command port and outliner dict to the Fetch tool UI
    - item is selected in the Fetch UI
        - command is sent to the bg process via command port
          to export the selected object to a file (like remote control)
        - command is sent from the bg process to the Fetch tool
          to import the specified maya file
"""

# just a test comment

import sys, os, ast, re, time
import sip
import platform
from PyQt4 import QtGui, QtCore, uic
#from functools import partial


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class MyWindow(QtGui.QMainWindow):
    def __init__(self,spApp):
        self.appDir = os.path.dirname(sys.argv[0])
        uiPath = self.appDir + '/' + 'turboFetch.ui'
        super(MyWindow, self).__init__()
        uic.loadUi(uiPath, self)

        self.imWidth = 230
        self.imHeight = 30
        self.xPos = (self.imWidth * -1)
        self.yPos = 0

        self.treeViewWidget = None
        
        self.setupUI()
        self.connectSignals()

        QtGui.QApplication.processEvents()
        # dummy time suck ----
        time.sleep(1)

        # start progress monitor ----
        self.progressMonitorData = {}
        self.progressMonitorData['widget'] = self.progressBar
        self.progressMonitorData['frameStart'] = 101
        self.progressMonitorData['frameEnd'] = 150
        self.progressMonitorData['filePrefix'] = 'frame'
        self.progressMonitorData['fileExt'] = 'txt'
        self.progressMonitorData['dir'] = self.appDir
        self.progressMonitorInit()
        self.progressMonitor.start()
            
        self.bannerAnimInit()
        self.bannerAnim.start()


        # this is to test a new way to lazy-load a UI ----
        self.testRefreshCount = 0
        self.testRefresherLoop()
        self.testRefresh.start()
        

    def setupUI(self):
        mayaFilePath = '/asdad/asdasd/asdasd/scenes/sq2181-a100-b001.ma'
        mayaFileVersion = 12
        self.show()

        outlinerDict = self.getOutlinerDict()
        
        self.refreshOutliner(
            mayaFilePath=mayaFilePath,
            mayaFileVersion=mayaFileVersion,
            outlinerDict=outlinerDict
            )
            
    def connectSignals(self):
        self.fetchButton.clicked.connect(self.executeFetchCB)
        

    def resizeEvent(self, event):
        self.bannerWindowAdjust()
        QtGui.QMainWindow.resizeEvent(self, event) 


    def testRefresherLoop(self):
        """
        a test of using QTimer for UI lazy-loading
        """
        interval = 0
        self.testRefresh = QtCore.QTimer(interval=interval,timeout=self.testRefresh_exec)

    def testRefresh_exec(self):
        """
        a test of using QTimer for UI lazy-loading
        """
        #self.treeViewWidget.setHeaderLabels([str(self.testRefreshCount)])
        itemText = 'Item: {0}'.format(self.testRefreshCount)
        QtGui.QTreeWidgetItem(self.treeViewWidget,[itemText])
        if self.testRefreshCount == 5000:
            self.testRefresh.stop()
            print ('UI Update Complete')
        self.testRefreshCount = self.testRefreshCount + 1
        
    def progressMonitorInit(self):
        """
        initialize the progress monitor
        """
        self.progressMonitorData['widget'].setMinimum(self.progressMonitorData['frameStart'] - 1)
        self.progressMonitorData['widget'].setMaximum(self.progressMonitorData['frameEnd'])
        self.progressMonitorData['widget'].setValue(0)
        interval = 1000
        self.progressMonitor = QtCore.QTimer(interval=interval,timeout=self.progressMonitorCheck)

    def progressMonitorCheck(self):
        """
        search the latest frame number and update the progress bar
        """
        
        listing = os.listdir(self.progressMonitorData['dir'])
        shortList = []
        for f in listing:
            if f.startswith(self.progressMonitorData['filePrefix']):
                if f.endswith(self.progressMonitorData['fileExt']):
                    shortList.append(f)
        if len(shortList) > 0:
            lastFrame = int(sorted(shortList)[-1].split('.')[-2])
        else:
            lastFrame = 0
            
        self.progressMonitorData['widget'].setValue(lastFrame)

        if lastFrame == self.progressMonitorData['frameEnd']:
            print ('Rendering complete!')
            self.progressMonitor.stop()

        


        
    def bannerAnimInit(self):
        """
        place the banner at the starting position
        """
        self.bannerInterval = 25
        self.bannerAnim = QtCore.QTimer(interval=self.bannerInterval,timeout=self.bannerAnimStep)
        self.bannerAnimStep()

    def bannerAnimStep(self):
        """
        move the banner 1 step to the right and stop at center window
        """
        self.bannerWidth = self.bannerWidget.width()
        self.bannerImage.setGeometry(self.xPos,self.yPos,self.imWidth,self.imHeight)
        if self.xPos >= ((self.bannerWidth - self.imWidth) / 2):
            self.bannerAnim.stop()
        self.xPos = self.xPos + 10

    def bannerWindowAdjust(self):
        """
        keep the banner centered when the window width is adjusted
        """
        self.bannerWidth = self.bannerWidget.width()
        xPos = ((self.bannerWidth - self.imWidth) / 2)
        self.bannerImage.setGeometry(xPos,self.yPos,self.imWidth,self.imHeight)


        
    def refreshOutliner(self,mayaFilePath=None,mayaFileVersion=None,outlinerDict={}):
        """
        build/re-build the treeView widget
        """
        mayaFileName = os.path.basename(mayaFilePath)
        header = '{0}  -   (v{1})'.format(mayaFileName,mayaFileVersion)
        
        # hide the loading image ----
        self.loadingImageWidget.setVisible(False)
        
        # add the new treeView ----
        self.treeViewWidget = ViewTree(outlinerDict)
        self.treeViewWidget.setHeaderLabels([header])
        self.treeViewWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.treeViewWidget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.outlinerLayout.addWidget(self.treeViewWidget)

        
        


    def getOutlinerDict(self):
        outlinerDict = {}
        outlinerDict['main'] = {}
        outlinerDict['main']['shots'] = {}
        outlinerDict['main']['shots']['p1'] = {}
        outlinerDict['main']['shots']['p2'] = {}
        outlinerDict['main']['chars'] = {}
        outlinerDict['main']['chars']['astrid'] = {}
        outlinerDict['main']['chars']['hiccup'] = {}
        outlinerDict['locator'] = None
        
        
        return outlinerDict

        
    def executeFetchCB(self):
        """
        get the selected item from the outliner treeView 
        and execute the fetching of that object
        """

        selectionPathList = self.getSelectionPathList()
        for itemPath in selectionPathList:
            print ('[turboFetch] - Fetching: {0}'.format(itemPath))
        self.xPos = (self.imWidth * -1)
        self.bannerAnim = QtCore.QTimer(interval=self.bannerInterval,timeout=self.bannerAnimStep)
        self.bannerAnim.start()


    def getSelectionPathList(self):
        """
        return the outliner path of the selected item
        """
        selectionPathList = []
        selectionList = self.treeViewWidget.selectedItems()
        for item in selectionList:
            if item.parent() is not None:
                selectionPath = item.text(0)
                while item.parent() is not None:
                    item = item.parent()
                    selectionPath = '{0}|{1}'.format(item.text(0),selectionPath)
            else:
                selectionPath = item.text(0)
            selectionPath = '|{0}'.format(selectionPath)
            selectionPathList.append(selectionPath)
        return selectionPathList
            
            


class ViewTree(QtGui.QTreeWidget):
    def __init__(self, value):
        super().__init__()
        def fill_item(item, value):
            def new_item(parent, text, val=None):
                child = QtGui.QTreeWidgetItem([text])
                fill_item(child, val)
                parent.addChild(child)
                child.setExpanded(True)
            if value is None: return
            elif isinstance(value, dict):
                for key, val in sorted(value.items()):
                    new_item(item, str(key), val)
            elif isinstance(value, (list, tuple)):
                for val in value:
                    text = (str(val) if not isinstance(val, (dict, list, tuple))
                            else '[%s]' % type(val).__name__)
                    new_item(item, text, val) 
            else:
                new_item(item, str(value))

        fill_item(self.invisibleRootItem(), value)
        

    
class App():
    def __init__(self):
        pass




if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    sApp = App()
    window = MyWindow(sApp)
    sys.exit(app.exec_())


