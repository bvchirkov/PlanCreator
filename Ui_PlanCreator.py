# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file Ui_PlanCreator.ui
# Created with: PyQt4 UI code generator 4.4.4
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_PlanCreator(object):
    def setupUi(self, PlanCreator):
        PlanCreator.setObjectName("PlanCreator")
        PlanCreator.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(PlanCreator)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.retranslateUi(PlanCreator)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), PlanCreator.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), PlanCreator.reject)
        QtCore.QMetaObject.connectSlotsByName(PlanCreator)

    def retranslateUi(self, PlanCreator):
        PlanCreator.setWindowTitle(QtGui.QApplication.translate("PlanCreator", "PlanCreator", None, QtGui.QApplication.UnicodeUTF8))
