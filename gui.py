import os, time, functools

from PyQt5.QtWidgets import (QApplication, QLabel, QVBoxLayout, QPushButton,
                             QWidget, QFileDialog, QGridLayout, QFrame,
                             QStackedWidget, QStyleOption, QStylePainter,
                             QStyle, QBoxLayout, QTabWidget, QListWidget,
                             QLayout, QListWidgetItem, QCheckBox, QHBoxLayout,
                             QLineEdit, QPlainTextEdit, QSpinBox,
                             QAbstractSpinBox, QDoubleSpinBox, QComboBox,
                             QMessageBox, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import QColor, QPicture, QPainter, QIcon
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QRect, QPoint, QEvent, Qt, QSettings
from natsort import os_sorted

from mc_helper import batch_gen_CPS_sheet, batch_extract_OSTs, get_OSTs_single, get_OSTs, check_OST_audit
from decoders import parse_VTT, parse_SRT
from fixes import fix_TCFOL, batch_fixes
from srt_handler import convert_to_JSON
from vtt_handler import batch_merge_subs
from checks import batch_quality_check
from utils import (copy_scene_changes_from_list, batch_generate_scene_changes,
                   batch_get_frame_rates_gui, batch_get_stats)

class LayoutLineWidget(QWidget):
    _borderColor = QColor(167, 202, 212, 80)
    _paintCache = None
    _redrawEvents = QEvent.LayoutRequest, QEvent.Resize

    def event(self, event):
        if event.type() in self._redrawEvents:
            self._paintCache = None
            self.update()
        return super().event(event)

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        qp = QStylePainter(self)
        qp.drawPrimitive(QStyle.PE_Widget, opt)
        # end of default painting

        layout = self.layout()

        if not layout or layout.count() <= 1:
            return

        if layout.spacing() < 1:
            layout.setSpacing(1)
            return

        try:
            qp.drawPicture(0, 0, self._paintCache)
        except TypeError:
            self._rebuildPaintCache()
            qp.drawPicture(0, 0, self._paintCache)


    def _rebuildPaintCache(self):
        layout = self.layout()
        self._paintCache = QPicture()
        qp = QPainter(self._paintCache)
        qp.setPen(self._borderColor)

        if isinstance(layout, QBoxLayout):
            lastGeo = layout.itemAt(0).geometry()

            if isinstance(layout, QVBoxLayout):
                for row in range(1, layout.count()):
                    newGeo = layout.itemAt(row).geometry()
                    y = (lastGeo.bottom() + (newGeo.y() - lastGeo.bottom()) // 2)
                    qp.drawLine(0, y, self.width(), y)
                    lastGeo = newGeo
            else:
                for col in range(1, layout.count()):
                    newGeo = layout.itemAt(row).geometry()
                    x = (lastGeo.right()
                         + (newGeo.x() - lastGeo.right()) // 2)
                    qp.drawLine(x, 0, x, self.height())
                    lastGeo = newGeo
        elif isinstance(layout, QGridLayout):
            for i in range(layout.count()):
                row, col, rowSpan, colSpan = layout.getItemPosition(i)
                if not row and not col:
                    continue
                cellRect = layout.cellRect(row, col)
                if rowSpan:
                    cellRect |= layout.cellRect(row + rowSpan - 1, col)
                if colSpan:
                    cellRect |= layout.cellRect(row, col + colSpan - 1)
                if col:
                    leftCell = layout.cellRect(row, col - 1)
                    x = (leftCell.right()
                         + (cellRect.x() - leftCell.right()) // 2)
                    qp.drawLine(x, cellRect.y(), x, cellRect.bottom() + 1)


class Window(LayoutLineWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet('''
            Window {
                background: #202021;
            }

            QLabel#welcome {
                font-size: 34pt;
            }


            QLabel {
                color: #c5cad4;
            }

            QLabel#header_1 {
                font-size: 16pt;
                font-weight: bold;
                border-bottom: 1px solid rgba(167, 202, 212, 80);
            }

            QLabel#header_2 {
                font-size: 16pt;
                font-weight: bold;
                border-bottom: 1px solid rgba(167, 202, 212, 80);
            }


            QLabel#header {
                background: #353436;
                qproperty-alignment: AlignVCenter;
                font-size: 20pt;
                padding-left: 10px;
                padding-top: 16px;
                padding-bottom: 16px;
            }

            QLabel#sub_title {
                margin-top: 20px;
                font-size: 10pt;
                font-weight: bold;
            }

            QLabel#bold_label {
                font-size: 10pt;
                font-weight: bold;
            }

            QLabel#fix_spin_label {
                padding-left: 30px;
            }


            QWidget#content {
                border: 1px solid #c5cad4;
                border-radius: 5px;
            }

            QLabel#border_widget {
                padding-bottom: 20px;
                border: 1px solid rgba(167, 202, 212, 80);
                border-top: none;
                border-right: none;
                border-left: none;

            }

            QPushButton#option {
                background: #202021;
                color: #c5cad4;
                border: none;
                border-radius: 5px;
                font-size: 12pt;
                font-weight: bold;
                padding: 10px;
            }

            QPushButton#browse {
                background: #343536;
                color: #c5cad4;
                border: none;
                font-size: 9pt;
                border-radius: 3px;
                padding: 5px 10px 5px 10px;
            }

            QPushButton#browse1 {
                background: #343536;
                color: #c5cad4;
                border: none;
                font-size: 10pt;
                border-radius: 3px;
                padding: 5px 10px 5px 10px;
                width: 3em;
            }

            QPushButton#browse:hover {
                color: white;
            }

            QPushButton#browse1:hover {
                color: white;
            }


            QPushButton#option:hover {
                background-color: #37373d;
            }

            QPushButton#run {
                background: #4b62c4;
                color: #c5cad4;
                border: none;
                font-size: 11pt;
                border-radius: 3px;
                padding: 10px;
                width: 80px;
            }

            QPushButton#run:hover {
                color: white;
            }

            QWidget#menu > QPushButton {
                width: 150px;
                height: 40px;
            }

            QCheckBox {
                color: #c5cad4;
            }

            QCheckBox#cps_spaces {
                padding-left: 10px;
            }

            QCheckBox#sett_check {
                padding-left: 80px;
            }

            QLineEdit#report_field {
                background: #1c1b1c;
                margin-left: 80px;
            }

            QSpinBox, QDoubleSpinBox {
                border: 1px solid rgba(167, 202, 212, 80);
                background: #1c1b1c;
                color: #c5cad4;
            }

            QSpinBox:hover, QSpinBox:selected, QSpinbox:active, QDoubleSpinBox:hover, QDoubleSpinBox:selected, QDoubleSpinbox:active {
                border: 1px solid rgba(167, 202, 212, 80);
            }

            QSpinBox#fix_spin {
                margin-left: 30px;
            }


            QListWidget {
                background-color: #1c1b1c;
                color: #c5cad4;
            }


            QListWidgetItem {
                color: #c5cad4;
            }


            QTabBar::tab {
                height: 30px;
                width: 150px;
                background-color: #202021;
                padding-bottom: 10px;
                margin: 0px;
                color: #c5cad4;
                font-family: "Arial";
                font-size: 10pt;
            }


            QTabBar::tab:hover {
                border-bottom: 4px solid #c5cad4;
            }

            QTabBar::tab:selected {
                border-bottom: 4px solid #2c4ac9;
                font-weight: bold;
            }

            QTabWidget::pane {
                background-color: #202021;
                border-top: 1px solid rgba(167, 202, 212, 80);
                margin-top: -2px;
            }

            QTabBar#utils_tab_bar::tab {
                width: 200px;
            }

            QListWidget {
                border: 1px solid rgba(167, 202, 212, 80);
                border-radius: 3px;
            }

            QLineEdit {
                background-color: #1c1b1c;
                border: 1px solid rgba(167, 202, 212, 80);
                border-radius: 2px;
                color: #c5cad4;
            }

            QPlainTextEdit {
                font-size: 9pt;
                font-family: "Lucida Console";
                border: 1px solid rgba(167, 202, 212, 80);
                border-radius: 3px;
                background-color: #1c1b1c;
                margin-top: 1em;
                color: #c5cad4;

            }

            QPlainTextEdit:selected {
                border: 1px solid rgba(167, 202, 212, 0.5);

            }









            QScrollBar:vertical {
                border: none;
                background: #1c1b1c;
                width: 3px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop: 0 rgb(44, 74, 201), stop: 0.5 rgb(44, 74, 201), stop:1 rgb(44, 74, 201));
                min-height: 0px;
            }
            QScrollBar::add-line:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop: 0 rgb(32, 47, 130), stop: 0.5 rgb(32, 47, 130),  stop:1 rgb(32, 47, 130));
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop: 0  rgb(32, 47, 130), stop: 0.5 rgb(32, 47, 130),  stop:1 rgb(32, 47, 130));
                height: 0 px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }

            QComboBox {
                width: 2em;
                background: #202021;
                color: #c5cad4;
            }

            QComboBox QAbstractItemView {
                background: #202021;
                color: #c5cad4;
            }

            QMessageBox {
                background: #202021;
                color: #c5cad4;
            }


        ''')

        self.settings = QSettings('Eclipse', 'Subtitling Copilot')

        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.setSpacing(0)

        self.header_label = QLabel('Subtitling Copilot v1.0', objectName='header')
        self.header_label.setMinimumHeight(90)
        main_layout.addWidget(self.header_label, 0, 0, 1, 2)

        self.files_1 = []
        self.files_2 = []


        # MENU
        self.menu_container = QWidget(objectName='menu')
        main_layout.addWidget(self.menu_container)
        menu_layout = QVBoxLayout(self.menu_container)
        menu_layout.setSpacing(15)

        self.option_1_button = QPushButton('OST', objectName='option')
        self.option_2_button = QPushButton('Batch QC', objectName='option')
        self.option_3_button = QPushButton('Issues', objectName='option')
        # self.option_4_button = QPushButton('Prefix', objectName='option')
        self.option_4_button = QPushButton('Fixes', objectName='option')
        self.option_5_button = QPushButton('Utilities', objectName='option')

        menu_layout.addWidget(self.option_1_button)
        menu_layout.addWidget(self.option_2_button)
        menu_layout.addWidget(self.option_3_button)
        # menu_layout.addWidget(self.option_4_button)
        menu_layout.addWidget(self.option_4_button)
        menu_layout.addWidget(self.option_5_button)
        menu_layout.addStretch()


        # ACTUAL TOOLS
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1, 1)

        # STACKED WIDGET FOR OPTION PAGES
        self.content = QStackedWidget()
        self.content.setContentsMargins(40, 40, 40, 40)
        right_layout.addWidget(self.content)
        right_layout.addStretch(1)

        # PAGE WIDGETS
        # CONTENTS OF THE PAGE WIDGETS (TAB WIDGETS)
        # TAB WIDGETS
        self.welcome_widget = QWidget(objectName='Welcome')
        self.opt_1_page_cont = QTabWidget(objectName='Option1tabs')
        # self.opt_2_page_cont = QWidget(objectName='Option-2-tabs')
        self.opt_2_page_cont = QTabWidget(objectName='Option-2-tabs')
        self.opt_3_page_cont = QWidget(objectName='Option-3-tabs')
        self.opt_4_page_cont = QTabWidget(objectName='Option-4-tabs')
        # self.opt_4_page_cont = QWidget(objectName='Option-4-tabs')
        self.opt_5_page_cont = QTabWidget(objectName='option_5_tabs')

        self.welcome_layout = QVBoxLayout(self.welcome_widget)
        self.welcome_message = QLabel('Welcome to Subtitling Copilot', objectName='welcome')
        self.welcome_message.setAlignment(QtCore.Qt.AlignCenter)
        self.welcome_layout.addWidget(self.welcome_message)


        tab_position = QTabWidget.North
        tab_shape = QTabWidget.Rounded
        self.opt_1_page_cont.setTabPosition(tab_position)
        self.opt_1_page_cont.setTabShape(tab_shape)

        self.opt_1_page_cont.setContentsMargins(0, 0, 0, 0)

        # TABS FOR OPTION 1
        self.opt_1_tab_1 = QWidget()
        self.opt_1_tab_2 = QWidget()
        self.opt_1_tab_3 = QWidget()

        self.opt_1_page_cont.addTab(self.opt_1_tab_1, 'Extract')
        self.opt_1_page_cont.addTab(self.opt_1_tab_2, 'Merge')
        self.opt_1_page_cont.addTab(self.opt_1_tab_3, 'Generate (MC only)')

        # CONTENTS OF THE FIRST TAB IN OPTION 1
        self.opt_1_tab_1_layout = QVBoxLayout(self.opt_1_tab_1)

        self.input_1_label = QLabel('Subtitle Files', objectName='sub_title')
        self.opt_1_tab_1_layout.addWidget(self.input_1_label)

        self.opt_1_tab_1_files_layout = QHBoxLayout()
        self.opt_1_tab_1_layout.addLayout(self.opt_1_tab_1_files_layout)

        self.file_list_1 = DropList(1, ['.vtt'])
        self.file_list_1.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.opt_1_tab_1_files_layout.addWidget(self.file_list_1)

        self.opt_1_tab_1_files_browse_layout = QVBoxLayout()
        self.opt_1_tab_1_files_layout.addLayout(self.opt_1_tab_1_files_browse_layout)

        self.opt_1_tab_1_add = QPushButton('Add...', objectName='browse')
        self.opt_1_tab_1_remove = QPushButton('Remove', objectName='browse')
        self.opt_1_tab_1_clear = QPushButton('Clear', objectName='browse')
        self.opt_1_tab_1_files_browse_layout.addWidget(self.opt_1_tab_1_add)
        self.opt_1_tab_1_files_browse_layout.addWidget(self.opt_1_tab_1_remove)
        self.opt_1_tab_1_files_browse_layout.addWidget(self.opt_1_tab_1_clear)

        self.opt_1_tab_1_files_browse_layout.addStretch()

        self.opt_1_tab_1_save_layout = QHBoxLayout()
        self.opt_1_tab_1_save_layout.setContentsMargins(0, 10, 0, 10)
        self.opt_1_tab_1_layout.addLayout(self.opt_1_tab_1_save_layout)
        self.opt_1_tab_1_save_label = QLabel('Save new files to:', objectName='bold_label')
        self.opt_1_tab_1_save_layout.addWidget(self.opt_1_tab_1_save_label)
        self.opt_1_tab_1_save_edit = QLineEdit()
        self.opt_1_tab_1_save_edit.setReadOnly(True)
        self.opt_1_tab_1_save_edit.setTextMargins(0, 0, 100, 0)
        self.opt_1_tab_1_save_layout.addWidget(self.opt_1_tab_1_save_edit)
        self.opt_1_tab_1_browse_save = QPushButton('Browse...', objectName='browse')
        self.opt_1_tab_1_save_layout.addWidget(self.opt_1_tab_1_browse_save)
        self.opt_1_tab_1_save_layout.addStretch()


        self.opt_1_tab_1_checkbox_1 = QCheckBox('Save extracted OSTs')
        self.opt_1_tab_1_layout.addWidget(self.opt_1_tab_1_checkbox_1)

        self.opt_1_tab_1_checkbox_2 = QCheckBox('Delete OSTs from files after extracting')
        self.opt_1_tab_1_layout.addWidget(self.opt_1_tab_1_checkbox_2)

        self.extract_ost_button = QPushButton('Extract', objectName='run')
        self.opt_1_tab_1_layout.addWidget(self.extract_ost_button, 0, QtCore.Qt.AlignRight)



        # self.input_1_label = QLabel('Subtitle Files', objectName='sub_title')
        # self.input_1_label.setContentsMargins(0, 0, 100, 10)
        # self.opt_1_tab_1_layout.addWidget(self.input_1_label, 0, 0)

        # # self.file_list_1 = QListWidget()
        # self.file_list_1 = DropList(['.vtt'])
        # self.opt_1_tab_1_layout.addWidget(self.file_list_1, 1, 0)

        # self.list_1_browse = QPushButton('Browse...', objectName='browse')
        # self.opt_1_tab_1_layout.addWidget(self.list_1_browse, 1, 1, QtCore.Qt.AlignBottom)

        # self.save_layout_widget = QWidget()
        # self.opt_1_tab_1_layout.addWidget(self.save_layout_widget, 4, 0)
        # self.save_layout = QHBoxLayout(self.save_layout_widget)
        # self.save_layout.setContentsMargins(0, 10, 0, 10)
        # self.save_label = QLabel('Save new files to:', objectName='bold_label')
        # self.save_layout.addWidget(self.save_label)
        # self.save_edit = QLineEdit()
        # self.save_edit.setReadOnly(True)
        # self.save_edit.setTextMargins(0, 0, 100, 0)
        # self.save_layout.addWidget(self.save_edit)
        # self.browse_save = QPushButton('Browse...', objectName='browse')
        # self.save_layout.addWidget(self.browse_save)
        # self.save_layout.addStretch()


        # self.checkbox_1 = QCheckBox('Save extracted OSTs')
        # self.opt_1_tab_1_layout.addWidget(self.checkbox_1, 5, 0)

        # self.checkbox_2 = QCheckBox('Delete OSTs from files after extracting')
        # self.opt_1_tab_1_layout.addWidget(self.checkbox_2, 6, 0)

        # self.extract_ost_button = QPushButton('Extract', objectName='run')
        # self.opt_1_tab_1_layout.addWidget(self.extract_ost_button, 7, 1)

        # self.messages = QPlainTextEdit()
        # self.messages.setReadOnly(True)
        # self.opt_1_tab_1_layout.addWidget(self.messages, 8, 0, 1, 2)



        # CONTENTS OF THE SECOND TAB IN OPTION 1
        # self.opt_1_tab_2_layout = QGridLayout(self.opt_1_tab_2)
        self.opt_1_tab_2_layout = QVBoxLayout(self.opt_1_tab_2)

        self.input_2_label = QLabel('Subtitle Files', objectName='sub_title')
        self.opt_1_tab_2_layout.addWidget(self.input_2_label)
        self.opt_1_tab_2_files_layout_1 = QHBoxLayout()
        self.opt_1_tab_2_layout.addLayout(self.opt_1_tab_2_files_layout_1)
        self.file_list_2 = DropList(1, ['.vtt', '.srt'])
        self.file_list_2.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.opt_1_tab_2_files_layout_1.addWidget(self.file_list_2)
        self.opt_1_tab_2_files_browse_layout_1 = QVBoxLayout()
        self.opt_1_tab_2_files_layout_1.addLayout(self.opt_1_tab_2_files_browse_layout_1)
        self.opt_1_tab_2_add_1 = QPushButton('Add...', objectName='browse')
        self.opt_1_tab_2_remove_1 = QPushButton('Remove', objectName='browse')
        self.opt_1_tab_2_clear_1 = QPushButton('Clear', objectName='browse')

        self.opt_1_tab_2_files_browse_layout_1.addWidget(self.opt_1_tab_2_add_1)
        self.opt_1_tab_2_files_browse_layout_1.addWidget(self.opt_1_tab_2_remove_1)
        self.opt_1_tab_2_files_browse_layout_1.addWidget(self.opt_1_tab_2_clear_1)
        self.opt_1_tab_2_files_browse_layout_1.addStretch()

        self.input_3_label = QLabel('OST Files', objectName='sub_title')
        self.input_3_label.setContentsMargins(0, 0, 100, 10)
        self.opt_1_tab_2_layout.addWidget(self.input_3_label)

        self.opt_1_tab_2_files_layout_2 = QHBoxLayout()
        self.opt_1_tab_2_layout.addLayout(self.opt_1_tab_2_files_layout_2)
        self.file_list_3 = DropList(2, ['.vtt', '.srt'])
        self.file_list_3.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.opt_1_tab_2_files_layout_2.addWidget(self.file_list_3)
        self.opt_1_tab_2_files_browse_layout_2 = QVBoxLayout()
        self.opt_1_tab_2_files_layout_2.addLayout(self.opt_1_tab_2_files_browse_layout_2)
        self.opt_1_tab_2_add_2 = QPushButton('Add...', objectName='browse')
        self.opt_1_tab_2_remove_2 = QPushButton('Remove', objectName='browse')
        self.opt_1_tab_2_clear_2 = QPushButton('Clear', objectName='browse')

        self.opt_1_tab_2_files_browse_layout_2.addWidget(self.opt_1_tab_2_add_2)
        self.opt_1_tab_2_files_browse_layout_2.addWidget(self.opt_1_tab_2_remove_2)
        self.opt_1_tab_2_files_browse_layout_2.addWidget(self.opt_1_tab_2_clear_2)
        self.opt_1_tab_2_files_browse_layout_2.addStretch()

        self.opt_1_tab_2_save_layout = QHBoxLayout()
        self.opt_1_tab_2_layout.addLayout(self.opt_1_tab_2_save_layout)

        self.opt_1_tab_2_save_label = QLabel('Save new files to:', objectName='bold_label')
        self.opt_1_tab_2_save_layout.addWidget(self.opt_1_tab_2_save_label)
        self.opt_1_tab_2_save_edit = QLineEdit()
        self.opt_1_tab_2_save_edit.setReadOnly(True)
        self.opt_1_tab_2_save_edit.setTextMargins(0, 0, 0, 0)
        self.opt_1_tab_2_save_layout.addWidget(self.opt_1_tab_2_save_edit)
        self.opt_1_tab_2_browse_save = QPushButton('Browse...', objectName='browse')
        self.opt_1_tab_2_save_layout.addWidget(self.opt_1_tab_2_browse_save)
        self.opt_1_tab_2_save_layout.addStretch()
        self.opt_1_tab_2_save_layout.setContentsMargins(0, 10, 0, 10)

        self.checkbox_3 = QCheckBox('Overwrite subtitle files')
        self.opt_1_tab_2_layout.addWidget(self.checkbox_3, 0, QtCore.Qt.AlignLeft)

        self.merge_ost_button = QPushButton('Merge', objectName='run')
        self.opt_1_tab_2_layout.addWidget(self.merge_ost_button, 0, QtCore.Qt.AlignRight)






















        # self.input_2_label = QLabel('Subtitle Files', objectName='sub_title')
        # self.input_2_label.setContentsMargins(0, 0, 100, 10)
        # self.opt_1_tab_2_layout.addWidget(self.input_2_label, 0, 0)

        # # self.file_list_2 = QListWidget()
        # self.file_list_2 = DropList(['.vtt', '.srt'])
        # self.opt_1_tab_2_layout.addWidget(self.file_list_2, 1, 0)

        # self.list_2_browse = QPushButton('Browse...', objectName='browse')
        # self.opt_1_tab_2_layout.addWidget(self.list_2_browse, 1, 1, QtCore.Qt.AlignBottom)

        # self.input_3_label = QLabel('OST Files', objectName='sub_title')
        # self.input_3_label.setContentsMargins(0, 0, 100, 10)
        # self.opt_1_tab_2_layout.addWidget(self.input_3_label, 2, 0)

        # # self.file_list_3 = QListWidget()
        # self.file_list_3 = DropList(['.vtt', '.srt'])
        # self.opt_1_tab_2_layout.addWidget(self.file_list_3, 3, 0)

        # self.list_3_browse = QPushButton('Browse...', objectName='browse')
        # self.opt_1_tab_2_layout.addWidget(self.list_3_browse, 3, 1, QtCore.Qt.AlignBottom)

        # self.save_layout_widget_1 = QWidget()
        # self.opt_1_tab_2_layout.addWidget(self.save_layout_widget_1, 4, 0)
        # self.save_layout_1 = QHBoxLayout(self.save_layout_widget_1)
        # self.save_layout_1.setContentsMargins(0, 10, 0, 10)
        # self.save_label_1 = QLabel('Save new files to:', objectName='bold_label')
        # self.save_layout_1.addWidget(self.save_label_1)
        # self.save_edit_1 = QLineEdit()
        # self.save_edit_1.setReadOnly(True)
        # self.save_edit_1.setTextMargins(0, 0, 0, 0)
        # self.save_layout_1.addWidget(self.save_edit_1)
        # self.browse_save_1 = QPushButton('Browse...', objectName='browse')
        # self.save_layout_1.addWidget(self.browse_save_1)
        # self.save_layout_1.addStretch()

        # self.checkbox_3 = QCheckBox('Overwrite subtitle files')
        # self.opt_1_tab_2_layout.addWidget(self.checkbox_3, 5, 0)

        # self.merge_ost_button = QPushButton('Merge', objectName='run')
        # self.opt_1_tab_2_layout.addWidget(self.merge_ost_button, 6, 1)

        # self.merge_messages = QPlainTextEdit()
        # self.merge_messages.setReadOnly(True)
        # self.opt_1_tab_2_layout.addWidget(self.merge_messages, 7, 0, 1, 2)



        # CONTENTS OF THE THIRD TAB IN OPTION 1
        self.opt_1_tab_3_layout = QVBoxLayout(self.opt_1_tab_3)

        self.input_4_label = QLabel('OST Audit File(s)', objectName='sub_title')
        self.input_4_label.setContentsMargins(0, 0, 100, 10)
        self.opt_1_tab_3_layout.addWidget(self.input_4_label)

        self.opt_1_tab_3_files_layout = QHBoxLayout()
        self.opt_1_tab_3_layout.addLayout(self.opt_1_tab_3_files_layout)

        self.file_list_4 = DropList(1, ['.docx'])
        self.file_list_4.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

        self.opt_1_tab_3_files_layout.addWidget(self.file_list_4)
        self.opt_1_tab_3_files_browse_layout = QVBoxLayout()
        self.opt_1_tab_3_files_layout.addLayout(self.opt_1_tab_3_files_browse_layout)
        self.opt_1_tab_3_add = QPushButton('Add...', objectName='browse')
        self.opt_1_tab_3_remove = QPushButton('Remove', objectName='browse')
        self.opt_1_tab_3_clear = QPushButton('Clear', objectName='browse')

        self.opt_1_tab_3_files_browse_layout.addWidget(self.opt_1_tab_3_add)
        self.opt_1_tab_3_files_browse_layout.addWidget(self.opt_1_tab_3_remove)
        self.opt_1_tab_3_files_browse_layout.addWidget(self.opt_1_tab_3_clear)
        self.opt_1_tab_3_files_browse_layout.addStretch()

        self.opt_1_tab_3_save_layout = QHBoxLayout()
        self.opt_1_tab_3_layout.addLayout(self.opt_1_tab_3_save_layout)

        self.opt_1_tab_3_save_label = QLabel('Save OST files to:', objectName='bold_label')
        self.opt_1_tab_3_save_layout.addWidget(self.opt_1_tab_3_save_label)
        self.opt_1_tab_3_save_edit = QLineEdit()
        self.opt_1_tab_3_save_edit.setReadOnly(True)
        self.opt_1_tab_3_save_edit.setTextMargins(0, 0, 0, 0)
        self.opt_1_tab_3_save_layout.addWidget(self.opt_1_tab_3_save_edit)
        self.opt_1_tab_3_browse_save = QPushButton('Browse...', objectName='browse')
        self.opt_1_tab_3_save_layout.addWidget(self.opt_1_tab_3_browse_save)
        self.opt_1_tab_3_save_layout.addStretch()
        self.opt_1_tab_3_save_layout.setContentsMargins(0, 10, 0, 10)

        self.generate_ost_button = QPushButton('Generate', objectName='run')
        self.opt_1_tab_3_layout.addWidget(self.generate_ost_button, 0, QtCore.Qt.AlignRight)






















        # self.opt_1_tab_3_layout = QGridLayout(self.opt_1_tab_3)
        # self.input_4_label = QLabel('OST Audit File(s)', objectName='sub_title')
        # self.input_4_label.setContentsMargins(0, 0, 100, 10)
        # self.opt_1_tab_3_layout.addWidget(self.input_4_label, 0, 0)

        # # self.file_list_4 = QListWidget()
        # self.file_list_4 = DropList(['.docx'])
        # self.opt_1_tab_3_layout.addWidget(self.file_list_4, 1, 0)

        # self.list_4_browse = QPushButton('Browse...', objectName='browse')
        # self.opt_1_tab_3_layout.addWidget(self.list_4_browse, 1, 1, QtCore.Qt.AlignBottom)

        # self.save_layout_widget_2 = QWidget()
        # self.opt_1_tab_3_layout.addWidget(self.save_layout_widget_2, 2, 0)
        # self.save_layout_2 = QHBoxLayout(self.save_layout_widget_2)
        # self.save_layout_2.setContentsMargins(0, 10, 0, 10)
        # self.save_label_2 = QLabel('Save OST files to:', objectName='bold_label')
        # self.save_layout_2.addWidget(self.save_label_2)
        # self.save_edit_2 = QLineEdit()
        # self.save_edit_2.setReadOnly(True)
        # self.save_edit_2.setTextMargins(0, 0, 100, 0)
        # self.save_layout_2.addWidget(self.save_edit_2)
        # self.browse_save_2 = QPushButton('Browse...', objectName='browse')
        # self.save_layout_2.addWidget(self.browse_save_2)
        # self.save_layout_2.addStretch()

        # self.generate_ost_button = QPushButton('Generate', objectName='run')
        # self.opt_1_tab_3_layout.addWidget(self.generate_ost_button, 3, 1)

        # self.generation_messages = QPlainTextEdit()
        # self.generation_messages.setReadOnly(True)
        # self.opt_1_tab_3_layout.addWidget(self.generation_messages, 4, 0, 1, 2)




        # OPTION 2 CONTENTS
        self.opt_2_page_cont.setTabPosition(tab_position)
        self.opt_2_page_cont.setTabShape(tab_shape)

        # TABS FOR OPTION 2
        self.opt_2_tab_1 = QWidget()
        self.opt_2_tab_2 = QWidget()

        self.opt_2_page_cont.addTab(self.opt_2_tab_1, 'Files and Settings')
        self.opt_2_page_cont.addTab(self.opt_2_tab_2, 'Results')

        # self.qc_layout_1 = QVBoxLayout(self.opt_2_page_cont)
        self.qc_layout_1 = QVBoxLayout(self.opt_2_tab_1)
        # self.qc_header = QLabel('Batch Quality Check', objectName='header_1')
        # self.qc_header.setContentsMargins(0, 0, 0, 0)
        # self.qc_layout_1.addWidget(self.qc_header)


        self.qc_files_label = QLabel('Subtitle Files Directory', objectName='bold_label')
        self.qc_files_label.setContentsMargins(0, 30, 0, 0)
        self.qc_layout_1.addWidget(self.qc_files_label)
        self.add_qc_files_layout = QHBoxLayout()
        self.qc_layout_1.addLayout(self.add_qc_files_layout)
        # self.qc_files_list = QListWidget()
        self.qc_files_list = QLineEdit()
        self.qc_files_list.setReadOnly(True)
        self.add_qc_files_layout.addWidget(self.qc_files_list)
        self.browse_qc_files = QPushButton('Browse...', objectName='browse')
        self.add_qc_files_layout.addWidget(self.browse_qc_files)
        self.add_qc_files_layout.addStretch()

        self.qc_videos_label = QLabel('Video Files Directory', objectName='bold_label')
        self.qc_videos_label.setContentsMargins(0, 10, 0, 0)
        self.qc_layout_1.addWidget(self.qc_videos_label)
        self.add_qc_videos_layout = QHBoxLayout()
        self.qc_layout_1.addLayout(self.add_qc_videos_layout)
        # self.qc_videos_list = QListWidget()
        self.qc_videos_list = QLineEdit()
        self.qc_videos_list.setReadOnly(True)
        self.add_qc_videos_layout.addWidget(self.qc_videos_list)
        self.browse_qc_videos = QPushButton('Browse...', objectName='browse')
        self.add_qc_videos_layout.addWidget(self.browse_qc_videos)
        self.add_qc_videos_layout.addStretch()

        self.qc_sc_label = QLabel('Scene Changes Directory', objectName='bold_label')
        self.qc_sc_label.setContentsMargins(0, 10, 0, 0)
        self.qc_layout_1.addWidget(self.qc_sc_label)
        self.add_qc_sc_layout = QHBoxLayout()
        self.qc_layout_1.addLayout(self.add_qc_sc_layout)
        self.qc_sc_list = QLineEdit()
        self.qc_sc_list.setReadOnly(True)
        if self.settings.value('last_qc_sc_dir'):
            self.qc_sc_list.insert(self.settings.value('last_qc_sc_dir'))
        self.add_qc_sc_layout.addWidget(self.qc_sc_list)
        self.browse_qc_sc_dir = QPushButton('Browse...', objectName='browse')
        self.add_qc_sc_layout.addWidget(self.browse_qc_sc_dir)
        self.add_qc_sc_layout.addStretch()


        self.qc_setts_label = QLabel('Settings', objectName='header_2')
        self.qc_setts_label.setContentsMargins(0, 70, 0, 30)
        self.qc_layout_1.addWidget(self.qc_setts_label)
        self.qc_setts_layout = QGridLayout()
        self.qc_layout_1.addLayout(self.qc_setts_layout)
        self.max_cps_label = QLabel('Max. CPS')
        self.max_cps_spin = QDoubleSpinBox()
        self.max_cps_spin.setDecimals(2)
        self.max_cps_spin.setSingleStep(0.1)
        self.max_cps_spin.setValue(25.00)
        self.cps_spaces_checkbox = QCheckBox(
            'CPS include spaces',
            objectName='cps_spaces'
        )

        self.max_cpl_label = QLabel('Max. CPL')
        self.max_cpl_spin = QSpinBox()
        self.max_cpl_spin.setValue(42)
        self.max_cpl_spin.setMinimum(1)
        self.max_lines_label = QLabel('Max. lines')
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setValue(2)
        self.max_lines_spin.setMinimum(1)
        self.min_duration_label = QLabel('Min. duration (ms)')
        self.min_duration_spin = QSpinBox()
        self.min_duration_spin.setRange(0, 10000)
        self.min_duration_spin.setValue(833)
        self.max_duration_label = QLabel('Max. duration (ms)')
        self.max_duration_spin = QSpinBox()
        self.max_duration_spin.setRange(1000, 100000000)
        self.max_duration_spin.setValue(7000)



        self.qc_setts_layout.addWidget(self.max_cps_label, 0, 0)
        self.qc_setts_layout.addWidget(self.max_cps_spin, 0, 1)
        self.qc_setts_layout.addWidget(self.cps_spaces_checkbox, 1, 0, 1, 1)
        self.qc_setts_layout.addWidget(self.max_cpl_label, 2, 0)
        self.qc_setts_layout.addWidget(self.max_cpl_spin, 2, 1)
        self.qc_setts_layout.addWidget(self.max_lines_label, 3, 0)
        self.qc_setts_layout.addWidget(self.max_lines_spin, 3, 1)
        self.qc_setts_layout.addWidget(self.min_duration_label, 4, 0)
        self.qc_setts_layout.addWidget(self.min_duration_spin, 4, 1)
        self.qc_setts_layout.addWidget(self.max_duration_label, 5, 0)
        self.qc_setts_layout.addWidget(self.max_duration_spin, 5, 1)







        self.check_ellipses_checkbox = QCheckBox(
            'Check ellipses',
            objectName='sett_check'
        )
        self.check_ellipses_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_ellipses_checkbox, 0, 2)
        self.check_gaps_checkbox = QCheckBox(
            'Check gaps',
            objectName='sett_check'
        )
        self.check_gaps_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_gaps_checkbox, 1, 2)
        self.check_sc_checkbox = QCheckBox(
            'Check timing to shot changes',
            objectName='sett_check'
        )
        self.check_sc_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_sc_checkbox, 2, 2)
        self.check_TCFOL_checkbox = QCheckBox(
            'Check text can fit in one line',
            objectName='sett_check'
        )
        self.check_TCFOL_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_TCFOL_checkbox, 3, 2)
        self.check_OST_checkbox = QCheckBox(
            'Check OSTs (MC only)',
            objectName='sett_check'
        )
        self.check_OST_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_OST_checkbox, 4, 2)
        self.check_NFG_checkbox = QCheckBox(
            'Check Netflix Glyph List',
            objectName='sett_check'
        )
        self.check_NFG_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_NFG_checkbox, 5, 2)

        self.save_report_checkbox = QCheckBox('Save Report', objectName='sett_check')
        self.qc_setts_layout.addWidget(self.save_report_checkbox, 0, 4)
        self.save_report_entry = QLineEdit(objectName='report_field')
        self.qc_setts_layout.addWidget(self.save_report_entry, 1, 4)
        self.save_report_browse = QPushButton('Browse...', objectName='browse')
        self.qc_setts_layout.addWidget(self.save_report_browse, 1, 5)

        self.qc_setts_layout.setColumnStretch(0, 0)
        self.qc_setts_layout.setColumnStretch(1, 0)
        self.qc_setts_layout.setColumnStretch(2, 0)
        self.qc_setts_layout.setColumnStretch(3, 150)
        self.qc_setts_layout.setColumnStretch(4, 200)
        self.qc_setts_layout.setColumnStretch(5, 0)
        self.qc_setts_layout.setColumnMinimumWidth(1, 55)

        # self.qc_setts_layout.setColumnStretch(5, 1)


        self.run_qc_button = QPushButton('Run', objectName='run')
        self.run_qc_button.setContentsMargins(0, 40, 0, 0)
        self.qc_layout_1.addWidget(self.run_qc_button, 0, QtCore.Qt.AlignRight)
        self.qc_layout_1.addStretch()

        self.qc_layout_2 = QVBoxLayout(self.opt_2_tab_2)
        self.qc_results_label = QLabel('Quality Check Results', objectName='bold_label')
        self.qc_results_label.setContentsMargins(0, 10, 0, 0)
        self.qc_layout_2.addWidget(self.qc_results_label, 0)
        self.qc_messages = QPlainTextEdit()
        self.qc_messages.setContentsMargins(0, 10, 0, 0)
        self.qc_messages.setReadOnly(True)
        self.qc_layout_2.addWidget(self.qc_messages, 0)
        self.qc_messages.setPlainText('No results to show.')


        # OPTION 3 CONTENTS

        self.issues_layout = QVBoxLayout(self.opt_3_page_cont)

        self.issues_file_label_1 = QLabel('Target Language Files', objectName='sub_title')
        self.issues_layout.addWidget(self.issues_file_label_1)
        self.add_target_files_layout = QHBoxLayout()
        self.issues_layout.addLayout(self.add_target_files_layout)
        # self.target_files_list = QListWidget()
        self.target_files_list = DropList(1, ['.vtt', 'srt'])
        self.target_files_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        # self.target_files_list.setReadOnly(True)
        self.add_target_files_layout.addWidget(self.target_files_list)
        self.target_files_browse_layout = QVBoxLayout()
        self.add_target_files_layout.addLayout(self.target_files_browse_layout)
        self.add_target_files = QPushButton('Add...', objectName='browse')
        self.remove_target_files = QPushButton('Remove', objectName='browse')
        self.clear_target_files = QPushButton('Clear', objectName='browse')
        self.target_files_browse_layout.addWidget(self.add_target_files)
        self.target_files_browse_layout.addWidget(self.remove_target_files)
        self.target_files_browse_layout.addWidget(self.clear_target_files)
        self.target_files_browse_layout.addStretch()

        # self.add_target_files_layout.addStretch()

        self.issues_file_label_2 = QLabel('Source Language Files', objectName='sub_title')
        self.issues_layout.addWidget(self.issues_file_label_2)
        self.add_source_files_layout = QHBoxLayout()
        self.issues_layout.addLayout(self.add_source_files_layout)
        # self.source_files_list = QListWidget()
        self.source_files_list = DropList(2, ['.vtt', '.srt'])
        self.source_files_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        # self.source_files_list.setReadOnly(True)
        self.add_source_files_layout.addWidget(self.source_files_list)
        self.source_files_browse_layout = QVBoxLayout()
        self.add_source_files_layout.addLayout(self.source_files_browse_layout)
        self.add_source_files = QPushButton('Add...', objectName='browse')
        self.remove_source_files = QPushButton('Remove', objectName='browse')
        self.clear_source_files = QPushButton('Clear', objectName='browse')
        self.source_files_browse_layout.addWidget(self.add_source_files)
        self.source_files_browse_layout.addWidget(self.remove_source_files)
        self.source_files_browse_layout.addWidget(self.clear_source_files)
        self.source_files_browse_layout.addStretch()
        # self.add_source_files_layout.addStretch()

        self.save_issues_label = QLabel('Save Spreadsheet To', objectName='sub_title')
        self.issues_layout.addWidget(self.save_issues_label)
        self.issues_save_layout = QHBoxLayout()
        self.issues_layout.addLayout(self.issues_save_layout)
        self.save_sheet_entry = QLineEdit()
        self.issues_save_layout.addWidget(self.save_sheet_entry)
        self.save_issues_browse = QPushButton('Browse...', objectName='browse')
        self.issues_save_layout.addWidget(self.save_issues_browse)
        self.issues_save_layout.addStretch()

        self.issues_gen_button = QPushButton('Generate', objectName='run')
        self.issues_layout.addWidget(self.issues_gen_button, 0, QtCore.Qt.AlignRight)
        # self.issues_messages = QPlainTextEdit()
        # self.issues_messages.setReadOnly(True)
        # self.issues_layout.addWidget(self.issues_messages)


        # OPTION 4 CONTENTS
        self.opt_4_page_cont.setTabPosition(tab_position)
        self.opt_4_page_cont.setTabShape(tab_shape)

        self.opt_4_tab_1 = QWidget()
        self.opt_4_tab_2 = QWidget()

        self.opt_4_page_cont.addTab(self.opt_4_tab_1, 'Files and Settings')
        self.opt_4_page_cont.addTab(self.opt_4_tab_2, 'Results')

        # self.fixes_layout = QVBoxLayout(self.opt_4_page_cont)
        self.fixes_layout = QVBoxLayout(self.opt_4_tab_1)

        self.fixes_files_label = QLabel('Subtitle Files Directory', objectName='bold_label')
        self.fixes_files_label.setContentsMargins(0, 10, 0, 0)
        self.fixes_layout.addWidget(self.fixes_files_label)
        self.add_fixes_files_layout = QHBoxLayout()
        self.fixes_layout.addLayout(self.add_fixes_files_layout)
        self.fixes_files_list = QLineEdit()
        self.fixes_files_list.setReadOnly(True)
        self.add_fixes_files_layout.addWidget(self.fixes_files_list)
        self.browse_fixes_files = QPushButton('Browse...', objectName='browse')
        self.add_fixes_files_layout.addWidget(self.browse_fixes_files)
        self.add_fixes_files_layout.addStretch()

        self.fixes_videos_label = QLabel('Video Files Directory', objectName='bold_label')
        self.fixes_videos_label.setContentsMargins(0, 10, 0, 0)
        self.fixes_layout.addWidget(self.fixes_videos_label)
        self.add_fixes_videos_layout = QHBoxLayout()
        self.fixes_layout.addLayout(self.add_fixes_videos_layout)
        self.fixes_videos_list = QLineEdit()
        self.fixes_videos_list.setReadOnly(True)
        self.add_fixes_videos_layout.addWidget(self.fixes_videos_list)
        self.browse_fixes_videos = QPushButton('Browse...', objectName='browse')
        self.add_fixes_videos_layout.addWidget(self.browse_fixes_videos)
        self.add_fixes_videos_layout.addStretch()

        self.fixes_sc_label = QLabel('Scene Changes Directory', objectName='bold_label')
        self.fixes_sc_label.setContentsMargins(0, 10, 0, 0)
        self.fixes_layout.addWidget(self.fixes_sc_label)
        self.add_fixes_sc_layout = QHBoxLayout()
        self.fixes_layout.addLayout(self.add_fixes_sc_layout)
        self.fixes_sc_list = QLineEdit()
        self.fixes_sc_list.setReadOnly(True)
        self.add_fixes_sc_layout.addWidget(self.fixes_sc_list)
        self.browse_fixes_sc = QPushButton('Browse...', objectName='browse')
        self.add_fixes_sc_layout.addWidget(self.browse_fixes_sc)
        self.add_fixes_sc_layout.addStretch()

        self.fixes_setts_label = QLabel('Settings', objectName='header_2')
        self.fixes_setts_label.setContentsMargins(0, 30, 0, 30)
        self.fixes_layout.addWidget(self.fixes_setts_label)
        self.fixes_setts_layout = QGridLayout()
        self.fixes_layout.addLayout(self.fixes_setts_layout, 0)

        self.snap_to_frames_checkbox = QCheckBox(
            'Snap times to frames (Recommended)',
            objectName='fix_sett_check'
        )
        self.fix_TCFOL_checkbox = QCheckBox(
            'Fix "text can fit in one line"',
            objectName='fix_sett_check'
        )
        self.fix_TCFOL_label = QLabel(
            'Shorter than',
            objectName='fix_spin_label'
        )
        self.unbreak_limit_spin = QSpinBox(objectName='fix_spin')
        self.unbreak_limit_spin.setValue(42)
        self.unbreak_limit_spin.setMinimum(1)
        self.close_gaps_checkbox = QCheckBox(
            'Close gaps',
            objectName='fix_sett_check'
        )
        self.apply_min_gaps_checkbox = QCheckBox(
            'Apply minimum gaps',
            objectName='fix_sett_check'
        )
        self.min_gap_label = QLabel(
            'Minimum gap (frames)',
            objectName='fix_spin_label'
        )
        self.min_gap = QSpinBox(objectName='fix_spin')
        self.min_gap.setValue(2)
        self.min_gap.setMinimum(0)
        self.invalid_italics_checkbox = QCheckBox(
            'Fix invalid italic tags',
            objectName='fix_sett_check'
        )
        self.unused_br_checkbox = QCheckBox(
            'Fixed unused line breaks',
            objectName='fix_sett_check'
        )
        self.empty_subs_checkbox = QCheckBox(
            'Flag empty subtitles',
            objectName='fix_sett_check'
        )
        self.sort_subs_checkbox = QCheckBox(
            'Sort by start time',
            objectName='fix_sett_check'
        )

        self.fixes_setts_layout.addWidget(self.snap_to_frames_checkbox, 0, 0)
        self.fixes_setts_layout.addWidget(self.fix_TCFOL_checkbox, 1, 0)
        self.fixes_setts_layout.addWidget(self.fix_TCFOL_label, 2, 0)
        self.fixes_setts_layout.addWidget(self.unbreak_limit_spin, 2, 1)
        self.fixes_setts_layout.addWidget(self.close_gaps_checkbox, 3, 0)
        self.fixes_setts_layout.addWidget(self.apply_min_gaps_checkbox, 4, 0)
        self.fixes_setts_layout.addWidget(self.min_gap_label, 5, 0)
        self.fixes_setts_layout.addWidget(self.min_gap, 5, 1)
        self.fixes_setts_layout.addWidget(self.invalid_italics_checkbox, 6, 0)
        self.fixes_setts_layout.addWidget(self.unused_br_checkbox, 7, 0)
        self.fixes_setts_layout.addWidget(self.empty_subs_checkbox, 8, 0)
        self.fixes_setts_layout.addWidget(self.sort_subs_checkbox, 9, 0)

        self.fixes_setts_layout.setColumnStretch(0, 0)
        self.fixes_setts_layout.setColumnStretch(1, 0)
        self.fixes_setts_layout.setColumnStretch(2, 1)
        self.fixes_setts_layout.setColumnMinimumWidth(1, 75)

        self.run_fixes_button = QPushButton('Run Fixes', objectName='run')
        self.fixes_layout.addWidget(self.run_fixes_button, 0, QtCore.Qt.AlignRight)

        self.fixes_layout_2 = QVBoxLayout(self.opt_4_tab_2)
        self.fixes_results_label = QLabel('Fixes results', objectName='bold_label')
        self.fixes_results_label.setContentsMargins(0, 10, 0, 0)
        self.fixes_layout_2.addWidget(self.fixes_results_label, 0)

        self.fixes_messages = QPlainTextEdit()
        self.fixes_messages.setContentsMargins(0, 10, 0, 0)
        self.fixes_messages.setReadOnly(True)
        self.fixes_layout_2.addWidget(self.fixes_messages, 1)
        self.fixes_layout_2.addStretch()
        self.fixes_messages.setPlainText('No results to show.')

        # OPTION 5 CONTENTS
        self.opt_5_page_cont.setTabPosition(tab_position)
        self.opt_5_page_cont.setTabShape(tab_shape)

        self.opt_5_page_cont.setContentsMargins(0, 0, 0, 0)

        self.utils_tab_bar = self.opt_5_page_cont.tabBar()
        self.utils_tab_bar.setObjectName('utils_tab_bar')

        self.opt_5_tab_1 = QWidget()
        self.opt_5_tab_2 = QWidget()
        self.opt_5_tab_3 = QWidget()
        self.opt_5_tab_4 = QWidget()
        self.opt_5_tab_5 = QWidget()

        self.opt_5_page_cont.addTab(self.opt_5_tab_1, 'Copy Shot Changes')
        self.opt_5_page_cont.addTab(self.opt_5_tab_2, 'Generate Shot Changes')
        self.opt_5_page_cont.addTab(self.opt_5_tab_3, 'Frame Rates')
        self.opt_5_page_cont.addTab(self.opt_5_tab_4, 'Statistics')
        self.opt_5_page_cont.addTab(self.opt_5_tab_5, 'Converters')

        self.sc_layout = QVBoxLayout(self.opt_5_tab_1)
        # self.sc_title_1_widget = QWidget(objectName='border_widget')
        # self.sc_title_1_layout = QVBoxLayout(self.sc_title_1_widget)
        # self.copy_sc_label = QLabel('Copy Shot Changes', objectName='border_widget')
        # self.sc_layout.addWidget(self.copy_sc_label)

        self.copy_sc_videos_label = QLabel('Videos', objectName='sub_title')
        self.sc_layout.addWidget(self.copy_sc_videos_label)
        self.sc_copy_videos_layout = QHBoxLayout()
        self.sc_layout.addLayout(self.sc_copy_videos_layout)
        # self.copy_sc_videos_list = QListWidget()
        self.copy_sc_videos_list = DropList(1, ['.mp4', '.m4v', '.mpg',
                                            '.avi', '.mov', '.wmv', '.mkv'])
        self.copy_sc_videos_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

        self.sc_copy_videos_layout.addWidget(self.copy_sc_videos_list)
        self.sc_copy_videos_browse_layout = QVBoxLayout()
        self.sc_copy_videos_layout.addLayout(self.sc_copy_videos_browse_layout)
        self.sc_copy_videos_add = QPushButton('Add...', objectName='browse')
        self.sc_copy_videos_remove = QPushButton('Remove', objectName='browse')
        self.sc_copy_videos_clear = QPushButton('Clear', objectName='browse')
        self.sc_copy_videos_browse_layout.addWidget(self.sc_copy_videos_add)
        self.sc_copy_videos_browse_layout.addWidget(self.sc_copy_videos_remove)
        self.sc_copy_videos_browse_layout.addWidget(self.sc_copy_videos_clear)
        self.sc_copy_videos_browse_layout.addStretch()

        self.sc_copy_dir_label = QLabel('Scene Changes Directory', objectName='sub_title')
        self.sc_layout.addWidget(self.sc_copy_dir_label)
        self.sc_copy_dir_layout = QHBoxLayout()
        self.sc_layout.addLayout(self.sc_copy_dir_layout)
        self.sc_dir_entry = QLineEdit()
        if self.settings.value('last_copy_sc_source_dir'):
            self.sc_dir_entry.insert(self.settings.value('last_copy_sc_source_dir'))
        self.sc_copy_dir_layout.addWidget(self.sc_dir_entry)
        self.sc_copy_dir_browse = QPushButton('Browse...', objectName='browse')
        self.sc_copy_dir_layout.addWidget(self.sc_copy_dir_browse, 0, QtCore.Qt.AlignBottom)
        self.sc_copy_dir_layout.addStretch()

        self.sc_copy_to_label = QLabel('Copy Scene Changes To', objectName='sub_title')
        self.sc_layout.addWidget(self.sc_copy_to_label)
        self.sc_copy_to_layout = QHBoxLayout()
        self.sc_layout.addLayout(self.sc_copy_to_layout)
        self.sc_copy_to_entry = QLineEdit()
        self.sc_copy_to_layout.addWidget(self.sc_copy_to_entry)
        self.sc_copy_to_browse = QPushButton('Browse...', objectName='browse')
        self.sc_copy_to_layout.addWidget(self.sc_copy_to_browse, 0, QtCore.Qt.AlignBottom)
        self.sc_copy_to_layout.addStretch()

        self.copy_sc_button = QPushButton('Run', objectName='run')
        self.sc_layout.addWidget(self.copy_sc_button, 0, QtCore.Qt.AlignRight)

        # self.sc_copy_messages = QPlainTextEdit()
        # self.sc_copy_messages.setReadOnly(True)
        # self.sc_layout.addWidget(self.sc_copy_messages)





        self.sc_gen_layout = QVBoxLayout(self.opt_5_tab_2)

        self.gen_sc_videos_label = QLabel('Videos', objectName='sub_title')
        self.sc_gen_layout.addWidget(self.gen_sc_videos_label)
        self.sc_gen_videos_layout = QHBoxLayout()
        self.sc_gen_layout.addLayout(self.sc_gen_videos_layout)
        # self.gen_sc_videos_list = QListWidget()
        self.gen_sc_videos_list = DropList(1, ['.mp4', '.m4v', '.mpg',
                                            '.avi', '.mov', '.wmv', '.mkv'])
        self.gen_sc_videos_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.sc_gen_videos_layout.addWidget(self.gen_sc_videos_list)
        self.sc_gen_videos_browse_layout = QVBoxLayout()
        self.sc_gen_videos_layout.addLayout(self.sc_gen_videos_browse_layout)
        self.sc_gen_videos_add = QPushButton('Add...', objectName='browse')
        self.sc_gen_videos_remove = QPushButton('Remove', objectName='browse')
        self.sc_gen_videos_clear = QPushButton('Clear', objectName='browse')
        self.sc_gen_videos_browse_layout.addWidget(self.sc_gen_videos_add)
        self.sc_gen_videos_browse_layout.addWidget(self.sc_gen_videos_remove)
        self.sc_gen_videos_browse_layout.addWidget(self.sc_gen_videos_clear)
        self.sc_gen_videos_browse_layout.addStretch()

        self.sc_gen_dir_label = QLabel('Save Scene Changes To', objectName='sub_title')
        self.sc_gen_layout.addWidget(self.sc_gen_dir_label)
        self.sc_gen_dir_layout = QHBoxLayout()
        self.sc_gen_layout.addLayout(self.sc_gen_dir_layout)
        self.sc_gen_dir_entry = QLineEdit()
        self.sc_gen_dir_layout.addWidget(self.sc_gen_dir_entry)
        self.sc_gen_dir_browse = QPushButton('Browse...', objectName='browse')
        self.sc_gen_dir_layout.addWidget(self.sc_gen_dir_browse, 0, QtCore.Qt.AlignBottom)
        self.sc_gen_dir_layout.addStretch()

        self.sc_gen_sens_layout = QHBoxLayout()
        self.sc_gen_layout.addLayout(self.sc_gen_sens_layout)
        self.sc_gen_sens_label = QLabel('Sensitivity', objectName='bold_label')
        self.sc_gen_sens_layout.addWidget(self.sc_gen_sens_label)
        self.sc_gen_sens = QDoubleSpinBox()
        self.sc_gen_sens.setDecimals(2)
        self.sc_gen_sens.setSingleStep(0.01)
        self.sc_gen_sens.setValue(0.10)
        self.sc_gen_sens_layout.addWidget(self.sc_gen_sens)
        self.sc_gen_sens_layout.addStretch()

        self.gen_sc_button = QPushButton('Run', objectName='run')
        self.sc_gen_layout.addWidget(self.gen_sc_button, 0, QtCore.Qt.AlignRight)

        # self.sc_gen_messages = QPlainTextEdit()
        # self.sc_gen_messages.setReadOnly(True)
        # self.sc_gen_layout.addWidget(self.sc_gen_messages)





        self.fr_layout = QVBoxLayout(self.opt_5_tab_3)

        self.gen_fr_videos_label = QLabel('Videos', objectName='sub_title')
        self.fr_layout.addWidget(self.gen_fr_videos_label)
        self.fr_gen_videos_layout = QHBoxLayout()
        self.fr_layout.addLayout(self.fr_gen_videos_layout)
        # self.gen_fr_videos_list = QListWidget()
        self.gen_fr_videos_list = DropList(1, ['.mp4', '.m4v', '.mpg',
                                            '.avi', '.mov', '.wmv', '.mkv'])
        self.gen_fr_videos_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.fr_gen_videos_layout.addWidget(self.gen_fr_videos_list)
        self.fr_gen_videos_browse_layout = QVBoxLayout()
        self.fr_gen_videos_layout.addLayout(self.fr_gen_videos_browse_layout)
        self.fr_gen_videos_add = QPushButton('Add...', objectName='browse')
        self.fr_gen_videos_remove = QPushButton('Remove', objectName='browse')
        self.fr_gen_videos_clear = QPushButton('Clear', objectName='browse')
        self.fr_gen_videos_browse_layout.addWidget(self.fr_gen_videos_add)
        self.fr_gen_videos_browse_layout.addWidget(self.fr_gen_videos_remove)
        self.fr_gen_videos_browse_layout.addWidget(self.fr_gen_videos_clear)
        self.fr_gen_videos_browse_layout.addStretch()

        self.run_fr_button = QPushButton('Run', objectName='run')
        self.run_fr_layout = QHBoxLayout()
        self.run_fr_layout.setContentsMargins(0, 15, 0, 0)
        self.fr_layout.addLayout(self.run_fr_layout)
        self.run_fr_layout.addWidget(self.run_fr_button, 0, QtCore.Qt.AlignRight)

        self.fr_gen_results_label = QLabel('Results', objectName='sub_title')
        self.fr_layout.addWidget(self.fr_gen_results_label)
        self.fr_gen_messages = QPlainTextEdit()
        self.fr_gen_messages.setReadOnly(True)
        self.fr_layout.addWidget(self.fr_gen_messages)





        self.stats_layout = QVBoxLayout(self.opt_5_tab_4)

        self.stats_files_label = QLabel('Subtitle Files', objectName='sub_title')
        self.stats_layout.addWidget(self.stats_files_label)
        self.stats_files_layout = QHBoxLayout()
        self.stats_layout.addLayout(self.stats_files_layout)
        # self.stats_files_list = QListWidget()
        self.stats_files_list = DropList(1, ['.vtt', '.srt'])
        self.stats_files_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.stats_files_layout.addWidget(self.stats_files_list)
        self.stats_files_browse_layout = QVBoxLayout()
        self.stats_files_layout.addLayout(self.stats_files_browse_layout)
        self.stats_files_add = QPushButton('Add...', objectName='browse')
        self.stats_files_remove = QPushButton('Remove', objectName='browse')
        self.stats_files_clear = QPushButton('Clear', objectName='browse')
        self.stats_files_browse_layout.addWidget(self.stats_files_add)
        self.stats_files_browse_layout.addWidget(self.stats_files_remove)
        self.stats_files_browse_layout.addWidget(self.stats_files_clear)
        self.stats_files_browse_layout.addStretch()

        self.stats_save_layout_check = QHBoxLayout()
        self.stats_layout.addLayout(self.stats_save_layout_check)
        self.stats_save_checkbox = QCheckBox('Save report')
        self.stats_save_layout_check.addWidget(self.stats_save_checkbox)
        self.stats_save_layout_check.setContentsMargins(0, 30, 0, 0)
        self.stats_save_layout = QHBoxLayout()
        self.stats_layout.addLayout(self.stats_save_layout)
        self.stats_save_edit = QLineEdit()
        self.stats_save_browse = QPushButton('...', objectName='browse')
        self.stats_save_layout.addWidget(self.stats_save_edit)
        self.stats_save_layout.addWidget(self.stats_save_browse)
        self.stats_save_layout.addStretch()

        self.run_stats_button = QPushButton('Run', objectName='run')
        self.run_stats_layout = QHBoxLayout()
        self.run_stats_layout.setContentsMargins(0, 15, 0, 0)
        self.stats_layout.addLayout(self.run_stats_layout)
        self.run_stats_layout.addWidget(self.run_stats_button, 0, QtCore.Qt.AlignRight)

        self.stats_results_label = QLabel('Results', objectName='sub_title')
        self.stats_layout.addWidget(self.stats_results_label)
        self.stats_gen_messages = QPlainTextEdit()
        self.stats_gen_messages.setReadOnly(True)
        self.stats_layout.addWidget(self.stats_gen_messages)




        self.converters_layout = QVBoxLayout(self.opt_5_tab_5)

        self.conv_files_label = QLabel('Subtitle Files', objectName='sub_title')
        self.converters_layout.addWidget(self.conv_files_label)
        self.conv_files_list = DropList(1, ['.vtt', '.srt'])
        self.conv_files_list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.conv_files_layout = QHBoxLayout()
        self.converters_layout.addLayout(self.conv_files_layout)
        self.conv_files_layout.addWidget(self.conv_files_list)

        self.conv_files_buttons_layout = QVBoxLayout()
        self.conv_files_layout.addLayout(self.conv_files_buttons_layout)

        self.add_conv_files_button = QPushButton('Add', objectName='browse')
        self.remove_conv_files_button = QPushButton('Remove', objectName='browse')
        self.clear_conv_files_button = QPushButton('Clear', objectName='browse')

        self.conv_files_buttons_layout.addWidget(self.add_conv_files_button)
        self.conv_files_buttons_layout.addWidget(self.remove_conv_files_button)
        self.conv_files_buttons_layout.addWidget(self.clear_conv_files_button)
        self.conv_files_buttons_layout.setContentsMargins(0, 10, 0, 0)

        self.conv_files_buttons_layout.addStretch()


        self.out_format_conv_layout = QHBoxLayout()
        self.converters_layout.addLayout(self.out_format_conv_layout)

        self.conv_format_label = QLabel('Output format:')
        self.out_format_conv_layout.addWidget(self.conv_format_label)

        self.conv_format_list = QComboBox()
        self.conv_format_list.addItems(['JSON', 'SRT', 'VTT'])
        self.out_format_conv_layout.addWidget(self.conv_format_list)

        self.out_format_conv_layout.addStretch()
        self.out_format_conv_layout.setContentsMargins(0, 10, 0, 0)

        self.conv_save_layout = QHBoxLayout()
        self.converters_layout.addLayout(self.conv_save_layout)

        self.conv_save_spacer = QWidget()
        self.conv_save_label = QLabel('Save to')
        self.conv_save_edit = QLineEdit()
        self.conv_save_edit.insert(os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'))
        self.conv_browse_save_butt = QPushButton('...', objectName='browse1')

        self.conv_save_layout.addWidget(self.conv_save_spacer, 2)
        self.conv_save_layout.addWidget(self.conv_save_label, 0, QtCore.Qt.AlignRight)
        self.conv_save_layout.addWidget(self.conv_save_edit, QtCore.Qt.AlignRight)
        self.conv_save_layout.addWidget(self.conv_browse_save_butt, 0, QtCore.Qt.AlignRight)

        self.run_conv_button = QPushButton('Convert', objectName='run')
        self.converters_layout.addWidget(self.run_conv_button, 0, QtCore.Qt.AlignRight)














        self.active_opt_button_ss = '''
                *{
                    background: #2c4ac9;
                    color: #c5cad4;
                    border: none;
                    border-radius: 5px;
                    font-size: 12pt;
                    font-weight: bold;
                    padding: 10px;
                }

                *:hover {
                    background: #2c4ac9;
                    color: #c5cad4;
                    border: none;
                    font-size: 12pt;
                    border-radius: 3px;
                    padding: 10px;
                }
            '''

        self.inactive_opt_button_ss = '''
                *{
                    background: #202021;
                    color: #c5cad4;
                    border: none;
                    border-radius: 5px;
                    font-size: 12pt;
                    font-weight: bold;
                    padding: 10px;
                }

                *:hover {
                    background: #37373d;
                    color: #c5cad4;
                    border: none;
                    font-size: 12pt;
                    border-radius: 3px;
                    padding: 10px;
                }
            '''


        self.content.addWidget(self.welcome_widget)
        self.content.addWidget(self.opt_1_page_cont)
        self.content.addWidget(self.opt_2_page_cont)
        self.content.addWidget(self.opt_3_page_cont)
        self.content.addWidget(self.opt_4_page_cont)
        self.content.addWidget(self.opt_5_page_cont)
        # self.content.addWidget(self.opt_6_page_cont)

        self.option_1_button.clicked.connect(self.option_1_clicked)
        self.option_2_button.clicked.connect(self.option_2_clicked)
        self.option_3_button.clicked.connect(self.option_3_clicked)
        self.option_4_button.clicked.connect(self.option_4_clicked)
        self.option_5_button.clicked.connect(self.option_5_clicked)
        # self.option_6_button.clicked.connect(self.option_6_clicked)

        # self.list_1_browse.clicked.connect(self.browse_list_1)
        # self.opt_1_tab_1_add.clicked.connect(self.browse_list_1)
        self.opt_1_tab_1_add.clicked.connect(self.add_files)
        self.opt_1_tab_1_remove.clicked.connect(self.remove_files)
        self.opt_1_tab_1_clear.clicked.connect(self.clear_files)
        self.opt_1_tab_1_browse_save.clicked.connect(self.browse_save_dir)
        self.extract_ost_button.clicked.connect(self.extract_ost)

        # self.list_2_browse.clicked.connect(self.browse_list_1)
        # self.list_3_browse.clicked.connect(self.browse_list_2)
        # self.browse_save_1.clicked.connect(self.browse_save_dir)
        self.opt_1_tab_2_add_1.clicked.connect(self.add_files)
        self.opt_1_tab_2_remove_1.clicked.connect(self.remove_files)
        self.opt_1_tab_2_clear_1.clicked.connect(self.clear_files)
        self.opt_1_tab_2_add_2.clicked.connect(self.add_files)
        self.opt_1_tab_2_remove_2.clicked.connect(self.remove_files)
        self.opt_1_tab_2_clear_2.clicked.connect(self.clear_files)
        self.opt_1_tab_2_browse_save.clicked.connect(self.browse_save_dir)
        self.merge_ost_button.clicked.connect(self.merge_ost)

        # self.list_4_browse.clicked.connect(self.browse_list_3)
        # self.browse_save_2.clicked.connect(self.browse_save_dir)
        # self.generate_ost_button.clicked.connect(self.generate_ost)
        self.opt_1_tab_3_add.clicked.connect(self.add_files)
        self.opt_1_tab_3_remove.clicked.connect(self.remove_files)
        self.opt_1_tab_3_clear.clicked.connect(self.clear_files)
        self.opt_1_tab_3_browse_save.clicked.connect(self.browse_save_dir)
        self.generate_ost_button.clicked.connect(self.generate_ost)

        self.browse_qc_files.clicked.connect(self.browse_qc_subs_dir)
        self.browse_qc_videos.clicked.connect(self.browse_qc_videos_dir)
        self.browse_qc_sc_dir.clicked.connect(self.browse_qc_sc_dir_call)
        self.save_report_browse.clicked.connect(self.save_single_file)
        self.run_qc_button.clicked.connect(self.run_qc)

        self.add_target_files.clicked.connect(self.add_files)
        self.remove_target_files.clicked.connect(self.remove_files)
        self.clear_target_files.clicked.connect(self.clear_files)
        self.add_source_files.clicked.connect(self.add_files)
        self.remove_source_files.clicked.connect(self.remove_files)
        self.clear_source_files.clicked.connect(self.clear_files)
        # self.browse_source_files.clicked.connect(self.browse_list_2)
        self.save_issues_browse.clicked.connect(self.save_issues_file)
        self.issues_gen_button.clicked.connect(self.generate_issue_sheet)

        self.browse_fixes_files.clicked.connect(self.browse_dir_1)
        self.browse_fixes_videos.clicked.connect(self.browse_dir_2)
        self.browse_fixes_sc.clicked.connect(self.browse_dir_3)
        self.run_fixes_button.clicked.connect(self.run_fixes)



        # self.sc_copy_videos_browse.clicked.connect(self.browse_video_list)
        self.sc_copy_videos_add.clicked.connect(self.add_files)
        self.sc_copy_videos_remove.clicked.connect(self.remove_files)
        self.sc_copy_videos_clear.clicked.connect(self.clear_files)
        self.sc_copy_dir_browse.clicked.connect(self.browse_dir_1)
        self.sc_copy_to_browse.clicked.connect(self.browse_dir_2)
        self.copy_sc_button.clicked.connect(self.copy_scene_changes)

        # self.sc_gen_videos_browse.clicked.connect(self.browse_video_list)
        self.sc_gen_videos_add.clicked.connect(self.add_files)
        self.sc_gen_videos_remove.clicked.connect(self.remove_files)
        self.sc_gen_videos_clear.clicked.connect(self.clear_files)
        self.sc_gen_dir_browse.clicked.connect(self.browse_save_dir)
        self.gen_sc_button.clicked.connect(self.generate_sc)

        self.fr_gen_videos_add.clicked.connect(self.add_files)
        self.fr_gen_videos_remove.clicked.connect(self.remove_files)
        self.fr_gen_videos_clear.clicked.connect(self.clear_files)
        self.run_fr_button.clicked.connect(self.run_fr)

        self.stats_files_add.clicked.connect(self.add_files)
        self.stats_files_remove.clicked.connect(self.remove_files)
        self.stats_files_clear.clicked.connect(self.clear_files)
        self.run_stats_button.clicked.connect(self.get_stats)

        self.add_conv_files_button.clicked.connect(self.add_files)
        self.remove_conv_files_button.clicked.connect(self.remove_files)
        self.clear_conv_files_button.clicked.connect(self.clear_files)
        self.conv_browse_save_butt.clicked.connect(self.conv_browse_save)
        self.run_conv_button.clicked.connect(self.convert_run)



        self.extract_ost_files_list = []
        self.save_extracted_ost_dir = ''
        self.extract_ost_errors = ''

        self.merge_subtitle_files_list = []
        self.merge_ost_files_list = []
        self.save_merged_ost_dir = ''
        self.merge_ost_errors = ''

        self.ost_audit_files_list = []
        self.save_gen_ost_dir = ''
        self.gen_ost_errors = ''

        self.qc_files_dir = ''
        self.qc_videos_dir = ''
        self.qc_sc_dir_send = ''
        self.qc_report_name = ''
        self.qc_errors = ''

        self.issues_tar_list = []
        self.issues_en_list = []
        self.issues_sheet_name = ''
        self.issues_errors = ''

        self.fixes_files_dir = ''
        self.fixes_videos_dir = ''
        self.fixes_sc_dir = ''
        self.fixes_errors = ''

        self.copy_sc_videos_list_send = []
        self.copy_sc_source_dir = ''
        self.copy_sc_dest_dir = ''
        self.copy_sc_errors = ''

        self.gen_sc_videos_list_send = []
        self.gen_sc_save_dir = ''
        self.gen_sc_errors = ''

        self.gen_fr_videos_list_send = []
        self.gen_fr_errors = ''

        self.stats_files_list_send = []
        self.get_stats_errors = ''


        screen = QApplication.primaryScreen()
        rect = QRect(QPoint(), screen.size() * .9)
        rect.moveCenter(screen.geometry().center())
        self.setGeometry(rect)
        self.setMinimumWidth(rect.width())
        self.setMinimumHeight(rect.height())

        self.setWindowTitle('Subtitling Copilot')



    def add_files(self, event):
        add_to_files_1 = False
        add_to_files_2 = False
        print(self.content.currentIndex())

        # OST Option
        if self.content.currentIndex() == 1:
            # Extract
            if self.content.currentWidget().currentIndex() == 0:
                supported_formats = '*.vtt'
                drop_list = self.file_list_1
                add_to_files_1 = True

            # Merge
            elif self.content.currentWidget().currentIndex() == 1:
                supported_formats = '*.vtt'
                if self.sender() == self.opt_1_tab_2_add_1:
                    drop_list = self.file_list_2
                    add_to_files_1 = True
                elif self.sender() == self.opt_1_tab_2_add_2:
                    drop_list = self.file_list_3
                    add_to_files_2 = True

            # Generate
            elif self.content.currentWidget().currentIndex() == 2:
                supported_formats = '*.docx'
                drop_list = self.file_list_4
                add_to_files_1 = True

        # Issues Option
        elif self.content.currentIndex() == 3:
            supported_formats = '*.vtt'
            if self.sender() == self.add_target_files:
                drop_list = self.target_files_list
                add_to_files_1 = True
            elif self.sender() == self.add_source_files:
                drop_list = self.source_files_list
                add_to_files_2 = True

        # Utilities Option
        elif self.content.currentIndex() == 5:
            # Copy shot changes
            if self.content.currentWidget().currentIndex() == 0:
                supported_formats = 'Video Files (*.mp4 *.m4v *.mpg *.avi *.mov *.wmv *.mkv)'
                drop_list = self.copy_sc_videos_list

            # Generate shot changes
            elif self.content.currentWidget().currentIndex() == 1:
                supported_formats = 'Video Files (*.mp4 *.m4v *.mpg *.avi *.mov *.wmv *.mkv)'
                drop_list = self.gen_sc_videos_list

            # Get frame rates
            elif self.content.currentWidget().currentIndex() == 2:
                supported_formats = 'Video Files (*.mp4 *.m4v *.mpg *.avi *.mov *.wmv *.mkv)'
                drop_list = self.gen_fr_videos_list

            # Get stats
            elif self.content.currentWidget().currentIndex() == 3:
                supported_formats = 'Subtitle Files (*.srt *.vtt)'
                drop_list = self.stats_files_list

            # Converters
            elif self.content.currentWidget().currentIndex() == 4:
                supported_formats = 'Subtitle Files (*.srt *.vtt)'
                drop_list = self.conv_files_list

            add_to_files_1 = True

        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Files...',
            os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'),
            supported_formats
        )

        prev_file_count = drop_list.count()
        prev_files = [drop_list.item(row).text()
                      for row in range(prev_file_count)]

        repeated_files = []
        valid_files = []

        # Get the clean file names and exclude repeated ones.
        if file_names:
            items_count = drop_list.count()
            for i, file_name in enumerate(file_names):
                if file_name in prev_files:
                    repeated_files.append('- ' + file_name)
                    continue
                current_item = QListWidgetItem()
                current_item.setText(file_name)

                drop_list.insertItem(items_count + i, current_item)
                valid_files.append(file_name)

        # Generate info modal to let the user know
        # about ignored repeated files.
        if repeated_files:
            repeated_file_names = '\n'.join(repeated_files)
            if len(repeated_files) == 1:
                title = 'Repeated file'
                message = (f'{repeated_files[0].replace("file:///", "")}'
                           f'\n\nis already in the list.\nIgnored.')
            else:
                title = 'Repeated files'
                message = (f'{repeated_file_names.replace("file:///", "")}'
                           f'\n\nare already in the list.\nIgnored.')

            info_modal = QMessageBox.information(
                self,
                title,
                message
            )

        # NOTE: This is not right. file_names should not be used here,
        #       but only the valid files.
        if add_to_files_1:
            self.files_1 = valid_files
        elif add_to_files_2:
            self.files_2 = valid_files


    def remove_files(self, event):
        if self.content.currentIndex() == 1:
            if self.content.currentWidget().currentIndex() == 0:
                drop_list = self.file_list_1
            elif self.content.currentWidget().currentIndex() == 1:
                if self.sender() == self.opt_1_tab_2_remove_1:
                    drop_list = self.file_list_2
                elif self.sender() == self.opt_1_tab_2_remove_2:
                    drop_list = self.file_list_3
            elif self.content.currentWidget().currentIndex() == 2:
                drop_list = self.file_list_4

        elif self.content.currentIndex() == 3:
            if self.sender() == self.remove_target_files:
                drop_list = self.target_files_list
            elif self.sender() == self.remove_source_files:
                drop_list = self.source_files_list

        elif self.content.currentIndex() == 5:
            if self.content.currentWidget().currentIndex() == 0:
                drop_list = self.copy_sc_videos_list
            elif self.content.currentWidget().currentIndex() == 1:
                drop_list = self.gen_sc_videos_list
            elif self.content.currentWidget().currentIndex() == 2:
                drop_list = self.gen_fr_videos_list
            elif self.content.currentWidget().currentIndex() == 3:
                drop_list = self.stats_files_list
            elif self.content.currentWidget().currentIndex() == 4:
                drop_list = self.conv_files_list

        selected_list = drop_list.selectedItems()

        for item in selected_list:
            current_row = drop_list.indexFromItem(item).row()
            drop_list.takeItem(current_row)

    def clear_files(self, event):
        clear_files_1 = False
        clear_files_2 = False

        # OST Option
        if self.content.currentIndex() == 1:
            # Extract
            if self.content.currentWidget().currentIndex() == 0:
                drop_list = self.file_list_1
                clear_files_1 = True

            # Merge
            elif self.content.currentWidget().currentIndex() == 1:
                if self.sender() == self.opt_1_tab_2_clear_1:
                    drop_list = self.file_list_2
                    clear_files_1 = True
                elif self.sender() == self.opt_1_tab_2_clear_2:
                    drop_list = self.file_list_3
                    clear_files_2 = True

            # Generate
            elif self.content.currentWidget().currentIndex() == 2:
                drop_list = self.file_list_4
                clear_files_1 = True

        # Issues Option
        elif self.content.currentIndex() == 3:
            if self.sender() == self.clear_target_files:
                drop_list = self.target_files_list
                clear_files_1 = True
            elif self.sender() == self.clear_source_files:
                drop_list = self.source_files_list
                clear_files_1 = True

        # Utilities Option
        elif self.content.currentIndex() == 5:
            # Copy shot changes
            if self.content.currentWidget().currentIndex() == 0:
                drop_list = self.copy_sc_videos_list

            # Generate shot changes
            elif self.content.currentWidget().currentIndex() == 1:
                drop_list = self.gen_sc_videos_list

            # Get frame rates
            elif self.content.currentWidget().currentIndex() == 2:
                drop_list = self.gen_fr_videos_list

            # Get stats
            elif self.content.currentWidget().currentIndex() == 3:
                drop_list = self.stats_files_list

            # Converters
            elif self.content.currentWidget().currentIndex() == 4:
                drop_list = self.conv_files_list

            clear_files_1 = True

        drop_list.clear()
        if clear_files_1:
            self.files_1 = []
        elif clear_files_2:
            self.files_2 = []


    def option_1_clicked(self, event):
        self.content.setCurrentWidget(self.opt_1_page_cont)

        self.option_1_button.setStyleSheet(self.active_opt_button_ss)
        self.option_2_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_3_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_4_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_5_button.setStyleSheet(self.inactive_opt_button_ss)
        # self.option_6_button.setStyleSheet(self.inactive_opt_button_ss)

    def option_2_clicked(self, event):
        self.content.setCurrentWidget(self.opt_2_page_cont)

        self.option_1_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_2_button.setStyleSheet(self.active_opt_button_ss)
        self.option_3_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_4_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_5_button.setStyleSheet(self.inactive_opt_button_ss)
        # self.option_6_button.setStyleSheet(self.inactive_opt_button_ss)

    def option_3_clicked(self, event):
        self.content.setCurrentWidget(self.opt_3_page_cont)

        self.option_1_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_2_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_3_button.setStyleSheet(self.active_opt_button_ss)
        self.option_4_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_5_button.setStyleSheet(self.inactive_opt_button_ss)
        # self.option_6_button.setStyleSheet(self.inactive_opt_button_ss)

    def option_4_clicked(self, event):
        self.content.setCurrentWidget(self.opt_4_page_cont)

        self.option_1_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_2_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_3_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_4_button.setStyleSheet(self.active_opt_button_ss)
        self.option_5_button.setStyleSheet(self.inactive_opt_button_ss)
        # self.option_6_button.setStyleSheet(self.inactive_opt_button_ss)

    def option_5_clicked(self, event):
        self.content.setCurrentWidget(self.opt_5_page_cont)

        self.option_1_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_2_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_3_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_4_button.setStyleSheet(self.inactive_opt_button_ss)
        self.option_5_button.setStyleSheet(self.active_opt_button_ss)
        # self.option_6_button.setStyleSheet(self.inactive_opt_button_ss)

    # def option_6_clicked(self, event):
    #     self.content.setCurrentWidget(self.opt_6_page_cont)

    #     self.option_1_button.setStyleSheet(self.inactive_opt_button_ss)
    #     self.option_2_button.setStyleSheet(self.inactive_opt_button_ss)
    #     self.option_3_button.setStyleSheet(self.inactive_opt_button_ss)
    #     self.option_4_button.setStyleSheet(self.inactive_opt_button_ss)
    #     self.option_5_button.setStyleSheet(self.inactive_opt_button_ss)
    #     self.option_6_button.setStyleSheet(self.active_opt_button_ss)

    def browse_list_1(self, event):
        print(self.content.currentIndex())

        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Files...',
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            '*.vtt'
        )

        if self.content.currentIndex() == 1:
            if self.content.currentWidget().currentIndex() == 0:

                if file_names:
                    self.file_list_1.clear()
                    self.extract_ost_files_list = []

                for i, file_name in enumerate(file_names):
                    self.extract_ost_files_list.append(file_name)

                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.file_list_1.insertItem(i, current_item)

            elif self.content.currentWidget().currentIndex() == 1:

                if file_names:
                    self.file_list_2.clear()
                    self.merge_subtitle_files_list = []

                for i, file_name in enumerate(file_names):
                    self.merge_subtitle_files_list.append(file_name)

                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.file_list_2.insertItem(i, current_item)

            elif self.content.currentWidget().currentIndex() == 2:
                pass


        elif self.content.currentIndex() == 2:
            pass

        elif self.content.currentIndex() == 3:

            if file_names:
                self.target_files_list.clear()
                self.issues_tar_list = []

            for i, file_name in enumerate(file_names):
                self.issues_tar_list.append(file_name)

                current_item = QListWidgetItem()
                current_item.setText(file_name)
                self.target_files_list.insertItem(i, current_item)

        elif self.content.currentIndex() == 4:
            pass

        elif self.content.currentIndex() == 5:
            if self.content.currentWidget().currentIndex() == 0:
                pass

            elif self.content.currentWidget().currentIndex() == 1:
                pass

            elif self.content.currentWidget().currentIndex() == 2:
                pass

            elif self.content.currentWidget().currentIndex() == 3:
                if file_names:
                    self.stats_files_list.clear()
                    self.stats_files_list_send = []

                for i, file_name in enumerate(file_names):
                    self.stats_files_list_send.append(file_name)

                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.stats_files_list.insertItem(i, current_item)


    def browse_list_2(self, event):
        print(self.content.currentIndex())

        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Files...',
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            '*.vtt'
        )

        if self.content.currentIndex() == 1:
            if self.content.currentWidget().currentIndex() == 0:
                pass

            elif self.content.currentWidget().currentIndex() == 1:
                if file_names:
                    self.file_list_3.clear()
                    self.merge_ost_files_list = []

                for i, file_name in enumerate(file_names):
                    self.merge_ost_files_list.append(file_name)
                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.file_list_3.insertItem(i, current_item)

            elif self.content.currentWidget().currentIndex() == 2:
                pass

        elif self.content.currentIndex() == 2:
            pass

        elif self.content.currentIndex() == 3:
            if file_names:
                self.source_files_list.clear()
                self.issues_en_list = []

            for i, file_name in enumerate(file_names):
                self.issues_en_list.append(file_name)

                current_item = QListWidgetItem()
                current_item.setText(file_name)
                self.source_files_list.insertItem(i, current_item)

        elif self.content.currentIndex() == 4:
            pass

        elif self.content.currentIndex() == 5:
            if self.content.currentWidget().currentIndex() == 0:
                pass

            elif self.content.currentWidget().currentIndex() == 1:
                pass

            elif self.content.currentWidget().currentIndex() == 2:
                pass

            elif self.content.currentWidget().currentIndex() == 3:
                pass


    def browse_list_3(self, event):
        print(self.content.currentIndex())
        print(self.content.currentWidget().currentIndex())

        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Files...',
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            '*.docx'
        )

        if file_names:
            self.file_list_4.clear()
            self.ost_audit_files_list = []

        for i, file_name in enumerate(file_names):
            self.ost_audit_files_list.append(file_name)

            current_item = QListWidgetItem()
            current_item.setText(file_name)
            self.file_list_4.insertItem(i, current_item)


    def browse_video_list(self, event):
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Files...',
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            '*.mp4'
        )

        if self.content.currentIndex() == 5:
            if self.content.currentWidget().currentIndex() == 0:
                if file_names:
                    self.copy_sc_videos_list.clear()
                    self.copy_sc_videos_list_send = []

                for i, file_name in enumerate(file_names):
                    self.copy_sc_videos_list_send.append(file_name)
                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.copy_sc_videos_list.insertItem(i, current_item)

            elif self.content.currentWidget().currentIndex() == 1:
                if file_names:
                    self.gen_sc_videos_list.clear()
                    self.gen_sc_videos_list_send = []

                for i, file_name in enumerate(file_names):
                    self.gen_sc_videos_list_send.append(file_name)
                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.gen_sc_videos_list.insertItem(i, current_item)

            elif self.content.currentWidget().currentIndex() == 2:
                if file_names:
                    self.gen_fr_videos_list.clear()
                    self.gen_fr_videos_list_send = []

                for i, file_name in enumerate(file_names):
                    self.gen_fr_videos_list_send.append(file_name)
                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.gen_fr_videos_list.insertItem(i, current_item)


    def browse_dir_1(self, event):
        # Fixes Option
        if self.content.currentIndex() == 4:
            if self.settings.value('last_fixes_files_dir'):
                start_dir = self.settings.value('last_fixes_files_dir')
            else:
                start_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

        # Utilities Option
        elif self.content.currentIndex() == 5:
            # Copy shot changes
            if self.content.currentWidget().currentIndex() == 0:
                if self.settings.value('last_copy_sc_source_dir'):
                    start_dir = self.settings.value('last_copy_sc_source_dir')
                else:
                    start_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            start_dir,
            QFileDialog.ShowDirsOnly
        )

        if self.content.currentIndex() == 4 and directory:
            self.fixes_files_dir = directory
            self.fixes_files_list.clear()
            self.fixes_files_list.insert(self.fixes_files_dir)
            self.settings.setValue('last_fixes_files_dir', directory)

        if self.content.currentIndex() == 5 and directory:
            if self.content.currentWidget().currentIndex() == 0:
                self.copy_sc_source_dir = directory
                self.sc_dir_entry.clear()
                self.sc_dir_entry.insert(self.copy_sc_source_dir)
                self.settings.setValue('last_copy_sc_source_dir', directory)


    def browse_dir_2(self, event):
        print(self.content.currentIndex())
        # print(self.content.currentWidget().currentIndex())
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )

        if self.content.currentIndex() == 4:
            self.fixes_videos_dir = directory
            self.fixes_videos_list.clear()
            self.fixes_videos_list.insert(self.fixes_videos_dir)

        elif self.content.currentIndex() == 5:
            if self.content.currentWidget().currentIndex() == 0:
                self.copy_sc_dest_dir = directory
                self.sc_copy_to_entry.clear()
                self.sc_copy_to_entry.insert(self.copy_sc_dest_dir)

    def browse_dir_3(self, event):
        print(self.content.currentIndex())
        # print(self.content.currentWidget().currentIndex())
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )

        if self.content.currentIndex() == 4:
            self.fixes_sc_dir = directory
            self.fixes_sc_list.clear()
            self.fixes_sc_list.insert(self.fixes_sc_dir)






    def browse_save_dir(self, event):
        print(self.content.currentIndex())
        print(self.content.currentWidget().currentIndex())

        save_dir = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )


        if self.content.currentIndex() == 1:
            if self.content.currentWidget().currentIndex() == 0:
                self.save_extracted_ost_dir = save_dir
                self.opt_1_tab_1_save_edit.clear()
                self.opt_1_tab_1_save_edit.insert(self.save_extracted_ost_dir)

            elif self.content.currentWidget().currentIndex() == 1:
                self.save_merged_ost_dir = save_dir
                self.opt_1_tab_2_save_edit.clear()
                self.opt_1_tab_2_save_edit.insert(self.save_merged_ost_dir)

            elif self.content.currentWidget().currentIndex() == 2:
                self.save_gen_ost_dir = save_dir
                self.opt_1_tab_3_save_edit.clear()
                self.opt_1_tab_3_save_edit.insert(self.save_gen_ost_dir)

        elif self.content.currentIndex() == 2:
            pass

        elif self.content.currentIndex() == 3:
            pass

        elif self.content.currentIndex() == 4:
            pass

        elif self.content.currentIndex() == 5:
            if self.content.currentWidget().currentIndex() == 0:
                pass

            elif self.content.currentWidget().currentIndex() == 1:
                self.gen_sc_save_dir = save_dir
                self.sc_gen_dir_entry.clear()
                self.sc_gen_dir_entry.insert(self.gen_sc_save_dir)

            elif self.content.currentWidget().currentIndex() == 2:
                pass

            elif self.content.currentWidget().currentIndex() == 3:
                pass


    def browse_qc_subs_dir(self, event):
        if self.settings.value('last_qc_subs_dir'):
            start_dir = self.settings.value('last_qc_subs_dir')
        else:
            start_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')


        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            # r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            start_dir,
            QFileDialog.ShowDirsOnly
        )

        if directory:
            self.settings.setValue('last_qc_subs_dir', directory)

            self.qc_files_dir = directory
            self.qc_files_list.clear()
            self.qc_files_list.insert(self.qc_files_dir)


    def browse_qc_videos_dir(self, event):
        if self.settings.value('last_qc_videos_dir'):
            start_dir = self.settings.value('last_qc_videos_dir')
        else:
            start_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')

        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            # r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            start_dir,
            QFileDialog.ShowDirsOnly
        )

        if directory:
            self.settings.setValue('last_qc_videos_dir', directory)
            self.qc_videos_dir = directory
            self.qc_videos_list.clear()
            self.qc_videos_list.insert(self.qc_videos_dir)

    def browse_qc_sc_dir_call(self, event):
        if self.settings.value('last_qc_sc_dir'):
            start_dir = self.settings.value('last_qc_sc_dir')
        else:
            start_dir = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            # r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            start_dir,
            QFileDialog.ShowDirsOnly
        )

        if directory:
            self.settings.setValue('last_qc_sc_dir', directory)
            self.qc_sc_dir_send = directory
            self.qc_sc_list.clear()
            self.qc_sc_list.insert(self.qc_sc_dir_send)


    def save_single_file(self, event):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            'Save Report as...',
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            '*.txt'
        )

        print(file_name)

        if self.content.currentIndex() == 2:
            self.qc_report_name = file_name
            self.save_report_entry.clear()
            self.save_report_entry.insert(self.qc_report_name)


    def save_issues_file(self, event):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            'Save Report as...',
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            '*.xlsx'
        )

        print(file_name)

        self.issues_sheet_name = file_name
        self.save_sheet_entry.clear()
        self.save_sheet_entry.insert(self.issues_sheet_name)


    def add_conv_files(self, event):
        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            'Select Files...',
            os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'),
            '(*.srt *.vtt)'
        )

        prev_file_count = self.conv_files_list.count()
        prev_files = [self.conv_files_list.item(row).text()
                      for row in range(prev_file_count)]


        repeated_files = []

        if file_names:
            items_count = prev_file_count
            for i, file_name in enumerate(file_names):
                if file_name in prev_files:
                    repeated_files.append('- ' + file_name)
                    continue
                current_item = QListWidgetItem()
                current_item.setText(file_name)

                self.conv_files_list.insertItem(items_count + i, current_item)

        if repeated_files:
            repeated_file_names = '\n'.join(repeated_files)
            if len(repeated_files) == 1:
                title = 'Repeated File'
                message = (f'{repeated_files[0].replace("file:///", "")}\n\n'
                           f'is already in the list.\nWill be ignored.')
            else:
                title = 'Repeated Files'
                message = (f'{repeated_file_names.replace("file:///", "")}\n\n'
                           f'are already in the list.\nWill be ignored.')

            info_modal = QMessageBox.information(
                self,
                title,
                message
            )

    def remove_conv_files(self, event):
        selected_list = self.conv_files_list.selectedItems()
        for item in selected_list:
            current_row = self.conv_files_list.indexFromItem(item).row()
            self.conv_files_list.takeItem(current_row)

    def clear_conv_files(self, event):
        self.conv_files_list.clear()

    def conv_browse_save(self, event):
        save_path = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop'),
            QFileDialog.ShowDirsOnly
        )

        if save_path:
            self.conv_save_edit.clear()
            self.conv_save_edit.insert(save_path)

    def convert_run(self, event):
        file_count = self.conv_files_list.count()
        files = [self.conv_files_list.item(row).text()
                 for row in range(file_count)]

        output_format = self.conv_format_list.currentText()

        save_path = self.conv_save_edit.text()

        if not files:

            error_modal = QMessageBox().critical(
                self,
                'Error',
                'Please add at least one subtitle file to convert.',
            )


            return

        if not save_path:
            error_modal = QMessageBox.critical(
                self,
                'Error',
                'Please select a path for the converted files.'
            )

            return

        if not os.path.isdir(save_path):
            error_modal = QMessageBox.critical(
                self,
                'Error',
                'The destination path does not exist.'
            )

            return

        for sub_file in files:
            name, ext = os.path.splitext(sub_file)
            actual_name = name.split('/')[-1]

            if ext == '.srt':
                subs = parse_SRT(sub_file)
                if output_format == 'JSON':
                    json_string = convert_to_JSON(subs)
                    with open(save_path+'\\'+actual_name+'.json', 'w', encoding='utf-8') as out_file:
                        out_file.write(json_string)


        success_modal = QMessageBox.information(
            self,
            'Success',
            'All files converted successfully'
        )


    def extract_ost(self, event):

        files = self.get_files(self.file_list_1)
        save_path = self.get_save_dir(self.opt_1_tab_1_save_edit)

        errors = ''

        if not files:
            errors += 'ERROR: Cannot extract OSTs. Please add at least one subtitle file.\n\n'
        if not save_path:
            errors += 'ERROR: Cannot save OSTs. Please select a directory for the OST files.'

        if not errors:
            ost_lang_path = '/'.join(files[0].split('/')[:-1])

            total_errors = batch_extract_OSTs(
                ost_lang_path,
                save_path,
                save_OSTs=self.opt_1_tab_1_checkbox_1.isChecked(),
                delete_OSTs=self.opt_1_tab_1_checkbox_2.isChecked()
            )

            if total_errors:
                warnings, errors = total_errors

                if warnings:
                    warnings_string = ''
                    for warning_key in warning.keys():
                        warnings_string += 'Warnings\n\n\n'
                        warnings_string += f'{warning_key}\n\t'
                        warnings_string += f'{warnings[warning_key]}\n'

            else:
                info_modal = QMessageBox.information(
                    self,
                    'Finished',
                    'OSTs extracted successfully.'
                )

        else:
            error_modal = QMessageBox.critical(
                self,
                'Error',
                errors,
            )


        # if not self.extract_ost_files_list:
        #     self.extract_ost_errors += 'ERROR: Cannot extract OSTs. Please select at least one subtitle file.\n'
        # if not self.save_extracted_ost_dir:
        #     self.extract_ost_errors += 'ERROR: Cannot save OSTs. Please select a directory for the OST files.'

        # if not self.extract_ost_errors:
        #     # text = 'Extracting OSTs files with...\n'
        #     # for file_name in self.extract_ost_files_list:
        #     #     text += '\n'
        #     #     text += file_name
        #     # text += '\n\n'
        #     # text += 'Saving to...\n'
        #     # text += self.save_extracted_ost_dir
        #     text = 'OSTs extracted successfully.'

        #     ost_lang_path = '/'.join(self.extract_ost_files_list[0].split('/')[:-1])


        #     total_errors = batch_extract_OSTs(
        #         ost_lang_path,
        #         self.save_extracted_ost_dir,
        #         save_OSTs=self.checkbox_1.isChecked(),
        #         delete_OSTs=self.checkbox_2.isChecked()
        #     )

        #     if total_errors:
        #         warnings, errors = total_errors

        #         if warnings:
        #             warnings_string = ''
        #             for warning_key in warnings.keys():
        #                 warnings_string += 'Warnings\n\n\n'
        #                 warnings_string += warning_key + '\n\t'
        #                 warnings_string += warnings[warning_key] + '\n'

        #             self.messages.setPlainText(warnings_string)

        #     self.messages.setPlainText(text)
        # else:
        #     self.messages.setPlainText(self.extract_ost_errors)
        #     self.extract_ost_errors = ''


    def merge_ost(self, event):

        sub_files = self.get_files(self.file_list_2)
        ost_files = self.get_files(self.file_list_3)
        save_path = self.get_save_dir(self.opt_1_tab_2_save_edit)

        errors = ''

        if not sub_files:
            errors += 'ERROR: Cannot merge OSTs. Please add at least one subtitle file.\n\n'
        if not ost_files:
            errors += 'ERROR: Cannot merge OSTs. Please add at least one OST file.\n\n'
        if not save_path:
            errors += 'ERROR: Cannot save OSTs. Please select a directory for the new files.'


        if not errors:
            # sub_dir = '/'.join(sub_files[0].split('/')[:-1])
            # ost_dir = '/'.join(ost_files[0].split('/')[:-1])

            if self.checkbox_3.isChecked():
                save_path = sub_dir

            batch_merge_subs(
                sub_files,
                ost_files,
                save_path
            )

            info_modal = QMessageBox.information(
                self,
                'Finished',
                'Files merged successfully'
            )

        else:
            error_modal = QMessageBox.critical(
                self,
                'Error',
                errors,
            )

        # if not self.merge_subtitle_files_list:
        #     self.merge_ost_errors += 'ERROR: Cannot merge OSTs. Please select at least one subtitle file.\n'
        # if not self.merge_ost_files_list:
        #     self.merge_ost_errors += 'ERROR: Cannot merge OSTs. Please select at least one OST file.\n'
        # if (len(self.merge_subtitle_files_list)
        #     != len(self.merge_ost_files_list)):
        #     # Different number of files.
        #     self.merge_ost_errors += 'ERROR: Cannot merge OSTs. The number of subtitle files is different from the number of OST files.\n'
        # if not self.save_merged_ost_dir and not self.checkbox_3.isChecked():
        #     self.merge_ost_errors += 'ERROR: Cannot save Subtitle file(s). Please select a directory for the subtitle files.'

        # if not self.merge_ost_errors:
        #     self.merge_messages.setPlainText('Merging...')
        #     sub_dir = '/'.join(self.merge_subtitle_files_list[0].split('/')[:-1])
        #     ost_dir = '/'.join(self.merge_ost_files_list[0].split('/')[:-1])


        #     if self.checkbox_3.isChecked():
        #         self.save_merged_ost_dir = sub_dir

        #     batch_merge_subs(
        #         sub_dir,
        #         ost_dir,
        #         self.save_merged_ost_dir
        #     )

        #     text = 'Files merged successfully'
        #     self.merge_messages.setPlainText(text)
        # else:
        #     self.merge_messages.setPlainText(self.merge_ost_errors)
        #     self.merge_ost_errors = ''


    def generate_ost(self, event):
        ost_doc_files = self.get_files(self.file_list_4)
        save_path = self.get_save_dir(self.opt_1_tab_3_save_edit)

        errors = ''

        if not ost_doc_files:
            errors += 'ERROR: Cannot generate OSTs. Please add at least one audit file.\n'
        if not save_path:
            errors += 'ERROR: Cannot generate OSTs. Please select a directory to save the generated OSTs.\n'

        if not errors:
            single_files = []
            multi_files = []

            for file_name in ost_doc_files:
                if check_OST_audit(file_name):
                    single_files.append(file_name)
                else:
                    multi_files.append(file_name)

            success = False

            if single_files and multi_files:
                pass
            elif single_files:
                for file_name in single_files:
                    get_OSTs_single(file_name, save_path)
                success = True


            elif multi_files:
                get_OSTs(multi_files, save_path)
                success = True


            if success:
                info_modal = QMessageBox.information(
                    self,
                    'Finished',
                    'OST files generated successfully.'
                )

        else:
            error_modal = QMessageBox.critical(
                self,
                'Error',
                errors
            )











        # if not self.ost_audit_files_list:
        #     self.gen_ost_errors += 'ERROR: Cannot generate OSTs. Please select at least one audit file.\n'
        # if not self.save_gen_ost_dir:
        #     self.gen_ost_errors += 'ERROR: Cannot generate OSTs. Please select a directory to save the generated OSTs.\n'

        # if not self.gen_ost_errors:
        #     # text = 'Generating OSTs files from...\n'
        #     # for file_name in self.ost_audit_files_list:
        #     #     text += '\n'
        #     #     text += file_name
        #     # text += '\n\n'
        #     # text += 'Saving to...\n'
        #     # text += self.save_gen_ost_dir
        #     # self.generation_messages.setPlainText(text)

        #     single_files = []
        #     multi_files = []

        #     for file_name in self.ost_audit_files_list:
        #         if check_OST_audit(file_name):
        #             single_files.append(file_name)
        #         else:
        #             multi_files.append(file_name)

        #     success = False

        #     print(single_files)
        #     print(multi_files)

        #     if single_files and multi_files:
        #         pass
        #     elif single_files:
        #         for file_name in single_files:
        #             get_OSTs_single(file_name, self.save_gen_ost_dir)
        #         success = True
        #         single_files = []
        #     elif multi_files:
        #         get_OSTs(multi_files    , self.save_gen_ost_dir)
        #         success = True
        #         multi_files = []

        #     self.ost_audit_files_list = []

        #     if success:
        #         text = 'OSTs generated successfully'

        #     self.generation_messages.setPlainText(text)
        # else:
        #     self.generation_messages.setPlainText(self.gen_ost_errors)
        #     self.gen_ost_errors = ''

    def run_qc(self, event):
        errors = ''
        if not self.qc_files_dir:
            errors += 'ERROR: Cannot run quality check. Please select a directory for the subtitle files.\n\n'
        if not self.qc_videos_dir and self.check_sc_checkbox.isChecked():
            errors += 'ERROR: Cannot run quality check with shot changes. Please select a directory for the videos.\n\n'
        if not self.qc_videos_dir and self.check_gaps_checkbox.isChecked():
            errors += 'ERROR: Cannot run quality check with gaps. Please select a directory for the videos.\n\n'
        if not self.qc_sc_dir_send and self.check_sc_checkbox.isChecked():
            errors += 'ERROR: Cannot run quality check with shot changes. Please select a directory for the scene changes.\n\n'
        if not self.qc_report_name and self.save_report_checkbox.isChecked():
            errors += 'ERROR: Cannot save quality check report. Please select a file name to save it.\n\n'

        print(errors)

        if not errors:
            text = 'Running quality check...\n'
            # print(text)

            # NOTE: For some reason this is not working.
            self.qc_messages.setPlainText(text)

            cps_limit = self.max_cps_spin.value()
            cps_spaces = self.cps_spaces_checkbox.isChecked()
            cpl_limit = self.max_cpl_spin.value()
            max_lines = self.max_lines_spin.value()
            min_duration = self.min_duration_spin.value()/1000
            max_duration = self.max_duration_spin.value()/1000
            ellipses = self.check_ellipses_checkbox.isChecked()
            gaps = self.check_gaps_checkbox.isChecked()
            shot_changes = self.check_sc_checkbox.isChecked()
            tcfol = self.check_TCFOL_checkbox.isChecked()
            ost = self.check_OST_checkbox.isChecked()
            nfgl = self.check_NFG_checkbox.isChecked()
            report = self.save_report_checkbox.isChecked()
            report_name = self.qc_report_name

            report = batch_quality_check(
                self.qc_files_dir,
                self.qc_videos_dir,
                self.qc_sc_dir_send,
                shot_changes=shot_changes,
                CPS=True,
                CPS_limit=cps_limit,
                CPS_spaces=cps_spaces,
                CPL=True,
                CPL_limit=cpl_limit,
                max_lines=max_lines,
                min_duration=min_duration,
                max_duration=max_duration,
                ellipses=ellipses,
                gaps=gaps,
                glyphs=False,
                old=False,
                check_TCFOL=tcfol,
                check_OST=ost,
                report=report,
                report_name=report_name
            )
            # print('Quality check DONE')
            # print(type(report))
            # print(report)

            if isinstance(report, str):
                error_modal = QMessageBox.critical(
                    self,
                    'Error',
                    report
                )

                return
            else:
                print(report)
                self.qc_messages.setPlainText('\n'.join(report))
                self.opt_2_page_cont.setCurrentIndex(1)

        else:


            error_modal = QMessageBox.critical(
                self,
                'Error',
                errors
            )

            return

            # self.qc_messages.setPlainText(self.qc_errors)
            # self.qc_errors = ''


    def generate_issue_sheet(self, event):
        target_files = self.get_files(self.target_files_list)
        source_files = self.get_files(self.source_files_list)
        save_path = self.get_save_dir(self.save_sheet_entry)

        errors = ''

        if not target_files:
            errors += 'ERROR: Cannot generate issues sheet. Please add at least one target language subtitle file.\n\n'
        if not source_files:
            errors += 'ERROR: Cannot generate issues sheet. Please add at least one source language subtitle file.\n\n'
        if (target_files and source_files
            and (len(target_files) != len(source_files))):
            # Different numbers of files
            errors += 'ERROR: Cannot generate issues sheet. Please select the same number of targe and source language files.\n\n'
        if not save_path:
            errors += 'ERROR: Cannot generate issues sheet. Please select a file name for the spreadsheet.'



        if not errors:
            en_path = '/'.join(source_files[0].split('/')[:-1])
            tar_path = '/'.join(target_files[0].split('/')[:-1])

            result = batch_gen_CPS_sheet(
                source_files,
                target_files,
                save_path,
                old=False,
                #-----
                CPS_limit=28,
                CPL_limit=96
            )

            info_modal = QMessageBox.information(
                self,
                'Finished',
                'Issue spreadsheet generated successfully'
            )

        else:
            error_modal = QMessageBox.critical(
                self,
                'Error',
                errors
            )

        # if not self.issues_tar_list:
        #     self.issues_errors += 'ERROR: Cannot generate issues sheet. Please select at least one target language subtitle file.\n'
        # if not self.issues_en_list:
        #     self.issues_errors += 'ERROR: Cannot generate issues sheet. Please select at least one source language subtitle file.\n'
        # if (self.issues_tar_list and self.issues_en_list
        #     and (len(self.issues_tar_list) != len(self.issues_en_list))):
        #     # Different numbers of files
        #     self.issues_errors += 'ERROR: Cannot generate issues sheet. Please select the same number of targe and source language files.\n'
        # if not self.issues_sheet_name:
        #     self.issues_errors += 'ERROR: Cannot generate issues sheet. Please select a file name for the spreadsheet.'

        # if not self.issues_errors:
        #     # text = 'Generating issue spreadsheet for target files...\n'
        #     # for file_name in self.issues_tar_list:
        #     #     text += '\n'
        #     #     text += file_name
        #     # text += '\nAnd source files...\n'
        #     # for file_name in self.issues_en_list:
        #     #     text += '\n'
        #     #     text += file_name
        #     # text += '\n\n'
        #     # text += 'Saving to...\n'
        #     # text += self.issues_sheet_name

        #     en_path = '/'.join(self.issues_en_list[0].split('/')[:-1])
        #     tar_path = '/'.join(self.issues_tar_list[0].split('/')[:-1])

        #     result = batch_gen_CPS_sheet(
        #         self.issues_en_list,
        #         self.issues_tar_list,
        #         self.issues_sheet_name,
        #         old=False
        #     )

        #     if type(result) == str:
        #         self.issues_messages.setPlainText(result)
        #     else:
        #         self.issues_messages.setPlainText(f'Issue spreadsheet generated successfully.\n{self.issues_sheet_name}')
        # else:
        #     self.issues_messages.setPlainText(self.issues_errors)
        #     self.issues_errors = ''


    def copy_scene_changes(self, event):
        if not self.copy_sc_videos_list_send:
            self.copy_sc_errors += 'ERROR: Cannot copy shot changes. Please select at least one video file.\n'
        if not self.copy_sc_source_dir:
            self.copy_sc_errors += 'ERROR: Cannot copy shot changes. Please specify the source directory for the shot changes file(s).\n'
        if not self.copy_sc_dest_dir:
            self.copy_sc_errors += 'ERROR: Cannot copy shot changes. Please specify the destination directory for the shot changes file(s).\n'

        if not self.copy_sc_errors:
            text = 'Copied shot changes files for videos...\n'
            for file_name in self.copy_sc_videos_list_send:
                text += '\n'
                text += file_name
            text += '\n\nFrom directory...\n'
            text += self.copy_sc_source_dir
            text += '\n\n'
            text += 'To directory...\n'
            text += self.copy_sc_dest_dir

            copy_scene_changes_from_list(
                self.copy_sc_videos_list_send,
                self.copy_sc_source_dir,
                self.copy_sc_dest_dir
            )

            self.sc_copy_messages.setPlainText(text)
        else:
            self.sc_copy_messages.setPlainText(self.copy_sc_errors)
            self.copy_sc_errors = ''


    def generate_sc(self, event):
        if not self.gen_sc_videos_list_send:
            self.gen_sc_errors += 'ERROR: Cannot generate shot changes. Please select at least one video file.\n'
        if not self.gen_sc_save_dir:
            self.gen_sc_errors += 'ERROR: Cannot generate shot changes. Please select a directory to save shot changes files.\n'

        if not self.gen_sc_errors:
            text = 'Generating shot changes files for videos...\n'
            for file_name in self.gen_sc_videos_list_send:
                text += '\n'
                text += file_name
            text += '\n\n'
            text += 'And saving to directory...\n'
            text += self.gen_sc_save_dir

            batch_generate_scene_changes(
                self.gen_sc_videos_list_send,
                self.gen_sc_save_dir,
                self.sc_gen_sens.value()
            )

            self.sc_gen_messages.setPlainText(text)
        else:
            self.sc_gen_messages.setPlainText(self.gen_sc_errors)
            self.gen_sc_errors = ''


    def run_fr(self, event):
        file_count = self.gen_fr_videos_list.count()
        files = [self.gen_fr_videos_list.item(row).text()
                 for row in range(file_count)]
        # if not self.gen_fr_videos_list_send:
        #     self.gen_fr_errors += 'ERROR: Cannot get frame rates. Please select at least one video file.\n'
        if not files:
            self.gen_fr_errors += 'ERROR: Cannot get frame rates. Please select at least one video file.\n'


        if not self.gen_fr_errors:
            # text = 'Getting frame rates for videos...\n'
            # for file_name in self.gen_fr_videos_list_send:
            #     text += '\n'
            #     text += file_name

            longest_name = 0

            # for m in range(1, len(self.gen_fr_videos_list_send)):
            for m in range(1, len(files)):
                # print(self.gen_fr_videos_list_send[m])
                # print(len(self.gen_fr_videos_list_send[m]))
                # print('\n\n')
                # if (len(self.gen_fr_videos_list_send[m]) > longest_name):
                if (len(files[m]) > longest_name):
                    #
                    # longest_name = len(self.gen_fr_videos_list_send[m])
                    longest_name = len(files[m])

            print(longest_name)

            distance = longest_name + 5


            frame_rates = batch_get_frame_rates_gui(
                # self.gen_fr_videos_list_send
                files
            )
            print(frame_rates)

            text = ''

            # for i, j in zip(self.gen_fr_videos_list_send, frame_rates):
            for i, j in zip(files, frame_rates):
                hyphens = '-' * (distance - len(i) - 2)

                text += f'{i} {hyphens} {format(j, ".3f")} fps\n\n'


            self.fr_gen_messages.setPlainText(text)
        else:
            self.fr_gen_messages.setPlainText(self.gen_fr_errors)
            self.gen_fr_errors = ''



    def get_stats(self, event):
        file_list = self.get_files(self.stats_files_list)


        # if not self.stats_files_list_send:
        if not file_list:
            self.get_stats_errors += 'ERROR: Cannot get stats. Please select at least one subtitle file.\n'

        if not self.get_stats_errors:
            text = ''
            # text = 'Getting stats for files...\n'
            # for file_name in self.stats_files_list_send:
            #     text += '\n'
            #     text += file_name

            stats = batch_get_stats(file_list)

            for key in stats.keys():
                text += f'{key}: {stats[key]}\n'

            self.stats_gen_messages.setPlainText(text)
        else:
            self.stats_gen_messages.setPlainText(self.get_stats_errors)
            self.get_stats_errors = ''


    def run_fixes(self, event):
        if not self.fixes_files_dir:
            self.fixes_errors += 'ERROR: Cannot run fixes. Please select a directory for the subtitle files.\n'
        if not self.fixes_videos_dir:
            self.fixes_errors += 'ERROR: Cannot run fixes. Please select a directory for the videos.\n'
        # if not self.fixes_sc_dir:
        #     self.fixes_errors += 'ERROR: Cannot run fixes. Please select a directory for the scene changes.\n'

        # if len(self.fixes_files_dir) != len(self.fixes_videos_dir):
        #     self.fixes_errors += 'ERROR: Cannot run fixes. The number of videos is not the same as the number of subtitle files.\n'

        if not self.fixes_errors:
            # text = 'Running fixes for files in directory...\n'
            # text += self.fixes_files_dir
            # text += '\n\nWith the videos in...\n'
            # text += self.fixes_videos_dir
            # text += '\n\nAnd shot changes in...\n'
            # text += self.fixes_sc_dir

            TCFOL = self.fix_TCFOL_checkbox.isChecked()
            snap_to_frames = self.snap_to_frames_checkbox.isChecked()
            fix_min_gaps = self.apply_min_gaps_checkbox.isChecked()
            min_gap = self.min_gap.value()

            batch_fixes(
                self.fixes_files_dir,
                self.fixes_videos_dir,
                self.unbreak_limit_spin.value(),
                TCFOL=TCFOL,
                snap_frames=snap_to_frames,
                apply_min_gaps=fix_min_gaps,
                min_gap=min_gap,
                apply_sort=True
            )

            text = 'Fixes applied successfully.'

            self.fixes_messages.setPlainText(text)
            self.opt_4_page_cont.setCurrentIndex(1)

        else:
            self.fixes_messages.setPlainText(self.fixes_errors)
            self.fixes_errors = ''

    def get_files(self, drop_list):
        file_count = drop_list.count()
        files = [drop_list.item(row).text() for row in range(file_count)]

        return files

    def get_save_dir(self, line_edit):
        save_dir = line_edit.text()

        return save_dir

    # def mousePressEvent(self, e):
    #     print(e.button())

