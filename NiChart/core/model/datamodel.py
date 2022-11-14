# This Python file uses the following encoding: utf-8
"""
contact: software@cbica.upenn.edu
Copyright (c) 2018 University of Pennsylvania. All rights reserved.
Use of this source code is governed by license located in license file: https://github.com/CBICA/NiChart/blob/main/LICENSE
"""

import pandas as pd
import numpy as np
import neuroHarmonize as nh
import importlib.resources as pkg_resources
import sys
import joblib
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5 import QtCore
from NiChart.core import iStagingLogger

logger = iStagingLogger.get_logger(__name__)

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data
        self.header_labels = None

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        self.header_labels = self._data.keys()
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.header_labels[section]
        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return QtCore.QVariant(str(
                    self._data.iloc[index.row()][index.column()]))
        return QtCore.QVariant()


class DataModelArr(QObject):
    """This class holds a collection of data models."""

    active_dset_changed = QtCore.pyqtSignal()

    def __init__(self):

        logger.info('In DataModelArr constructor')

        QObject.__init__(self)
        """The constructor."""
        
        self._datasets = []         ## An array of datasets
        self._data_dict = None      ## Data dictionary
                                    ## Note: We keep a single dictionary and concat multiple
                                    ##  dictionaries, with the assumption that multiple dictionaries
                                    ##  are consistent (the last one will overwrite otherwise) and
                                    ##  they are common to all datasets
                                    
        self._dataset_names = []    ## Names of datasets (auto generated for now)
        
        self._active_index = -1     ## An index that keeps the index of active dataset

        logger.info('Exit DataModelArr constructor')

    ## Setter and Getter functions for all variables 
    ## https://stackoverflow.com/questions/2627002/whats-the-pythonic-way-to-use-getters-and-setters

    #############################
    ## decorators for datasets
    @property
    def datasets(self):
        return self._datasets

    @datasets.setter
    def datasets(self, value):
        self._datasets = value

    @datasets.deleter
    def datasets(self):
        del self._datasets

    #############################
    ## decorators for data_dict
    @property
    def data_dict(self):
        return self._data_dict

    @data_dict.setter
    def data_dict(self, value):
        self._data_dict = value

    @data_dict.deleter
    def data_dict(self):
        del self._data_dict

    #############################
    ## decorators for dataset_names
    @property
    def dataset_names(self):
        return self._dataset_names

    @dataset_names.setter
    def dataset_names(self, value):
        self._dataset_names = value

    @dataset_names.deleter
    def dataset_names(self):
        del self._dataset_names

    #############################
    ## decorators for active_index
    @property
    def active_index(self):
        return self._active_index

    @active_index.setter
    def active_index(self, value):
        self._active_index = value

    @active_index.deleter
    def active_index(self):
        del self._active_index

    #############################
    ## Function to add new dataset
    def AddDataset(self, value):

        logger.info('In DataModelArr.AddDataSet()')

        ## Get new index for dataset
        self.active_index = len(self.datasets)
        
        ## Add dataset
        self.datasets.append(value)
        
        ## Add dataset name        
        self.dataset_names.append('DSET_' + str(self.active_index))
        
        ## Apply data dictionary
        self.datasets[self.active_index].ApplyDict(self.data_dict)
        
        logger.info('Exit DataModelArr.AddDataSet()')
        
    #############################
    ## Emit signal when data was changed
    def OnDataChanged(self):
        logger.info('Signal to emit: active_dset_changed')
        self.active_dset_changed.emit()

    #############################
    ## Add data dictionary
    def AddDataDict(self, dfDict):

        logger.info('In DataModelArr.AddDataDict()')

        ## Update current data dictionary
        if self.data_dict is None:
            self.data_dict = dfDict
            
        else:
            ## Add new dict to old one, overwrite those with same index
            tmpDict = pd.concat([self.data_dict, dfDict])
            tmpDict = tmpDict[~tmpDict.index.duplicated(keep='last')]
            self.data_dict = tmpDict

        ## Apply updated data dict on each dataset
        
        if len(self.datasets) > 0:                              ## FIXME this is not necessary
            for i in np.arange(0, len(self.datasets)):
                self.datasets[i].ApplyDict(self.data_dict)

        logger.info('Exit DataModelArr.AddDataDict()')
        

