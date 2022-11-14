from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QTextEdit, QComboBox, QLayout
import sys, os
import pandas as pd
from NiChart.core.dataio import DataIO
# import dtale
from NiChart.core.baseplugin import BasePlugin
from NiChart.core import iStagingLogger
from NiChart.core.gui.SearchableQComboBox import SearchableQComboBox
from NiChart.core.gui.CheckableQComboBox import CheckableQComboBox
from NiChart.core.plotcanvas import PlotCanvas
from NiChart.core.model.datamodel import PandasModel
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D

logger = iStagingLogger.get_logger(__name__)

class DsetView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(DsetView,self).__init__()
        
        ## Variable to keep all datasets (was linked to a common variable for all plugins by mainwindow)
        self.data_model_arr = None
        
        ## Index of curr dataset
        self.active_index = -1

        ## Variable to keeps commands (was linked to a common variable for all plugins by mainwindow)
        self.cmds = None

        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'dsetview.ui'),self)
        
        ## Main view panel
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))

        ## Panel for dataset selection
        self.ui.comboBoxDsets = QComboBox(self.ui)
        self.ui.comboBoxDsets.setEditable(False)        
        self.ui.vlComboDSets.addWidget(self.ui.comboBoxDsets)
        
        ## Panel for sorting
        self.ui.comboBoxSortCat1 = QComboBox(self.ui)
        self.ui.vlComboSort1.addWidget(self.ui.comboBoxSortCat1)
        self.ui.comboBoxSortCat1.setCurrentIndex(-1)
        
        self.ui.comboBoxSortVar1 = SearchableQComboBox(self.ui)
        self.ui.vlComboSort1.addWidget(self.ui.comboBoxSortVar1)

        self.ui.comboBoxSortCat2 = QComboBox(self.ui)
        self.ui.vlComboSort2.addWidget(self.ui.comboBoxSortCat2)

        self.ui.comboBoxSortVar2 = SearchableQComboBox(self.ui)
        self.ui.vlComboSort2.addWidget(self.ui.comboBoxSortVar2)       

        #self.ui.wOptions.setMaximumWidth(300)
        
        #self.ui.mainVLayout.setSizeConstraint(QLayout.SetFixedSize)
              

        ## Info panel        
        
        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()
    
    
    def SetupConnections(self):

        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)

        self.ui.showTableBtn.clicked.connect(self.OnShowTableBtnClicked)
        self.ui.showDictBtn.clicked.connect(self.OnShowDictBtnClicked)
        self.ui.comboBoxDsets.currentIndexChanged.connect(self.OnDataSelectionChanged)
        self.ui.comboBoxSortCat1.currentIndexChanged.connect(self.OnSortCat1Changed)
        self.ui.comboBoxSortCat2.currentIndexChanged.connect(self.OnSortCat2Changed)


    def OnShowDictBtnClicked(self):
        
        tmpDict = self.data_model_arr.data_dict.reset_index()
        self.PopulateTable(tmpDict)         ## Show dict in a table
        
        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()

    def OnShowTableBtnClicked(self):
        
        currDset = self.ui.comboBoxDsets.currentText()
        
        ##-------
        ## Set data sorting order
        sortCols = []
        sortOrders = []
        if self.ui.check_sort1.isChecked():
            sortCols.append(self.ui.comboBoxSortVar1.currentText())
            if self.ui.check_asc1.isChecked():
                sortOrders.append(True)
            else:   
                sortOrders.append(False)
        if self.ui.check_sort2.isChecked():
            sortCols.append(self.ui.comboBoxSortVar2.currentText())
            if self.ui.check_asc2.isChecked():
                sortOrders.append(True)
            else:
                sortOrders.append(False)
        ##-------

        ## Apply the sorting
        # We keep an array of commands for saving them in a notebook
        dset_name = self.data_model_arr.dataset_names[self.active_index]       
        str_sortCols = ','.join('"{0}"'.format(x) for x in sortCols)
        str_sortOrders = ','.join('"{0}"'.format(x) for x in sortOrders)


        if len(sortCols)>0:

            logger.info('Sorting data by : ' + str_sortCols)

            # Get active dset, apply sort, reassign it
            dtmp = self.data_model_arr.datasets[self.active_index].GetData()
            dtmp = dtmp.sort_values(sortCols, ascending=sortOrders)
            self.data_model_arr.datasets[self.active_index].data = dtmp
            

        ## Show data table
        tmpData = self.data_model_arr.datasets[self.active_index].data
        self.PopulateTable(tmpData)


        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()
        
        ##-------
        ## Populate commands that will be written in a notebook
        cmds = ['']
        if len(sortCols)>0:
            cmds.append(dset_name + ' = ' + dset_name + '.sort_values([' + 
                             str_sortCols  + '], ascending = [' + str_sortOrders + '])')
        cmds.append(dset_name + '.head()')
        cmds.append('')
        self.cmds.add_cmds(cmds)
        ##-------
        
        

    def PopulateTable(self, data):
        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    #add the values to comboBox
    def PopulateComboBox(self, cbox, values, strPlaceholder = None, currTxt = None):
        cbox.blockSignals(True)
        cbox.clear()
        cbox.addItems(values)
        if strPlaceholder is not None:
            cbox.setCurrentIndex(-1)
            cbox.setEditable(True)
            cbox.setCurrentText(strPlaceholder)
        if currTxt is not None:
            cbox.setCurrentText(currTxt)
        cbox.blockSignals(False)
        
    def OnSortCat1Changed(self):
        selCat = self.ui.comboBoxSortCat1.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxSortVar1, selVars)

    def OnSortCat2Changed(self):
        selCat = self.ui.comboBoxSortCat2.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxSortVar2, selVars)


    def OnDataChanged(self):
        
        logger.info('Data changed')

        ## Make options panel visible
        self.ui.wOptions.show()

        ## Set visibility for parts of options panel
        if self.data_model_arr.data_dict is None:
            self.ui.wShowDict.hide()
        else:
            self.ui.wShowDict.show()

        if len(self.data_model_arr.datasets) == 0:
            self.ui.wActiveDset.hide()
            self.ui.wSorting.hide()
            self.ui.wShowTable.hide()
        else:
            self.ui.wActiveDset.show()
            self.ui.wSorting.show()
            self.ui.wShowTable.show()

        ## Set fields for various options
        self.active_index = self.data_model_arr.active_index
        if self.active_index >= 0:
            
            ## Get data variables
            dataset = self.data_model_arr.datasets[self.active_index]

            colNames = dataset.data.columns.tolist()
            dsetName = dataset.file_name
            dsetShape = dataset.data.shape
            catNames = dataset.data_cat_map.index.unique().tolist()
            dataset_names = self.data_model_arr.dataset_names

            ## Set data info fields
            self.ui.edit_fname.setText(os.path.basename(dsetName))
            self.ui.edit_dshape.setText(str(dsetShape))

            ## Update sorting panel
            self.UpdateSortingPanel(catNames, colNames)
            
            ## Update dataset selection
            #self.ui.comboBoxDsets.blockSignals(True)
            #logger.critical('Calling cbox update S1')           
            self.PopulateComboBox(self.ui.comboBoxDsets, dataset_names, currTxt = dataset_names[self.active_index])
            #logger.critical('Calling cbox update S2')
            #self.ui.comboBoxDsets.setCurrentText(dataset_names[self.active_index])
            #logger.critical('Calling cbox update S3')
            #self.ui.comboBoxDsets.blockSignals(False)

    def UpdateSortingPanel(self, catNames, colNames):
        
        ## Uncheck edit boxes
        self.ui.check_sort1.setChecked(False)
        self.ui.check_asc1.setChecked(False)
        self.ui.check_sort2.setChecked(False)
        self.ui.check_asc2.setChecked(False)
        
        if len(catNames) == 1:      ## Single variable category, no need for category combobox
            self.ui.comboBoxSortCat1.hide()
            self.ui.comboBoxSortCat2.hide()
        else:
            self.ui.comboBoxSortCat1.show()
            self.ui.comboBoxSortCat2.show()
            self.PopulateComboBox(self.ui.comboBoxSortCat1, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboBoxSortCat2, catNames, '--var group--')
        self.PopulateComboBox(self.ui.comboBoxSortVar1, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxSortVar2, colNames, '--var name--')

    def OnDataSelectionChanged(self):
        
        logger.info('Dataset selection changed')

        ## Set current dataset
        selDsetName = self.ui.comboBoxDsets.currentText()
        self.active_index = np.where(np.array(self.data_model_arr.dataset_names) == selDsetName)[0][0]
        self.data_model_arr.active_index = self.active_index
        
        self.data_model_arr.OnDataChanged()
        

        ### Get data variables
        #dataset = self.data_model_arr.datasets[self.active_index]
        #colNames = dataset.GetData().columns.tolist()
        #fileName = os.path.basename(self.data_model_arr.datasets[self.active_index].file_name)
        #dsetName = dataset.file_name
        #dsetShape = dataset.data.shape
        #catNames = dataset.data_cat_map.index.unique().tolist()

        ### Set data info fields
        #self.ui.edit_fname.setText(os.path.basename(dsetName))
        #self.ui.edit_dshape.setText(str(dsetShape))

        ### Update sorting panel
        #self.UpdateSortingPanel(catNames, colNames)
        

