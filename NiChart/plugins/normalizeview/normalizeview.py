from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QLineEdit, QComboBox, QMenu, QAction, QWidgetAction
import sys, os
import pandas as pd
from NiChart.core.dataio import DataIO
# import dtale
from NiChart.core.baseplugin import BasePlugin
from NiChart.core import iStagingLogger
from NiChart.core.gui.SearchableQComboBox import SearchableQComboBox
from NiChart.core.gui.CheckableQComboBox import CheckableQComboBox
from NiChart.core.gui.NestedQMenu import NestedQMenu
from NiChart.core.model.datamodel import PandasModel

import inspect

logger = iStagingLogger.get_logger(__name__)

class NormalizeView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(NormalizeView,self).__init__()
        
        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None        

        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'normalizeview.ui'),self)
        
        ## Main view panel        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
                
        ## Panel for Divide By
        self.ui.comboBoxDivideByCat = QComboBox(self.ui)
        self.ui.comboBoxDivideByCat.setEditable(False)
        self.ui.vlComboDivideBy.addWidget(self.ui.comboBoxDivideByCat)

        self.ui.comboBoxDivideByVar = QComboBox(self.ui)
        self.ui.comboBoxDivideByVar.setEditable(False)
        self.ui.vlComboDivideBy.addWidget(self.ui.comboBoxDivideByVar)

        ## Panel for Apply To
        self.ui.comboBoxSelCat = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelCat.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelCat)

        self.ui.comboBoxSelVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelVar.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelVar)

        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()
        
        self.ui.wOptions.setMaximumWidth(300)
        

    def SetupConnections(self):
        
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)
        
        self.ui.normalizeBtn.clicked.connect(self.OnNormalizeBtnClicked)

        self.ui.comboBoxSelCat.view().pressed.connect(self.OnApplyToCatSelected)

        self.ui.comboBoxDivideByCat.currentIndexChanged.connect(self.OnDivideByCatChanged)

        ## https://gist.github.com/ales-erjavec/7624dd1d183dfbfb3354600b285abb94

    def OnApplyToCatSelected(self, index):
        
        selItem = self.ui.comboBoxSelCat.model().itemFromIndex(index) 
        
        ## Read selected cat value
        selCat = selItem.text()

        ## Get list of cat to var name mapping
        dmap = self.data_model_arr.datasets[self.active_index].data_cat_map
        
        ## Check status of edit box for sel category
        isChecked = selItem.checkState()
        
        ## Set/reset check mark for selected var names in combobox for variables
        ## Update sel cat check box
        checkedVars = dmap.loc[[selCat]].VarName.tolist()
        if selItem.checkState() == QtCore.Qt.Checked: 
            self.ui.comboBoxSelVar.uncheckItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.ui.comboBoxSelVar.checkItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Checked)
        
        #logger.info(checkedVars)


    def OnDivideByCatChanged(self):
        selCat = self.ui.comboBoxDivideByCat.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxDivideByVar, selVars)

    def PopulateTable(self, data):
        
        ### FIXME : Data is truncated to single precision for the display
        ### Add an option in settings to let the user change this
        data = data.round(1)

        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    #add the values to comboBox
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
        
        if self.data_model_arr.active_index >= 0:
     
            ## Make options panel visible
            self.ui.wOptions.show()
        
            ## Set fields for various options     
            self.active_index = self.data_model_arr.active_index
                
            ## Get data variables
            dataset = self.data_model_arr.datasets[self.active_index]
            colNames = dataset.data.columns.tolist()
            catNames = dataset.data_cat_map.index.unique().tolist()

            logger.info(self.active_index)
            logger.info(catNames)
            
            ## Set active dset name
            self.ui.edit_activeDset.setText(self.data_model_arr.dataset_names[self.active_index])

            ## Update selection, sorting and drop duplicates panels
            self.UpdatePanels(catNames, colNames)

    def UpdatePanels(self, catNames, colNames):
        
        if len(catNames) == 1:      ## Single variable category, no need for category combobox
            self.ui.comboBoxDivideByCat.hide()
            self.ui.comboBoxSelCat.hide()
        else:
            self.ui.comboBoxDivideByCat.show()
            self.ui.comboBoxSelCat.show()
            self.PopulateComboBox(self.ui.comboBoxDivideByCat, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboBoxSelCat, catNames, '--var group--')
        self.PopulateComboBox(self.ui.comboBoxDivideByVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboBoxSelVar, colNames, '--var name--')
    
    ## Normalize data by the given variable
    def NormalizeData(self, df, selVars, normVar, outSuff):
        dfNorm = 100 * df[selVars].div(df[normVar], axis=0)
        dfNorm = dfNorm.add_suffix(outSuff)
        outVarNames = dfNorm.columns.tolist()
        dfOut = pd.concat([df, dfNorm], axis=1)        
        return dfOut, outVarNames
    
    def OnNormalizeBtnClicked(self):
        
        ## Read normalize options
        normVar = self.ui.comboBoxDivideByVar.currentText()
        selVars = self.ui.comboBoxSelVar.listCheckedItems()
        outSuff = self.ui.edit_outSuff.text()
        if outSuff == '':
            outSuff = 'NORM'
        if outSuff[0] == '_':
            outSuff = outSuff[1:]
        outCat = outSuff

        ## Apply normalization
        df = self.data_model_arr.datasets[self.active_index].data
        dfNorm, outVarNames = self.NormalizeData(df, selVars, normVar, outSuff)

        ## Set updated dset
        self.data_model_arr.datasets[self.active_index].data = dfNorm
        
        ## Create dict with info about new columns
        outDesc = 'Created by NiChart NormalizeView Plugin'
        outSource = 'NiChart NormalizeView Plugin'
        self.data_model_arr.AddNewVarsToDict(outVarNames, outCat, outDesc, outSource)
            
        ## Call signal for change in data
        self.data_model_arr.OnDataChanged()
        
        ## Load data to data view 
        self.dataView = QtWidgets.QTableView()
        
        ## Reduce data size to make the app run faster
        tmpData = self.data_model_arr.datasets[self.active_index].data
        tmpData = tmpData.head(self.data_model_arr.TABLE_MAXROWS)

        ## Show only columns involved in application
        tmpData = tmpData[outVarNames]
        
        self.PopulateTable(tmpData)
                                                                                                                        
        ## Set data view to mdi widget
        sub = QMdiSubWindow()
        sub.setWidget(self.dataView)
        self.mdi.addSubWindow(sub)        
        sub.show()
        self.mdi.tileSubWindows()
        
        ## Display status
        self.statusbar.showMessage('Displaying normalized outcome variables')                

        ##-------
        ## Populate commands that will be written in a notebook
        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Add NormalizeData function definiton to notebook
        fCode = inspect.getsource(self.NormalizeData).replace('(self, ','(')
        self.cmds.add_funcdef('NormalizeData', ['', fCode, ''])
        
        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Normalize data')

        str_selVars = '[' + ','.join('"{0}"'.format(x) for x in selVars) + ']'
        cmds.append('selVars = ' + str_selVars)

        cmds.append('normVar = "' + normVar + '"')
        
        cmds.append('outSuff  = "' + outSuff + '"')
        
        cmds.append(dset_name + ', outVarNames = NormalizeData(' + dset_name + ', selVars, normVar, outSuff)')
        
        cmds.append(dset_name + '[outVarNames].head()')
        cmds.append('')
        self.cmds.add_cmd(cmds)
        ##-------
   
    
