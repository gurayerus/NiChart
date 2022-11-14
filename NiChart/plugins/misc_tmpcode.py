        #self.ui.menuTest = NestedQMenu(self.ui)
        #self.ui.vlComboTEST.addWidget(self.ui.menuTest)
        #self.ui.menuTest.hide()
        

        ## Example 1
        #self.projCombo = CheckableQComboBox(self.ui)
        #self.projCombo.addItem('example slot')
        #self.projCombo.addItem('another example slot')
        #self.projCombo.addItem('the last example slot')
        
        #self.ShapeLayerList=QWidgetAction(None)
        #self.ShapeLayerList.setDefaultWidget(self.projCombo)

        ## build the sub-menus for CSV attribute editor
        #self.popupMenu2A = QMenu( self.ui)
        #self.popupMenu2A.setTitle("Shape Data")
        #self.popupMenu2A.addAction(self.ShapeLayerList)
        
        #self.ui.menuTest.addMenu(self.popupMenu2A)
        
        ## Example 2
        #for i, vals in enumerate(['AAA', 'BBB', 'CCC']):
            #sub_menu = self.ui.menuTest.addMenu(vals)
            #for j, vals2 in enumerate(['Sub1', 'Sub2', 'Sub3', 'Sub4']):
                #sub_menu.addAction(QAction(vals + '_' + vals2 , self, checkable=True, checked=True))

        
        ### Example 3
        ## build the sub-menus for CSV attribute editor
        #self.popupMenu2A = QMenu( self.ui)
        #self.popupMenu2A.setTitle("Shape Data")
        #self.popupMenu2A.addAction(self.ShapeLayerList)
        
        ##self.ui.comboTest = NestedCheckableQComboBox(self.ui)
        #self.ui.comboTest = QComboBox(self.ui)
        #self.ui.menuTest.addMenu(self.ui.comboTest)
