# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/itma/Documents/piaras_scripts/WorkCode/ITMA_video_batch_process/QT interface dev/test.ui'
#
# Created: Wed Jan  7 15:51:31 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
import sys,os

import datetime

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Form(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(400, 300)
        self.horizontalLayout_2 = QtGui.QHBoxLayout(Form)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.hello_world_btn = QtGui.QPushButton(Form)
        self.hello_world_btn.setObjectName(_fromUtf8("hello_world_btn"))
        self.horizontalLayout.addWidget(self.hello_world_btn)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "QTest", None))
        self.hello_world_btn.setText(_translate("Form", "Choose A Source Directory", None))
        self.hello_world_btn.clicked.connect(self.printHelloWorld)

    def printHelloWorld(self):
        fname = QtGui.QFileDialog.getExistingDirectory(self,'Choose Source Directory')
        for x in os.listdir(fname):
            print x



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = Ui_Form()
    ex.show()        
    sys.exit(app.exec_())