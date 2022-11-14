# This Python file uses the following encoding: utf-8
"""
contact: software@cbica.upenn.edu
Copyright (c) 2018 University of Pennsylvania. All rights reserved.
Use of this source code is governed by license located in license file: https://github.com/CBICA/NiChart/blob/main/LICENSE
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import argparse
import os, sys
from NiChart.mainwindow import MainWindow
from NiChart.NiChartCmdApp import NiChartCmdApp

def main():
    parser = argparse.ArgumentParser(description='NiChart Data Visualization and Preparation')
    parser.add_argument('--data_file', type=str, help='Data file containing data frame.', default=None, required=False)
    parser.add_argument('--dict_file', type=str, help='Dict file containing data dictionary.', default=None, required=False)
    parser.add_argument("-nogui", action="store_true", help="Launch application in CLI mode to do data processing without any visualization or graphical user interface.")

    args = parser.parse_args(sys.argv[1:])

    data_file = args.data_file
    dict_file = args.dict_file
    noGUI = args.nogui

    if(noGUI):
        app = QtCore.QCoreApplication(sys.argv)
        if(compute_spares):
            if((data_file == None) or (SPARE_model_file == None) or (output_file == None)):
                print("Please provide '--data_file', '--SPARE_model_file' and '--output_file_name' to compute spares.")
                exit()
            NiChartCmdApp().ComputeSpares(data_file, SPARE_model_file, output_file)
    else:
        app = QtWidgets.QApplication(sys.argv)
        
        # Set the style sheet
        with open('./style.qss', 'r') as f:         ## FIXME this is absolute path to curr dir
            style = f.read()
        app.setStyleSheet(style)
        
        mw = MainWindow(dataFile = data_file, dictFile = dict_file)
        mw.show()

        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
