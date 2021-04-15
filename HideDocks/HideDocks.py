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
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
try:
    from qgis.PyQt import sip
except ImportError:
    import sip
from qgis.core import QgsProject
from .HideDocksUI import HideDocksDialog, HideDocksToolBar, ShrinkedDock, icons


class MainWindowFilter(QObject):
    show = pyqtSignal()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Show:
            self.show.emit()
        return False


class CentralWidgetFilter(QObject):
    enter = pyqtSignal(QWidget)
    leave = pyqtSignal(QWidget)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.enter.emit(obj)
        elif event.type() == QEvent.Leave:
            self.leave.emit(obj)
        return False


class HideDocks(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface

        if QSettings().value('locale/overrideFlag', type=bool):
            locale = QLocale(QSettings().value('locale/userLocale'))
        else:
            locale = QLocale.system()
        self.translator = QTranslator()
        if self.translator.load(locale, '', '',
                os.path.join(os.path.dirname(__file__), 'i18n')):
            qApp.installTranslator(self.translator)

    def initGui(self):
        self.mw = self.iface.mainWindow()
        self.hided = {}
        self.current_tab = []
        self.sds = {}  # ShrinkedDocks
        for area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea,
                     Qt.TopDockWidgetArea, Qt.BottomDockWidgetArea):
            sd = ShrinkedDock(area)
            sd.pressed.connect(self.show_area)
            sd.resize.connect(self.sd_resize)
            self.sds[area] = sd
        self.cwf = CentralWidgetFilter()
        self.cwf.enter.connect(self.cw_enter)
        self.cwf.leave.connect(self.cw_leave)
        self.mw.centralWidget().installEventFilter(self.cwf)
        qApp.aboutToQuit.connect(self.show_all)

        self.toolbar = HideDocksToolBar(self.mw)
        self.toolbar.checks[0].toggled.connect(lambda checked:
                self.check_toggled(Qt.LeftDockWidgetArea, checked))
        self.toolbar.checks[1].toggled.connect(lambda checked:
                self.check_toggled(Qt.RightDockWidgetArea, checked))
        self.toolbar.checks[2].toggled.connect(lambda checked:
                self.check_toggled(Qt.TopDockWidgetArea, checked))
        self.toolbar.checks[3].toggled.connect(lambda checked:
                self.check_toggled(Qt.BottomDockWidgetArea, checked))
        self.mw.addToolBar(self.toolbar)

        self.plugin_name = self.tr('Hide Docks')
        self.plugin_act = QAction(self.tr('Options…'))
        self.plugin_act.setObjectName('mActionHideDocksOption')
        self.plugin_act.triggered.connect(self.open_dialog)
        self.iface.addPluginToMenu(self.plugin_name, self.plugin_act)
        w = self.plugin_act.associatedWidgets()[0]
        w.setObjectName('mActionHideDocks')
        w.setIcon(icons[1])

        self.dialog = HideDocksDialog(self.mw)

        if self.mw.isVisible():
            self.restore_setting()
        else:
            self.mwf = MainWindowFilter()
            self.mwf.show.connect(self.first_show)
            self.mw.installEventFilter(self.mwf)

    def first_show(self):
        self.mw.removeEventFilter(self.mwf)
        self.restore_setting()

    def restore_setting(self):
        self.toolbar.set_state(int(QSettings().value(
                self.__class__.__name__ + '/toolbarState',
                Qt.NoDockWidgetArea)))
        self.dialog.set_state(int(QSettings().value(
                self.__class__.__name__ + '/dialogState',
                Qt.NoDockWidgetArea)))

    def save_setting(self):
        QSettings().setValue(
                self.__class__.__name__ + '/toolbarState',
                self.toolbar.get_state())
        QSettings().setValue(
                self.__class__.__name__ + '/dialogState',
                self.dialog.get_state())

    def unload(self):
        self.save_setting()
        self.mw.centralWidget().removeEventFilter(self.cwf)
        self.iface.removePluginMenu(self.plugin_name, self.plugin_act)
        self.mw.removeToolBar(self.toolbar)
        self.dialog.hide()
        self.show_all()

    def check_toggled(self, area, checked):
        if checked:
            self.hide_area(area)
        else:
            self.show_area(area)

    def sd_resize(self, area):
        def sd_resized():
            for dock in self.mw.findChildren(QDockWidget):
                if self.mw.dockWidgetArea(dock) == area \
                        and dock.isVisible() and not dock.isFloating() \
                        and dock not in self.sds.values():
                    self.show_area(area, dock)
                    break
        QTimer.singleShot(0, sd_resized)

    def cw_enter(self, cw):
        pos = QCursor.pos()
        geom = cw.geometry()
        win_geom = cw.window().geometry()
        l = [pos.x() - (win_geom.x() + geom.x()),
             win_geom.x() + geom.x() + geom.width() - pos.x(),
             pos.y() - (win_geom.y() + geom.y()),
             win_geom.y() + geom.y() + geom.height() - pos.y()]
        idx = l.index(min(l))
        area = 2 ** idx
        if self.toolbar.get_state() & area:
            self.hide_area(area)

    def cw_leave(self, cw):
        pos = QCursor.pos()
        geom = cw.geometry()
        win_geom = cw.window().geometry()
        if pos.x() < win_geom.x() + geom.x():
            area = Qt.LeftDockWidgetArea
        elif pos.x() >= win_geom.x() + geom.x() + geom.width():
            area = Qt.RightDockWidgetArea
        elif pos.y() < win_geom.y() + geom.y():
            area = Qt.TopDockWidgetArea
        elif pos.y() >= win_geom.y() + geom.y() + geom.height():
            area = Qt.BottomDockWidgetArea
        else:
            area = Qt.NoDockWidgetArea
        if self.toolbar.get_state() & area and self.dialog.get_state() & area:
            self.show_area(area)

    def hide_area(self, area):
        self.cwf.blockSignals(True)
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
        self.cwf.blockSignals(False)

    def show_area(self, area, trigger_dock=None):
        if area == Qt.NoDockWidgetArea:
            return
        self.cwf.blockSignals(True)
        self.mw.removeDockWidget(self.sds[area])
        docks = []
        for dock in self.hided.keys():
            if self.mw.dockWidgetArea(dock) == area:
                docks.append(dock)
                dock.show()
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
                            if trigger_dock:
                                for i in range(tabbar.count()):
                                    if sip.wrapinstance(tabbar.tabData(i),
                                            QWidget) == trigger_dock:
                                        tabbar.setCurrentIndex(i)
                    except TypeError:
                        pass
            for dock in docks:
                del self.hided[dock]
        self.cwf.blockSignals(False)

    def show_all(self):
        for i in range(4):
            self.show_area(2 ** i)

    def open_dialog(self):
        self.dialog.show()
