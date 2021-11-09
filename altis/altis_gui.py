#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Altimetric Time Series (AlTiS)
#
# module load python/3.7
# source activate gui_py37
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------
import os
import sys

# import pdb
import tempfile
import shutil
import csv
import warnings
import pkg_resources
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull, Delaunay

import yaml

# pour déactiver les warning des modules utilisant yaml
yaml.warnings({"YAMLLoadWarning": False})
# pour déactiver les FutureWarning des différents modules.
warnings.filterwarnings("ignore")

# Performance GUI
# Line segment simplification and Using the fast style
import matplotlib.style as mplstyle
import matplotlib as mpl

mplstyle.use("fast")
mpl.rcParams["path.simplify"] = True
mpl.rcParams["path.simplify_threshold"] = 1.0
mpl.rcParams["agg.path.chunksize"] = 10000

from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()


import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy.feature import NaturalEarthFeature, COLORS, GSHHSFeature
import cartopy.feature as cfeature

# try:
from cartopy.io.img_tiles import StamenTerrain

# else:
# from cartopy.io.img_tiles import Stamen
# import cartopy.io.img_tiles as cimgt


from altis.track_structure import Track, GDR_altis
from altis.data_selection_gui import DatasetSelection

from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.cm import ScalarMappable

from altis.common_data import Singleton

from altis.download_data_gui import Load_data_Window
from altis.help_html_gui import Help_Window

from altis.time_series import Time_Series_Panel
from altis.colinear_analysis import ColinAnal_Panel

from altis.connection_check import check_internet

from altis.para_detection import hough_transform    #, hough_transform_linear

from altis._version import __version__  #, __revision__

import wx


# -------------------------------------------------------------------------------
# Control window : This window display the list of the cycle dowloaded in memory.
#    This window is used for the cycle selection.
# -------------------------------------------------------------------------------
class CtrlWindow(wx.Frame):
    """
        Windows control class for Dataset display.
    """

    def __init__(self, parent):  # ,cycle,date):
        """
            initialisation
        """
        super().__init__(
            parent,
            title="AlTiS : Dataset Display",
            style=wx.FRAME_FLOAT_ON_PARENT
            | wx.MINIMIZE_BOX
            | wx.MAXIMIZE_BOX
            | wx.RESIZE_BORDER
            | wx.SYSTEM_MENU
            | wx.CAPTION,
            pos=(10, 50),
            size=(250, 700),
        )

        self.parent = parent

        panel = wx.Panel(self)
        self.create_toolbar()
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.lctrlSelectCycle = wx.ListCtrl(panel, -1, style=wx.LC_REPORT)
        self.lctrlSelectCycle.InsertColumn(0, "Date", wx.LIST_FORMAT_LEFT, 80)
        self.lctrlSelectCycle.InsertColumn(1, "Cycle", wx.LIST_FORMAT_CENTER, width=50)
        self.lctrlSelectCycle.InsertColumn(2, "Track", wx.LIST_FORMAT_CENTER, width=50)

        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, self.parent.onSelectCycle, self.lctrlSelectCycle
        )

        box.Add(self.lctrlSelectCycle, 1, wx.EXPAND)
        panel.SetSizer(box)
        panel.Fit()
        self.Centre()

    def update(self, cycle, date, tracks):
        """
            Update the dataset display.
        """
        self.lctrlSelectCycle.DeleteAllItems()
        index = 0
        for i in zip(cycle, date, tracks):
            index = self.lctrlSelectCycle.InsertItem(
                index, "{:04d}/{:02d}/{:02d}".format(i[1][0], i[1][1], i[1][2])
            )
            self.lctrlSelectCycle.SetItem(index, 1, "{:03d}".format(i[0]))
            self.lctrlSelectCycle.SetItem(index, 2, "{:04d}".format(i[2]))
            index += 1

        list_track = np.unique(tracks)
        self.comboSelPass.Clear()
        for track in list_track:
            self.comboSelPass.Append(str(track))
        self.comboSelPass.SetValue("All-Tracks")

    def create_toolbar(self):
        """
        Create a toolbar
        """
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((20, 20))

        self.btnSelectAll = wx.Button(self.toolbar, label="Select All")
        self.toolbar.AddControl(self.btnSelectAll)

        self.comboSelPass = wx.ComboBox(
            self.toolbar, value="Select_pass", choices=[], size=(120, 30)
        )
        self.toolbar.AddControl(self.comboSelPass, label="Select a pass")

        self.toolbar.AddStretchableSpace()
        self.iconHelp = self.mk_iconbar("About AlTiS", wx.ART_HELP, "About AlTiS")

        self.toolbar.Realize()

        self.btnSelectAll.Disable()

        self.Bind(wx.EVT_BUTTON, self.parent.onSelectAll, self.btnSelectAll)
        self.comboSelPass.Bind(wx.EVT_COMBOBOX, self.parent.onSelectPassCombox)

    def mk_iconbar(self, bt_txt, art_id, bt_lg_txt):
        """
            create icon into the toolbar
        """
        if wx.Platform == '__WXGTK__':
            if art_id == wx.ART_HELP:
#                gtk_icon_label = "gtk-cdrom"
                gtk_icon_label = "gtk-info"
            elif  art_id == wx.ART_QUIT:
 #               gtk_icon_label = "gtk-cdrom"
                gtk_icon_label = "gtk-close"
            else:
                gtk_icon_label = "gtk-cdrom"
#                gtk_icon_label = "gtk-indent"

            ico = wx.ArtProvider.GetBitmap(gtk_icon_label, wx.ART_TOOLBAR, (20, 20))
        else:
            ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (16, 16))

        itemTool = self.toolbar.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool

    def onSelectAll(self, event):
        """
            action selection of all datatset
        """
        for idx in range(self.lctrlSelectCycle.GetItemCount()):
            self.lctrlSelectCycle.Select(idx)
        self.comboSelPass.SetValue("All-Tracks")
        return np.ones((self.lctrlSelectCycle.GetItemCount()), dtype=bool)

    def onSelectPassCombox(self, event):
        """
            action selection for pass combox
        """
        mask = []
        for idx in range(self.lctrlSelectCycle.GetItemCount()):
            if int(self.comboSelPass.GetValue()) == int(
                self.lctrlSelectCycle.GetItem(idx, 2).GetText()
            ):
                if not self.lctrlSelectCycle.IsSelected(idx):
                    self.lctrlSelectCycle.Select(idx)
            else:
                if self.lctrlSelectCycle.IsSelected(idx):
                    self.lctrlSelectCycle.Select(idx, on=0)

            mask.extend([self.lctrlSelectCycle.IsSelected(idx)])
        return np.array(mask)

    def getselectcyle(self):
        """
            action
        """
        mask = []
        for idx in range(self.lctrlSelectCycle.GetItemCount()):
            mask.extend([self.lctrlSelectCycle.IsSelected(idx)])
        self.comboSelPass.SetValue("-------")
        return np.array(mask)


