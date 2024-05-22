# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'organinserterwidget.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QPushButton,
    QSizePolicy, QSpacerItem, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_OrganInserterWidget(object):
    def setupUi(self, OrganInserterWidget):
        if not OrganInserterWidget.objectName():
            OrganInserterWidget.setObjectName(u"OrganInserterWidget")
        OrganInserterWidget.resize(483, 604)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(OrganInserterWidget.sizePolicy().hasHeightForWidth())
        OrganInserterWidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(OrganInserterWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tableViewOrganFiles = QTableWidget(OrganInserterWidget)
        self.tableViewOrganFiles.setObjectName(u"tableViewOrganFiles")

        self.verticalLayout.addWidget(self.tableViewOrganFiles)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.pushButtonDone = QPushButton(OrganInserterWidget)
        self.pushButtonDone.setObjectName(u"pushButtonDone")

        self.horizontalLayout_2.addWidget(self.pushButtonDone)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(OrganInserterWidget)

        QMetaObject.connectSlotsByName(OrganInserterWidget)
    # setupUi

    def retranslateUi(self, OrganInserterWidget):
        OrganInserterWidget.setWindowTitle(QCoreApplication.translate("OrganInserterWidget", u"Organ Inserter", None))
        self.pushButtonDone.setText(QCoreApplication.translate("OrganInserterWidget", u"Done", None))
    # retranslateUi

