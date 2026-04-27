# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'control_panel.ui'
##
## Created by: Qt User Interface Compiler version 6.10.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QPushButton, QSizePolicy,
    QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(436, 300)
        font = QFont()
        font.setFamilies([u"MS Sans Serif"])
        Form.setFont(font)
        self.horizontalLayoutWidget = QWidget(Form)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(0, 10, 471, 151))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btnPrev = QPushButton(self.horizontalLayoutWidget)
        self.btnPrev.setObjectName(u"btnPrev")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnPrev.sizePolicy().hasHeightForWidth())
        self.btnPrev.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.btnPrev)

        self.btnNext = QPushButton(self.horizontalLayoutWidget)
        self.btnNext.setObjectName(u"btnNext")
        sizePolicy.setHeightForWidth(self.btnNext.sizePolicy().hasHeightForWidth())
        self.btnNext.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.btnNext)

        self.btnFinish = QPushButton(self.horizontalLayoutWidget)
        self.btnFinish.setObjectName(u"btnFinish")
        sizePolicy.setHeightForWidth(self.btnFinish.sizePolicy().hasHeightForWidth())
        self.btnFinish.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.btnFinish)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.btnPrev.setText(QCoreApplication.translate("Form", u"\u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439 \u0432\u043e\u043f\u0440\u043e\u0441", None))
        self.btnNext.setText(QCoreApplication.translate("Form", u"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u0439 \u0432\u043e\u043f\u0440\u043e\u0441", None))
        self.btnFinish.setText(QCoreApplication.translate("Form", u"\u0417\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u044c \u0442\u0435\u0441\u0442", None))
    # retranslateUi

