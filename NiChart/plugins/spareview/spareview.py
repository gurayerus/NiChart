from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QMdiArea, QMdiSubWindow, QLineEdit, QComboBox, QMenu, QAction, QWidgetAction
import sys, os
import pandas as pd
import gzip
import pickle
import numpy as np
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

class SpareView(QtWidgets.QWidget,BasePlugin):

    def __init__(self):
        super(SpareView,self).__init__()
        
        self.data_model_arr = None
        self.active_index = -1
        
        self.cmds = None
        
        self.model = None

        ## Status bar of the main window
        ## Initialized by the mainwindow during loading of plugin
        self.statusbar = None

        root = os.path.dirname(__file__)
        self.readAdditionalInformation(root)
        self.ui = uic.loadUi(os.path.join(root, 'spareview.ui'),self)
        
        ## Main view panel        
        self.mdi = self.findChild(QMdiArea, 'mdiArea')       
        self.mdi.setBackground(QtGui.QColor(245,245,245,255))
                
        ## Options panel is not shown if there is no dataset loaded
        self.ui.wOptions.hide()
        
        self.ui.wOptions.setMaximumWidth(300)
        
        filename = '/home/guray/Desktop/Spare/Mdl/mdl_SPARE_AD_MUSE_single.pkl.gz'
        self.LoadModelFile(filename)

    def SetupConnections(self):
        
        self.data_model_arr.active_dset_changed.connect(self.OnDataChanged)
        
        self.ui.loadModelBtn.clicked.connect(self.OnLoadModelBtnClicked)
        self.ui.calcSpareBtn.clicked.connect(self.OnCalcSpareBtnClicked)


    def LoadModelFile(self, filename):
        #read input data
        
        # Load model
        with gzip.open(filename, 'rb') as f:
            self.mdl = pickle.load(f)
    
        logger.critical(self.mdl.keys())

    def OnLoadModelBtnClicked(self):

        #if self.dataPathLast == '':
            #directory = QtCore.QDir().homePath()
        #else:
            #directory = self.dataPathLast
        directory = QtCore.QDir().homePath()

        filename = QtWidgets.QFileDialog.getOpenFileName(None,
            caption = 'Open model file',
            directory = directory,
            filter = "Pickle/pickle.gz files (*.pkl *.gz)")

        if filename[0] == "":
            logger.warning("No file was selected")
        else:
            self.LoadModelFile(filename[0])
            
        self.statusbar.showMessage('Loaded model')

    
    def spare_test(self, df, mdl):
    
        ## Output model description
        #print('Trained on', mdl['n'], 'individuals')
        #if mdl['spare_type']=='classification':
            #print('Expected AUC =', np.round(np.mean(mdl['auc']),3))
        #elif mdl['spare_type']=='regression':
            #print('Expected MAE =', np.round(np.mean(mdl['mae']),3))
            
        # Convert categorical variables
        if 'categorical_var_map' in mdl.keys():
            for var in mdl['categorical_var_map'].keys():
                if isinstance(mdl['categorical_var_map'][var], dict):
                    df[var] = df[var].map(mdl['categorical_var_map'][var])

        # Calculate SPARE scores
        X = mdl['scaler'][0].transform(df[mdl['predictors']])
        df_results = pd.DataFrame(data={'SPARE_scores':np.sum(X * mdl['mdl'][0].coef_, axis=1) + mdl['mdl'][0].intercept_})

        return df_results


    def OnCalcSpareBtnClicked(self):

        df = self.data_model_arr.datasets[self.active_index].data
        
        logger.info('CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCc')

        dfOut = self.spare_test(df, self.mdl)
        
        logger.info(dfOut.shape)
        

    def PopulateTable(self, data):
        
        ### FIXME : Data is truncated to single precision for the display
        ### Add an option in settings to let the user change this
        data = data.round(1)

        model = PandasModel(data)
        self.dataView = QtWidgets.QTableView()
        self.dataView.setModel(model)

    def OnDataChanged(self):
        
        if self.data_model_arr.active_index >= 0:
     
            ## Make options panel visible
            self.ui.wOptions.show()
        
            ## Set fields for various options     
            self.active_index = self.data_model_arr.active_index
                
            ## Get data variables
            dataset = self.data_model_arr.datasets[self.active_index]

            ## Set active dset name
            self.ui.edit_activeDset.setText(self.data_model_arr.dataset_names[self.active_index])

            ### Update selection, sorting and drop duplicates panels
            #self.UpdatePanels(catNames, colNames)