# class DropList(QListWidget):
#     """Subclass of the QListWidget to make it accept drops
#     and handle events.
#     """

#     def __init__(self):
#         super().__init__()
#         self.setAcceptDrops(True)

#     def dragEnterEvent(self, event):
#         if event.mimeData().hasText():
#             event.accept()
#         else:
#             event.ignore()

#     def dragMoveEvent(self, event):
#         if event.mimeData().hasText():
#             event.accept()
#         else:
#             event.ignore()

#     def dropEvent(self, event):
#         prev_file_count = self.count()
#         prev_files = [self.item(row).text() for row in range(prev_file_count)]

#         md = event.mimeData()
#         invalid_files = []
#         repeated_files = []
#         valid_files = []

#         valid_extensions = ['.srt', '.vtt']

#         if md.hasText():
#             file_names = md.text().split('\n')
#             if len(file_names) > 1:
#                 file_names.pop(-1)
#             for i, file_name in enumerate(file_names):
#                 name, ext = os.path.splitext(file_name)
#                 if ext not in valid_extensions:
#                     invalid_files.append(file_name.replace('file:///', ''))
#                     continue

#                 elif file_name.replace('file:///', '') in prev_files:
#                     repeated_files.append(
#                         '- ' + file_name.replace('file:///', ''))
#                     continue
#                 self.insertItem(i, file_name.replace('file:///', ''))

