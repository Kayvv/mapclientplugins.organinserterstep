import csv
import os

from PySide6 import QtCore, QtGui, QtWidgets

from mapclientplugins.organinserterstep.ui_organinserterwidget import Ui_OrganInserterWidget


class OrganInserterWidget(QtWidgets.QWidget):
    def __init__(self, input_model_file, input_data_files, output_directory, parent=None):
        super(OrganInserterWidget, self).__init__(parent)
        if input_model_file:
            input_data_files.append(input_model_file)
        self._input_data_files = input_data_files
        # organ_transformer = OrganTransformer(input_data_files, marker_coordinates.output_filename(), output_directory)
        # self._output_filename = organ_transformer.output_filename()
        self._ui = Ui_OrganInserterWidget()
        self._ui.setupUi(self)
        self._callback = None

        self.setTableViewOrganFiles()
        self._ui.pushButtonDone.clicked.connect(self._done_button_clicked)

    def setTableViewOrganFiles(self):
        self._ui.tableViewOrganFiles.setRowCount(len(self._input_data_files))
        self._ui.tableViewOrganFiles.setColumnCount(2)
        self._ui.tableViewOrganFiles.setHorizontalHeaderLabels(["Filename", "Organ"])
        header = self._ui.tableViewOrganFiles.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self._ui.tableViewOrganFiles.setItemDelegateForColumn(1, ComboBoxDelegate(self._ui.tableViewOrganFiles))
        for i in range(len(self._input_data_files)):
            item_name = QtWidgets.QTableWidgetItem(self._input_data_files[i])
            self._ui.tableViewOrganFiles.setItem(i, 0, item_name)
        self._ui.tableViewOrganFiles.setItemDelegateForColumn(1, ComboBoxDelegate(self._ui.tableViewOrganFiles))

    def register_done_execution(self, callback):
        self._callback = callback

    def _done_button_clicked(self):
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.CursorShape.WaitCursor)
        organ_file_dict = {}
        for row in range(self._ui.tableViewOrganFiles.rowCount()):
            # item(row, 0) Returns the item for the given row and column if one has been set; otherwise returns nullptr.
            _item = self._ui.tableViewOrganFiles.item(row, 1)
            if _item and _item.text() != '-':
                organ_file_dict[_item.text()] = self._ui.tableViewOrganFiles.item(row, 0).text()
        print(organ_file_dict)
        # organ_file_dict = {'lung': 'C:\\Users\\ywan787\\mapclient_workflows\\organinster\\output_Retrieve_Portal_Data\\brainstem.exf',
        #                    'heart': 'C:\\Users\\ywan787\\mapclient_workflows\\organinster\\output_Retrieve_Portal_Data\\heart.exf',
        #                    'whole body': 'C:\\Users\\ywan787\\mapclient_workflows\\organinster\\output_Retrieve_Portal_Data\\whole-body.exf'}
        self._callback(organ_file_dict)
        QtWidgets.QApplication.restoreOverrideCursor()


class ComboBoxDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(ComboBoxDelegate, self).__init__(parent)
        self.organsList = ['-', 'whole body', 'lung', 'heart', 'brainstem', 'stomach', 'bladder']

    def createEditor(self, widget, option, index):
        editor = QtWidgets.QComboBox(widget)
        editor.addItems(self.organsList)
        return editor

    # def setEditorData(self, editor, index):
    #     editor.setCurrentText(self.organsList[index.row()])

    def paint(self, painter, option, index):
        # text = self.organsList[index.row()]
        # option.text = self.organsList[index.row()]
        # QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.ControlElement.CE_ItemViewItem, option, painter)
        # super().paint(painter, option, index)

        value = index.data(QtGui.Qt.ItemDataRole.DisplayRole)
        opt = QtWidgets.QStyleOptionComboBox()
        opt.text = str(value)
        opt.rect = option.rect
        QtWidgets.QApplication.style().drawComplexControl(QtWidgets.QStyle.ComplexControl.CC_ComboBox, opt, painter)
        super().paint(painter, option, index)
