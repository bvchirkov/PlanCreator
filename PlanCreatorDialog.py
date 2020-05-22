"""
/***************************************************************************
Name			 	 : PlanCreator plugin
Description          : Allows input building's floor plans and export them into json
Date                 : 23/Apr/14 
copyright            : (C) 2014 by M G
email                : m.a.galiullin@gmail.com 
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4 import QtCore, QtGui 
from Ui_PlanCreator import Ui_PlanCreator
# create the dialog for PlanCreator
class PlanCreatorDialog(QtGui.QDialog):
  def __init__(self): 
    QtGui.QDialog.__init__(self) 
    # Set up the user interface from Designer. 
    self.ui = Ui_PlanCreator ()
    self.ui.setupUi(self)