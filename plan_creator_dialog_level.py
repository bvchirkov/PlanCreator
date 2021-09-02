# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'plan_creator_dialog_level.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(312, 223)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(140, 190, 171, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setEnabled(True)
        self.groupBox.setGeometry(QtCore.QRect(-1, 9, 311, 171))
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.QDoubleTransitHeight = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.QDoubleTransitHeight.setProperty("value", 2.0)
        self.QDoubleTransitHeight.setObjectName("QDoubleTransitHeight")
        self.gridLayout.addWidget(self.QDoubleTransitHeight, 2, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
        self.QDoubleFloorHeight = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.QDoubleFloorHeight.setProperty("value", 3.0)
        self.QDoubleFloorHeight.setObjectName("QDoubleFloorHeight")
        self.gridLayout.addWidget(self.QDoubleFloorHeight, 1, 1, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.QDoubleLevelHeight = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.QDoubleLevelHeight.setObjectName("QDoubleLevelHeight")
        self.gridLayout.addWidget(self.QDoubleLevelHeight, 0, 1, 1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.groupBox.setTitle(_translate("Dialog", "Уровень"))
        self.label.setText(_translate("Dialog", "Высота потолков в метрах"))
        self.label_2.setText(_translate("Dialog", "Высота проемов в метрах"))
        self.label_3.setText(_translate("Dialog", "Высота уровня над землей в метрах"))
