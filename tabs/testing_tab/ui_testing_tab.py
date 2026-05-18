# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'testing_tab.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(675, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        font = QFont()
        font.setFamilies([u"MS Sans Serif"])
        Form.setFont(font)
        self.mainLayout = QVBoxLayout(Form)
        self.mainLayout.setSpacing(12)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setContentsMargins(24, 16, 24, 16)
        self.progressBar = QProgressBar(Form)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMaximumSize(QSize(16777215, 8))
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)

        self.mainLayout.addWidget(self.progressBar)

        self.labelProgress = QLabel(Form)
        self.labelProgress.setObjectName(u"labelProgress")
        self.labelProgress.setMaximumSize(QSize(16777215, 20))
        font1 = QFont()
        font1.setFamilies([u"Bahnschrift"])
        font1.setPointSize(14)
        self.labelProgress.setFont(font1)
        self.labelProgress.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.mainLayout.addWidget(self.labelProgress)

        self.labelTitle = QLabel(Form)
        self.labelTitle.setObjectName(u"labelTitle")
        self.labelTitle.setMinimumSize(QSize(0, 36))
        self.labelTitle.setMaximumSize(QSize(16777215, 60))
        font2 = QFont()
        font2.setFamilies([u"Bahnschrift"])
        font2.setPointSize(24)
        self.labelTitle.setFont(font2)
        self.labelTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelTitle.setWordWrap(True)

        self.mainLayout.addWidget(self.labelTitle)

        self.labelQuestion = QLabel(Form)
        self.labelQuestion.setObjectName(u"labelQuestion")
        self.labelQuestion.setMinimumSize(QSize(0, 60))
        font3 = QFont()
        font3.setFamilies([u"Bahnschrift"])
        font3.setPointSize(16)
        self.labelQuestion.setFont(font3)
        self.labelQuestion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labelQuestion.setWordWrap(True)

        self.mainLayout.addWidget(self.labelQuestion)

        self.groupBox = QGroupBox(Form)
        self.groupBox.setObjectName(u"groupBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy1)
        self.groupBox.setFont(font1)
        self.answersLayout = QVBoxLayout(self.groupBox)
        self.answersLayout.setSpacing(10)
        self.answersLayout.setObjectName(u"answersLayout")
        self.answersLayout.setContentsMargins(16, 12, 16, 12)

        self.mainLayout.addWidget(self.groupBox)

        self.hboxLayout = QHBoxLayout()
        self.hboxLayout.setObjectName(u"hboxLayout")
        self.spacerItem = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout.addItem(self.spacerItem)

        self.btnStart = QPushButton(Form)
        self.btnStart.setObjectName(u"btnStart")
        self.btnStart.setMinimumSize(QSize(160, 40))
        self.btnStart.setMaximumSize(QSize(200, 40))
        self.btnStart.setFont(font1)

        self.hboxLayout.addWidget(self.btnStart)

        self.spacerItem1 = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.hboxLayout.addItem(self.spacerItem1)


        self.mainLayout.addLayout(self.hboxLayout)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.labelProgress.setText(QCoreApplication.translate("Form", u"\u0412\u043e\u043f\u0440\u043e\u0441 0 \u0438\u0437 0", None))
        self.labelTitle.setText(QCoreApplication.translate("Form", u"\u041f\u0435\u0440\u0432\u0438\u0447\u043d\u043e\u0435 \u0442\u0435\u0441\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435", None))
        self.labelQuestion.setText(QCoreApplication.translate("Form", u"\u0412\u0430\u043c \u0431\u0443\u0434\u0443\u0442 \u043f\u0440\u0435\u0434\u043b\u043e\u0436\u0435\u043d\u044b \u0432\u043e\u043f\u0440\u043e\u0441\u044b, \u0441\u0432\u044f\u0437\u0430\u043d\u043d\u044b\u0435 \u0441 3 \u0440\u0430\u0437\u0434\u0435\u043b\u0430\u043c\u0438: \u043c\u0435\u0434\u0438\u0446\u0438\u043d\u0441\u043a\u0430\u044f \u0438\u043d\u0444\u043e\u043c\u0430\u0446\u0438\u044f, \u0438\u043d\u0442\u0435\u0440\u0435\u0441\u044b \u0438 \u043f\u0440\u0435\u0434\u043f\u043e\u0447\u0442\u0435\u043d\u0438\u044f", None))
        self.groupBox.setTitle(QCoreApplication.translate("Form", u"\u0412\u0430\u0440\u0438\u0430\u043d\u0442\u044b \u043e\u0442\u0432\u0435\u0442\u0430", None))
        self.btnStart.setText(QCoreApplication.translate("Form", u"\u041d\u0430\u0447\u0430\u0442\u044c \u0442\u0435\u0441\u0442", None))
    # retranslateUi

