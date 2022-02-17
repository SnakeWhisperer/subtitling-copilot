import os

from PyQt5.QtWidgets import (QApplication, QLabel, QVBoxLayout, QPushButton,
                             QWidget, QFileDialog, QGridLayout, QFrame,
                             QStackedWidget, QStyleOption, QStylePainter,
                             QStyle, QBoxLayout, QTabWidget, QListWidget,
                             QLayout, QListWidgetItem, QCheckBox, QHBoxLayout,
                             QLineEdit, QPlainTextEdit, QSpinBox,
                             QAbstractSpinBox, QDoubleSpinBox)
from PyQt5.QtGui import QColor, QPicture, QPainter, QIcon
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QRect, QPoint, QEvent

from mc_helper import batch_gen_CPS_sheet, batch_extract_OSTs, get_OSTs_single, get_OSTs
from vtt_handler import batch_merge_subs
from checks import batch_quality_check

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
                background: #1c1c1c;
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
                background: #2a2a2b;
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
                background: #1c1c1c;
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
                font-size: 10pt;
                border-radius: 3px;
                padding: 5px 10px 5px 10px;
            }

            QPushButton#browse:hover {
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
                margin-left: 80px;
            }

            QSpinBox, QDoubleSpinBox {
                border: 1px solid rgba(167, 202, 212, 80);
                background: #1c1c1c;
                color: #c5cad4;
            }

            QSpinBox:hover, QSpinBox:selected, QSpinbox:active, QDoubleSpinBox:hover, QDoubleSpinBox:selected, QDoubleSpinbox:active {
                border: 1px solid rgba(167, 202, 212, 80);
            }

            QSpinBox#fix_spin {
                margin-left: 30px;
            }


            QListWidget {
                background-color: #1c1c1c;
                color: #c5cad4;
            }
            
            
            QListWidgetItem {
                color: #c5cad4;
            }            


            QTabBar::tab {
                height: 30px;
                width: 100px;
                background-color: #1c1c1c;
                padding-bottom: 10px;
                margin: 0px;
                color: #c5cad4;
                font-size: 12pt;
            }


            QTabBar::tab:hover {
                border-bottom: 4px solid #c5cad4;
            }

            QTabBar::tab:selected {
                border-bottom: 4px solid #2c4ac9;
            }

            QTabWidget::pane {
                background-color: #1c1c1c;
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
                background-color: #1c1c1c;
                border: 1px solid rgba(167, 202, 212, 80);
                color: #c5cad4;
            }

            QPlainTextEdit {
                border: 1px solid rgba(167, 202, 212, 80);
                border-radius: 3px;
                background-color: #1c1c1c;
                margin-top: 5em;
                color: #c5cad4;
                
            }

            QPlainTextEdit:selected {
                border: 1px solid rgba(167, 202, 212, 0.5);
                
            }


            
        ''')        

        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.setSpacing(0)

        self.header_label = QLabel('Subtitling Copilot v1.0', objectName='header')
        self.header_label.setMinimumHeight(90)
        main_layout.addWidget(self.header_label, 0, 0, 1, 2)


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
        self.opt_2_page_cont = QWidget(objectName='Option-2-tabs')
        self.opt_3_page_cont = QWidget(objectName='Option-3-tabs')
        # self.opt_4_page_cont = QTabWidget(objectName='Option-4-tabs')
        self.opt_4_page_cont = QTabWidget(objectName='Option-5-tabs')
        self.opt_5_page_cont = QTabWidget(objectName='option_6_tabs')

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
        self.opt_1_page_cont.addTab(self.opt_1_tab_3, 'Generate')

        # CONTENTS OF THE FIRST TAB IN OPTION 1
        self.opt_1_tab_1_layout = QGridLayout(self.opt_1_tab_1)

        self.input_1_label = QLabel('Subtitle Files', objectName='sub_title')
        self.input_1_label.setContentsMargins(0, 0, 100, 10)
        self.opt_1_tab_1_layout.addWidget(self.input_1_label, 0, 0)

        self.file_list_1 = QListWidget()
        self.opt_1_tab_1_layout.addWidget(self.file_list_1, 1, 0)

        self.list_1_browse = QPushButton('Browse...', objectName='browse')
        self.opt_1_tab_1_layout.addWidget(self.list_1_browse, 1, 1, QtCore.Qt.AlignBottom)

        self.save_layout_widget = QWidget()
        self.opt_1_tab_1_layout.addWidget(self.save_layout_widget, 4, 0)
        self.save_layout = QHBoxLayout(self.save_layout_widget)
        self.save_layout.setContentsMargins(0, 10, 0, 10)
        self.save_label = QLabel('Save new files to:', objectName='bold_label')
        self.save_layout.addWidget(self.save_label)
        self.save_edit = QLineEdit()
        self.save_edit.setReadOnly(True)
        self.save_edit.setTextMargins(0, 0, 100, 0)
        self.save_layout.addWidget(self.save_edit)
        self.browse_save = QPushButton('Browse...', objectName='browse')
        self.save_layout.addWidget(self.browse_save)
        self.save_layout.addStretch()


        self.checkbox_1 = QCheckBox('Save extracted OSTs')
        self.opt_1_tab_1_layout.addWidget(self.checkbox_1, 5, 0)

        self.checkbox_2 = QCheckBox('Delete OSTs from files after extracting')
        self.opt_1_tab_1_layout.addWidget(self.checkbox_2, 6, 0)

        self.extract_ost_button = QPushButton('Extract', objectName='run')
        self.opt_1_tab_1_layout.addWidget(self.extract_ost_button, 7, 1)
        
        self.messages = QPlainTextEdit()
        self.messages.setReadOnly(True)
        self.opt_1_tab_1_layout.addWidget(self.messages, 8, 0, 1, 2)

        # CONTENTS OF THE SECOND TAB IN OPTION 1
        self.opt_1_tab_2_layout = QGridLayout(self.opt_1_tab_2)
        self.input_2_label = QLabel('Subtitle Files', objectName='sub_title')
        self.input_2_label.setContentsMargins(0, 0, 100, 10)
        self.opt_1_tab_2_layout.addWidget(self.input_2_label, 0, 0)

        self.file_list_2 = QListWidget()
        self.opt_1_tab_2_layout.addWidget(self.file_list_2, 1, 0)

        self.list_2_browse = QPushButton('Browse...', objectName='browse')
        self.opt_1_tab_2_layout.addWidget(self.list_2_browse, 1, 1, QtCore.Qt.AlignBottom)

        self.input_3_label = QLabel('OST Files', objectName='sub_title')
        self.input_3_label.setContentsMargins(0, 0, 100, 10)
        self.opt_1_tab_2_layout.addWidget(self.input_3_label, 2, 0)

        self.file_list_3 = QListWidget()
        self.opt_1_tab_2_layout.addWidget(self.file_list_3, 3, 0)

        self.list_3_browse = QPushButton('Browse...', objectName='browse')
        self.opt_1_tab_2_layout.addWidget(self.list_3_browse, 3, 1, QtCore.Qt.AlignBottom)

        self.save_layout_widget_1 = QWidget()
        self.opt_1_tab_2_layout.addWidget(self.save_layout_widget_1, 4, 0)
        self.save_layout_1 = QHBoxLayout(self.save_layout_widget_1)
        self.save_layout_1.setContentsMargins(0, 10, 0, 10)
        self.save_label_1 = QLabel('Save new files to:', objectName='bold_label')
        self.save_layout_1.addWidget(self.save_label_1)
        self.save_edit_1 = QLineEdit()
        self.save_edit_1.setReadOnly(True)
        self.save_edit_1.setTextMargins(0, 0, 100, 0)
        self.save_layout_1.addWidget(self.save_edit_1)
        self.browse_save_1 = QPushButton('Browse...', objectName='browse')
        self.save_layout_1.addWidget(self.browse_save_1)
        self.save_layout_1.addStretch()

        self.checkbox_3 = QCheckBox('Overwrite subtitle files')
        self.opt_1_tab_2_layout.addWidget(self.checkbox_3, 5, 0)

        self.merge_ost_button = QPushButton('Merge', objectName='run')
        self.opt_1_tab_2_layout.addWidget(self.merge_ost_button, 6, 1)

        self.merge_messages = QPlainTextEdit()
        self.merge_messages.setReadOnly(True)
        self.opt_1_tab_2_layout.addWidget(self.merge_messages, 7, 0, 1, 2)

        # CONTENTS OF THE THIRD TAB IN OPTION 1
        self.opt_1_tab_3_layout = QGridLayout(self.opt_1_tab_3)
        self.input_4_label = QLabel('OST Audit File(s)', objectName='sub_title')
        self.input_4_label.setContentsMargins(0, 0, 100, 10)
        self.opt_1_tab_3_layout.addWidget(self.input_4_label, 0, 0)

        self.file_list_4 = QListWidget()
        self.opt_1_tab_3_layout.addWidget(self.file_list_4, 1, 0)

        self.list_4_browse = QPushButton('Browse...', objectName='browse')
        self.opt_1_tab_3_layout.addWidget(self.list_4_browse, 1, 1, QtCore.Qt.AlignBottom)

        self.save_layout_widget_2 = QWidget()
        self.opt_1_tab_3_layout.addWidget(self.save_layout_widget_2, 2, 0)
        self.save_layout_2 = QHBoxLayout(self.save_layout_widget_2)
        self.save_layout_2.setContentsMargins(0, 10, 0, 10)
        self.save_label_2 = QLabel('Save OST files to:', objectName='bold_label')
        self.save_layout_2.addWidget(self.save_label_2)
        self.save_edit_2 = QLineEdit()
        self.save_edit_2.setReadOnly(True)
        self.save_edit_2.setTextMargins(0, 0, 100, 0)
        self.save_layout_2.addWidget(self.save_edit_2)
        self.browse_save_2 = QPushButton('Browse...', objectName='browse')
        self.save_layout_2.addWidget(self.browse_save_2)
        self.save_layout_2.addStretch()

        self.generate_ost_button = QPushButton('Generate', objectName='run')
        self.opt_1_tab_3_layout.addWidget(self.generate_ost_button, 3, 1)

        self.generation_messages = QPlainTextEdit()
        self.generation_messages.setReadOnly(True)
        self.opt_1_tab_3_layout.addWidget(self.generation_messages, 4, 0, 1, 2)


        # OPTION 2 CONTENTS

        self.qc_layout_1 = QVBoxLayout(self.opt_2_page_cont)
        # self.qc_header = QLabel('Batch Quality Check', objectName='header_1')
        # self.qc_header.setContentsMargins(0, 0, 0, 0)
        # self.qc_layout_1.addWidget(self.qc_header)


        self.qc_files_label = QLabel('Subtitle Files Directory', objectName='bold_label')
        self.qc_files_label.setContentsMargins(0, 10, 0, 0)
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
        self.add_qc_sc_layout.addWidget(self.qc_sc_list)
        self.browse_qc_sc_dir = QPushButton('Browse...', objectName='browse')
        self.add_qc_sc_layout.addWidget(self.browse_qc_sc_dir)
        self.add_qc_sc_layout.addStretch()


        self.qc_setts_label = QLabel('Settings', objectName='header_2')
        self.qc_setts_label.setContentsMargins(0, 30, 0, 30)
        self.qc_layout_1.addWidget(self.qc_setts_label)
        self.qc_setts_layout = QGridLayout()
        self.qc_layout_1.addLayout(self.qc_setts_layout)
        self.max_cps_label = QLabel('Max. CPS')
        self.qc_setts_layout.addWidget(self.max_cps_label, 0, 0)
        self.max_cps_spin = QDoubleSpinBox()
        self.max_cps_spin.setDecimals(2)
        self.max_cps_spin.setSingleStep(0.1)
        self.max_cps_spin.setValue(25.00)
        self.qc_setts_layout.addWidget(self.max_cps_spin, 0, 1)
        self.cps_spaces_checkbox = QCheckBox(
            'CPS include spaces',
            objectName='cps_spaces'
        )
        self.qc_setts_layout.addWidget(self.cps_spaces_checkbox, 1, 0, 1, 1)
        self.max_cpl_label = QLabel('Max. CPL')
        self.qc_setts_layout.addWidget(self.max_cpl_label, 2, 0)
        self.max_cpl_spin = QSpinBox()
        self.max_cpl_spin.setValue(42)
        self.max_cpl_spin.setMinimum(1)
        self.qc_setts_layout.addWidget(self.max_cpl_spin, 2, 1)
        self.max_lines_label = QLabel('Max. lines')
        self.qc_setts_layout.addWidget(self.max_lines_label, 3, 0)
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setValue(2)
        self.max_lines_spin.setMinimum(1)
        self.qc_setts_layout.addWidget(self.max_lines_spin, 3, 1)
        self.min_duration_label = QLabel('Min. duration (ms)')
        self.qc_setts_layout.addWidget(self.min_duration_label, 4, 0)
        self.min_duration_spin = QSpinBox()
        self.min_duration_spin.setRange(0, 10000)
        self.min_duration_spin.setValue(833)
        self.qc_setts_layout.addWidget(self.min_duration_spin, 4, 1)
        self.max_duration_label = QLabel('Max. duration (ms)')
        self.qc_setts_layout.addWidget(self.max_duration_label, 5, 0)
        self.max_duration_spin = QSpinBox()
        self.max_duration_spin.setRange(1000, 100000000)
        self.max_duration_spin.setValue(7000)
        self.qc_setts_layout.addWidget(self.max_duration_spin, 5, 1)

        self.check_ellipses_checkbox = QCheckBox('Check ellipses', objectName='sett_check')
        self.check_ellipses_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_ellipses_checkbox, 0, 2)
        self.check_gaps_checkbox = QCheckBox('Check gaps', objectName='sett_check')
        self.check_gaps_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_gaps_checkbox, 1, 2)
        self.check_sc_checkbox = QCheckBox('Check timing to shot changes', objectName='sett_check')
        self.check_sc_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_sc_checkbox, 2, 2)
        self.check_TCFOL_checkbox = QCheckBox('Check text can fit in one line', objectName='sett_check')
        self.check_TCFOL_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_TCFOL_checkbox, 3, 2)
        self.check_OST_checkbox = QCheckBox('Check OSTs', objectName='sett_check')
        self.check_OST_checkbox.setChecked(True)
        self.qc_setts_layout.addWidget(self.check_OST_checkbox, 4, 2)
        self.check_NFG_checkbox = QCheckBox('Check Netflix Glyph List', objectName='sett_check')
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
        self.qc_setts_layout.setColumnStretch(3, 20)
        self.qc_setts_layout.setColumnStretch(4, 19)
        self.qc_setts_layout.setColumnStretch(5, 0)
        self.qc_setts_layout.setColumnMinimumWidth(1, 55)

        # self.qc_setts_layout.setColumnStretch(5, 1)


        self.run_qc_button = QPushButton('Run', objectName='run')
        self.qc_layout_1.addWidget(self.run_qc_button, 0, QtCore.Qt.AlignRight)
        self.qc_messages = QPlainTextEdit()
        self.qc_messages.setReadOnly(True)
        self.qc_layout_1.addWidget(self.qc_messages)
        

        # OPTION 3 CONTENTS

        self.issues_layout = QVBoxLayout(self.opt_3_page_cont)

        self.issues_file_label_1 = QLabel('Target Language Files', objectName='sub_title')
        self.issues_layout.addWidget(self.issues_file_label_1)
        self.add_target_files_layout = QHBoxLayout()
        self.issues_layout.addLayout(self.add_target_files_layout)
        self.target_files_list = QListWidget()
        # self.target_files_list.setReadOnly(True)
        self.add_target_files_layout.addWidget(self.target_files_list)
        self.browse_target_files = QPushButton('Browse...', objectName='browse')
        self.add_target_files_layout.addWidget(self.browse_target_files, 0, QtCore.Qt.AlignBottom)
        # self.add_target_files_layout.addStretch()

        self.issues_file_label_2 = QLabel('Source Language Files', objectName='sub_title')
        self.issues_layout.addWidget(self.issues_file_label_2)
        self.add_source_files_layout = QHBoxLayout()
        self.issues_layout.addLayout(self.add_source_files_layout)
        self.source_files_list = QListWidget()
        # self.source_files_list.setReadOnly(True)
        self.add_source_files_layout.addWidget(self.source_files_list)
        self.browse_source_files = QPushButton('Browse...', objectName='browse')
        self.add_source_files_layout.addWidget(self.browse_source_files, 0, QtCore.Qt.AlignBottom)
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
        self.issues_messages = QPlainTextEdit()
        self.issues_messages.setReadOnly(True)
        self.issues_layout.addWidget(self.issues_messages)


        # OPTION 4 CONTENTS

        self.fixes_layout = QVBoxLayout(self.opt_4_page_cont)

        self.fixes_files_label = QLabel('Subtitle Files Directory', objectName='sub_title')
        self.fixes_layout.addWidget(self.fixes_files_label)
        self.add_fixes_files_layout = QHBoxLayout()
        self.fixes_layout.addLayout(self.add_fixes_files_layout)
        self.fixes_files_list = QLineEdit()
        self.fixes_files_list.setReadOnly(True)
        self.add_fixes_files_layout.addWidget(self.fixes_files_list)
        self.browse_fixes_files = QPushButton('Browse...', objectName='browse')
        self.add_fixes_files_layout.addWidget(self.browse_fixes_files)
        self.add_fixes_files_layout.addStretch()

        self.fixes_videos_label = QLabel('Video Files Directory', objectName='sub_title')
        self.fixes_layout.addWidget(self.fixes_videos_label)
        self.add_fixes_videos_layout = QHBoxLayout()
        self.fixes_layout.addLayout(self.add_fixes_videos_layout)
        self.fixes_videos_list = QLineEdit()
        self.fixes_videos_list.setReadOnly(True)
        self.add_fixes_videos_layout.addWidget(self.fixes_videos_list)
        self.browse_fixes_videos = QPushButton('Browse...', objectName='browse')
        self.add_fixes_videos_layout.addWidget(self.browse_fixes_videos)
        self.add_fixes_videos_layout.addStretch()

        self.fixes_sc_label = QLabel('Scene Changes Directory', objectName='sub_title')
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

        self.snap_to_frames_checkbox = QCheckBox('Snap times to frames (Recommended)', objectName='fix_sett_check')
        self.fix_TCFOL_checkbox = QCheckBox('Fix "text can fit in one line"', objectName='fix_sett_check')
        self.fix_TCFOL_label = QLabel('Shorter than', objectName='fix_spin_label')
        self.unbreak_limit_spin = QSpinBox(objectName='fix_spin')
        self.unbreak_limit_spin.setValue(42)
        self.unbreak_limit_spin.setMinimum(1)
        self.close_gaps_checkbox = QCheckBox('Close gaps', objectName='fix_sett_check')
        self.apply_min_gaps_checkbox = QCheckBox('Apply minimum gaps', objectName='fix_sett_check')
        self.min_gap_label = QLabel('Minimum gap (frames)', objectName='fix_spin_label')
        self.min_gap = QSpinBox(objectName='fix_spin')
        self.min_gap.setValue(2)
        self.min_gap.setMinimum(0)
        self.invalid_italics_checkbox = QCheckBox('Fix invalid italic tags', objectName='fix_sett_check')
        self.unused_br_checkbox = QCheckBox('Fixed unused line breaks', objectName='fix_sett_check')
        self.empty_subs_checkbox = QCheckBox('Flag empty subtitles', objectName='fix_sett_check')
        self.sort_subs_checkbox = QCheckBox('Sort by start time', objectName='fix_sett_check')
        self.empty_widget = QWidget()
        self.run_fixes_button = QPushButton('Run Fixes', objectName='run')
        self.fixes_messages = QPlainTextEdit()



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
        self.fixes_setts_layout.addWidget(self.empty_widget, 10, 0)
        
        self.fixes_layout.addWidget(self.run_fixes_button, 0, QtCore.Qt.AlignRight)
        self.fixes_layout.addWidget(self.fixes_messages)


        self.fixes_setts_layout.setColumnStretch(0, 0)
        self.fixes_setts_layout.setColumnStretch(1, 0)
        self.fixes_setts_layout.setColumnStretch(2, 1)
        self.fixes_setts_layout.setColumnMinimumWidth(1, 75)

        self.fixes_setts_layout.setRowStretch(0, 0)
        self.fixes_setts_layout.setRowStretch(1, 0)
        self.fixes_setts_layout.setRowStretch(2, 0)
        self.fixes_setts_layout.setRowStretch(3, 0)
        self.fixes_setts_layout.setRowStretch(4, 0)
        self.fixes_setts_layout.setRowStretch(5, 0)
        self.fixes_setts_layout.setRowStretch(6, 0)
        self.fixes_setts_layout.setRowStretch(7, 0)
        self.fixes_setts_layout.setRowStretch(8, 0)
        self.fixes_setts_layout.setRowStretch(9, 0)
        self.fixes_setts_layout.setRowStretch(10, 100)

        for i in range(10):
            self.fixes_setts_layout.setRowMinimumHeight(i, 100)


        

        
        

        









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
        
        self.opt_5_page_cont.addTab(self.opt_5_tab_1, 'Copy Shot Changes')
        self.opt_5_page_cont.addTab(self.opt_5_tab_2, 'Generate Shot Changes')
        self.opt_5_page_cont.addTab(self.opt_5_tab_3, 'Frame Rates')
        self.opt_5_page_cont.addTab(self.opt_5_tab_4, 'Statistics')

        self.sc_layout = QVBoxLayout(self.opt_5_tab_1)
        # self.sc_title_1_widget = QWidget(objectName='border_widget')
        # self.sc_title_1_layout = QVBoxLayout(self.sc_title_1_widget)
        # self.copy_sc_label = QLabel('Copy Shot Changes', objectName='border_widget')
        # self.sc_layout.addWidget(self.copy_sc_label)
        
        self.copy_sc_videos_label = QLabel('Videos', objectName='sub_title')
        self.sc_layout.addWidget(self.copy_sc_videos_label)
        self.sc_copy_videos_layout = QHBoxLayout()
        self.sc_layout.addLayout(self.sc_copy_videos_layout)
        self.copy_sc_videos_list = QListWidget()
        self.sc_copy_videos_layout.addWidget(self.copy_sc_videos_list)
        self.sc_copy_videos_browse = QPushButton('Browse...', objectName='browse')
        self.sc_copy_videos_layout.addWidget(self.sc_copy_videos_browse, 0, QtCore.Qt.AlignBottom)
        
        self.sc_copy_dir_label = QLabel('Scene Changes Directory', objectName='sub_title')
        self.sc_layout.addWidget(self.sc_copy_dir_label)
        self.sc_copy_dir_layout = QHBoxLayout()
        self.sc_layout.addLayout(self.sc_copy_dir_layout)
        self.sc_dir_entry = QLineEdit()
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

        self.sc_copy_messages = QPlainTextEdit()
        self.sc_copy_messages.setReadOnly(True)
        self.sc_layout.addWidget(self.sc_copy_messages)





        self.sc_gen_layout = QVBoxLayout(self.opt_5_tab_2)
        
        self.gen_sc_videos_label = QLabel('Videos', objectName='sub_title')
        self.sc_gen_layout.addWidget(self.gen_sc_videos_label)
        self.sc_gen_videos_layout = QHBoxLayout()
        self.sc_gen_layout.addLayout(self.sc_gen_videos_layout)
        self.gen_sc_videos_list = QListWidget()
        self.sc_gen_videos_layout.addWidget(self.gen_sc_videos_list)
        self.sc_gen_videos_browse = QPushButton('Browse...', objectName='browse')
        self.sc_gen_videos_layout.addWidget(self.sc_gen_videos_browse, 0, QtCore.Qt.AlignBottom)
        
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
        self.sc_gen_sens_label = QLabel('Sensitivity')
        self.sc_gen_sens_layout.addWidget(self.sc_gen_sens_label)
        self.sc_gen_sens = QDoubleSpinBox()
        self.sc_gen_sens.setDecimals(2)
        self.sc_gen_sens.setSingleStep(0.01)
        self.sc_gen_sens.setValue(0.10)
        self.sc_gen_sens_layout.addWidget(self.sc_gen_sens)
        self.sc_gen_sens_layout.addStretch()

        self.gen_sc_button = QPushButton('Run', objectName='run')
        self.sc_gen_layout.addWidget(self.gen_sc_button, 0, QtCore.Qt.AlignRight)

        self.sc_gen_messages = QPlainTextEdit()
        self.sc_gen_messages.setReadOnly(True)
        self.sc_gen_layout.addWidget(self.sc_gen_messages)





        self.fr_layout = QVBoxLayout(self.opt_5_tab_3)
        
        self.gen_fr_videos_label = QLabel('Videos', objectName='sub_title')
        self.fr_layout.addWidget(self.gen_fr_videos_label)
        self.fr_gen_videos_layout = QHBoxLayout()
        self.fr_layout.addLayout(self.fr_gen_videos_layout)
        self.gen_fr_videos_list = QListWidget()
        self.fr_gen_videos_layout.addWidget(self.gen_fr_videos_list)
        self.fr_gen_videos_browse = QPushButton('Browse...', objectName='browse')
        self.fr_gen_videos_layout.addWidget(self.fr_gen_videos_browse, 0, QtCore.Qt.AlignBottom)

        self.run_fr_button = QPushButton('Run', objectName='run')
        self.fr_layout.addWidget(self.run_fr_button, 0, QtCore.Qt.AlignRight)

        self.fr_gen_messages = QPlainTextEdit()
        self.fr_gen_messages.setReadOnly(True)
        self.fr_layout.addWidget(self.fr_gen_messages)



        self.stats_layout = QVBoxLayout(self.opt_5_tab_4)
        
        self.stats_files_label = QLabel('Subtitle Files', objectName='sub_title')
        self.stats_layout.addWidget(self.stats_files_label)
        self.stats_files_layout = QHBoxLayout()
        self.stats_layout.addLayout(self.stats_files_layout)
        self.stats_files_list = QListWidget()
        self.stats_files_layout.addWidget(self.stats_files_list)
        self.stats_files_browse = QPushButton('Browse...', objectName='browse')
        self.stats_files_layout.addWidget(self.stats_files_browse, 0, QtCore.Qt.AlignBottom)

        self.run_stats_button = QPushButton('Run', objectName='run')
        self.stats_layout.addWidget(self.run_stats_button, 0, QtCore.Qt.AlignRight)

        self.stats_gen_messages = QPlainTextEdit()
        self.stats_gen_messages.setReadOnly(True)
        self.stats_layout.addWidget(self.stats_gen_messages)





        






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
                    background: #1c1c1c;
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

        self.list_1_browse.clicked.connect(self.browse_list_1)
        self.browse_save.clicked.connect(self.browse_save_dir)
        self.extract_ost_button.clicked.connect(self.extract_ost)

        self.list_2_browse.clicked.connect(self.browse_list_1)
        self.list_3_browse.clicked.connect(self.browse_list_2)
        self.browse_save_1.clicked.connect(self.browse_save_dir)
        self.merge_ost_button.clicked.connect(self.merge_ost)

        self.list_4_browse.clicked.connect(self.browse_list_3)
        self.browse_save_2.clicked.connect(self.browse_save_dir)
        self.generate_ost_button.clicked.connect(self.generate_ost)

        self.browse_qc_files.clicked.connect(self.browse_qc_subs_dir)
        self.browse_qc_videos.clicked.connect(self.browse_qc_videos_dir)
        self.browse_qc_sc_dir.clicked.connect(self.browse_qc_sc_dir_call)
        self.save_report_browse.clicked.connect(self.save_single_file)
        self.run_qc_button.clicked.connect(self.run_qc)

        self.browse_target_files.clicked.connect(self.browse_list_1)
        self.browse_source_files.clicked.connect(self.browse_list_2)
        self.save_issues_browse.clicked.connect(self.save_issues_file)
        self.issues_gen_button.clicked.connect(self.generate_issue_sheet)

        self.browse_fixes_files.clicked.connect(self.browse_dir_1)
        self.browse_fixes_videos.clicked.connect(self.browse_dir_2)
        self.browse_fixes_sc.clicked.connect(self.browse_dir_3)
        self.run_fixes_button.clicked.connect(self.run_fixes)



        self.sc_copy_videos_browse.clicked.connect(self.browse_video_list)
        self.sc_copy_dir_browse.clicked.connect(self.browse_dir_1)
        self.sc_copy_to_browse.clicked.connect(self.browse_dir_2)
        self.copy_sc_button.clicked.connect(self.copy_scene_changes)

        self.sc_gen_videos_browse.clicked.connect(self.browse_video_list)
        self.sc_gen_dir_browse.clicked.connect(self.browse_save_dir)
        self.gen_sc_button.clicked.connect(self.generate_sc)

        self.fr_gen_videos_browse.clicked.connect(self.browse_video_list)
        self.run_fr_button.clicked.connect(self.run_fr)

        self.stats_files_browse.clicked.connect(self.browse_list_1)
        self.run_stats_button.clicked.connect(self.get_stats)
        



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
                for i, file_name in enumerate(file_names):
                    self.extract_ost_files_list.append(file_name)

                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.file_list_1.insertItem(i, current_item)

            elif self.content.currentWidget().currentIndex() == 1:
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
                for i, file_name in enumerate(file_names):
                    self.copy_sc_videos_list_send.append(file_name)
                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.copy_sc_videos_list.insertItem(i, current_item)
            
            elif self.content.currentWidget().currentIndex() == 1:
                for i, file_name in enumerate(file_names):
                    self.gen_sc_videos_list_send.append(file_name)
                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.gen_sc_videos_list.insertItem(i, current_item)

            elif self.content.currentWidget().currentIndex() == 2:
                for i, file_name in enumerate(file_names):
                    self.gen_fr_videos_list_send.append(file_name)
                    current_item = QListWidgetItem()
                    current_item.setText(file_name)
                    self.gen_fr_videos_list.insertItem(i, current_item)
    

    def browse_dir_1(self, event):

        print(self.content.currentIndex())
        print(self.content.currentWidget().currentIndex())
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )

        if self.content.currentIndex() == 4:
            self.fixes_files_dir = directory
            self.fixes_files_list.insert(self.fixes_files_dir)

        if self.content.currentIndex() == 5:
            if self.content.currentWidget().currentIndex() == 0:
                self.copy_sc_source_dir = directory
                self.sc_dir_entry.insert(self.copy_sc_source_dir)


    def browse_dir_2(self, event):
        print(self.content.currentIndex())
        print(self.content.currentWidget().currentIndex())
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )

        if self.content.currentIndex() == 4:
            self.fixes_videos_dir = directory
            self.fixes_videos_list.insert(self.fixes_videos_dir)

        elif self.content.currentIndex() == 5:
            if self.content.currentWidget().currentIndex() == 0:
                self.copy_sc_dest_dir = directory
                self.sc_copy_to_entry.insert(self.copy_sc_dest_dir)

    def browse_dir_3(self, event):
        print(self.content.currentIndex())
        print(self.content.currentWidget().currentIndex())
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )

        if self.content.currentIndex() == 4:
            self.fixes_sc_dir = directory
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
                self.save_edit.insert(self.save_extracted_ost_dir)

            elif self.content.currentWidget().currentIndex() == 1:
                self.save_merged_ost_dir = save_dir
                self.save_edit_1.insert(self.save_merged_ost_dir)

            elif self.content.currentWidget().currentIndex() == 2:
                self.save_gen_ost_dir = save_dir
                self.save_edit_2.insert(self.save_gen_ost_dir)

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
                self.sc_gen_dir_entry.insert(self.gen_sc_save_dir)

            elif self.content.currentWidget().currentIndex() == 2:
                pass

            elif self.content.currentWidget().currentIndex() == 3:
                pass


    def browse_qc_subs_dir(self, event):
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )

        self.qc_files_dir = directory
        self.qc_files_list.insert(self.qc_files_dir)

    
    def browse_qc_videos_dir(self, event):
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )

        self.qc_videos_dir = directory
        self.qc_videos_list.insert(self.qc_videos_dir)
    
    def browse_qc_sc_dir_call(self, event):
        directory = QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            # QtCore.QDir.rootPath(),
            r'C:\Users\karka\Tr_CC_Sub\MasterClass',
            QFileDialog.ShowDirsOnly
        )

        self.qc_sc_dir_send = directory
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
        self.save_sheet_entry.insert(self.issues_sheet_name)
    
    def extract_ost(self, event):
        
        if not self.extract_ost_files_list:
            self.extract_ost_errors += 'ERROR: Cannot extract OSTs. Please select at least one subtitle file.\n'
        if not self.save_extracted_ost_dir:
            self.extract_ost_errors += 'ERROR: Cannot save OSTs. Please select a directory for the OST files.'
        
        if not self.extract_ost_errors:
            # text = 'Extracting OSTs files with...\n'
            # for file_name in self.extract_ost_files_list:
            #     text += '\n'
            #     text += file_name
            # text += '\n\n'
            # text += 'Saving to...\n'
            # text += self.save_extracted_ost_dir
            text = 'OSTs extracted successfully.'

            ost_lang_path = '/'.join(self.extract_ost_files_list[0].split('/')[:-1])


            total_errors = batch_extract_OSTs(
                ost_lang_path,
                self.save_extracted_ost_dir,
                save_OSTs=self.checkbox_1.isChecked(),
                delete_OSTs=self.checkbox_2.isChecked()
            )

            if total_errors:
                warnings, errors = total_errors

                if warnings:
                    warnings_string = ''
                    for warning_key in warnings.keys():
                        warnings_string += 'Warnings\n\n\n'
                        warnings_string += warning_key + '\n\t'
                        warnings_string += warnings[warning_key] + '\n'

                    self.messages.setPlainText(warnings_string)

            self.messages.setPlainText(text)
        else:
            self.messages.setPlainText(self.extract_ost_errors)
            self.extract_ost_errors = ''


    def merge_ost(self, event):
        if not self.merge_subtitle_files_list:
            self.merge_ost_errors += 'ERROR: Cannot merge OSTs. Please select at least one subtitle file.\n'
        if not self.merge_ost_files_list:
            self.merge_ost_errors += 'ERROR: Cannot merge OSTs. Please select at least one OST file.\n'
        if (len(self.merge_subtitle_files_list)
            != len(self.merge_ost_files_list)):
            # Different number of files.
            self.merge_ost_errors += 'ERROR: Cannot merge OSTs. The number of subtitle files is different from the number of OST files.\n'
        if not self.save_merged_ost_dir:
            self.merge_ost_errors += 'ERROR: Cannot save Subtitle file(s). Please select a directory for the subtitle files.'
        
        if not self.merge_ost_errors:
            # text = 'Merging OSTs files with...\n'
            # for file_name in self.merge_subtitle_files_list:
            #     text += '\n'
            #     text += file_name
            # text += '\nAnd...\n'
            # for file_name in self.merge_ost_files_list:
            #     text += '\n'
            #     text += file_name
            # text += '\n\n'
            # text += 'Saving to...\n'
            # text += self.save_merged_ost_dir

            sub_dir = '/'.join(self.merge_subtitle_files_list[0].split('/')[:-1])
            ost_dir = '/'.join(self.merge_ost_files_list[0].split('/')[:-1])

            batch_merge_subs(
                sub_dir,
                ost_dir,
                self.save_merged_ost_dir
            )

            text = 'Files merged successfully'
            self.merge_messages.setPlainText(text)
        else:
            self.merge_messages.setPlainText(self.merge_ost_errors)
            self.merge_ost_errors = ''


    def generate_ost(self, event):
        if not self.ost_audit_files_list:
            self.gen_ost_errors += 'ERROR: Cannot generate OSTs. Please select at least one audit file.\n'
        if not self.save_gen_ost_dir:
            self.gen_ost_errors += 'ERROR: Cannot generate OSTs. Please select a directory to save the generated OSTs.\n'

        if not self.gen_ost_errors:
            text = 'Generating OSTs files from...\n'
            for file_name in self.ost_audit_files_list:
                text += '\n'
                text += file_name
            text += '\n\n'
            text += 'Saving to...\n'
            text += self.save_gen_ost_dir
            self.generation_messages.setPlainText(text)
        else:
            self.generation_messages.setPlainText(self.gen_ost_errors)
            self.gen_ost_errors = ''
        
    def run_qc(self, event):
        if not self.qc_files_dir:
            self.qc_errors += 'ERROR: Cannot run quality check. Please select a directory for the subtitle files.\n'
        if not self.qc_videos_dir:
            self.qc_errors += 'ERROR: Cannot run quality check. Please select a directory for the videos.\n'
        if not self.qc_sc_dir_send:
            self.qc_errors += 'ERROR: Cannot run quality check. Please select a directory for the scene changes.\n'
        if not self.qc_report_name and self.save_report_checkbox.isChecked():
            self.qc_errors += 'ERROR: Cannot save quality check report. Please select a file name to save it.\n'
        print(self.save_report_checkbox.isChecked())


        if not self.qc_errors:
            text = 'Running quality check for files in directory...\n'
            text += self.qc_files_dir + '\n\n'
            text += 'With videos in directory...\n'
            text += self.qc_videos_dir + '\n\n'
            text += 'And scene changes in...\n'
            text += self.qc_sc_dir_send + '\n\n'            
            text += 'And saving report to...\n'
            text += self.qc_report_name
            self.qc_messages.setPlainText(text)

            cps_spaces = self.cps_spaces_checkbox.isChecked()
            ellipses = self.check_ellipses_checkbox.isChecked()
            gaps = self.check_gaps_checkbox.isChecked()
            shot_changes = self.check_sc_checkbox.isChecked()
            tcfol = self.check_TCFOL_checkbox.isChecked()
            ost = self.check_OST_checkbox.isChecked()
            nfgl = self.check_NFG_checkbox.isChecked()

            print(cps_spaces)
            print(ellipses)
            print(gaps)
            print(shot_changes)
            print(tcfol)
            print(ost)
            print(nfgl)
            
        else:
            self.qc_messages.setPlainText(self.qc_errors)
            self.qc_errors = ''


    def generate_issue_sheet(self, event):
        if not self.issues_tar_list:
            self.issues_errors += 'ERROR: Cannot generate issues sheet. Please select at least one target language subtitle file.\n'
        if not self.issues_en_list:
            self.issues_errors += 'ERROR: Cannot generate issues sheet. Please select at least one source language subtitle file.\n'
        if (self.issues_tar_list and self.issues_en_list
            and (len(self.issues_tar_list) != len(self.issues_en_list))):
            # Different numbers of files
            self.issues_errors += 'ERROR: Cannot generate issues sheet. Please select the same number of targe and source language files.\n'
        if not self.issues_sheet_name:
            self.issues_errors += 'ERROR: Cannot generate issues sheet. Please select a file name for the spreadsheet.'

        if not self.issues_errors:
            # text = 'Generating issue spreadsheet for target files...\n'
            # for file_name in self.issues_tar_list:
            #     text += '\n'
            #     text += file_name
            # text += '\nAnd source files...\n'
            # for file_name in self.issues_en_list:
            #     text += '\n'
            #     text += file_name
            # text += '\n\n'
            # text += 'Saving to...\n'
            # text += self.issues_sheet_name

            en_path = '/'.join(self.issues_en_list[0].split('/')[:-1])
            tar_path = '/'.join(self.issues_tar_list[0].split('/')[:-1])
            
            result = batch_gen_CPS_sheet(
                self.issues_en_list,
                self.issues_tar_list,
                self.issues_sheet_name,
                old=False
            )

            if type(result) == str:
                self.issues_messages.setPlainText(result)
            else:
                self.issues_messages.setPlainText(f'Issue spreadsheet generated successfully.\n{self.issues_sheet_name}')
        else:
            self.issues_messages.setPlainText(self.issues_errors)
            self.issues_errors = ''


    def copy_scene_changes(self, event):
        if not self.copy_sc_videos_list_send:
            self.copy_sc_errors += 'ERROR: Cannot copy shot changes. Please select at least one video file.\n'
        if not self.copy_sc_source_dir:
            self.copy_sc_errors += 'ERROR: Cannot copy shot changes. Please specify the source directory for the shot changes file(s).\n'
        if not self.copy_sc_dest_dir:
            self.copy_sc_errors += 'ERROR: Cannot copy shot changes. Please specify the destination directory for the shot changes file(s).\n'

        if not self.copy_sc_errors:
            text = 'Copying shot changes files for videos...\n'
            for file_name in self.copy_sc_videos_list_send:
                text += '\n'
                text += file_name
            text += '\n\nFrom directory...\n'
            text += self.copy_sc_source_dir
            text += '\n\n'
            text += 'To directory...\n'
            text += self.copy_sc_dest_dir
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
            self.sc_gen_messages.setPlainText(text)
        else:
            self.sc_gen_messages.setPlainText(self.gen_sc_errors)
            self.gen_sc_errors = ''
    

    def run_fr(self, event):
        if not self.gen_fr_videos_list_send:
            self.gen_fr_errors += 'ERROR: Cannot get frame rates. Please select at least one video file.\n'


        if not self.gen_fr_errors:
            text = 'Getting frame rates for videos...\n'
            for file_name in self.gen_fr_videos_list_send:
                text += '\n'
                text += file_name
            self.fr_gen_messages.setPlainText(text)
        else:
            self.fr_gen_messages.setPlainText(self.gen_fr_errors)
            self.gen_fr_errors = ''

    def get_stats(self, event):
        if not self.stats_files_list_send:
            self.get_stats_errors += 'ERROR: Cannot get stats. Please select at least one subtitle file.\n'
        
        if not self.get_stats_errors:
            text = 'Getting stats for files...\n'
            for file_name in self.stats_files_list_send:
                text += '\n'
                text += file_name
            self.stats_gen_messages.setPlainText(text)
        else:
            self.stats_gen_messages.setPlainText(self.get_stats_errors)
            self.get_stats_errors = ''


    def run_fixes(self, event):
        if not self.fixes_files_dir:
            self.fixes_errors += 'ERROR: Cannot run fixes. Please select a directory for the subtitle files.\n'
        if not self.fixes_videos_dir:
            self.fixes_errors += 'ERROR: Cannot run fixes. Please select a directory for the videos.\n'
        if not self.fixes_sc_dir:
            self.fixes_errors += 'ERROR: Cannot run fixes. Please select a directory for the scene changes.\n'

        if not self.fixes_errors:
            text = 'Running fixes for files in directory...\n'
            text += self.fixes_files_dir
            text += '\n\nWith the videos in...\n'
            text += self.fixes_videos_dir
            text += '\n\nAnd shot changes in...\n'
            text += self.fixes_sc_dir
            self.fixes_messages.setPlainText(text)
        else:
            self.fixes_messages.setPlainText(self.fixes_errors)
            self.fixes_errors = ''

    



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())