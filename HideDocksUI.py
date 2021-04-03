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
 *   (at your option) any later version.       f                            *
 *                                                                         *
 ***************************************************************************/
"""

import os
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *


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
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok,
                                     accepted=self.accept)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(buttonBox)

        self.setLayout(vbox)
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
        self.setIcon(icons[1])
        self.action = self.addAction(self.tr('Options…'))
'''


class HideDocksToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.checks = []
        self.checks.append(QAction(icons[0], self.tr('Hide left dock')))
        self.checks.append(QAction(icons[1], self.tr('Hide right dock')))
        self.checks.append(QAction(icons[2], self.tr('Hide top dock')))
        self.checks.append(QAction(icons[3], self.tr('Hide bottom dock')))
        for d in (0, 3, 2, 1):
            self.checks[d].setCheckable(True)
            self.addAction(self.checks[d])

        self.setWindowTitle(self.tr('Hide Docks Toolbar'))

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