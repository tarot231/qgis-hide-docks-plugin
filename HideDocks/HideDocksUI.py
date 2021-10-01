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


plugin_dir  = os.path.dirname(__file__)
icons = []
for d in ('left', 'right', 'top', 'bottom'):
    icons.append(QIcon(os.path.join(plugin_dir, 'icons', 'icon_%s.svg' % d)))


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
        for act in self.checks:
            act.setCheckable(True)

        self.rearrange_buttons()
        self.orientationChanged.connect(self.rearrange_buttons)

        title = self.tr('Hide Docks Toolbar')
        self.setObjectName('mHideDocksToolbar')
        self.setToolTip(title)
        self.setWindowTitle(title)

    def rearrange_buttons(self):
        self.clear()
        order = ((2, 0, 1, 3)
                 if self.orientation() == Qt.Vertical else
                 (0, 3, 2, 1))
        for d in order:
            self.addAction(self.checks[d])

    def get_state(self):
        return sum(self.checks[i].isChecked() << i for i in range(4))

    def set_state(self, state):
        for i in range(4):
            self.checks[i].setChecked(
                    bool(self.checks[i].isEnabled() and state & 1 << i))


class ShrinkedDock(QDockWidget):
    def __init__(self, area):
        super().__init__()
        self.area = area
        self.setWidget(QWidget())  # required
        self.setTitleBarWidget(QWidget())
        self.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.toggleViewAction().setVisible(False)  # hide from toolbar menu
        self.setMaximumSize(1, 1)
