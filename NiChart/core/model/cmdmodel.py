# This Python file uses the following encoding: utf-8
"""
contact: software@cbica.upenn.edu
Copyright (c) 2018 University of Pennsylvania. All rights reserved.
Use of this source code is governed by license located in license file: https://github.com/CBICA/NiChart/blob/main/LICENSE
"""

import pandas as pd
import numpy as np
import importlib.resources as pkg_resources
import sys
import json
import joblib
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5 import QtCore
from NiChart.core import iStagingLogger

logger = iStagingLogger.get_logger(__name__)

class CmdModel(QObject):
    """This class holds a collection of commands to create a jupyter notebook file."""

    def __init__(self):

        QObject.__init__(self)
        """The constructor."""
        self.cmds = []
        self.add_hdr_cmds()

    def add_hdr_cmds(self):
        self.cmds.append('## NiChart Notebook')
        self.cmds.append('#### Generated automatically by NiChart')
        self.cmds.append('')
        self.cmds.append('#### Import statements')
        self.cmds.append('')
        self.cmds.append('import pandas as pd')
        self.cmds.append('import numpy as np')
        self.cmds.append('import seaborn as sns')
        self.cmds.append('import matplotlib.pyplot as plt')
        self.cmds.append('from matplotlib.cm import get_cmap')
        self.cmds.append('from matplotlib.lines import Line2D')
        self.cmds.append('')
        self.cmds.append('#### Function definitions')
        self.cmds.append('')
        self.cmds.append('def hue_regplot(data, x, y, hue, palette=None, **kwargs):')
        self.cmds.append('    regplots = []')
        self.cmds.append('    levels = data[hue].unique()')
        self.cmds.append('    if palette is None:')
        self.cmds.append('        default_colors = get_cmap("tab10")')
        self.cmds.append('        palette = {k: default_colors(i) for i, k in enumerate(levels)}')
        self.cmds.append('    legendhandls=[]')
        self.cmds.append('    for key in levels:')
        self.cmds.append('        regplots.append(sns.regplot(x=x, y=y, data=data[data[hue] == key], color=palette[key], **kwargs))')
        self.cmds.append('        legendhandls.append(Line2D([], [], color=palette[key], label=key))')
        self.cmds.append('    return (regplots, legendhandls)')
        self.cmds.append('')
        self.cmds.append('#### Main notebook')
        self.cmds.append('')
        

    def add_cmd(self, cvalue):
        self.cmds.append(cvalue)
        logger.info('Command added to command array')        
        
    def add_cmds(self, cvalue):
        self.cmds = self.cmds + cvalue
        logger.info('Commands added to command array')        

    def print_cmds(self):
        for i, tmpcmd in enumerate(self.cmds):
            print('Cmd ' + str(i) + ' : ' + self.cmds[i])

    ## Function to write commands as a regular file (FIXME: this is tmp for now)
    def cmds_to_file(self, fname):
        with open(fname, mode='w') as fout:
            logger.info('Writing file ' + fname)
            fout.write('Commands:')
            fout.write('\n'.join(self.cmds))
            logger.info(self.cmds)        
        
    ## Function to write commands as a notebook
    def cmds_to_notebook(self, fname):
    
        ## Components of a notebook initialized to empty
        d_code = {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": []
            }
        d_mark = {
                "cell_type": "markdown",
                "metadata": {},
                "source": []
            }
        d_meta = {
                "metadata": {
                    "kernelspec": {
                        "display_name": "Python 3",
                        "language": "python",
                        "name": "python3"
                    },
                    "language_info": {
                        "codemirror_mode": {
                            "name": "ipython",
                            "version": 3
                        },
                        "file_extension": ".py",
                        "mimetype": "text/x-python",
                        "name": "python",
                        "nbconvert_exporter": "python",
                        "pygments_lexer": "ipython3",
                        "version": "3"
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 2
            }

        # Initialise variables
        notebook = {}       # Final notebook
        cells = []          # Cells of the notebook
        cell = []           # Contents of single cell


        # Read commands and store into cells
        cmd_type = 'end_block'        
        for i, tmp_cmd in enumerate(self.cmds):
            
            ## Start of block
            if cmd_type == 'end_block':
                if tmp_cmd == "":
                    continue
                
                else:
                    cell.append("{}".format(tmp_cmd + '\n'))
                    if tmp_cmd.startswith('#'):
                        cmd_type = 'mark'
                    else:
                        cmd_type = 'code'

            ## Middle of block
            else:
                ## Block ends
                if tmp_cmd == "":
                    if cmd_type == 'mark':
                        d_mark["source"] = cell
                        cells.append(dict(d_mark)) 
                    
                    else:
                        d_code["source"] = cell
                        cells.append(dict(d_code)) 
                    cell = []
                    cmd_type = 'end_block'

                ## Block continues
                else:
                    cell.append("{}".format(tmp_cmd + '\n'))
                
        # Add to notebook
        notebook["cells"] = cells
        notebook.update(d_meta)

        # Write notebook
        with open(fname, "w", encoding="utf-8") as fp:
            json.dump(notebook, fp, indent=1, ensure_ascii=False)