class DataModel(QObject):
    """This class holds the data model."""

    dset_changed = QtCore.pyqtSignal()

    def __init__(self, data=None, fname=None, data_index=None):
        QObject.__init__(self)

        self._data = None        ## The dataset (a pandas dataframe)
        self._data_dict = None   ## The dictionary with info about variables (a pandas dataframe)
        self._data_cat_map = None   ## Keeps a list of mapping between var names and categories
        self._data_dict_inv_map = None   ## A dict to keep inverse mapping between vars and dict var names
        self._file_name = None   ## The name of the data file

        if data is not None: 
            self.data = data
            self.file_name = fname
            self.data_index = data_index

            ## Create dict with default placeholder values
            dictCols = ['VarName', 'VarDesc', 'VarCat', 'SourceDict']
            dfDict = pd.DataFrame(index = data.columns, columns = dictCols)
            dfDict['VarName'] = dfDict.index
            dfDict['VarDesc'] = 'No Description'
            #dfDict['VarDesc'] = dfDict.VarDesc.apply(lambda x: [x])
            dfDict['VarCat'] = 'No Category'
            dfDict['VarCat'] = dfDict.VarCat.apply(lambda x: [x])
            dfDict['SourceDict'] = 'No dictionary file'
            self.data_dict = dfDict
            

    ## Setter and Getter functions for all variables 
    ## https://stackoverflow.com/questions/2627002/whats-the-pythonic-way-to-use-getters-and-setters

    #############################
    ## decorators for data
    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @data.deleter
    def data(self):
        del self._data

    #############################
    ## decorators for data_dict
    @property
    def data_dict(self):
        return self._data_dict

    @data_dict.setter
    def data_dict(self, value):

        logger.info('In DataModel setter for data_dict')

        self._data_dict = value
        
        ### inverse map used to switch between default names (Var) and dict names (VarName)
        ### in a simple way (backward search is done using VarName as an index)
        #tmpMap = value[['VarName']].reset_index().set_index('VarName')
        #tmpMap.columns = ['Var']
        #self._data_dict_inv_map = tmpMap
        
        logger.info('Exit DataModel setter for data_dict')

    @data_dict.deleter
    def data_dict(self):
        del self._data_dict

    #############################
    ## decorators for data_cat_map
    @property
    def data_cat_map(self):
        return self._data_cat_map

    @data_cat_map.setter
    def data_cat_map(self, value):
        self._data_cat_map = value

    @data_cat_map.deleter
    def data_cat_map(self):
        del self._data_cat_map

    #############################
    ## decorators for file_name
    @property
    def file_name(self):
        return self._file_name
    @file_name.setter
    def file_name(self, value):
        self._file_name = value
    @file_name.deleter
    def file_name(self):
        del self._file_name

    #############################
    ## Check if dataset is valid
    def IsValidData(self, data=None):
        """Checks if the data is valid or not."""
        if data is None:
            data = self.data
        
        if not isinstance(data, pd.DataFrame):
            return False
        else:
            return True

    ### Use getter function
    #def GetData(self):
        #return self._data

    #############################
    ## If data columns change , update the dictionary and mapping btw categories and var names
    ##   based on current columns
    def UpdateDictNewCols(self, newCols):
        tmpDf = pd.DataFrame(data = newCols, columns = ['VarName'])
        tmpDf['Var'] = tmpDf.VarName
        tmpDf = tmpDf.set_index('Var')
        self.data_dict = pd.concat([self.data_dict, tmpDf])

        ### FIXME this should not be necessary
        ###self.data_cat_map = self.data_cat_map[self.data_cat_map.VarName.isin(currCols)]

    #############################
    ## If a subset of data columns are selected, update dict
    def UpdateDictSelCols(self, selCols):
        self.data_dict = self.data_dict[self.data_dict.VarName.isin(selCols)]
        self.data_cat_map = self.data_cat_map[self.data_cat_map.VarName.isin(selCols)]


    #############################
    ## Add the data dictionary
    def ApplyDict(self, dfDict):

        logger.info('In DataModel.ApplyDict()')

        """ Adds data dictionary to existing dictionary items."""
        """  Input dictionary (data frame) can be either:"""
        """  - Input data dictionary file"""
        """  - Created automatically by a process to annotate new variables added to the data"""
        
        ## Update dict
        ## If there are new columns in data file, add them to dict with default values
        if self.data.shape[0]>0:
            currCols = self.data.columns.tolist()
            dictVars = self.data_dict.VarName.tolist()
            newCols = list(set(currCols).difference(set(dictVars)))
            
            if len(newCols)>0:
                self.UpdateDictNewCols(newCols)

            #self.UpdateDict(self.data.columns.tolist())

            ## Update dictionary
            self.data_dict.update(dfDict)

            ## Create mapping for categories
            ##  - Get all categories from the current dictionary
            ##  - Find all variables that match with this category
            df1 = self.data_dict
            df2 = pd.DataFrame(df1['VarCat'].tolist())
            df2['VarName'] = df1.VarName.tolist()
            
            tmpList = []
            for tmpCol in df2.columns[0:-1]:
                tmpList.append(df2[[tmpCol,'VarName']].dropna().set_index(tmpCol))
            df2 = pd.concat(tmpList)
            
            self.data_cat_map = df2

            ## Update var names
            tmpData = self.data
            tmpCol = self.data_dict.index.intersection(tmpData.columns.tolist())
            tmpDf = self.data_dict.loc[tmpCol][['VarName']]
            tmpDict = dict(zip(tmpDf.index, tmpDf.VarName))
            tmpData = tmpData.rename(columns=tmpDict)

            self.data = tmpData
            
            logger.info('Exit DataModel.ApplyDict()')

    #############################
    ## Get data type of columns
    def GetColumnDataTypes(self):
        """Returns all header names for all columns in the dataset."""
        d = self.data.dtypes
        return d

    #############################
    ## Reset the data set
    def Reset(self):
        #clear all contents of data/model and release memory etc.
        #TODO: this needs to be done correctly,
        #is there a better way to clear data?
        del self.data
        self.data = None

