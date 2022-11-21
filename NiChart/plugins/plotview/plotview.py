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

import inspect

logger = iStagingLogger.get_logger(__name__)

class PlotView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(PlotView,self).__init__()

        self.data_model_arr = None
        self.active_index = -1

        self.cmds = None

        root = os.path.dirname(__file__)

        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'plotview.ui'),self)
        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
        
        ## Panel for X var
        self.ui.comboXCat = QComboBox(self.ui)
        self.ui.comboXCat.setEditable(False)
        self.ui.vlComboX.addWidget(self.ui.comboXCat)

        self.ui.comboXVar = QComboBox(self.ui)
        self.ui.comboXVar.setEditable(False)
        self.ui.vlComboX.addWidget(self.ui.comboXVar)

        ## Panel for Y var
        self.ui.comboYCat = QComboBox(self.ui)
        self.ui.comboYCat.setEditable(False)
        self.ui.vlComboY.addWidget(self.ui.comboYCat)

        self.ui.comboYVar = QComboBox(self.ui)
        self.ui.comboYVar.setEditable(False)
        self.ui.vlComboY.addWidget(self.ui.comboYVar)
        
        ## Panel for filter var
        self.ui.comboFilterCat = QComboBox(self.ui)
        self.ui.comboFilterCat.setEditable(False)
        self.ui.vlComboFilter.addWidget(self.ui.comboFilterCat)

        self.ui.comboFilterVar = QComboBox(self.ui)
        self.ui.comboFilterVar.setEditable(False)
        self.ui.vlComboFilter.addWidget(self.ui.comboFilterVar)
        
        self.ui.comboFilterVal = CheckableQComboBox(self.ui)
        self.ui.comboFilterVal.setEditable(False)
        self.ui.hlComboFilterVal.addWidget(self.ui.comboFilterVal)

        self.ui.comboFilterVal.hide()

        ## Panel for hue var
        self.ui.comboHueCat = QComboBox(self.ui)
        self.ui.comboHueCat.setEditable(False)
        self.ui.vlComboHue.addWidget(self.ui.comboHueCat)

        self.ui.comboHueVar = QComboBox(self.ui)
        self.ui.comboHueVar.setEditable(False)
        self.ui.vlComboHue.addWidget(self.ui.comboHueVar)

        self.ui.comboHueVal = CheckableQComboBox(self.ui)
        self.ui.comboHueVal.setEditable(False)
        self.ui.hlComboHueVal.addWidget(self.ui.comboHueVal)

        self.ui.comboHueVal.hide()
        
        
        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()
        
        self.ui.edit_activeDset.setReadOnly(True)               

        self.ui.wOptions.setMaximumWidth(300)
    

    def SetupConnections(self):

        self.data_model_arr.active_dset_changed.connect(lambda: self.OnDataChanged())

        self.ui.comboHueVar.currentIndexChanged.connect(lambda: self.OnHueIndexChanged())
        self.ui.comboFilterVar.currentIndexChanged.connect(lambda: self.OnFilterIndexChanged())

        self.ui.comboXCat.currentIndexChanged.connect(self.OnXCatChanged)
        self.ui.comboYCat.currentIndexChanged.connect(self.OnYCatChanged)
        self.ui.comboFilterCat.currentIndexChanged.connect(self.OnFilterCatChanged)
        self.ui.comboHueCat.currentIndexChanged.connect(self.OnHueCatChanged)

        self.ui.plotBtn.clicked.connect(lambda: self.OnPlotBtnClicked())

    def hue_regplot(self, data, x, y, hue, palette=None, **kwargs):
        regplots = []
        levels = data[hue].unique()
        if palette is None:
            default_colors = get_cmap('tab10')
            palette = {k: default_colors(i) for i, k in enumerate(levels)}
        legendhandls=[]
        for key in levels:
            regplots.append(sns.regplot(x=x, y=y, data=data[data[hue] == key], color=palette[key], **kwargs))
            legendhandls.append(Line2D([], [], color=palette[key], label=key))
        return (regplots, legendhandls)

    def OnXCatChanged(self):
        selCat = self.ui.comboXCat.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboXVar, selVars)

    def OnYCatChanged(self):
        selCat = self.ui.comboYCat.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboYVar, selVars)

    def OnFilterCatChanged(self):
        selCat = self.ui.comboFilterCat.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboFilterVar, selVars)

    def OnHueCatChanged(self):
        selCat = self.ui.comboHueCat.currentText()
        tmpData = self.data_model_arr.datasets[self.active_index]
        selVars = tmpData.data_cat_map.loc[[selCat]].VarName.tolist()
        self.PopulateComboBox(self.ui.comboHueVar, selVars)

    def OnFilterIndexChanged(self):
        
        ## Threshold to show categorical values for selection
        TH_NUM_UNIQ = 20    
        
        selFilter = self.ui.comboFilterVar.currentText()
        selFilterVals = self.data_model_arr.datasets[self.active_index].data[selFilter].unique()
        
        if len(selFilterVals) < TH_NUM_UNIQ:
            self.PopulateComboBox(self.ui.comboFilterVal, selFilterVals)
            self.ui.comboFilterVal.show()
            
        else:
            print('Too many unique values for selection, skip : ' +  selFilter + ' ' + str(len(selFilterVals)))

    def OnHueIndexChanged(self):
        
        TH_NUM_UNIQ = 20
        
        selHue = self.ui.comboHueVar.currentText()
        selHueVals = self.data_model_arr.datasets[self.active_index].data[selHue].unique()
        
        if len(selHueVals) < TH_NUM_UNIQ:
            self.PopulateComboBox(self.ui.comboHueVal, selHueVals)
            self.ui.comboHueVal.show()
            
        else:
            print('Too many unique values for selection, skip : ' + str(len(selHueVals)))



    def PlotData(self, axes, df, xVar, yVar, filterVar, filterVals, hueVar, hueVals):

        ## Get data
        colSel = [xVar, yVar]
        if len(filterVals)>0:
            colSel.append(filterVar)
        if len(hueVals)>0:
            colSel.append(hueVar)
        ## Remove duplicates in selected vars
        colSel = [*set(colSel)]
        
        dtmp = df[colSel]
        
        ## Filter data
        if len(filterVals)>0:
            dtmp = dtmp[dtmp[filterVar].isin(filterVals)]

        ## Get hue values
        if len(hueVals)>0:
            dtmp = dtmp[dtmp[hueVar].isin(hueVals)]

        # seaborn plot on axis
        #a = sns.scatterplot(x=xVar, y=yVar, hue=hueVar, ax=axes, s=5, data=dtmp)
        
        if len(hueVals)>0:
            a,b = self.hue_regplot(dtmp, xVar, yVar, hueVar, ax=axes)
            axes.legend(handles=b)
            
        else:
            sns.regplot(data = dtmp, x = xVar, y = yVar, ax=axes)
            
        axes.yaxis.set_ticks_position('left')
        axes.xaxis.set_ticks_position('bottom')
        sns.despine(fig=axes.get_figure(), trim=True)
        axes.get_figure().set_tight_layout(True)
        axes.set(xlabel=xVar)
        axes.set(ylabel=yVar)


    def OnPlotBtnClicked(self):

        dset_name = self.data_model_arr.dataset_names[self.active_index]        

        ## Read data
        df = self.data_model_arr.datasets[self.active_index].data
        
        ## Read user selections for the plot
        xVar = self.ui.comboXVar.currentText()
        yVar = self.ui.comboYVar.currentText()
        hueVar = self.ui.comboHueVar.currentText()
        hueVals = self.ui.comboHueVal.listCheckedItems()
        filterVar = self.ui.comboFilterVar.currentText()
        filterVals = self.ui.comboFilterVal.listCheckedItems()
        if filterVals == []:
            filterVar = ''
        if hueVals == []:
            hueVar = ''
        
        ## Plot data    
        self.plotCanvas = PlotCanvas(self.ui)
        self.plotCanvas.axes = self.plotCanvas.fig.add_subplot(111)

        sub = QMdiSubWindow()
        sub.setWidget(self.plotCanvas)
        self.mdi.addSubWindow(sub)        
        
        self.PlotData(self.plotCanvas.axes, df, xVar, yVar, filterVar, filterVals, hueVar, hueVals)
        self.plotCanvas.draw()
        
        sub.show()
        self.mdi.tileSubWindows()
        
        ##-------
        ## Populate commands that will be written in a notebook
        dset_name = self.data_model_arr.dataset_names[self.active_index]       

        ## Add function definitons to notebook
        fCode = inspect.getsource(self.hue_regplot).replace('(self, ','(')
        self.cmds.add_funcdef('hue_regplot', ['', fCode, ''])

        fCode = inspect.getsource(self.PlotData).replace('(self, ','(').replace('self.','').replace('ax=axes','')
        self.cmds.add_funcdef('PlotData', ['', fCode, ''])

        ## Add cmds to call the function
        cmds = ['']
        cmds.append('# Plot data')

        cmds.append('xVar = "' + xVar + '"')

        cmds.append('yVar = "' + yVar + '"')

        cmds.append('filterVar = "' + filterVar + '"')

        str_filterVals = '[' + ','.join('"{0}"'.format(x) for x in filterVals) + ']'
        cmds.append('filterVals = ' + str_filterVals)

        cmds.append('hueVar = "' + hueVar + '"')

        str_hueVals = '[' + ','.join('"{0}"'.format(x) for x in hueVals) + ']'
        cmds.append('hueVals = ' + str_hueVals)

        cmds.append('f, axes = plt.subplots(1, 1, figsize=(5, 4), dpi=100)')

        cmds.append('axes = PlotData(axes, ' + dset_name + ', xVar, yVar, filterVar, filterVals, hueVar, hueVals)')
        
        #cmds.append('plt.show()')

        cmds.append('')
        self.cmds.add_cmd(cmds)
        ##-------
        
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
            self.ui.comboXCat.hide()
            self.ui.comboYCat.hide()
            self.ui.comboFilterCat.hide()
            self.ui.comboHueCat.hide()
        else:
            self.ui.comboXCat.show()
            self.ui.comboYCat.show()
            self.ui.comboFilterCat.show()
            self.ui.comboHueCat.show()
            self.PopulateComboBox(self.ui.comboXCat, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboYCat, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboFilterCat, catNames, '--var group--')
            self.PopulateComboBox(self.ui.comboHueCat, catNames, '--var group--')
        self.PopulateComboBox(self.ui.comboXVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboYVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboFilterVar, colNames, '--var name--')
        self.PopulateComboBox(self.ui.comboHueVar, colNames, '--var name--')
        
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
        
