from PyQt5 import QtCore, QtGui, QtWidgets, uic
import os, sys
from PyQt5.QtWidgets import QAction, QApplication
import pandas as pd
import sys

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()

        #uic.loadUi('/home/guray/Desktop/AAA/des2.ui', self)
        uic.loadUi('/home/guray/Desktop/AAA/des5.ui', self)
        
        self.show()
        
app = QApplication(sys.argv)
myWindow = MainWindow()
app.exec_()