#         if invalid_files:
#             invalid_file_names = '\n'.join(invalid_files)
#             if len(invalid_files) == 1:
#                 message = (f'The following file will be ignored because its format is not supported:\n\n'
#                            f'{invalid_file_names}')
#             else:
#                 message = (f'The following files will be ignored because their format is not supported:\n\n'
#                            f'{invalid_file_names}')

#             error_modal = QMessageBox.warning(
#                 self,
#                 'Warning',
#                 message
#             )

#         if repeated_files:
#             repeated_file_names = '\n'.join(repeated_files)
#             if len(repeated_files) == 1:
#                 title = 'Repeated file'
#                 message = (f'{repeated_files[0].replace("file:///", "")}\n\n'
#                            f'is already in the list.\nWill be ignored.')
#             else:
#                 title = 'Repeated files'
#                 message = (f'{repeated_file_names.replace("file:///", "")}\n\n'
#                            f'are already in the list.\nWill be ignored.')

#             info_modal = QMessageBox.information(
#                 self,
#                 title,
#                 message
#             )


class DropList(QListWidget):
    """Subclass of the QListWidget to make it accept drops
    and handle events.
    """
    def __init__(self, list_index, supported_formats=[]):
        super().__init__()
        self.setAcceptDrops(True)
        # self.options_widget = options_widget
        self.list_index = list_index
        self.supported_formats = supported_formats

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        prev_file_count = self.count()
        prev_files = [self.item(row).text() for row in range(prev_file_count)]

        # current_option = self.options_widget.currentText()

        md = event.mimeData()
        invalid_files = []
        repeated_files = []
        valid_files = []
        if md.hasText():
            file_names = md.text().split('\n')
            if len(file_names) > 1:
                file_names.pop(-1)
            for i, file_name in enumerate(file_names):
                name, ext = os.path.splitext(file_name)
                # if ext != '.csv':
                if ext not in self.supported_formats:
                    sup = [form[1:].upper() for form in self.supported_formats]
                    invalid_files.append(file_name.replace('file:///', ''))
                    if len(self.supported_formats) > 1:
                        sup_message = f'{", ".join(sup[:-1])}, and {sup[-1]}'
                    else:
                        sup_message = f'{sup[0]}'
                    continue
                # if ext != '.csv' and self.options_widget.currentIndex() == 0:
                #     supported_formats = 'CSV'
                #     invalid_files.append(file_name.replace('file:///', ''))
                #     continue

                # elif ext != '.xlsx' and self.options_widget.currentIndex() == 1:
                #     supported_formats = 'XLSX'
                #     invalid_files.append(file_name.replace('file:///', ''))
                #     continue

                # elif ext != '.mp4' and self.options_widget.currentIndex() == 2:
                #     supported_formats = 'MP4'
                #     invalid_files.append(file_name.replace('file:///', ''))
                #     continue

                elif file_name.replace('file:///', '') in prev_files:
                    repeated_files.append(
                        '- ' + file_name.replace('file:///', ''))
                    continue

                # NOTE: This is very different from what is done
                #       in add_files.  Note that here QListWidgetItem
                #       is not used, just the text is inserted directly
                #       into the DropList.
                #       Why does it work like this too?
                self.insertItem(i, file_name.replace('file:///', ''))
                valid_files.append(file_name)

        if invalid_files:
            invalid_file_names = '\n\n'.join(invalid_files)
            if len(invalid_files) == 1:
                message = (f'Only {sup_message} files are supported.\n'
                           f'The following file was ignored:\n\n'
                           f'{invalid_file_names}')
            else:
                message = (f'Only {sup_message} files are supported.\n'
                           f'The following files were ignored:\n\n'
                           f'{invalid_file_names}')

            error_modal = QMessageBox.warning(
                self,
                'Warning',
                message
            )

        if repeated_files:
            repeated_file_names = '\n'.join(repeated_files)
            if len(repeated_files) == 1:
                title = 'Repeated file'
                message = (f'{repeated_files[0].replace("file:///", "")}\n\n'
                           f'is already in the list.\nWill be ignored.')
            else:
                title = 'Repeated files'
                message = (f'{repeated_file_names.replace("file:///", "")}\n\n'
                           f'are already in the list.\nWill be ignored.')

            info_modal = QMessageBox.information(
                self,
                title,
                message
            )

        current_file_count = self.count()
        current_files = [self.item(row).text()
                         for row in range(current_file_count)]

        current_files_sorted = os_sorted(current_files)
        self.clear()

        for j, current_file in enumerate(current_files_sorted):
            item = QListWidgetItem()
            item.setText(current_file)
            self.insertItem(j, item)

        if self.list_index == 1:
            self.files_1 = valid_files
        elif self.list_index == 2:
            self.files_2 = valid_files


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())