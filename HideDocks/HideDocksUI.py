# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Hide Docks
                                 A QGIS plugin
 Hide docked panels in each area
                             -------------------
        begin                : 2021-03-21
        copyright            : (C) 2021 by Tarot Osuji
        email                : tarot@sdf.org
        git sha              : $Format:%H$
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

import os
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import *
from qgis.gui import QgsSpinBox


plugin_dir  = os.path.dirname(__file__)
icons = []
for d in ('left', 'right', 'top', 'bottom'):
    icons.append(QIcon(os.path.join(plugin_dir, 'icons', 'icon_%s.svg' % d)))


def rescale(size):
    dpi = qApp.primaryScreen().logicalDotsPerInch()
    return int(round(size * dpi / 96))


def icon_to_label(icon, size=24):
    label = QLabel()
    label.setPixmap(icon.pixmap(rescale(size)))
    return label


class HideDocksDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.checks = []
        for i in range(4):
            self.checks.append(QCheckBox())

        grid = QGridLayout()
        grid.addWidget(QLabel(self.tr('Auto-unhide')), 1, 0)
        for i, d in enumerate((0, 3, 2, 1)):
            grid.addWidget(icon_to_label(icons[d]),
                           0, i + 1, alignment=Qt.AlignHCenter)
            grid.addWidget(self.checks[d],
                           1, i + 1, alignment=Qt.AlignHCenter)
        gridWidget = QWidget()
        gridWidget.setLayout(grid)

        self.spinUnhide = QgsSpinBox()
        self.spinRehide = QgsSpinBox()
        for w in (self.spinUnhide, self.spinRehide):
            w.setSuffix(' ms')
            w.setMaximum(10000)
            w.setSingleStep(50)
            w.setClearValue(500)

        form = QFormLayout()
        form.addRow(self.tr('Auto-unhide'), self.spinUnhide)
        form.addRow(self.tr('Auto-rehide'), self.spinRehide)
        groupDelay = QGroupBox(self.tr('Delay Time'))
        groupDelay.setLayout(form)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok,
                                     accepted=self.accept)

        vbox = QVBoxLayout()
        vbox.addWidget(gridWidget)
        vbox.addWidget(groupDelay)
        vbox.addWidget(buttonBox)

        self.setLayout(vbox)
        self.setMaximumSize(0, 0)
        self.setWindowTitle(self.tr('Options'))

    def get_state(self):
        state = 0
        for i in range(4):
            state += bool(self.checks[i].checkState()) * 2 ** i
        return state

    def set_state(self, state):
        for i in range(4):
            if state & 2 ** i:
                self.checks[i].setCheckState(Qt.Checked)


'''
class HideDocksMenu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setTitle(self.tr('Hide Docks'))
        self.setObjectName('mActionHideDocks')
        self.setIcon(icons[1])
        self.action = self.addAction(self.tr('Options…'))
        self.action.setObjectName('mActionHideDocksOptions')
'''


class HideDocksToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.checks = []
        self.checks.append(QAction(icons[0],
                                   self.tr('Hide left dock'), parent))
        self.checks.append(QAction(icons[1],
                                   self.tr('Hide right dock'), parent))
        self.checks.append(QAction(icons[2],
                                   self.tr('Hide top dock'), parent))
        self.checks.append(QAction(icons[3],
                                   self.tr('Hide bottom dock'), parent))
        self.checks[0].setObjectName('mActionHideLeftDock')
        self.checks[1].setObjectName('mActionHideRightDock')
        self.checks[2].setObjectName('mActionHideTopDock')
        self.checks[3].setObjectName('mActionHideBottomDock')
        for d in (0, 3, 2, 1):
            self.checks[d].setCheckable(True)
            self.addAction(self.checks[d])

        title = self.tr('Hide Docks Toolbar')
        self.setObjectName('mHideDocksToolbar')
        self.setToolTip(title)
        self.setWindowTitle(title)

    def get_state(self):
        state = 0
        for i in range(4):
            state += self.checks[i].isChecked() * 2 ** i
        return state

    def set_state(self, state):
        for i in range(4):
            if state & 2 ** i:
                self.checks[i].setChecked(True)


class ShrinkedDock(QDockWidget):
    def __init__(self, area, size=12):
        super().__init__()
        self.area = area

        button = QToolButton()
        button.setAutoRaise(True)
        button.setFocusPolicy(Qt.NoFocus)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if area == Qt.LeftDockWidgetArea:
            button.setArrowType(Qt.RightArrow)
            button.setFixedWidth(rescale(size))
        elif area == Qt.RightDockWidgetArea:
            button.setArrowType(Qt.LeftArrow)
            button.setFixedWidth(rescale(size))
        elif area == Qt.TopDockWidgetArea:
            button.setArrowType(Qt.DownArrow)
            button.setFixedHeight(rescale(size))
        elif area == Qt.BottomDockWidgetArea:
            button.setArrowType(Qt.UpArrow)
            button.setFixedHeight(rescale(size))
        button.pressed.connect(self.button_pressed)

        self.setWidget(button)
        self.setTitleBarWidget(QWidget())
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.toggleViewAction().setVisible(False)  # hide from toolbar menu

    pressed = pyqtSignal(Qt.DockWidgetArea)
    resize = pyqtSignal(Qt.DockWidgetArea)

    def button_pressed(self):
        self.pressed.emit(self.area)

    def resizeEvent(self, event):
        self.resize.emit(self.area)
