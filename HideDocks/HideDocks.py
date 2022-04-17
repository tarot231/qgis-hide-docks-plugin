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
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
try:
    from qgis.PyQt import sip  # from QGIS 3.4
except ImportError:
    import sip
from .HideDocksUI import HideDocksToolBar, ShrinkedDock


class MainWindowFilter(QObject):
    layoutRequest = pyqtSignal()
    mousePress    = pyqtSignal()
    mouseRelease  = pyqtSignal()
    show          = pyqtSignal()

    def eventFilter(self, obj, event):
        if event.type()   == QEvent.LayoutRequest:
            self.layoutRequest.emit()
        elif event.type() == QEvent.MouseButtonPress \
                and event.button() == Qt.LeftButton:
            self.mousePress.emit()
        elif event.type() == QEvent.MouseButtonRelease \
                and event.button() == Qt.LeftButton:
            self.mouseRelease.emit()
        elif event.type() == QEvent.Show:
            self.show.emit()
        return False


class HideDocks(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface

        self.translator = QTranslator()
        if self.translator.load(QLocale(QgsApplication.locale()),
                '', '', os.path.join(os.path.dirname(__file__), 'i18n')):
            qApp.installTranslator(self.translator)

    def initGui(self):
        self.mw = self.iface.mainWindow()
        self.hided = {}
        self.current_tab = []

        self.panel_states = {dock: (dock.isVisible(), dock.isFloating())
                             for dock in self.mw.findChildren(QDockWidget)}
        self.trigger = []

        self.sds = {}  # ShrinkedDocks
        for area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea,
                     Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
            self.sds[area] = ShrinkedDock(area)

        self.toolbar = HideDocksToolBar(self.mw)
        self.iface.addToolBar(self.toolbar)

        '''  ## bad ##
        for i in range(4):
            self.toolbar.checks[i].toggled.connect(
                    lambda checked: self.on_check_toggled(1 << i, checked))
        '''
        self.toolbar.checks[0].toggled.connect(lambda checked:
                self.on_check_toggled(Qt.LeftDockWidgetArea, checked))
        self.toolbar.checks[1].toggled.connect(lambda checked:
                self.on_check_toggled(Qt.RightDockWidgetArea, checked))
        self.toolbar.checks[2].toggled.connect(lambda checked:
                self.on_check_toggled(Qt.TopDockWidgetArea, checked))
        self.toolbar.checks[3].toggled.connect(lambda checked:
                self.on_check_toggled(Qt.BottomDockWidgetArea, checked))

        self.mouse_pos = QPoint()
        self.mwf = MainWindowFilter()
        self.mwf.layoutRequest.connect(self.on_layout_request)
        self.mwf.mousePress.connect(self.on_mouse_press)
        self.mwf.mouseRelease.connect(self.on_mouse_release)
        self.mw.installEventFilter(self.mwf)

        qApp.aboutToQuit.connect(self.show_all)

        if self.mw.isVisible():
            self.restore_setting()
        else:
            self.mwf.show.connect(self.first_show)

    def first_show(self):
        self.mwf.show.disconnect(self.first_show)
        #self.restore_setting()  # bad
        QTimer.singleShot(0, self.restore_setting)

    def restore_setting(self):
        self.toolbar.set_state(int(QSettings().value(
                self.__class__.__name__ + '/toolbarState',
                Qt.NoDockWidgetArea)))

    def save_setting(self):
        QSettings().setValue(
                self.__class__.__name__ + '/toolbarState',
                self.toolbar.get_state())

    def unload(self):
        self.save_setting()
        self.mw.removeEventFilter(self.mwf)
        self.toolbar.deleteLater()
        self.show_all()

    def on_check_toggled(self, area, checked):
        if checked:
            self.hide_area(area)
        else:
            self.show_area(area)

    def on_mouse_press(self):
        self.mouse_pos = QCursor.pos()

    def on_mouse_release(self):
        print(qApp.widgetAt(self.mouse_pos))
        if self.mouse_pos == QCursor.pos() and \
                isinstance(qApp.widgetAt(self.mouse_pos), QMainWindow):
            area = self.get_separator_area()
            if area:
                num = len(bin(area)) - 3
                self.toolbar.checks[num].setChecked(
                        not self.toolbar.checks[num].isChecked())

    def get_separator_area(self):
        cw = self.mw.centralWidget()
        pos = cw.mapFromGlobal(self.mouse_pos)
        l = [pos.x(),                               # left
             cw.geometry().width()  - pos.x() - 1,  # right
             pos.y(),                               # top
             cw.geometry().height() - pos.y() - 1]  # bottom
        areas = [i for i, x in enumerate(l) if x < 0]
        if len(areas) == 1:
            return 1 << areas[0]
        else:
            corner = areas[0] + (areas[1] - 2) * 2
            dock_area = self.mw.corner(corner)
            if dock_area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea):
                return 1 << areas[0]
            else:
                return 1 << areas[1]

    def on_layout_request(self):
        self.trigger = []
        for dock in self.mw.findChildren(QDockWidget):
            if dock not in self.sds.values():
                panel_state = (dock.isVisible(), dock.isFloating())
                if dock in self.panel_states:
                    if self.panel_states[dock] != panel_state:
                        continue
                self.panel_states[dock] = panel_state
                if panel_state == (True, False):
                    self.trigger += [dock]

        # Catch the newly displayed docking panel and setChecked() to False
        state = self.toolbar.get_state()
        enabled = 0
        for dock in self.mw.findChildren(QDockWidget):
            area = self.mw.dockWidgetArea(dock)
            if dock.isVisible() and not dock.isFloating():
                enabled |= area
                if area & state and \
                        dock not in self.sds.values():
                    num = len(bin(area)) - 3
                    self.toolbar.checks[num].setChecked(False)
                    state = self.toolbar.get_state()
        for i in range(4):
            self.toolbar.checks[i].setEnabled(
                    bool(enabled & 1 << i))

    def hide_area(self, area):
        if area == Qt.NoDockWidgetArea:
            return
        self.mwf.blockSignals(True)
        docks = []
        for dock in self.mw.findChildren(QDockWidget):
            if self.mw.dockWidgetArea(dock) == area \
                    and dock.isVisible() and not dock.isFloating():
                docks.append(dock)
                self.hided[dock] = dock.geometry()
        if docks:
            for tabbar in self.mw.findChildren(QTabBar):
                idx = tabbar.currentIndex()
                if idx != -1:
                    try:
                        dock = sip.wrapinstance(tabbar.tabData(idx), QWidget)
                        if dock in docks:
                            self.current_tab.append(dock)
                    except TypeError:
                        pass
            for dock in docks:
                dock.hide()
            self.mw.addDockWidget(area, self.sds[area])
            self.sds[area].show()
        self.mwf.blockSignals(False)

    def show_area(self, area):
        if area == Qt.NoDockWidgetArea:
            return
        self.mwf.blockSignals(True)
        self.mw.removeDockWidget(self.sds[area])
        docks = []
        deleted = []
        for dock in self.hided.keys():
            try:
                if self.mw.dockWidgetArea(dock) == area:
                    docks.append(dock)
                    dock.show()
            except RuntimeError:  # for deleted panel (e.g. attribute table)
                deleted.append(dock)
        for dock in deleted:
            del self.hided[dock]
        if docks:
            self.mw.resizeDocks(docks,
                    [self.hided[dock].width() for dock in docks], Qt.Horizontal)
            self.mw.resizeDocks(docks,
                    [self.hided[dock].height() for dock in docks], Qt.Vertical)
            for tabbar in self.mw.findChildren(QTabBar):
                for idx in range(tabbar.count()):
                    try:
                        dock = sip.wrapinstance(tabbar.tabData(idx), QWidget)
                        if dock in self.current_tab:
                            tabbar.setCurrentIndex(idx)
                            self.current_tab.remove(dock)
                            if area in (Qt.LeftDockWidgetArea,
                                        Qt.RightDockWidgetArea):
                                self.mw.resizeDocks([dock],
                                        [self.hided[dock].width()],
                                        Qt.Horizontal)
                            else:
                                self.mw.resizeDocks([dock],
                                        [self.hided[dock].height()],
                                        Qt.Vertical)
                            if self.trigger:
                                for i in range(tabbar.count()):
                                    if sip.wrapinstance(tabbar.tabData(i),
                                            QWidget) in self.trigger:
                                        tabbar.setCurrentIndex(i)
                    except TypeError:
                        pass
            for dock in docks:
                del self.hided[dock]
        self.trigger = []
        self.mwf.blockSignals(False)

    def show_all(self):
        for i in range(4):
            self.show_area(1 << i)
