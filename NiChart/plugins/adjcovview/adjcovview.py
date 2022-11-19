from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QTextEdit, QComboBox
import sys, os
import pandas as pd
from NiChart.core.dataio import DataIO
# import dtale
from NiChart.core.baseplugin import BasePlugin
from NiChart.core import iStagingLogger
from NiChart.core.gui.SearchableQComboBox import SearchableQComboBox
from NiChart.core.gui.CheckableQComboBox import CheckableQComboBox
from NiChart.core.plotcanvas import PlotCanvas
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import get_cmap
from matplotlib.lines import Line2D
import statsmodels.formula.api as sm

logger = iStagingLogger.get_logger(__name__)

class AdjCovView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(AdjCovView,self).__init__()

        self.data_model_arr = None
        self.active_index = -1

        self.cmds = None

        root = os.path.dirname(__file__)

        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'adjcovview.ui'),self)
        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
        
        ## Panel for outcome vars
        self.ui.comboBoxOutCat = CheckableQComboBox(self.ui)
        self.ui.comboBoxOutCat.setEditable(False)
        self.ui.vlComboOut.addWidget(self.ui.comboBoxOutCat)

        self.ui.comboBoxOutVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxOutVar.setEditable(False)
        self.ui.vlComboOut.addWidget(self.ui.comboBoxOutVar)
        
        ## Panel for cov to keep
        self.ui.comboBoxCovKeepCat = CheckableQComboBox(self.ui)
        self.ui.comboBoxCovKeepCat.setEditable(False)
        self.ui.vlComboCovKeep.addWidget(self.ui.comboBoxCovKeepCat)

        self.ui.comboBoxCovKeepVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxCovKeepVar.setEditable(False)
        self.ui.vlComboCovKeep.addWidget(self.ui.comboBoxCovKeepVar)
        
        ## Panel for cov to correct
        self.ui.comboBoxCovCorrCat = CheckableQComboBox(self.ui)
        self.ui.comboBoxCovCorrCat.setEditable(False)
        self.ui.vlComboCovCorr.addWidget(self.ui.comboBoxCovCorrCat)

        self.ui.comboBoxCovCorrVar = CheckableQComboBox(self.ui)
        self.ui.comboBoxCovCorrVar.setEditable(False)
        self.ui.vlComboCovCorr.addWidget(self.ui.comboBoxCovCorrVar)

        ## Panel for selection
        self.ui.comboBoxSelCat = QComboBox(self.ui)
        self.ui.comboBoxSelCat.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelCat)

        self.ui.comboBoxSelVar = QComboBox(self.ui)
        self.ui.comboBoxSelVar.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelVar)

        self.ui.comboBoxSelVal = CheckableQComboBox(self.ui)
        self.ui.comboBoxSelVal.setEditable(False)
        self.ui.vlComboSel.addWidget(self.ui.comboBoxSelVal)

        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()

        self.ui.edit_activeDset.setReadOnly(True)

        self.ui.wOptions.setMaximumWidth(300)
        


    def SetupConnections(self):
        self.data_model_arr.active_dset_changed.connect(lambda: self.OnDataChanged())

        self.ui.comboBoxSelVar.currentIndexChanged.connect(lambda: self.OnSelIndexChanged())

        self.ui.comboBoxOutCat.view().pressed.connect(self.OnOutCatSelected)
        self.ui.comboBoxCovKeepCat.view().pressed.connect(self.OnCovKeepCatSelected)
        self.ui.comboBoxCovCorrCat.view().pressed.connect(self.OnCovCorrCatSelected)
        self.ui.comboBoxSelCat.currentIndexChanged.connect(self.OnSelCatChanged)

        self.ui.adjCovBtn.clicked.connect(lambda: self.OnAdjCovBtnClicked())

    def OnOutCatSelected(self, index):

        selItem = self.ui.comboBoxOutCat.model().itemFromIndex(index) 
        
        ## Read selected cat value
        selCat = selItem.text()

        logger.info(selCat)

        ## Get list of cat to var name mapping
        dmap = self.data_model_arr.datasets[self.active_index].data_cat_map
        
        ## Check status of edit box for sel category
        isChecked = selItem.checkState()
        
        ## Set/reset check mark for selected var names in combobox for variables
        ## Update sel cat check box
        checkedVars = dmap.loc[[selCat]].VarName.tolist()
        
        if selItem.checkState() == QtCore.Qt.Checked: 
            self.ui.comboBoxOutVar.uncheckItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.ui.comboBoxOutVar.checkItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Checked)

    def OnCovKeepCatSelected(self, index):

        selItem = self.ui.comboBoxCovKeepCat.model().itemFromIndex(index) 
        
        ## Read selected cat value
        selCat = selItem.text()

        ## Get list of cat to var name mapping
        dmap = self.data_model_arr.datasets[self.active_index].data_cat_map
        
        ## Check status of edit box for sel category
        isChecked = selItem.checkState()
        
        ## Set/reset check mark for selected var names in combobox for variables
        ## Update sel cat check box
        checkedVars = dmap.loc[[selCat]].VarName.tolist()
        
        logger.info(checkedVars)
        
        if selItem.checkState() == QtCore.Qt.Checked: 
            self.ui.comboBoxCovKeepVar.uncheckItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.ui.comboBoxCovKeepVar.checkItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Checked)
        #logger.info(checkedVars)

    def OnCovCorrCatSelected(self, index):

        selItem = self.ui.comboBoxCovCorrCat.model().itemFromIndex(index) 
        
        ## Read selected cat value
        selCat = selItem.text()

        ## Get list of cat to var name mapping
        dmap = self.data_model_arr.datasets[self.active_index].data_cat_map
        
        ## Check status of edit box for sel category
        isChecked = selItem.checkState()
        
        ## Set/reset check mark for selected var names in combobox for variables
        ## Update sel cat check box
        checkedVars = dmap.loc[[selCat]].VarName.tolist()
        
        logger.info(checkedVars)
        
        if selItem.checkState() == QtCore.Qt.Checked: 
            self.ui.comboBoxCovCorrVar.uncheckItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Unchecked)
        else:
            self.ui.comboBoxCovCorrVar.checkItems(checkedVars)      ## Selected vars are set to "checked"
            selItem.setCheckState(QtCore.Qt.Checked)
        #logger.info(checkedVars)

    def OnSelCatChanged(self):
        selCat = self.ui.comboBoxSelCat.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboBoxSelVar, selVars)

    ## Apply a linear regression model and correct for covariates
    ## It runs independently for each outcome variable
    ## The estimation is done on the selected subset and then applied to all samples
    ## The user can indicate covariates that will be corrected and not
    def AdjCov(self, df, outVars, covCorrVars, covKeepVars=None, selCol=None, selVals=None, outSuff='_COVADJ'):
        
        dfInit = df.copy()
        
        ## Combine covariates (to keep + to correct)
        #if covKeepVars is None:
        if covKeepVars is []:
            covList = covCorrVars;
            isCorr = list(np.ones(len(covCorrVars)).astype(int))
        else:
            covList = covKeepVars + covCorrVars;
            isCorr = list(np.zeros(len(covKeepVars)).astype(int)) + list(np.ones(len(covCorrVars)).astype(int))
        str_covList = ' + '.join(covList)
        
        ## Prep data
        TH_MAX_NUM_CAT = 10
        dfCovs = []
        isCorrArr = []
        for i, tmpVar in enumerate(covList):
            ## Detect if var is categorical
            is_num = pd.to_numeric(df[tmpVar].dropna(), errors='coerce').notnull().all()
            if df[tmpVar].unique().shape[0] < TH_MAX_NUM_CAT:
                is_num = False
            ## Create dummy vars for categorical data
            if is_num == False:
                dfDummy = pd.get_dummies(df[tmpVar], prefix=tmpVar, drop_first=True)
                dfCovs.append(dfDummy)
                isCorrArr = isCorrArr + list(np.zeros(dfDummy.shape[1]).astype(int)+isCorr[i])
            else:
                dfCovs.append(df[tmpVar])
                isCorrArr.append(isCorr[i])
        dfCovs = pd.concat(dfCovs, axis=1)

        ## Get cov names
        covVars = dfCovs.columns.tolist()
        str_covVars = ' + '.join(covVars)

        ## Get data with all vars
        df = pd.concat([df[outVars], dfCovs], axis=1)

        ## Select training dataset (regression parameters estimated from this set)
        if selVals == []:
            dfTrain = df
        else:
            dfTrain = df[df[selCol]==selVals]

        ## Fit and apply model for each outcome var
        for i, tmpOutVar in enumerate(outVars):
            ## Fit model
            str_model = tmpOutVar + '  ~ ' + str_covVars

            logger.info(' Running model : ' + str_model)
            logger.info(' ddddd : ' + df.columns)
            logger.info(covVars)
            logger.info(isCorrArr)

            mod = sm.ols(str_model, data=dfTrain)
            res = mod.fit()

            ## Apply model
            corrVal = df[tmpOutVar]

            for j, tmpCovVar in enumerate(covVars):
                if isCorrArr[j] == 1:
                    corrVal = corrVal - df[tmpCovVar]*res.params[tmpCovVar]
            dfInit[tmpOutVar + outSuff] = corrVal
        
        return dfInit

    def OnAdjCovBtnClicked(self):
        
        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Read data
        dtmp = self.data_model_arr.datasets[self.active_index].data
        
        ## Read user selections for correction
        outVars = self.ui.comboBoxOutVar.listCheckedItems()
        covKeepVars = self.ui.comboBoxCovKeepVar.listCheckedItems()
        covCorrVars = self.ui.comboBoxCovCorrVar.listCheckedItems()
        selCol = self.ui.comboBoxSelVar.currentText()
        selVals = self.ui.comboBoxSelVal.listCheckedItems()
        outSuff = self.ui.edit_outSuff.text()
        
        logger.info(outVars)
        
        ## Correct data    
        dcorr = self.AdjCov(dtmp, outVars, covCorrVars, covKeepVars, selCol, selVals, outSuff)

        ## Update data
        self.data_model_arr.datasets[self.active_index].data = dcorr

        #self.dataView = QtWidgets.QTableView()
        #plot_cmds = self.PopulateTable()
        
        #self.cmds.add_cmd('')
        #self.cmds.add_cmds(plot_cmds)
        #self.cmds.add_cmd('')


        #sub = QMdiSubWindow()
        #sub.setWidget(self.dataView)
        
        #self.mdi.addSubWindow(sub)        
        #sub.show()
        #self.mdi.tileSubWindows()

    def PopulateSelect(self):

        #get data column header names
        colNames = self.data_model_arr.datasets[self.active_index].data.columns.tolist()

        #add the list items to comboBox
        self.ui.comboBoxSelect.blockSignals(True)
        self.ui.comboBoxSelect.clear()
        self.ui.comboBoxSelect.addItems(colNames)
        self.ui.comboBoxSelect.blockSignals(False)

    def OnSelColChanged(self):
        
        ## Threshold to show categorical values for selection
        TH_NUM_UNIQ = 20    
        
        selcol = self.ui.comboBoxSelCol.currentText()
        dftmp = self.data_model_arr.datasets[self.active_index].data[selcol]
        val_uniq = dftmp.unique()
        num_uniq = len(val_uniq)

        self.ui.comboBoxSelVals.show()

        ## Select values if #unique values for the field is less than set threshold
        if num_uniq <= TH_NUM_UNIQ:
            #self.ui.wFilterNumerical.hide()
            #self.ui.wFilterCategorical.show()
            self.PopulateComboBox(self.ui.comboBoxSelVals, val_uniq)
        
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

    
    def OnSelIndexChanged(self):
        
        TH_NUM_UNIQ = 20
        
        selCol = self.ui.comboBoxSelVar.currentText()
        selColVals = self.data_model_arr.datasets[self.active_index].data[selCol].unique()
        
        if len(selColVals) < TH_NUM_UNIQ:
            self.PopulateComboBox(self.ui.comboBoxSelVal, selColVals)
        else:
            print('Too many unique values for selection, skip : ' + str(len(selColVals)))

    
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
            self.ui.comboBoxOutCat.hide()
            self.ui.comboBoxCovKeepCat.hide()
            self.ui.comboBoxCovKeepCat.hide()
            self.ui.comboBoxSelCat.hide()
        else:
            self.ui.comboBoxOutCat.show()
            self.ui.comboBoxCovKeepCat.show()
            self.ui.comboBoxCovKeepCat.show()
            self.ui.comboBoxSelCat.show()
            self.PopulateComboBox(self.ui.comboBoxOutCat, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboBoxCovKeepCat, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboBoxCovCorrCat, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboBoxSelCat, catNames, '--var group--')
        self.PopulateComboBox(self.ui.comboBoxOutVar, colNames)
        self.PopulateComboBox(self.ui.comboBoxCovKeepVar, colNames)
        self.PopulateComboBox(self.ui.comboBoxCovCorrVar, colNames)
        self.PopulateComboBox(self.ui.comboBoxSelVar, colNames)