# -------------------------------------------------------------------------------
# Main window : This is the main window
# -------------------------------------------------------------------------------
class Main_Window(wx.Frame):
    """
        main window class
    """

    def __init__(self,):
        """
            initialisation
        """
        super().__init__(
            None, title="Altimetry Time Series (AlTiS) Software", size=wx.DisplaySize()
        )
        self.common_data = Singleton()
        self.InitUI()
        self.Center()

    def InitUI(self):
        """
            GUI Initialisation 
        """
        self.get_env_var()

        self.main_panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.mk_left_toolbar(self.main_panel)
        #        self.mk_left_toolbar()

        self.CanvasPanel(self.main_panel)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        #        hbox1.Add(self.toolbar_left)
        hbox1.Add(self.toolbar_left_panel)
        hbox1.Add(self.plot_panel, proportion=1, flag=wx.EXPAND | wx.CENTER, border=8)
        vbox.Add(hbox1, proportion=1, flag=wx.LEFT | wx.RIGHT | wx.EXPAND, border=10)
        self.main_panel.SetSizer(vbox)

        self.create_toolbar()
        self.statusbar = self.CreateStatusBar(2)
        #        self.SetStatusText(0,"\tCentered")
        #        self.SetStatusText(1,"\t\tRight Aligned")
        status_bar_right_text = "AlTiS - version : " + __version__ + "              "
        print(status_bar_right_text)
        version_size = wx.Window.GetTextExtent(self, status_bar_right_text)
        self.SetStatusWidths([-1, version_size.width])
        self.statusbar.SetStatusText(status_bar_right_text, 1)

        self.cycle = []
        self.date = []
        self.data_selection_frame = CtrlWindow(self)
        self.data_selection_frame.Show()

    #        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onTest, self.data_selection_frame.lctrlSelectCycle)
    #        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectCycle, self.lctrlSelectCycle)

    def mk_left_toolbar(self, panel):
        """
            Left toolbar initialisation
        """
        self.toolbar_left_panel = wx.Panel(panel)

        vbox = wx.BoxSizer(wx.VERTICAL)

        line = wx.StaticLine(self.toolbar_left_panel)
        vbox.Add(line, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        #        vbox.Add((-1, 5))
        #        vbox.Add((-1,40))

        hbox_label = wx.BoxSizer(wx.HORIZONTAL)
        self.stattext_label = wx.StaticText(self.toolbar_left_panel, label="Selection")
        hbox_label.Add(self.stattext_label, flag=wx.EXPAND | wx.CENTER, border=10)
        vbox.Add(
            hbox_label,
            flag=wx.EXPAND | wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT | wx.TOP,
            border=10,
        )

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.btnSelectData = wx.Button(self.toolbar_left_panel, label="Data Select.")
        hbox1.Add(self.btnSelectData, border=10)
        vbox.Add(hbox1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        #        vbox.Add((-1, 5))

        #        self.iconUndo = self.mk_iconbar_left("Undo",wx.ART_UNDO,"Undo")
        # Ok button
        hbox_undo = wx.BoxSizer(wx.HORIZONTAL)
#        self.iconUndo = wx.Button(self.toolbar_left_panel, wx.ID_UNDO, label="Undo")
        self.iconUndo = wx.Button(self.toolbar_left_panel, label="Undo")
        hbox_undo.Add(self.iconUndo, border=10)
        vbox.Add(hbox_undo, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)
        #        vbox.Add((-1, 5))

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
#        self.btnRefresh = wx.Button(
#            self.toolbar_left_panel, wx.ID_REFRESH, label="Refresh"
#        )
        self.btnRefresh = wx.Button(
            self.toolbar_left_panel, label="Refresh"
        )
        hbox2.Add(self.btnRefresh, border=10)
        vbox.Add(hbox2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        #        vbox.Add((-1, 30))

        line = wx.StaticLine(self.toolbar_left_panel)
        vbox.Add(line, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox_label = wx.BoxSizer(wx.HORIZONTAL)
        self.stattext_label = wx.StaticText(self.toolbar_left_panel, label="Plots")
        hbox_label.Add(self.stattext_label, border=10)
        vbox.Add(hbox_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.btnRescale = wx.Button(self.toolbar_left_panel, label="Rescale")
        hbox3.Add(self.btnRescale, border=10)
        vbox.Add(hbox3, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        #        vbox.Add((-1, 30))

        line = wx.StaticLine(self.toolbar_left_panel)
        vbox.Add(line, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox_label = wx.BoxSizer(wx.HORIZONTAL)
        self.stattext_label = wx.StaticText(self.toolbar_left_panel, label="Dataset")
        hbox_label.Add(self.stattext_label, border=10)
        vbox.Add(hbox_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
#        self.btnSave = wx.Button(self.toolbar_left_panel, wx.ID_SAVE, label="Save")
        self.btnSave = wx.Button(self.toolbar_left_panel, label="Save")
        hbox4.Add(self.btnSave, border=10)
        vbox.Add(hbox4, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        #        vbox.Add((-1, 30))

        line = wx.StaticLine(self.toolbar_left_panel)
        vbox.Add(line, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox_label = wx.BoxSizer(wx.HORIZONTAL)
        self.stattext_label = wx.StaticText(self.toolbar_left_panel, label="Processing")
        hbox_label.Add(self.stattext_label, border=10)
        vbox.Add(hbox_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        self.btnTimeSeries = wx.Button(self.toolbar_left_panel, label="Time Series")
        hbox5.Add(self.btnTimeSeries, border=10)
        vbox.Add(hbox5, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        #        vbox.Add((-1, 50))

        line = wx.StaticLine(self.toolbar_left_panel)
        vbox.Add(line, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox_label = wx.BoxSizer(wx.HORIZONTAL)
        self.stattext_label = wx.StaticText(
            self.toolbar_left_panel, label="Hooking effect"
        )
        hbox_label.Add(self.stattext_label, border=10)
        vbox.Add(hbox_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox_ScanHook = wx.BoxSizer(wx.HORIZONTAL)
        self.btnScanHook = wx.Button(self.toolbar_left_panel, label="Scan")
        hbox_ScanHook.Add(self.btnScanHook, border=10)
        vbox.Add(hbox_ScanHook, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        line = wx.StaticLine(self.toolbar_left_panel)
        vbox.Add(line, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox_label = wx.BoxSizer(wx.HORIZONTAL)
        self.stattext_label = wx.StaticText(
            self.toolbar_left_panel, label="Convex hull"
        )
        hbox_label.Add(self.stattext_label, border=10)
        vbox.Add(hbox_label, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox_ExpEnv = wx.BoxSizer(wx.HORIZONTAL)
        self.btnExpEnv = wx.Button(self.toolbar_left_panel, label="Export")
        hbox_ExpEnv.Add(self.btnExpEnv, border=10)
        vbox.Add(hbox_ExpEnv, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        hbox_ImpEnv = wx.BoxSizer(wx.HORIZONTAL)
        self.btnImpEnv = wx.Button(
            self.toolbar_left_panel, label="Import", size=wx.Size(55, 35)
        )
        hbox_ImpEnv.Add(self.btnImpEnv, border=10)
        #        vbox.Add(hbox_ImpEnv, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        #        hbox_MkEnv = wx.BoxSizer(wx.HORIZONTAL)
        self.btnMkEnv = wx.Button(
            self.toolbar_left_panel, label="Apply", size=wx.Size(55, 35)
        )
        #        hbox_MkEnv.Add(self.btnMkEnv, border=10)
        hbox_ImpEnv.Add(self.btnMkEnv, border=10)
        #        vbox.Add(hbox_MkEnv, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        vbox.Add(hbox_ImpEnv, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        #        vbox.Add((-1, 50))

        line = wx.StaticLine(self.toolbar_left_panel)
        vbox.Add(line, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

#        hbox_cfg = wx.BoxSizer(wx.HORIZONTAL)
#        self.btnCfg = wx.Button(
#            self.toolbar_left_panel, wx.ID_PREFERENCES, label="Config. File"
#        )
        hbox_cfg = wx.BoxSizer(wx.HORIZONTAL)
        self.btnCfg = wx.Button(
            self.toolbar_left_panel, label="Config. File"
        )
        hbox_cfg.Add(self.btnCfg, border=10)
        vbox.Add(hbox_cfg, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, border=10)

        self.toolbar_left_panel.SetSizer(vbox)

        # --------------------------------------------------------------------------------
        self.btnSelectData.Disable()
        self.iconUndo.Disable()
        self.btnRefresh.Disable()
        self.btnRescale.Disable()
        self.btnSave.Disable()
        self.btnTimeSeries.Disable()
        self.btnExpEnv.Disable()
        self.btnImpEnv.Disable()
        self.btnMkEnv.Disable()
        self.btnScanHook.Disable()
        # --------------------------------------------------------------------------------
        self.btnTimeSeries.Bind(wx.EVT_BUTTON, self.onTimeSeries)
        self.btnExpEnv.Bind(wx.EVT_BUTTON, self.onExpEnv)
        self.btnImpEnv.Bind(wx.EVT_BUTTON, self.onImpEnv)
        self.iconUndo.Bind(wx.EVT_BUTTON, self.onUndo)
        self.btnRefresh.Bind(wx.EVT_BUTTON, self.onRefresh)
        self.btnRescale.Bind(wx.EVT_BUTTON, self.onRescale)
        self.btnSave.Bind(wx.EVT_BUTTON, self.onSave)
        self.btnCfg.Bind(wx.EVT_BUTTON, self.onCfg)
        self.btnMkEnv.Bind(wx.EVT_BUTTON, self.onAppEnv)
        self.btnScanHook.Bind(wx.EVT_BUTTON, self.onScanHook)


    def mk_subplot_ax1(self,):
        """
            create ax1 subplot
        """
#        self.ax1 = self.figure.add_subplot(2, 2, 1, projection=self.projection)
        self.ax1 = self.figure.add_subplot(2, 2, 1, projection=ccrs.PlateCarree())
        self.ax1.set_xlabel('Longitude (deg)')
        self.ax1.set_ylabel("Latitude (deg)")

        self.ax1.text(-0.1, 0.5, "Latitude (deg)", va='bottom', ha='center',
                    rotation='vertical', rotation_mode='anchor',
                    transform=self.ax1.transAxes)
        self.ax1.text(0.5, -0.1, 'Longitude (deg)', va='bottom', ha='center',
                    rotation='horizontal', rotation_mode='anchor',
                    transform=self.ax1.transAxes)
        #self.ax1.set_aspect('auto', adjustable='datalim')
        self.ax1.set_aspect("auto", adjustable="datalim", anchor="C", share=False)
        self.gl1 = self.ax1.gridlines(ccrs.PlateCarree(), draw_labels=True) #,auto_update=True,) 
#        self.grd_map = self.ax1.add_image(self.osm_img, 1)  #, crs=cimgt.OSM().crs)
#        print('self.grd_map ',self.grd_map)

    def mk_subplot_ax2(self,):
        """
            create ax2 subplot
        """
#        self.ax2 = self.figure.add_subplot(2, 2, 2, sharey=self.ax1, projection=self.projection)
        self.ax2 = self.figure.add_subplot(2, 2, 2, sharey=self.ax1) # , projection=ccrs.PlateCarree())
        self.ax2.set_ylabel("Latitude (deg)")

#        self.ax2.text(-0.1, 0.5, "Latitude (deg)", va='bottom', ha='center',
#        rotation='vertical', rotation_mode='anchor',
#        transform=self.ax2.transAxes)
        self.ax2.set_aspect('auto', adjustable='datalim')
        self.ax2.grid(True)

    def mk_subplot_ax3(self,):
        """
            create ax3 subplot
        """
#        self.ax3 = self.figure.add_subplot(2, 2, 3, sharex=self.ax1, projection=self.projection)
        self.ax3 = self.figure.add_subplot(2, 2, 3, sharex=self.ax1)    # , projection=ccrs.PlateCarree())
        self.ax3.set_xlabel('Longitude (deg)')
#        self.ax3.text(0.5, -0.1, 'Longitude (deg)', va='bottom', ha='center',
#        rotation='horizontal', rotation_mode='anchor',
#        transform=self.ax3.transAxes)
        self.ax3.set_aspect('auto', adjustable='datalim')
        self.ax3.grid(True)

    def mk_subplot_ax4(self,):
        """
            create ax4 subplot
        """
        self.ax4 = self.figure.add_subplot(2, 2, 4, sharey=self.ax3)
        self.ax4.set_xlabel("Time (YYYY-MM)")
        self.ax4.xaxis_date()
        self.ax4.grid(True)



    def CanvasPanel(self, panel):
        """
            Matplotlib canvas initialisation
        """
        self.projection = ccrs.PlateCarree()
        self.crs_lonlat = ccrs.PlateCarree()
        
        self.plot_panel = wx.Panel(panel)
        self.figure = Figure()
        
        self.mk_subplot_ax1()
        self.ax1.set_extent([-179., 179., -85., 85.], crs=ccrs.PlateCarree())
        self.ax1.add_feature(cfeature.COASTLINE)
        self.ax1.add_feature(cfeature.LAKES, color="m", zorder=0,alpha=0.5)
        self.ax1.add_feature(cfeature.RIVERS, edgecolor="blue")
        self.ax1.autoscale()
        
        self.mk_subplot_ax2()
#        self.ax2 = self.figure.add_subplot(2, 2, 2, sharey=self.ax1)
#        self.ax2.set_ylabel("Latitude (deg)")

        self.mk_subplot_ax3()
#        self.ax3 = self.figure.add_subplot(2, 2, 3, sharex=self.ax1)
#        self.ax3.set_xlabel("Longitude (deg)")

        self.mk_subplot_ax4()
#        self.ax4.set_ylim([-1,1])
#        self.ax4.grid(True)

#        self.ax4 = self.figure.add_subplot(2, 2, 4, sharey=self.ax3)
#        self.ax4.set_xlabel("Time (YYYY-MM)")

        self.canvas = FigureCanvas(self.plot_panel, -1, self.figure)

        self.list_axes = [self.ax1, self.ax2, self.ax3, self.ax4]
        self.list_axes_coord = [
            ["Lon", "Lat"],
            ["Param", "Lat"],
            ["Lon", "Param"],
            ["Time", "Param"],
        ]
        self.mpl_toolbar = NavigationToolbar(self.canvas)

        vbox = wx.BoxSizer(wx.VERTICAL)

        vbox.Add(self.mpl_toolbar, proportion=0, flag=wx.CENTER, border=8)
        vbox.Add(self.canvas, proportion=1, flag=wx.EXPAND | wx.CENTER, border=8)

        self.plot_panel.SetSizer(vbox)
        #        self.figure.tight_layout()
        self.mouseMoveID = self.figure.canvas.mpl_connect(
            "motion_notify_event", self.onMotion
        )

    def onMotion(self, event):
        """
            mouse action event to display coordinates in the statusbar.
        """
        xdata = event.xdata
        ydata = event.ydata
        if event.inaxes in self.list_axes:
            idx = self.list_axes.index(event.inaxes)
            [xlabel, ylabel] = self.list_axes_coord[idx]
            if idx == 0:
                if not 'PlateCarree' in ('%s' % getattr(self.ax1.projection,'__class__')):
                    xdata,ydata = self.crs_lonlat.transform_point(xdata, ydata, self.ax1.projection)
            self.statusbar.SetStatusText(
                "Coordinates :\t%s : %s, %s : %s"
                % (xlabel, "{: 10.6f}".format(xdata), ylabel, "{: 10.6f}".format(ydata))
            )
        else:
            self.statusbar.SetStatusText("Coordinates :")

    def draw(self, lon, lat, time, param, mask, cm, groundmap):
        """
            draw the data selection
        """
        if self.data_sel_config["gdr_flag"] | self.data_sel_config["gdr_altis_flag"]:
            mode_flag = "GDR files"
        elif self.data_sel_config["normpass_flag"]:
            mode_flag = "NormPass file"

        if self.data_sel_config["kml_file"] is None:
            kml_filename = ""
        else:
            kml_filename = (
                " | select. file : "
                + self.data_sel_config["kml_file"].split(os.path.sep)[-1]
            )

        #        main_plot_title = 'Mission : '+self.data_sel_config['mission']+' | '+' track number : '+str(self.data_sel_config['track'])+' | '+mode_flag+kml_filename+'\n\n'+self.param
        main_plot_title = (
            "Mission : "
            + self.data_sel_config["mission"]
            + " | "
            + mode_flag
            + kml_filename
            + "\n\n"
            + self.param
        )

        self.figure.suptitle(main_plot_title, fontsize=16)

        self.plt1 = self.ax1.scatter(
            lon, lat, c=param, marker="+", cmap=cm, transform=ccrs.PlateCarree()
        )

#        gl = self.ax1.gridlines(linewidth=0.5)

#        #        gl = self.ax1.gridlines(crs=ccrs.PlateCarree(),draw_labels=True)
#        gl.xlabels_top = gl.ylabels_right = False
#        gl.xformatter = LONGITUDE_FORMATTER
#        gl.yformatter = LATITUDE_FORMATTER
#        #
#        #        self.ax1.plot(x,y,transform=ccrs.PlateCarree())
#        #        gl = self.ax1.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
#        #                          linewidth=0.5, color='white', alpha=1.0, linestyle='--')
#        #        gl.xlabels_top = True
#        #        gl.ylabels_left = True
#        #        gl.xlabels_bottom = False
#        #        gl.ylabels_right = False
#        #        gl.xlines = True
#        #        gl.xformatter = LONGITUDE_FORMATTER
#        #        gl.yformatter = LATITUDE_FORMATTER

#        self.ax1.set_aspect("auto", adjustable="datalim", anchor="C", share=False)

        self.ax2.set_xlabel(param.attrs["long_name"])
#        self.ax2.set_ylabel("Latitude (deg)")
        self.plt2 = self.ax2.scatter(param, lat, c=param, marker="+", cmap=cm)
#        self.ax2.grid(True)

        self.plt3 = self.ax3.scatter(lon, param, c=param, marker="+", cmap=cm)
#        self.ax3.grid(True)
        self.ax3.set_ylabel(param.attrs["long_name"])
#        self.ax3.set_xlabel("Longitude (deg)")

        self.plt4 = self.ax4.scatter(
            np.array(time), param, c=param, marker="+", cmap=cm
        )
#        self.ax4.grid(True)
#        self.ax4.set_xlabel("Time (YYYY-MM)")
        self.ax4.set_ylabel(param.attrs["long_name"])

        if hasattr(self, "cbar"):
            self.cbar.remove()
#            self.scalarmap.set_clim(vmin=np.min(param), vmax=np.max(param))
#            self.scalarmap.set_cmap(cmap=cm)
#            self.cbar.set_label(param.attrs["long_name"], rotation=270, labelpad=10, y=0.5)
##            self.cbar.draw_all()
#        else:
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        axins = inset_axes(self.ax2,
               width="2.5%",  # width = 5% of parent_bbox width
               height="100%",  # height : 50%
               loc='lower left',
               bbox_to_anchor=(1.1, -0.5, 1, 1),
               bbox_transform=self.ax2.transAxes,
               borderpad=.2,
               )
        self.scalarmap = ScalarMappable(cmap=cm)
#            self.cbar = self.figure.colorbar(
#                self.scalarmap, ax=[self.ax2, self.ax4], orientation="vertical"
#            )
        self.cbar = self.figure.colorbar(
            self.scalarmap, cax=axins)
        self.scalarmap.set_clim(vmin=np.min(param), vmax=np.max(param))
        self.cbar.set_label(param.attrs["long_name"], rotation=270, labelpad=10, y=0.5)

        self.rescale(coord=True)


    def create_toolbar(self):
        """
        Create a toolbar
        """
        self.toolbar = self.CreateToolBar(style=wx.TB_HORZ_TEXT)
        self.toolbar.SetToolBitmapSize((20, 20))

        self.iconQuit = self.mk_iconbar("Quit", wx.ART_QUIT, "Quit AlTiS")
        self.toolbar.AddSeparator()

        self.ListKindData = ["Import data ... ", "GDR Tracks", "AlTiS GDR"] #, "Normpass"]
        self.comboKindData = wx.ComboBox(
            self.toolbar,
            value=self.ListKindData[0],
            choices=self.ListKindData[1:],
            size=(130, 30),
        )
        self.toolbar.AddControl(self.comboKindData, label="Kind of data to import")

        self.toolbar.AddSeparator()

        self.comboSelParam = wx.ComboBox(
            self.toolbar, value="Select_parameter", choices=[], size=(200, 30)
        )
        self.toolbar.AddControl(self.comboSelParam, label="Select a paramter")

        self.toolbar.AddSeparator()

        self.checkCoast = wx.CheckBox(self.toolbar, label="Coastline")
        self.toolbar.AddControl(self.checkCoast, label="Show Coastline")

        self.checkRiversLakes = wx.CheckBox(self.toolbar, label="Rivers-Lakes")
        self.toolbar.AddControl(self.checkRiversLakes, label="Show Rivers-Lakes")

        self.toolbar.AddSeparator()
        self.comboColorMap = wx.ComboBox(
            self.toolbar,
            value="jet",
            choices=["jet", "hsv", "ocean", "terrain", "coolwarm", "RdBu", "viridis"],
        )
        self.toolbar.AddControl(self.comboColorMap, label="Color palet")
        self.comboGroundMap = wx.ComboBox(
            self.toolbar,
            value="Ground Map None",
            choices=["Ground Map None", "LandSat"],
        )  # ,"Open Street Map"])
        self.toolbar.AddControl(self.comboGroundMap, label="Ground Map")

        self.toolbar.AddStretchableSpace()
        self.iconHelp = self.mk_iconbar("Help", wx.ART_HELP, "Help on AlTiS")

        self.toolbar.Realize()

        self.checkCoast.Disable()
        self.checkRiversLakes.Disable()
        self.comboColorMap.Disable()
        self.comboGroundMap.Disable()

        self.Bind(wx.EVT_MENU, self.onQuit, self.iconQuit)
        self.comboKindData.Bind(wx.EVT_COMBOBOX, self.onOpen)
        self.comboSelParam.Bind(wx.EVT_COMBOBOX, self.onSelParam)
        self.btnSelectData.Bind(wx.EVT_BUTTON, self.onSelectData)
        self.checkCoast.Bind(wx.EVT_CHECKBOX, self.onCoast)
        self.checkRiversLakes.Bind(wx.EVT_CHECKBOX, self.onRiversLakes)
        self.comboColorMap.Bind(wx.EVT_COMBOBOX, self.onColorMap)
        self.comboGroundMap.Bind(wx.EVT_COMBOBOX, self.onGroundMap)
        self.Bind(wx.EVT_MENU, self.onHelp, self.iconHelp)

    def mk_iconbar(self, bt_txt, art_id, bt_lg_txt):
        """
            to make icon in the toolbar
        """
        if wx.Platform == '__WXGTK__':
            if art_id == wx.ART_HELP:
                gtk_icon_label = "gtk-info"
            elif  art_id == wx.ART_QUIT:
                gtk_icon_label = "gtk-close"
            else:
                gtk_icon_label = "gtk-cdrom"

            ico = wx.ArtProvider.GetBitmap(gtk_icon_label, wx.ART_TOOLBAR, (20, 20))
        else:
            ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (20, 20))
            
        itemTool = self.toolbar.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool

    def mk_iconbar_left(self, bt_txt, art_id, bt_lg_txt):
        """
            to make icon in the toolbar
        """
        ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (20, 20))
        itemTool = self.toolbar_left.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool

    def plot_hull(self, lon_hull, lat_hull, param_hull, color):
        """
            plot hull.
        """
        hull_lonlat = ConvexHull(np.array([lon_hull, lat_hull]).T)
        hull_paramlat = ConvexHull(np.array([param_hull, lat_hull]).T)
        hull_lonparam = ConvexHull(np.array([lon_hull, param_hull]).T)

        self.plt1_hull = []
        for s in hull_lonlat.simplices:
            s = np.append(s, s[0])  # Here we cycle back to the first coordinate
            self.plt1_hull.extend(
                self.ax1.plot(
                    lon_hull[s],
                    lat_hull[s],
                    color=color,
                    marker=".",
                    linestyle="-",
                    linewidth=0.5,
                    markersize=5,
                    transform=ccrs.PlateCarree(),
                )
            )

        self.plt2_hull = []
        for s in hull_paramlat.simplices:
            s = np.append(s, s[0])  # Here we cycle back to the first coordinate
            self.plt2_hull.extend(
                self.ax2.plot(
                    param_hull[s],
                    lat_hull[s],
                    color=color,
                    marker=".",
                    linestyle="-",
                    linewidth=0.5,
                    markersize=5,
                )
            )

        self.plt3_hull = []
        for s in hull_lonparam.simplices:
            s = np.append(s, s[0])  # Here we cycle back to the first coordinate
            self.plt3_hull.extend(
                self.ax3.plot(
                    lon_hull[s],
                    param_hull[s],
                    color=color,
                    marker=".",
                    linestyle="-",
                    linewidth=0.5,
                    markersize=5,
                )
            )

        self.canvas.draw()

    def onExpEnv(self, event):
        """
           Export convex hull into csv file. 
        """
        mask = (
            self.common_data.CYCLE_SEL
            & self.common_data.DATA_MASK_SEL[-1]
            & self.common_data.DATA_MASK_PARAM
        )

        param = self.common_data.param.where(mask)
        lon = self.common_data.lon.where(mask)
        lat = self.common_data.lat.where(mask)

        mask_nan = ~np.isnan(lon) & ~np.isnan(lat) & ~np.isnan(param)

        mask_nan = mask_nan.data.reshape(-1)
        lon = lon.data.reshape(-1)[mask_nan]
        lat = lat.data.reshape(-1)[mask_nan]
        param = param.data.reshape(-1)[mask_nan]

        hull = ConvexHull(np.array([lon, lat, param]).T)

        #        lon_hull = hull.points[hull.vertices,0]
        #        lat_hull = hull.points[hull.vertices,1]
        #        param_hull = hull.points[hull.vertices,2]

        #        self.plot_hull(lon_hull,lat_hull,param_hull, 'r')

        if min(self.tracks[mask.any(axis=1)]) == max(self.tracks[mask.any(axis=1)]):
            track_value = str(min(self.tracks[mask.any(axis=1)]))
        else:
            track_value = "Tracks"

        cycle_min = np.min(self.cycle[self.common_data.CYCLE_SEL.any(axis=1)])
        cycle_max = np.max(self.cycle[self.common_data.CYCLE_SEL.any(axis=1)])
        mission = self.data_sel_config["mission"]
        convexhull_filename = (
            "AlTiS_convexhull_"
            + mission
            + "_"
            + track_value
            + "_"
            + self.param
            + "_cy"
            + str(cycle_min)
            + "_cy"
            + str(cycle_max)
            + ".csv"
        )

        with wx.FileDialog(
            self,
            message="Export Convex Hull Dataset as CSV file",
            defaultDir=self.data_sel_config["data_dir"],
            defaultFile=convexhull_filename,
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                with open(pathname, "w", newline="") as csvfile:
                    spamwriter = csv.writer(
                        csvfile,
                        dialect="excel",
                        delimiter=",",
                        quotechar="#",
                        quoting=csv.QUOTE_MINIMAL,
                    )
                    #                    spamwriter.writerow(['lon', 'lat', self.param])
                    for idx in hull.vertices:
                        spamwriter.writerow(
                            hull.points[idx]
                        )  # [lon[idx[0]],lat[idx[1]],param[idx[2]]])
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    def onImpEnv(self, event):
        """
            import convex hull csv file.
        """
        with wx.FileDialog(
            self,
            message="Import Convex Hull Dataset as CSV file",
            defaultDir=self.data_sel_config["data_dir"],
            defaultFile="",
            wildcard="CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        ) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            hull_pts = []
            try:
                with open(pathname, "r", newline="") as csvfile:
                    reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC)
                    for line in reader:
                        hull_pts.append(line)
            except IOError:
                wx.LogError("Cannot read current data in file '%s'." % pathname)

            self.hull = np.array(hull_pts)

            lon_hull = self.hull[:, 0]
            lat_hull = self.hull[:, 1]
            param_hull = self.hull[:, 2]

            self.plot_hull(lon_hull, lat_hull, param_hull, "r")
            self.btnMkEnv.Enable()

    def in_hull(self, p, hull):
        """
            Test if the point is into the hull
        """
        if not isinstance(hull, Delaunay):
            hull = Delaunay(hull)

        return hull.find_simplex(p) >= 0

    def onAppEnv(self, event):
        """
            Applied the hull selection on to the dataset
        """
        mask = (
            self.common_data.CYCLE_SEL
            & self.common_data.DATA_MASK_SEL[-1]
            & self.common_data.DATA_MASK_PARAM
        )

        param = self.common_data.param.where(mask)
        lon = self.common_data.lon.where(mask)
        lat = self.common_data.lat.where(mask)

        mask_nan = ~np.isnan(lon) & ~np.isnan(lat) & ~np.isnan(param)

        mask_nan = mask_nan.data.reshape(-1)
        lon = lon.data.reshape(-1)[mask_nan]
        lat = lat.data.reshape(-1)[mask_nan]
        param = param.data.reshape(-1)[mask_nan]

        pts = np.array([lon, lat, param]).T

        mask_hull = self.in_hull(pts, self.hull)

        mask_output = np.ones(mask_nan.shape, dtype="bool")
        mask_index = np.where(mask_output)[0]
        mask_index_sel = mask_index[mask_nan]

        output_mask_index_sel = mask_index_sel[mask_hull]

        mask_nan[:] = False
        mask_nan[output_mask_index_sel] = True

        mask_output = mask_nan.reshape(mask.shape)
        self.common_data.DATA_MASK_SEL.append(mask_output)

        _ = [b.remove() for b in self.plt1_hull]
        _ = [b.remove() for b in self.plt2_hull]
        _ = [b.remove() for b in self.plt3_hull]

        self.update_plot()

    def onCfg(self, event):
        """
            Dialog window for Export the configuration file
        """
        message = (
            "You have specific parameters in Normpass or GDR pass files.\n\n"
            + "You can make you own configuration file.\n\n"
            + "For that you need to export the native AlTiS configuration"
            + " file, modify it and select it for the next data importation.\n\n"
            + "Click Ok to generate a configuration file otherwise Cancel."
        )
        with wx.MessageDialog(
            None,
            message=message,
            caption="Make your own configuration file.",
            style=wx.OK | wx.CANCEL | wx.OK_DEFAULT | wx.ICON_INFORMATION,
        ) as save_dataset_dlg:

            if save_dataset_dlg.ShowModal() == wx.ID_OK:
                #                print('Make cofig file!')
                self.mkCfgFile()

    def mkCfgFile(self):
        """
            Export the configuration file
        """
        altis_mission_cfg = pkg_resources.resource_filename(
            "altis", "../etc/products_config.yml"
        )
        default_filename = "AlTiS_products_config.yml"
        with wx.FileDialog(
            self,
            message="Export AlTiS configuration file",
            defaultDir=self.data_sel_config["data_dir"],
            defaultFile=default_filename,
            wildcard="YAML files (*.yml)|*.yml",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        ) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # save the current contents in the file
            export_pathname = fileDialog.GetPath()
            try:
                shutil.copy(altis_mission_cfg, export_pathname)
            except IOError:
                wx.LogError(
                    "Cannot export Altis configuration file '%s'." % export_pathname
                )

    def onScanHook(self, event):
        """
            Hooking scan processing. 
        """
        cursor_wait = wx.BusyCursor()

        self.progress = wx.ProgressDialog(
            "Hooking effect",
            "please wait",
            maximum=100,
            parent=self,
            style=wx.PD_SMOOTH | wx.PD_AUTO_HIDE,
        )
        self.progress.Update(0, "Cycle scanning...")

        mask = (
            self.common_data.CYCLE_SEL
            & self.common_data.DATA_MASK_SEL[-1]
            & self.common_data.DATA_MASK_PARAM
        )

        param = self.common_data.param.where(mask)
        lon = self.common_data.lon.where(mask)
        lat = self.common_data.lat.where(mask)
#        time = self.common_data.time.where(mask)

        if "gdr_index" in self.common_data.param.dims:
            self.dim_index = "gdr_index"
            self.dim_cycle = "cycle_index"
        else:
            self.dim_index = "norm_index"
            self.dim_cycle = "cycle"

        lat_SV = lat.mean(dim=self.dim_index)

        all_x_tab = []
        all_y_tab = []
        all_a = []
        all_err_a = []
        all_b = []
        all_err_b = []
        all_cu = []
        all_nb = []

        all_lon = []
        all_lat = []

#        all_x_tab_line = []
#        all_y_tab_line = []
#        all_h = []
#        all_nwf = []
#        all_nb_line = []

        x_idx = np.array(param.coords[self.dim_index].data, dtype="int")
        self.lonlat_para_center = []
        self.lonparam_para_center = []
        self.paramlat_para_center = []
        for cy_idx, cycle in enumerate(param.coords[self.dim_cycle].data):
            self.progress.Update(
                100 * (cy_idx / len(param.coords[self.dim_cycle].data)),
                "Cycle scanning...",
            )
            #            print('cy_idx,cycle',cy_idx,cycle)
            y = param[cy_idx, :].data
            mask = ~np.isnan(y)
            x = x_idx[mask]
            y = y[mask]

            x_tab, y_tab, a, err_a, b, err_b, cu, nb = hough_transform(
                lat_SV[cy_idx], x, y
            )
            all_x_tab.append(x_tab)
            all_y_tab.append(y_tab)
            all_a.append(a)
            all_err_a.append(err_a)
            all_b.append(b)
            all_err_b.append(err_b)
            all_cu.append(cu)
            all_nb.append(nb)

            if nb > 0:
                i = []
                for idx in b:
                    #                    print ('idx',idx)
                    int_idx = int(idx)
                    i.append(np.where(x_idx == int_idx)[0][0])
                #                    print('i,',i)
                #                print ('>>>> a, b, cu, nb : ',a,b,lon[cy_idx,i].data,lat[cy_idx,i].data,cu,nb )
                all_lon.append(lon[cy_idx, i].data)
                all_lat.append(lat[cy_idx, i].data)
                self.lonlat_para_center.extend(
                    self.ax1.plot(lon[cy_idx, i].data, lat[cy_idx, i].data, ".k")
                )
                self.lonparam_para_center.extend(
                    self.ax3.plot(lon[cy_idx, i].data, param[cy_idx, i].data, ".k")
                )
                self.paramlat_para_center.extend(
                    self.ax2.plot(param[cy_idx, i].data, lat[cy_idx, i].data, ".k")
                )
                self.canvas.draw()
            else:
                all_lon.append(None)
                all_lat.append(None)

        #            x_tab_line,y_tab_line,h,nwf,nb_line = hough_transform_linear(x,y)
        #            all_x_tab_line.append(x_tab_line)
        #            all_y_tab_line.append(y_tab_line)
        #            all_h.append(h)
        #            all_nwf.append(nwf)
        #            all_nb_line.append(nb_line)
        self.progress.Update(100, "Done.")
        self.progress.Destroy()
        del cursor_wait

    def onColAnalysis(self, event):
        """
            Colinear Processing Dialog window
        """
        #        mask = self.common_data.CYCLE_SEL\
        #             &  self.common_data.DATA_MASK_SEL[-1]\
        #             & self.common_data.DATA_MASK_PARAM

        self.colana_panel = ColinAnal_Panel(self, self.data_sel_config, self.param)
        self.colana_panel.Show()

    def onTimeSeries(self, event):
        """
            Time series Dialog window
        """
        #        mask = self.common_data.CYCLE_SEL\
        #             &  self.common_data.DATA_MASK_SEL[-1]\
        #             & self.common_data.DATA_MASK_PARAM

        self.ts_panel = Time_Series_Panel(self, self.data_sel_config)
        self.ts_panel.Show()

    def onRefresh(self, event):
        """
            Refresh action to update the plot.
        """
        self.btnSelectData.Enable()
        if hasattr(self, "select_text_info"):
            self.select_text_info.set_text("")
        self.update_plot()

    def onRescale(self, event):
        """
            Rescale action
        """
        self.rescale()

    def rescale(self, coord=False):
        """
            To rescale the plots
        """
        cursor_wait = wx.BusyCursor()

        xy_coord = self.plt1.get_offsets()
        xy_data = self.plt2.get_offsets()
        rato_threshold_coord = 0.001
        rato_threshold = 0.05
        if coord:
            mean_lon = (np.min(xy_coord[:, 0]) + np.max(xy_coord[:, 0])) / 2.0
            delta_lon = np.abs(np.max(xy_coord[:, 0]) - np.min(xy_coord[:, 0]))
            lon_min = mean_lon - (delta_lon + delta_lon * rato_threshold_coord)
            lon_max = mean_lon + (delta_lon + delta_lon * rato_threshold_coord)
            lon_lim = [lon_min, lon_max]

            mean_lat = (np.min(xy_coord[:, 1]) + np.max(xy_coord[:, 1])) / 2.0
            delta_lat = np.abs(np.max(xy_coord[:, 1]) - np.min(xy_coord[:, 1]))
            lat_min = mean_lat - (delta_lat + delta_lat * rato_threshold_coord)
            lat_max = mean_lat + (delta_lat + delta_lat * rato_threshold_coord)
            lat_lim = [lat_min, lat_max]

            self.ax1.set_xlim(lon_lim)
            self.ax1.set_ylim(lat_lim)

        mean_data = (np.min(xy_data[:, 0]) + np.max(xy_data[:, 0])) / 2.0
        delta_data = np.abs(np.max(xy_data[:, 0]) - np.min(xy_data[:, 0]))
        data_min = mean_data - (delta_data + delta_data * rato_threshold)
        data_max = mean_data + (delta_data + delta_data * rato_threshold)
        param_lim = [data_min, data_max]

        self.ax2.set_xlim(param_lim)
        self.ax3.set_ylim(param_lim)
        self.ax4.set_ylim(param_lim)
        self.canvas.draw()
        
        del cursor_wait

    def get_ax1_xylim(self,):
        """
            get xlim and ylim of the plt1 into ax1.
        """
        if hasattr(self, "plt1"):
            x0, x1 = self.ax1.get_xlim()
            y0, y1 = self.ax1.get_ylim()
            x0,y0 = self.get_xylim_PlateCarree(x0, y0, self.projection)
            x1,y1 = self.get_xylim_PlateCarree(x1, y1, self.projection)
            self.ax1_zoom = {"x": (x0,x1), "y": (y0,y1)}
            
        else:
            self.ax1_zoom = {"x": None, "y": None}


    def onCoast(self, event):
        """
            event to display the coast line
        """
        self.update_CoastFeatures()
        self.canvas.draw()
    
    def update_CoastFeatures(self,):
        """
            To display the coast line.
        """
        cursor_wait = wx.BusyCursor()
        self.get_ax1_xylim()
        if self.ax1_zoom['x'] is not None:
            xlim_diff = np.diff(self.ax1_zoom['x'])
            ylim_diff = np.diff(self.ax1_zoom['y'])
            resol_param = np.sqrt(xlim_diff * xlim_diff + ylim_diff * ylim_diff)
        else:
            resol_param = None


        if resol_param < 0.5:
            resol = "full"
        if resol_param < 1.0:
            resol = "high"
        elif resol_param < 5.0:
            resol = "intermediate"
        elif resol_param < 10.0:
            resol = "low"
        else:
            resol = "coarse"

        print ('resol_coast',resol)
        if self.checkCoast.IsChecked():
            COAST = GSHHSFeature(scale=resol, levels=[1, 2, 3, 4], edgecolor="red")
            self.coast = self.ax1.add_feature(COAST)
            self.canvas.draw()
        #            print('Done')
        else:
            if hasattr(self,"coast"):
                self.coast.remove()

        del cursor_wait

    def update_RiversFeatures(self,):
        """
            update map plot display of rivers features (hid/show)
        """
        """
            To display the rivers and lakes shapeline
        """
        cursor_wait = wx.BusyCursor()
        self.get_ax1_xylim()
        if self.ax1_zoom['x'] is not None:
            xlim_diff = np.diff(self.ax1_zoom['x'])
            ylim_diff = np.diff(self.ax1_zoom['y'])
            resol_param = np.sqrt(xlim_diff * xlim_diff + ylim_diff * ylim_diff)
        else:
            resol_param = None
            

        riverslakes_resol = {"low": "110m", "medium": "50m", "high": "10m"}

        if resol_param < 1.0:
            resol = "high"
        elif resol_param < 5.0:
            resol = "medium"
        else:
            resol = "low"

        print ('resol_river',resol)
#                print(resol_param,resol,self.checkRiversLakes.IsChecked())
        if self.checkRiversLakes.IsChecked():
            RIVERS = NaturalEarthFeature(
                "physical",
                "rivers_lake_centerlines",
                riverslakes_resol[resol],
                edgecolor=COLORS["water"],
                facecolor="none",
            )
            self.rivers = self.ax1.add_feature(RIVERS)
            self.canvas.draw()
#                    print('Done')
        else:
            if hasattr(self,"rivers"):
                self.rivers.remove()

        del cursor_wait

    def onRiversLakes(self, event):
        self.update_RiversFeatures()
        self.canvas.draw()
        
    def onColorMap(self, event):
        """
            To change the color bar
        """
        cursor_wait = wx.BusyCursor()
        self.get_ax1_xylim()

        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        self.param = self.comboSelParam.GetValue()
        #        print(self.cm)
        self.update_plot()

        del cursor_wait

    def onGroundMap(self, event):
        """
            To display the groundMAP
        """
        if self.internet_connection_check() :
            self.comboGroundMap.SetSelection(0)
            return -1
        
        print('mk background')
        cursor_wait = wx.BusyCursor()
        
        self.get_ax1_xylim()

        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        self.param = self.comboSelParam.GetValue()
        
        if self.groundmap == "LandSat":
            altis_cfg = pkg_resources.resource_filename(
                "altis", "../etc/altis_config.yml"
            )
            with open(altis_cfg) as f:
                #                try:
                #                    yaml_data = yaml.safe_load(f)
                #                except:
                yaml_data = yaml.load(
                    f, Loader=yaml.FullLoader
                )  # A revoir pour créer un vrai loader
            url = yaml_data["wmts"]["ground_map"]["url"]
            layer = yaml_data["wmts"]["ground_map"]["layer"]
        elif self.groundmap == "Open Street Map":
            tiler = StamenTerrain()
        #            tiler = Stamen('terrain-background')
        elif self.groundmap == "Ground Map None":
            pass

        if self.groundmap == "LandSat":
            #            print('ground : url,layer ',url,layer)
            if hasattr(self, "grd_map"):
                if self.grd_map is None:
                    self.grd_map = self.ax1.add_wmts(url, layer)
                else:
                    self.grd_map.remove()
                    self.grd_map = self.ax1.add_wmts(url, layer)
            else:

                self.grd_map = self.ax1.add_wmts(url, layer)

        elif self.groundmap == "Open Street Map":
            if hasattr(self, "grd_map"):
                if self.grd_map is None:
                    x0, x1 = self.ax1.get_xlim()
                    y0, y1 = self.ax1.get_ylim()
                    self.ax1.set_extent([x0, x1, y0, y1])
                    self.grd_map = self.ax1.add_image(tiler, 6)
                else:
                    self.grd_map.remove()
                    x0, x1 = self.ax1.get_xlim()
                    y0, y1 = self.ax1.get_ylim()
                    self.ax1.set_extent([x0, x1, y0, y1])
                    self.grd_map = self.ax1.add_image(tiler, 6)
            else:
                x0, x1 = self.ax1.get_xlim()
                y0, y1 = self.ax1.get_ylim()
                self.ax1.set_extent([x0, x1, y0, y1])
                self.grd_map = self.ax1.add_image(tiler, 6)
        elif self.groundmap == "Ground Map None":
            if hasattr(self, "grd_map"):
                if self.grd_map is not None:
                    self.grd_map.remove()
                    self.grd_map = None
            else:
                self.grd_map = None
        #        print(self.groundmap)
        self.canvas.draw()

        del cursor_wait

    def get_xylim_PlateCarree(self,x,y, proj):
        """
            return x,y coordinates in lon/lat
        """
        if not 'PlateCarree' in ('%s' % getattr(proj,'__class__')):
            x, y = self.crs_lonlat.transform_point(x, y, proj)

        return x, y

    def internet_connection_check(self,):
        """
            Check internet connection availability
            
        """
        if check_internet():
            print('Internet connection ok.')
            return False
        else:
            message = ("The internet connection is not allowed. Check your network configuration.")
            
            with wx.MessageDialog(None, message=message, caption="Info",
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_WARNING,)as mssg_dlg:

                if mssg_dlg.ShowModal() == wx.ID_OK:
                    return True
        


    def onSelectData(self, event):
        """
            Graphical data selection
        """        
#        print("self.mpl_toolbar.mode",self.mpl_toolbar.mode)

        if self.mpl_toolbar.mode == "zoom rect":
            self.mpl_toolbar.ToggleTool(self.mpl_toolbar.wx_ids["Zoom"], False)
            self.mpl_toolbar.zoom()

        if self.mpl_toolbar.mode == "pan/zoom":
            self.mpl_toolbar.ToggleTool(self.mpl_toolbar.wx_ids["Pan"], False)
            self.mpl_toolbar.pan()

        #        print('onSelectData')
        #        pdb.set_trace()
        self.btnSelectData.Disable()
        self.select_text_info = self.figure.text(
            -0.1,
            1.2,
            "Selection processing ...",
            horizontalalignment="center",
            verticalalignment="center",
            color="r",
            fontweight="bold",
            fontsize=15,
            transform=self.ax1.transAxes, zorder = 0,
        )
        self.canvas.draw()
        selection = DatasetSelection(
            self.main_panel,
            self.figure,
            [self.plt1, self.plt2, self.plt3, self.plt4],
            [self.ax1, self.ax2, self.ax3, self.ax4],
            self.select_text_info, self.selectall_flag
        )
        self.iconUndo.Enable()
        self.btnRefresh.Enable()
        del selection

    def onSave(self, event):
        """
            Save action of the current dataset
        """
        if hasattr(self, "tr"):

            mask = (
                self.common_data.CYCLE_SEL
                & self.common_data.DATA_MASK_SEL[-1]
                & self.common_data.DATA_MASK_PARAM
            )

            if np.min(self.tracks[mask.any(axis=1).data]) == np.max(
                self.tracks[mask.any(axis=1).data]
            ):
                self.tr.track_value = np.min(self.tracks[mask.any(axis=1).data])
            else:
                self.tr.track_value = "Tracks"

            if self.data_sel_config["gdr_altis_flag"]:
                default_filename = self.tr.mk_filename_gdr_data(mask)

                with wx.FileDialog(
                    self,
                    message="Export AlTiS GDR Dataset as NetCDF file",
                    defaultDir=self.data_sel_config["data_dir"],
                    defaultFile=default_filename,
                    wildcard="NetCDF files (*.nc)|*.nc",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                ) as fileDialog:

                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return  # the user changed their mind

                    # save the current contents in the file
                    pathname = fileDialog.GetPath()
                    try:
                        self.tr.save_gdr_data(mask, filename=pathname)
                    except IOError:
                        wx.LogError("Cannot save current data in file '%s'." % pathname)

            if self.data_sel_config["gdr_flag"]:
                default_filename = self.tr.mk_filename_gdr_data(mask)

                with wx.FileDialog(
                    self,
                    message="Export AlTiS GDR Dataset as NetCDF file",
                    defaultDir=self.data_sel_config["data_dir"],
                    defaultFile=default_filename,
                    wildcard="NetCDF files (*.nc)|*.nc",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                ) as fileDialog:

                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return  # the user changed their mind

                    # save the current contents in the file
                    pathname = fileDialog.GetPath()
                    try:
                        self.tr.save_gdr_data(mask, filename=pathname)
                    except IOError:
                        wx.LogError("Cannot save current data in file '%s'." % pathname)

            if self.data_sel_config["normpass_flag"]:
                default_filename = self.tr.mk_filename_norm_data(mask)

                with wx.FileDialog(
                    self,
                    message="Export AlTiS GDR Dataset as NetCDF file",
                    defaultDir=self.data_sel_config["data_dir"],
                    defaultFile=default_filename,
                    wildcard="NetCDF files (*.nc)|*.nc",
                    style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                ) as fileDialog:

                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return  # the user changed their mind

                    # save the current contents in the file
                    pathname = fileDialog.GetPath()
                    try:
                        self.tr.save_norm_data(mask, filename=pathname)
                    except IOError:
                        wx.LogError("Cannot save current data in file '%s'." % pathname)

        else:
            message = "No dataset !"
            with wx.MessageDialog(
                None,
                message=message,
                caption="Warning",
                style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
            ) as save_dataset_dlg:

                if save_dataset_dlg.ShowModal() == wx.ID_OK:
                    print("No dataset!")

    def onQuit(self, event):
        """
            Close action of AlTiS Software
        """
        self.data_selection_frame.Close()
        if hasattr(self, "ts_panel"):
            try:
                self.ts_panel.Close()
            except:
                pass
        self.Close()

    def onUndo(self, event):
        """
            Undo action data seltect
        """
        if len(self.common_data.DATA_MASK_SEL) > 1:
            self.common_data.DATA_MASK_SEL.pop()
            self.update_plot()

    def update_plot(self,):
        """
            Update diplay plots
        """
        cursor_wait = wx.BusyCursor()

        mask = (
            self.common_data.CYCLE_SEL
            & self.common_data.DATA_MASK_SEL[-1]
            & self.common_data.DATA_MASK_PARAM
        )

        param = self.common_data.param.where(mask)
        lon = self.common_data.lon.where(mask)
        lat = self.common_data.lat.where(mask)
        time = self.common_data.time.where(mask)
        self.plt1.remove()
        self.plt1 = self.ax1.scatter(
            lon, lat, c=param, marker="+", cmap=self.cm, transform=ccrs.PlateCarree()
        )
        self.plt2.remove()
        self.plt2 = self.ax2.scatter(param, lat, c=param, marker="+", cmap=self.cm)
        self.plt3.remove()
        self.plt3 = self.ax3.scatter(lon, param, c=param, marker="+", cmap=self.cm)
        self.plt4.remove()
        self.plt4 = self.ax4.scatter(
            np.array(time), param, c=param, marker="+", cmap=self.cm
        )

        #        self.cbar.remove()
        self.scalarmap.set_cmap(cmap=self.cm)
        self.cbar.set_label(param.attrs["long_name"], rotation=270)
        self.cbar.draw_all()

        self.canvas.draw()
        del cursor_wait

    def onHelp(self, event):
        """
            Help Dialog window
        """
        help = Help_Window()
        help.OnAboutBox()

    def onSelParam(self, event):
        """
           Parameter selection action 
        """
        cursor_wait = wx.BusyCursor()

        self.param = self.comboSelParam.GetValue()
        self.common_data.param_name = self.param
        self.common_data.param = self.tr.data_val[self.param]


        self.common_data.DATA_MASK_PARAM = (
            ~np.isnan(self.common_data.param)
            & ~np.isnan(self.common_data.lon)
            & ~np.isnan(self.common_data.lat)
            & ~np.isnat(self.common_data.time)
        )
     #   print('>> DATA_MASK_PARAM.shape',self.common_data.DATA_MASK_PARAM.shape)
      #  print('>> DATA_MASK_SEL[-1].shape',self.common_data.DATA_MASK_SEL[-1].shape)

        mask = (
            self.common_data.CYCLE_SEL
            & self.common_data.DATA_MASK_SEL[-1]
            & self.common_data.DATA_MASK_PARAM
        )

        param = self.common_data.param.where(mask)
        lon = self.common_data.lon.where(mask)
        lat = self.common_data.lat.where(mask)
        time = self.common_data.time.where(mask)

        if (self.data_sel_config["mission"] == self.current_mission) and (
            self.data_sel_config["track"] == self.current_track
        ):

            self.ax1_zoom = {"x": self.ax1.get_xlim(), "y": self.ax1.get_ylim()}
        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        #        print('Drawing... ',self.param,self.cm,self.groundmap)

        if hasattr(self, "plt1"):
            self.plt1.remove()
            del self.plt1
            self.plt2.remove()
            del self.plt2
            self.plt3.remove()
            del self.plt3
            self.plt4.remove()
            del self.plt4
            self.canvas.draw()

        self.draw(lon, lat, time, param, mask, self.cm, self.groundmap)

#        if (self.data_sel_config["mission"] == self.current_mission) and (
#            self.data_sel_config["track"] == self.current_track
#        ):

#            self.ax1.set_xlim(self.ax1_zoom["x"])
#            self.ax1.set_ylim(self.ax1_zoom["y"])

#        self.canvas.draw()
        self.current_mission = self.data_sel_config["mission"]
        self.current_track = self.data_sel_config["track"]

        self.checkCoast.Enable()
        self.checkRiversLakes.Enable()
        self.comboColorMap.Enable()
        self.comboGroundMap.Enable()
        self.data_selection_frame.btnSelectAll.Enable()

        self.btnSelectData.Enable()
        self.btnSave.Enable()
        self.btnTimeSeries.Enable()
        self.btnExpEnv.Enable()
        self.btnImpEnv.Enable()
        self.btnRescale.Enable()
#        self.btnScanHook.Enable()
        del cursor_wait

    def onOpen(self, event):
        """
            Data file selection Dialog
        """
        if self.comboKindData.GetValue() != self.ListKindData[0]:
            self.get_env_var()
            self.data_sel_config["data_type"] = self.comboKindData.GetValue()
            self.comboKindData.SetValue(self.ListKindData[0])

            with Load_data_Window(self.data_sel_config) as load_data_args:
                load_data_args.Center()
                load_data_args.Show()
                if load_data_args.ShowModal() == wx.ID_OK:
                 #   print("ShowModal == wx.ID_OK")
                    self.load_data_process(event, load_data_args.data_sel_config)
                else:
                    print("Cancel")

    def load_data_process(self, event, load_data_args):
        """
            Data loading process
        """
        self.data_sel_config = load_data_args

        self.progress = wx.ProgressDialog(
            "Opening dataset",
            "please wait",
            maximum=100,
            parent=self,
            style=wx.PD_SMOOTH | wx.PD_AUTO_HIDE,
        )
        self.progress.Update(10, "Data loading...")

        self.current_mission = None
        self.current_track = None

        cursor_wait = wx.BusyCursor()
        
        # If any data file is already open, it has to be closed.
        if hasattr(self,'tr'):
            if hasattr(self.tr,'data_val'):
                if isinstance(self.tr.data_val,dict):
                    for k in self.tr.data_val.keys():
                        self.tr.data_val[k].close()
                else:
                    self.tr.data_val.close()
        
        if self.data_sel_config["normpass_flag"]:
            mission = self.data_sel_config["mission"]
            kml_file = self.data_sel_config["kml_file"]
            filename = self.data_sel_config["normpass_file"]
            cfgfile_name = self.data_sel_config["cfg_file"]
            self.set_env_var()

            if len(filename) == 0:
                self.progress.Update(100, "Done.")
                self.progress.Destroy()
                return -1

            #            print('>>>>>:',mission,filename,kml_file)
            try:
                self.tr = Normpass(
                    mission,
                    filename,
                    mission_config_file=cfgfile_name,
                    kml_file=kml_file,
                )
            except FileNotFoundError as e:
                message = e.message_gui
                print(">>>>>>>>> ", message)
                with wx.MessageDialog(
                    None,
                    message=message,
                    caption="Error",
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
                ) as save_dataset_dlg:

                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print("No dataset!")
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1
            except Exception:
                message = (
                    "The data file does not suit to the "
                    + mission
                    + " name.\n\n"
                    + " - Check the mission name field and the data file."
                )
                with wx.MessageDialog(
                    None,
                    message=message,
                    caption="Warning",
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
                ) as save_dataset_dlg:

                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print("No dataset!")
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1

            #            pdb.set_trace()
            self.data_sel_config["track"] = str(self.tr.data_val.pass_number)
    #        print("Normpass file has been successfully read.")

            param_name = self.tr.time_hf_name
            data = self.tr.data_val[param_name]
            self.norm_index = np.array(data.coords["norm_index"])

        elif self.data_sel_config["gdr_flag"]:
            mission = self.data_sel_config["mission"]
            surf_type = self.data_sel_config["surf_type"]
            kml_file = self.data_sel_config["kml_file"]
            file_list = self.data_sel_config["list_file"]
            data_dir = self.data_sel_config["data_dir"]
            cfgfile_name = self.data_sel_config["cfg_file"]
            self.set_env_var()

            if len(file_list) == 0:
                self.progress.Update(100, "Done.")
                self.progress.Destroy()
                return -1

            try:
                self.tr = Track(
                    mission,
                    surf_type,
                    data_dir,
                    file_list,
                    mission_config_file=cfgfile_name,
                    kml_file=kml_file,
                )
            except (
                Track.InterpolationError,
                Track.TimeAttMissing,
                Track.ListFileEmpty,
                Track.SurfaceHeightError,
                Track.OutOfAreaError,
            ) as e:
                message = e.message_gui
                print(">>>>>>>>> ", message)
                with wx.MessageDialog(
                    None,
                    message=message,
                    caption="Error",
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
                ) as save_dataset_dlg:

                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print("No dataset has been downloaded!")
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1
            except (Track.ParamMissing) as e:
                message = e.message_gui
                print(">>>>>>>>> ", message)
                print("Data loading is aborted. No dataset!")
                self.progress.Update(100, "Done.")
                self.progress.Destroy()
                return -1
            except Exception:
                tbe = sys.exc_info()
                print("Exception in Track class: type %s value %s " % (tbe[0], tbe[1]))
                message = (
                    "An error has occured during the data loading : \n"
                    + " - Check the mission name suitability with the dataset file.\n"
                    + " - Check the consol for Warning messages."
                )
                with wx.MessageDialog(
                    None,
                    message=message,
                    caption="Warning",
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
                ) as save_dataset_dlg:

                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print("No dataset!")
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1

      #      print("GDR files have been successfully read.")

            param_name = self.tr.time_hf_name
            data = self.tr.data_val[param_name]
            self.norm_index = np.array(data.coords["gdr_index"])

        elif self.data_sel_config["gdr_altis_flag"]:
            mission = self.data_sel_config["mission"]
            kml_file = self.data_sel_config["kml_file"]
            filename = self.data_sel_config["gdr_altis_file"]
            cfgfile_name = self.data_sel_config["cfg_file"]
            self.set_env_var()

            if len(filename) == 0:
                self.progress.Update(100, "Done.")
                self.progress.Destroy()
                return -1

            #print('>>>>>:',mission,filename,kml_file)
            try:
                self.tr = GDR_altis(self.data_sel_config,
                    filename,
                    mission_config_file=cfgfile_name,
                    kml_file=kml_file,
                )
            except (GDR_altis.OutOfAreaError,
                        GDR_altis.NotAltisGDRFileError) as e:
                message = e.message_gui
                print(">>>>>>>>> ", message)
                with wx.MessageDialog(
                    None,
                    message=message,
                    caption="Error",
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
                ) as save_dataset_dlg:

                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print("No dataset!")
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1
            
            except Exception:
                message = (
                    "The data file does not suit to the "
                    + mission
                    + " name.\n\n"
                    + " - Check the mission name field and the data file."
                )

                with wx.MessageDialog(
                    None,
                    message=message,
                    caption="Warning",
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
                ) as save_dataset_dlg:

                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print("No dataset!")
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1
         #   print("GDR files have been successfully read.")

            param_name = self.tr.time_hf_name
            data = self.tr.data_val[param_name]
            self.norm_index = np.array(data.coords["gdr_index"])

        else:
            raise Exception("Error: normpass_flag and gdr_flag")

        self.common_data.lon = self.tr.data_val[self.tr.lon_hf_name]
        self.common_data.lat = self.tr.data_val[self.tr.lat_hf_name]
        self.common_data.time = self.tr.data_val[self.tr.time_hf_name]

        self.common_data.tr = self.tr.data_val
        self.common_data.lon_hf_name = self.tr.lon_hf_name
        self.common_data.lat_hf_name = self.tr.lat_hf_name
        self.common_data.time_hf_name = self.tr.time_hf_name

        self.progress.Update(50, "Data reading...")

        self.param_list = list(self.tr.data_val.keys())
        self.param_list.sort()

        #        param_name='time_20hz'
        #        data = self.tr.data_val[param_name]
        self.cycle = np.array(data.coords["cycle"])
        if "tracks" in data.coords.keys():
            self.tracks = np.array(data.coords["tracks"])
            if self.tracks.min() == self.tracks.max():
                self.data_sel_config["track"] = str(self.tracks.min())
            else:
                self.data_sel_config["track"] = "Tracks"

        else:
            self.tracks = np.empty(len(self.cycle), dtype="int")
            self.tracks.fill(self.data_sel_config["track"])
        #            self.data_sel_config['track'] = str(self.tr.pass_number)

        #        self.norm_index = np.array(data.coords['norm_index'])
        dataset_date = np.array(data.coords["date"], dtype=np.datetime64)
        self.date = [
            (y, m, d)
            for y, m, d in zip(
                pd.DatetimeIndex(dataset_date).year,
                pd.DatetimeIndex(dataset_date).month,
                pd.DatetimeIndex(dataset_date).day,
            )
        ]
        if self.norm_index.size == 0:
            message = "The dataset size is null. Check the dataset suitability with the KML file."
            with wx.MessageDialog(
                None,
                message=message,
                caption="Warning",
                style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR,
            ) as save_dataset_dlg:

                if save_dataset_dlg.ShowModal() == wx.ID_OK:
                    print("No dataset!")
                    self.progress.Update(100, "Done.")
                    self.progress.Destroy()
                    return -1

        self.progress.Update(50, "Data conditionning...")

        if hasattr(self, "plt1"):
            #            delattr(self,'plt1')
            #            print('self.plt1.get_visible() :',self.plt1.get_visible())
            self.plt1.remove()
            del self.plt1
            self.plt2.remove()
            del self.plt2
            self.plt3.remove()
            del self.plt3
            self.plt4.remove()
            del self.plt4
            self.canvas.draw()
        #        if hasattr(self,"grd_map"):
        #            self.comboGroundMap.SetValue("Ground Map None")
        #            self.grd_map.remove()
        #            self.grd_map = None
        #            self.canvas.draw()
        #        if hasattr(self,"rivers"):
        #            self.checkRiversLakes.SetValue(False)
        #            self.rivers.remove()
        #            self.canvas.draw()

        self.initDataSelect(event)
        self.selectall_flag=True
        self.comboSelParam.Clear()
        for param in self.param_list:
            self.comboSelParam.Append(param)

        self.comboSelParam.SetValue(self.param_list[0])
        self.progress.Update(100, "Done.")
        self.progress.Destroy()
        del cursor_wait

        if "messagedialog" not in self.data_sel_config.keys():
            self.data_sel_config["messagedialog"] = True
        self.set_env_var()

        if self.data_sel_config["messagedialog"]:
            message = ("The data loading has been successfully done.\n\n"
                        +" You have to choose an altimetric parameter in \n\tthe selection menu to display it.")
            
            with wx.RichMessageDialog(None, message=message, caption="Info",
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_INFORMATION,)as mssg_dlg:

                mssg_dlg.ShowCheckBox("Don't show again")

                if mssg_dlg.ShowModal() == wx.ID_OK:
                    if mssg_dlg.IsCheckBoxChecked():
#                     ... make sure we won't show it again the next time ...
                        self.data_sel_config["messagedialog"] = False
                        self.set_env_var()
#                    print('check?',mssg_dlg.IsCheckBoxChecked(),self.data_sel_config["messagedialog"])
                    return -1

    def initDataSelect(self, event):
        """
            Initialisation mask data selection
        """
        self.data_selection_frame.update(self.cycle, self.date, self.tracks)
        self.cycle_mask = self.data_selection_frame.onSelectAll(event)
        self.cycle_mask = np.tile(self.cycle_mask, (len(self.norm_index), 1)).T
        self.common_data.CYCLE_SEL = self.cycle_mask
        self.common_data.DATA_MASK_SEL = list()
        self.common_data.DATA_MASK_SEL.append(self.cycle_mask)
       # print('DATA_MASK_SEL[-1].shape',self.common_data.DATA_MASK_SEL[-1].shape)

    def onSelectCycle(self, event):
        """
            Mask data configuration for cycle 
        """
        cycle_mask = self.data_selection_frame.getselectcyle()
        cycle_mask = np.tile(cycle_mask, (len(self.norm_index), 1)).T
        self.common_data.CYCLE_SEL = cycle_mask
        self.update_plot()
        self.selectall_flag=False

    def onSelectAll(self, event):
        """
            Mask data configuration for all cycles
        """
        cycle_mask = self.data_selection_frame.onSelectAll(event)
        cycle_mask = np.tile(cycle_mask, (len(self.norm_index), 1)).T
        self.common_data.CYCLE_SEL = cycle_mask
        self.update_plot()
        self.selectall_flag=True

    def onSelectPassCombox(self, event):
        """
            Mask data Selection for a pass
        """
        cycle_mask = self.data_selection_frame.onSelectPassCombox(event)
        cycle_mask = np.tile(cycle_mask, (len(self.norm_index), 1)).T
        self.common_data.CYCLE_SEL = cycle_mask
        self.update_plot()

    def get_env_var(self):
        """
            Environment variable load file.
        """
        altis_tmp_file = os.path.join(tempfile.gettempdir(), "altis.tmp")

        if os.path.isfile(altis_tmp_file):

            with open(altis_tmp_file, "r") as f:
                #                try:
                #                    yaml_data = yaml.load(f)
                #                except:
                yaml_data = yaml.load(
                    f, Loader=yaml.FullLoader
                )  # A revoir pour créer un vrai loader

            self.data_sel_config = dict()
            for k in yaml_data.keys():
                self.data_sel_config[k] = yaml_data[k]

        else:
            self.data_sel_config = dict()
            self.data_sel_config["cfg_file"] = None
            self.data_sel_config["data_type"] = ""
            self.data_sel_config["data_dir"] = ""
            self.data_sel_config["list_file"] = []
            self.data_sel_config["track"] = None
            self.data_sel_config["list_track"] = []
            self.data_sel_config["mission"] = ""
            self.data_sel_config["surf_type"] = None
            self.data_sel_config["kml_file"] = None
            self.data_sel_config["normpass_flag"] = None
            self.data_sel_config["gdr_flag"] = None
            self.data_sel_config["normpass_file"] = ""
            self.data_sel_config["gdr_altis_flag"] = None
            self.data_sel_config["gdr_altis_file"] = ""
            self.data_sel_config["messagedialog"] = True
            with open(altis_tmp_file, "w") as f:
                yaml.dump(self.data_sel_config, f, default_flow_style=False)

    def set_env_var(self):
        """
            Save environment variable.
        """
        altis_tmp_file = os.path.join(tempfile.gettempdir(), "altis.tmp")
        #        pdb.set_trace()
        with open(altis_tmp_file, "w") as f:
            yaml.dump(self.data_sel_config, f, default_flow_style=False)


def main():
    """
        Main
    """
    app = wx.App(redirect=False)
    frame_main = Main_Window()
    frame_main.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
