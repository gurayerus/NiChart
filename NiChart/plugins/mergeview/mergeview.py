from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QTextEdit, QComboBox
import sys, os
import pandas as pd
import numpy as np
from NiChart.core.dataio import DataIO
# import dtale
from NiChart.core.baseplugin import BasePlugin
from NiChart.core import iStagingLogger
from NiChart.core.gui.SearchableQComboBox import SearchableQComboBox
from NiChart.core.gui.CheckableQComboBox import CheckableQComboBox
from NiChart.core.model.datamodel import PandasModel

logger = iStagingLogger.get_logger(__name__)


class MergeView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(MergeView,self).__init__()
        
        self.data_model_arr = None
        self.active_index = -1
        self.dataset2_index = -1
        
        self.cmds = None

        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'mergeview.ui'),self)
        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
                
        ### Panel for dset1 merge variables selection
        #self.ui.comboBoxMergeCat1 = CheckableQComboBox(self.ui)
        #self.ui.comboBoxMergeCat1.setEditable(False)
        #self.ui.vlComboMerge1.addWidget(self.ui.comboBoxMergeCat1)
        
        self.ui.comboBoxMergeVar1 = CheckableQComboBox(self.ui)
        self.ui.comboBoxMergeVar1.setEditable(False)
        self.ui.vlComboMerge1.addWidget(self.ui.comboBoxMergeVar1)

        ## Panel for dset2 selection
        self.ui.comboBoxDataset2 = QComboBox(self.ui)
        self.ui.hlMergeDset2.addWidget(self.ui.comboBoxDataset2)

        ### Panel for dset2 merge variables selection
        #self.ui.comboBoxMergeCat2 = CheckableQComboBox(self.ui)
        #self.ui.comboBoxMergeCat2.setEditable(False)
        #self.ui.vlComboMerge2.addWidget(self.ui.comboBoxMergeCat2)
        
        self.ui.comboBoxMergeVar2 = CheckableQComboBox(self.ui)
        self.ui.comboBoxMergeVar2.setEditable(False)
        self.ui.vlComboMerge2.addWidget(self.ui.comboBoxMergeVar2)

        self.ui.wOptions.setMaximumWidth(300)
        
        
        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()

    

    def SetupConnections(self):
        self.data_model_arr.active_dset_changed.connect(lambda: self.OnDataChanged())        

        #self.ui.comboBoxMergeCat1.view().pressed.connect(self.OnMergeCat1Selected)
        #self.ui.comboBoxMergeCat2.view().pressed.connect(self.OnMergeCat2Selected)

        self.ui.comboBoxDataset2.currentIndexChanged.connect(lambda: self.OnDataset2Changed())

        self.ui.mergeBtn.clicked.connect(lambda: self.OnMergeDataBtnClicked())


    def OnDataset2Changed(self):
        logger.info('Dataset2 selection changed')
        selDsetName = self.ui.comboBoxDataset2.currentText()
        self.dataset2_index = np.where(np.array(self.data_model_arr.dataset_names) == selDsetName)[0][0]
        
        colNames = self.data_model_arr.datasets[self.dataset2_index].data.columns.tolist()
        
        self.PopulateComboBox(self.ui.comboBoxMergeVar2, colNames)
        self.ui.comboBoxMergeVar2.show()
        self.ui.label_mergeon2.show()
        
        logger.info('Dataset2 changed to : ' + selDsetName)
        logger.info('Dataset2 index changed to : ' + str(self.dataset2_index))


    def OnMergeDataBtnClicked(self):

        plot_cmds = []
        dset_name = self.data_model_arr.dataset_names[self.active_index]        
        dset_name2 = self.data_model_arr.dataset_names[self.dataset2_index]        
        
        mergeFields1 = self.ui.comboBoxMergeVar1.listCheckedItems()
        mergeFields2 = self.ui.comboBoxMergeVar1.listCheckedItems()

        str_mergeFields1 = str_filterVarVals = ','.join('"{0}"'.format(x) for x in mergeFields1)
        str_mergeFields2 = str_filterVarVals = ','.join('"{0}"'.format(x) for x in mergeFields2)

        dtmp1 = self.data_model_arr.datasets[self.active_index].data
        dtmp2 = self.data_model_arr.datasets[self.dataset2_index].data
        
        dtmp1 = dtmp1.merge(dtmp2, left_on = mergeFields1, right_on = mergeFields2)
        
        self.data_model_arr.datasets[self.active_index].data = dtmp1
    
        plot_cmds.append(dset_name + ' = ' + dset_name + '.merge(' + dset_name2 + 
                         ', right_on = [' + str_mergeFields1 +'], left_on = [' + str_mergeFields2 + '])')

        plot_cmds.append(dset_name + '.head()')
    
        self.dataView = QtWidgets.QTableView()
        
        ## Load data to data view (reduce data size to make the app run faster)
        tmpData = self.data_model_arr.datasets[self.active_index].data
        tmpData = tmpData.head(self.data_model_arr.TABLE_MAXROWS)
        self.PopulateTable(tmpData)

        self.cmds.add_cmd('')
        self.cmds.add_cmds(plot_cmds)
        self.cmds.add_cmd('')

        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()

    def PopulateTable(self, data):
        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    # Add the values to comboBox
    def PopulateComboBox(self, cbox, values, strPlaceholder = None, bypassCheckable=False):
        cbox.blockSignals(True)
        cbox.clear()

        if bypassCheckable:
            cbox.addItemsNotCheckable(values)  ## The checkableqcombo for var categories
                                               ##   should not be checkable
        else:
            cbox.addItems(values)
            
        if strPlaceholder is not None:
            cbox.setCurrentIndex(-1)
            cbox.setEditable(True)
            cbox.setCurrentText(strPlaceholder)
        cbox.blockSignals(False)
        
    def OnDataChanged(self):

        ## rge , there should be at least 2 datasets
        if self.data_model_arr.active_index >= 1:
     
            ## Make options panel visible
            self.ui.wOptions.show()
        
            ## Set fields for various options     
            self.active_index = self.data_model_arr.active_index
                
            ## Get data variables
            dataset = self.data_model_arr.datasets[self.active_index]
            dsetName = self.data_model_arr.dataset_names[self.active_index]
            colNames = dataset.data.columns.tolist()
            catNames = dataset.data_cat_map.index.unique().tolist()

            ## Set active dset name
            self.ui.edit_dset1.setText(dsetName)

            ## Update Merge Vars for dset1 and dset2
            self.PopulateComboBox(self.ui.comboBoxMergeVar1, colNames, '--var name--')
            self.PopulateComboBox(self.ui.comboBoxMergeVar2, colNames, '--var name--')

            ## Var selection for dataset2 is hidden until the user selects the dataset
            self.ui.comboBoxMergeVar2.hide()
            self.ui.label_mergeon2.hide()
            
            dataset_names = self.data_model_arr.dataset_names.copy()
            dataset_names.remove(dsetName)
            
            self.PopulateComboBox(self.ui.comboBoxDataset2, dataset_names, '--dset name--')
