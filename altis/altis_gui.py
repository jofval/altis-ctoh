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
# Copyright (c) 2019 Legos/CTOH. All rights reserved.
# ----------------------------------------------------------------------
import wx
#import wx.adv
import yaml
import os
import sys
#import matplotlib
import numpy as np
import pandas as pd
#import glob
import xarray as xr
import pkg_resources
import re
import pdb
import tempfile

# Performance GUI
# Line segment simplification and Using the fast style
#import matplotlib.style as mplstyle
#import matplotlib as mpl
#mplstyle.use('fast')
#mpl.rcParams['path.simplify'] = True
#mpl.rcParams['path.simplify_threshold'] = 1.0
#mpl.rcParams['agg.path.chunksize'] = 10000


from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
        

from altis_utils.tools import __config_load__,update_progress,__regex_file_parser__

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy.feature import ShapelyFeature,NaturalEarthFeature,COLORS,GSHHSFeature

#try:
from cartopy.io.img_tiles import StamenTerrain  
#else:
#from cartopy.io.img_tiles import Stamen
#import cartopy.io.img_tiles as cimgt



from altis.track_structure import Track, Normpass, GDR_altis
from altis.data_selection_gui import DatasetSelection

from matplotlib.widgets import MultiCursor, Cursor
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from altis.common_data import Singleton

from altis.download_data_gui import Load_data_Window
from altis.help_gui import Help_Window

from altis.time_series import Time_Series_Panel
from altis.colinear_analysis import ColinAnal_Panel

from altis.patch_code_oswlib_wmts import *


from altis._version import __version__,__revision__
#-------------------------------------------------------------------------------
# Control window : This window display the list of the cycle dowloaded in memory. 
#    This window is used for the cycle selection.
#-------------------------------------------------------------------------------
class Ctrl_Window(wx.Frame):
    def __init__(self,parent): #,cycle,date):        
        super().__init__(parent, title = "AlTiS : Dataset Selection",
            style=wx.FRAME_FLOAT_ON_PARENT | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX |\
             wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION ,\
             pos=(10,50),size=(250,700))

        self.parent = parent 

        panel = wx.Panel(self)
        self.create_toolbar() 
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.lctrlSelectCycle = wx.ListCtrl(panel, -1, style = wx.LC_REPORT) 
        self.lctrlSelectCycle.InsertColumn(0, 'Date', wx.LIST_FORMAT_LEFT, 80) 
        self.lctrlSelectCycle.InsertColumn(1, 'Cycle', wx.LIST_FORMAT_CENTER, width = 50) 
        self.lctrlSelectCycle.InsertColumn(2, 'Track', wx.LIST_FORMAT_CENTER, width = 50) 

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.parent.onSelectCycle, self.lctrlSelectCycle)
        
        box.Add(self.lctrlSelectCycle,1,wx.EXPAND) 
        panel.SetSizer(box) 
        panel.Fit() 
        self.Centre() 

    def update(self,cycle,date,tracks):
        self.lctrlSelectCycle.DeleteAllItems()
        index = 0
        for i in zip(cycle,date,tracks):
#            print(index,i, 'cycle: {:03d}'.format(i[0]))
#            index = self.list.InsertStringItem(index, '{:03d}'.format(i[0])) 
#            self.list.SetStringItem(index, 1,'{:04d}/{:02d}/{:02d}'.format(i[1][0],i[1][1],i[1][2]) ) 
#            index = self.lctrlSelectCycle.InsertItem(index, '{:03d}'.format(i[0])) 
#            self.lctrlSelectCycle.SetItem(index, 1,'{:04d}'.format(i[2]) ) 
#            self.lctrlSelectCycle.SetItem(index, 2,'{:04d}/{:02d}/{:02d}'.format(i[1][0],i[1][1],i[1][2]) ) 
            index = self.lctrlSelectCycle.InsertItem(index,'{:04d}/{:02d}/{:02d}'.format(i[1][0],i[1][1],i[1][2]) ) 
            self.lctrlSelectCycle.SetItem(index, 1, '{:03d}'.format(i[0])) 
            self.lctrlSelectCycle.SetItem(index, 2, '{:04d}'.format(i[2]) ) 
            index += 1  

    def create_toolbar(self):
        """
        Create a toolbar
        """
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((20,20))
 
        self.btnSelectAll = wx.Button(self.toolbar, label='Select All')
        self.toolbar.AddControl(self.btnSelectAll)
        self.toolbar.AddStretchableSpace()
        self.iconHelp = self.mk_iconbar("Help",wx.ART_HELP,"Help on AlTiS")

        self.toolbar.Realize()

        self.Bind(wx.EVT_BUTTON, self.parent.onSelectAll, self.btnSelectAll)
 
    def mk_iconbar(self,bt_txt,art_id,bt_lg_txt):
    
        ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (16,16))
        itemTool = self.toolbar.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool

    def onSelectAll(self,event):
        for idx in range(self.lctrlSelectCycle.GetItemCount()):
            self.lctrlSelectCycle.Select(idx)
        print('onSelectAll')
        return np.ones((self.lctrlSelectCycle.GetItemCount()),dtype=bool)
            
#    def onSelectCycle(self,event):
#        mask=[]
#        for idx in range(self.lctrlSelectCycle.GetItemCount()):
#            mask.extend([self.lctrlSelectCycle.IsSelected(idx)])

#        print('onSelectCycle')
#        return np.array(mask)
    
    def getselectcyle(self):
        mask=[]
        for idx in range(self.lctrlSelectCycle.GetItemCount()):
            mask.extend([self.lctrlSelectCycle.IsSelected(idx)])
        print('getSelectCycle')
        return np.array(mask)
        
#-------------------------------------------------------------------------------
# Main window : This is the main window
#-------------------------------------------------------------------------------
class Main_Window(wx.Frame):
    def __init__(self,):        
        super().__init__(None, title = "Altimetry Time Series (AlTiS) Software",size = wx.DisplaySize())
        self.common_data = Singleton()
        self.InitUI()
        self.Center()
        
    def InitUI(self):
        
        self.get_env_var()

        main_panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.CanvasPanel(main_panel)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.plot_panel, proportion=1, flag=wx.EXPAND|wx.CENTER, border=8)
        vbox.Add(hbox1, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=10)
        main_panel.SetSizer(vbox)

        self.create_toolbar()
        self.statusbar = self.CreateStatusBar(2)
#        self.SetStatusText(0,"\tCentered")
#        self.SetStatusText(1,"\t\tRight Aligned")
        status_bar_right_text = 'AlTiS - version : '+__version__+'       '
        print(status_bar_right_text)
        version_size = wx.Window.GetTextExtent(self, status_bar_right_text)
        self.SetStatusWidths([-1, version_size.width])
        self.statusbar.SetStatusText(status_bar_right_text,1) 

        self.cycle=[]
        self.date=[]
        self.data_selection_frame = Ctrl_Window(self)
        self.data_selection_frame.Show()

#        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onTest, self.data_selection_frame.lctrlSelectCycle)
#        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelectCycle, self.lctrlSelectCycle)
        
    def CanvasPanel(self,panel):
        print('plot_panel')
        self.plot_panel=wx.Panel(panel)
        self.figure = Figure()
        self.ax1 = self.figure.add_subplot(2,2,1, projection=ccrs.PlateCarree())
        self.ax1.set_xlabel('Longitude (deg)')
        self.ax1.set_ylabel('Latitude (deg)')
        self.ax1.autoscale()
        self.ax2 = self.figure.add_subplot(2,2,2,sharey=self.ax1)
        self.ax2.set_ylabel('Latitude (deg)')
        self.ax3 = self.figure.add_subplot(2,2,3,sharex=self.ax1)
        self.ax3.set_xlabel('Longitude (deg)')
        self.ax4 = self.figure.add_subplot(2,2,4,sharey=self.ax3)
        self.ax4.set_xlabel('Time (YYYY-MM)')
        self.canvas = FigureCanvas(self.plot_panel, -1, self.figure)
        
        self.list_axes = [self.ax1,self.ax2,self.ax3,self.ax4]
        self.list_axes_coord = [['Lon','Lat'],['Param','Lat'],['Lon','Param'],['Time','Param']]
        self.mpl_toolbar = NavigationToolbar(self.canvas)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        
        vbox.Add(self.mpl_toolbar, proportion=0, flag=wx.CENTER, border=8)
        vbox.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.CENTER, border=8)

        self.plot_panel.SetSizer(vbox)
        
        self.mouseMoveID = self.figure.canvas.mpl_connect('motion_notify_event',self.onMotion)

    def onMotion(self, event):
        x = event.x
        y = event.y
        xdata = event.xdata
        ydata = event.ydata
        if event.inaxes in self.list_axes:
            idx = self.list_axes.index(event.inaxes)
            [xlabel,ylabel] = self.list_axes_coord[idx]
            self.statusbar.SetStatusText("Coordinates :\t%s : %s, %s : %s" % (xlabel,"{: 10.6f}".format(xdata),ylabel,"{: 10.6f}".format(ydata)))
        else:
            self.statusbar.SetStatusText("Coordinates :")

    def draw(self,lon,lat,time,param,mask,cm,groundmap):
    
        if self.data_sel_config['gdr_flag'] | self.data_sel_config['gdr_altis_flag']:
            mode_flag = 'GDR files'
        elif self.data_sel_config['normpass_flag']:
            mode_flag = 'NormPass file'
        
        if self.data_sel_config['kml_file'] is None:
            kml_filename=''
        else:
            kml_filename=' | select. file : '+self.data_sel_config['kml_file'].split(os.path.sep)[-1]
        
#        main_plot_title = 'Mission : '+self.data_sel_config['mission']+' | '+' track number : '+str(self.data_sel_config['track'])+' | '+mode_flag+kml_filename+'\n\n'+self.param
        main_plot_title = 'Mission : '+self.data_sel_config['mission']+' | '+mode_flag+kml_filename+'\n\n'+self.param
                        
        self.figure.suptitle(main_plot_title, fontsize=16)
        
        self.plt1 = self.ax1.scatter(lon,lat,c=param, marker='+',cmap=cm,transform=ccrs.PlateCarree())

        
        gl = self.ax1.gridlines(linewidth=0.5)

#        gl = self.ax1.gridlines(crs=ccrs.PlateCarree(),draw_labels=True)
        gl.xlabels_top = gl.ylabels_right = False
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER   
             
#        self.ax1.plot(x,y,transform=ccrs.PlateCarree())
#        gl = self.ax1.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
#                          linewidth=0.5, color='white', alpha=1.0, linestyle='--')
#        gl.xlabels_top = True
#        gl.ylabels_left = True
#        gl.xlabels_bottom = False
#        gl.ylabels_right = False
#        gl.xlines = True
#        gl.xformatter = LONGITUDE_FORMATTER
#        gl.yformatter = LATITUDE_FORMATTER

        self.ax1.set_aspect('auto', adjustable='datalim', anchor='C', share=False)
            
        self.ax2.set_xlabel(param.attrs['long_name'])
        self.ax2.set_ylabel('Latitude (deg)')
        self.plt2 = self.ax2.scatter(param,lat,c=param, marker='+',cmap=cm ) 
        self.ax2.grid(True)

        self.plt3 = self.ax3.scatter(lon,param,c=param, marker='+',cmap=cm ) 
        self.ax3.grid(True)
        self.ax3.set_ylabel(param.attrs['long_name'])
        self.ax3.set_xlabel('Longitude (deg)')

        self.plt4 = self.ax4.scatter(np.array(time),param,c=param, marker='+',cmap=cm ) 
        self.ax4.grid(True)
        self.ax4.set_xlabel('Time (YYYY-MM)')
        self.ax4.set_ylabel(param.attrs['long_name'])

        if hasattr(self,"cbar"):
            self.cbar.set_clim(vmin=np.min(param),vmax=np.max(param))
            self.cbar.set_cmap(cmap=cm)
            self.cbar.set_label(param.attrs['long_name'], rotation=270)
            self.cbar.draw_all()
        else:
            self.cbar = self.figure.colorbar(self.plt1, ax=[self.ax2,self.ax4],orientation='vertical')
            self.cbar.set_label(param.attrs['long_name'], rotation=270)

#        self.cursor = MultiCursor(self.figure.canvas, (self.ax1, self.ax2, self.ax3), color='black', lw=0.5, horizOn=True, vertOn=True, useblit=True)

    def create_toolbar(self):
        """
        Create a toolbar
        """
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((20,20))
 
        self.iconQuit = self.mk_iconbar("Quit",wx.ART_QUIT,"Quit AlTiS")

#        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
#        self.toolbar.AddStretchableSpace()
        
        self.ListKindData = ['Import data ... ','Normpass', 'AlTiS GDR', 'GDR Tracks']
        self.comboKindData = wx.ComboBox( self.toolbar, value = self.ListKindData[0], choices = self.ListKindData[1:],size=(130,30))
        self.toolbar.AddControl(self.comboKindData, label="Kind of data to import" )
#        self.toolbar.AddStretchableSpace()
#        self.btnImport = wx.Button(self.toolbar, label="Import ...")
#        self.toolbar.AddControl(self.btnImport, label="Normpass or GDR")

#        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
#        self.toolbar.AddStretchableSpace()

#        self.iconOpen = self.mk_iconbar("Open",wx.ART_FILE_OPEN,"Load Altimetry Dataset")
        self.comboSelParam = wx.ComboBox( self.toolbar, value = "Select_parameter", choices = [],size=(200,30))
        self.toolbar.AddControl(self.comboSelParam, label="Select a paramter" )
#        self.toolbar.AddStretchableSpace()
#        self.iconSave = self.mk_iconbar("Save",wx.ART_FILE_SAVE,"Save Altimetry Dataset")
        self.btnSave = wx.Button(self.toolbar, label="Save")
        self.toolbar.AddControl(self.btnSave, label="Save the current selection.")
        
#        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
#        self.toolbar.AddStretchableSpace()
    
#        self.btnSelectData = self.mk_iconbar("Selection",wx.ART_CUT,"Dataset Selection")
        self.btnSelectData = wx.Button(self.toolbar, label="Selection")
        self.toolbar.AddControl(self.btnSelectData, label="Select and Remove")
#        self.toolbar.AddStretchableSpace()
        self.iconUndo = self.mk_iconbar("Undo",wx.ART_UNDO,"Undo")
#        self.iconRedo = self.mk_iconbar("Redo",wx.ART_REDO,"Redo")
#        self.toolbar.AddStretchableSpace()
#        self.iconRefresh = self.mk_iconbar("Refresh",wx.ART_NEW,"Refresh scale")
        self.btnRefresh = wx.Button(self.toolbar, label="Refresh")
        self.toolbar.AddControl(self.btnRefresh, label="Update the scale")

#        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
#        self.toolbar.AddStretchableSpace()

        self.checkCoast = wx.CheckBox( self.toolbar, label="Coastline")
        self.toolbar.AddControl(self.checkCoast, label="Show Coastline" )
#        self.toolbar.AddStretchableSpace()
        self.checkRiversLakes = wx.CheckBox( self.toolbar, label="Rivers-Lakes")
        self.toolbar.AddControl(self.checkRiversLakes, label="Show Rivers-Lakes" )
#        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.comboColorMap = wx.ComboBox( self.toolbar, value = "jet", choices = ["jet","hsv","ocean","terrain","coolwarm","RdBu","viridis"])
        self.toolbar.AddControl(self.comboColorMap, label="Color palet" )
        self.comboGroundMap = wx.ComboBox( self.toolbar, value = "Ground Map None", choices = ["Ground Map None","LandSat","Open Street Map"])
        self.toolbar.AddControl(self.comboGroundMap, label="Ground Map")

#        self.toolbar.AddStretchableSpace()

        self.toolbar.AddSeparator()
#        self.toolbar.AddStretchableSpace()

#        self.btnHooking = wx.Button(self.toolbar, label="Hooking correction")
#        self.toolbar.AddControl(self.btnHooking )
#        self.btnColAnalysis = wx.Button(self.toolbar, label="Collinear Analysis")
#        self.toolbar.AddControl(self.btnColAnalysis)
        
#        self.btnTimeSeries = self.mk_iconbar("Time Series",wx.ART_EXECUTABLE_FILE,"Time Series")
        self.btnTimeSeries = wx.Button(self.toolbar, label = "Time Series")
        self.toolbar.AddControl(self.btnTimeSeries, label = "Compute the Time Series")

#        self.toolbar.AddStretchableSpace()

#        self.toolbar.AddSeparator()  


        self.toolbar.AddStretchableSpace()
        self.iconHelp = self.mk_iconbar("Help",wx.ART_HELP,"Help on AlTiS")

        self.toolbar.Realize()


        self.Bind(wx.EVT_MENU, self.onQuit,self.iconQuit)
#        self.iconOpen.Bind(wx.EVT_MENU, self.onOpen)
#        self.btnImport.Bind(wx.EVT_BUTTON, self.onOpen)
        self.comboKindData.Bind(wx.EVT_COMBOBOX, self.onOpen)
        self.comboSelParam.Bind(wx.EVT_COMBOBOX, self.onSelParam)
#        self.iconSave.Bind(wx.EVT_MENU, self.onSave)
        self.btnSave.Bind(wx.EVT_BUTTON, self.onSave)
        self.btnSelectData.Bind(wx.EVT_BUTTON, self.onSelectData)
#        self.btnHooking.Bind(wx.EVT_BUTTON, self.onHooking)
#        self.btnColAnalysis.Bind(wx.EVT_BUTTON, self.onColAnalysis)
        self.btnTimeSeries.Bind(wx.EVT_BUTTON, self.onTimeSeries)
        self.Bind(wx.EVT_MENU, self.onUndo,self.iconUndo)
#        self.Bind(wx.EVT_MENU, self.onRedo, self.iconRedo)
#        self.iconRefresh.Bind(wx.EVT_MENU,self.onRefresh)
        self.btnRefresh.Bind(wx.EVT_BUTTON,self.onRefresh)
        self.checkCoast.Bind(wx.EVT_CHECKBOX, self.onCoast)
        self.checkRiversLakes.Bind(wx.EVT_CHECKBOX, self.onRiversLakes)
        self.comboColorMap.Bind(wx.EVT_COMBOBOX, self.onColorMap)
        self.comboGroundMap.Bind(wx.EVT_COMBOBOX, self.onGroundMap)
        self.Bind(wx.EVT_MENU, self.onHelp, self.iconHelp)


    def mk_iconbar(self,bt_txt,art_id,bt_lg_txt):
    
        ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (20,20))
        itemTool = self.toolbar.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool

    def onHooking(self,event):
        print('Hooking !!')

    def onColAnalysis(self,event): 
        mask = self.common_data.CYCLE_SEL\
             &  self.common_data.DATA_MASK_SEL[-1]\
             & self.common_data.DATA_MASK_PARAM

        self.colana_panel = ColinAnal_Panel(self,self.data_sel_config,self.param)
        self.colana_panel.Show()
    
    
    def onTimeSeries(self,event):
        mask = self.common_data.CYCLE_SEL\
             &  self.common_data.DATA_MASK_SEL[-1]\
             & self.common_data.DATA_MASK_PARAM

        self.ts_panel = Time_Series_Panel(self,self.data_sel_config)
        self.ts_panel.Show()
        
        
        
    def onRefresh(self,event):
        cursor_wait = wx.BusyCursor()
        print('On Refresh')
        xy_coord=self.plt1.get_offsets()
        xy_data=self.plt2.get_offsets()
        rato_threshold=0.05
        lon_lim = [np.min(xy_coord[:,0])-np.min(xy_coord[:,0])*rato_threshold
                        ,np.max(xy_coord[:,0])+np.max(xy_coord[:,0])*rato_threshold]
        lat_lim = [np.min(xy_coord[:,1])-np.min(xy_coord[:,1])*rato_threshold
                        ,np.max(xy_coord[:,1])+np.max(xy_coord[:,1])*rato_threshold]
        param_lim = [np.min(xy_data[:,0])-np.min(xy_data[:,0])*rato_threshold
                        ,np.max(xy_data[:,0])+np.max(xy_data[:,0])*rato_threshold]
        print('param_lim', param_lim)
#        self.ax1.set_xlim(lat_lim)
#        self.ax1.set_ylim(lon_lim)
        self.ax2.set_xlim(param_lim)
        self.ax3.set_ylim(param_lim)
        self.ax4.set_ylim(param_lim)
        self.canvas.draw()
    
    
    
    def onCoast(self,event):
        cursor_wait = wx.BusyCursor()
        if hasattr(self,"plt1"):
            self.ax1_zoom = {'x':self.ax1.get_xlim(),'y':self.ax1.get_ylim()}
            xlim_diff=np.diff(self.ax1.get_xlim())
            ylim_diff=np.diff(self.ax1.get_ylim())
            resol_param = np.sqrt(xlim_diff*xlim_diff+ylim_diff*ylim_diff)
        else:
            self.ax1_zoom = {'x':None,'y':None}
            resol_param=None
        
        if resol_param < 0.5:
            resol = 'full'
        if resol_param < 1.0:
            resol = 'high'
        elif resol_param < 5.0:
            resol = 'intermediate'
        elif resol_param < 10.0:
            resol = 'low'
        else:
            resol = 'coarse'
        
        print(resol_param,resol,self.checkCoast.IsChecked())
        if self.checkCoast.IsChecked():
            COAST = GSHHSFeature(scale=resol, levels=[1,2,3,4],edgecolor="red")
            self.coast = self.ax1.add_feature(COAST)
            self.canvas.draw()
            print('Done')
        else:
            self.coast.remove()
            self.canvas.draw()
            print('removed')

    
    def onRiversLakes(self,event):
        cursor_wait = wx.BusyCursor()
        if hasattr(self,"plt1"):
            self.ax1_zoom = {'x':self.ax1.get_xlim(),'y':self.ax1.get_ylim()}
            xlim_diff=np.diff(self.ax1.get_xlim())
            ylim_diff=np.diff(self.ax1.get_ylim())
            resol_param = np.sqrt(xlim_diff*xlim_diff+ylim_diff*ylim_diff)
        else:
            self.ax1_zoom = {'x':None,'y':None}
            resol_param=None
        
        riverslakes_resol = {'low' : '110m', 'medium' : '50m', 'high' : '10m'}
        
        if resol_param < 1.0:
            resol = 'high'
        elif resol_param < 5.0:
            resol = 'medium'
        else:
            resol = 'low'
        
        print(resol_param,resol,self.checkRiversLakes.IsChecked())
        if self.checkRiversLakes.IsChecked():
            RIVERS = NaturalEarthFeature('physical','rivers_lake_centerlines', \
               riverslakes_resol[resol], edgecolor=COLORS['water'],facecolor='none')
            self.rivers = self.ax1.add_feature(RIVERS)
            self.canvas.draw()
            print('Done')
        else:
            self.rivers.remove()
            self.canvas.draw()
            print('removed')

    def onColorMap(self,event):
        cursor_wait = wx.BusyCursor()
        if hasattr(self,"plt1"):
            self.ax1_zoom = {'x':self.ax1.get_xlim(),'y':self.ax1.get_ylim()}
        else:
            self.ax1_zoom = {'x':None,'y':None}
        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        self.param = self.comboSelParam.GetValue()
        print(self.cm)
        self.update_plot()

        print('done')


    def onGroundMap(self,event):
        cursor_wait = wx.BusyCursor()
        if hasattr(self,"plt1"):
            self.ax1_zoom = {'x':self.ax1.get_xlim(),'y':self.ax1.get_ylim()}
        else:
            self.ax1_zoom = {'x':None,'y':None}
        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        self.param = self.comboSelParam.GetValue()

        if self.groundmap == 'LandSat':
            altis_cfg = pkg_resources.resource_filename('altis', '../etc/altis_config.yml')
            with open(altis_cfg) as f:
                try:
                    yaml_data = yaml.safe_load(f)
                except:
                    yaml_data = yaml.safe_load(f, Loader=yaml.FullLoader) # A revoir pour créer un vrai loader
            url = yaml_data['wmts']['ground_map']['url']
            layer = yaml_data['wmts']['ground_map']['layer']
        elif self.groundmap == 'Open Street Map':
            tiler = StamenTerrain()
#            tiler = Stamen('terrain-background')
        elif self.groundmap == "Ground Map None":
            pass            

        if self.groundmap == 'LandSat':
            print('ground : url,layer ',url,layer)
            if hasattr(self,"grd_map"):
                if self.grd_map is None:
                    self.grd_map = self.ax1.add_wmts(url,layer)
                else:
                    self.grd_map.remove()
                    self.grd_map = self.ax1.add_wmts(url,layer)
            else:
            
                self.grd_map = self.ax1.add_wmts(url,layer)
                
        elif self.groundmap == 'Open Street Map':
            if hasattr(self,"grd_map"):
                if self.grd_map is None:
                    x0,x1 = self.ax1.get_xlim()
                    y0,y1 = self.ax1.get_ylim()
                    self.ax1.set_extent([x0,x1,y0,y1])
                    self.grd_map = self.ax1.add_image(tiler,6)
                else:
                    self.grd_map.remove()
                    x0,x1 = self.ax1.get_xlim()
                    y0,y1 = self.ax1.get_ylim()
                    self.ax1.set_extent([x0,x1,y0,y1])
                    self.grd_map = self.ax1.add_image(tiler,6)
            else:
                x0,x1 = self.ax1.get_xlim()
                y0,y1 = self.ax1.get_ylim()
                self.ax1.set_extent([x0,x1,y0,y1])
                self.grd_map = self.ax1.add_image(tiler,6)
        elif self.groundmap == "Ground Map None":
            if hasattr(self,"grd_map"):
                if not self.grd_map is None:
                    self.grd_map.remove()
                    self.grd_map = None
            else:
                self.grd_map = None
        print(self.groundmap)
        self.canvas.draw()
        print('done')
    

    def onSelectData(self,event):
        print('onSelectData')
#        pdb.set_trace()
        selection = DatasetSelection(self.figure,
                                [self.plt1,self.plt2,self.plt3,self.plt4],
                                [self.ax1,self.ax2,self.ax3,self.ax4],
                                self.cm,self.cbar)

    def onSave(self,event):
        if hasattr(self,"tr"):

            mask = self.common_data.CYCLE_SEL\
                 &  self.common_data.DATA_MASK_SEL[-1]\
                 & self.common_data.DATA_MASK_PARAM
            
            if min(self.tracks[mask.any(axis=1)]) == max(self.tracks[mask.any(axis=1)]):
                self.tr.track_value = min(self.tracks[mask.any(axis=1)])
            else:
                self.tr.track_value = 'Tracks'
                
            
            if self.data_sel_config['gdr_altis_flag']:
                default_filename = self.tr.mk_filename_gdr_data (mask)

                with wx.FileDialog(self, message="Export AlTiS GDR Dataset as NetCDF file" ,
                       defaultDir=self.data_sel_config['data_dir'], defaultFile=default_filename ,wildcard="NetCDF files (*.nc)|*.nc",
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,) as fileDialog:

                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return     # the user changed their mind

                    # save the current contents in the file
                    pathname = fileDialog.GetPath()
                    try:
                        self.tr.save_gdr_data(mask,filename=pathname)
                    except IOError:
                        wx.LogError("Cannot save current data in file '%s'." % pathname)

                        
            if self.data_sel_config['gdr_flag']: 
                default_filename = self.tr.mk_filename_gdr_data (mask)

                with wx.FileDialog(self, message="Export AlTiS GDR Dataset as NetCDF file" ,
                       defaultDir=self.data_sel_config['data_dir'], defaultFile=default_filename ,wildcard="NetCDF files (*.nc)|*.nc",
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,) as fileDialog:

                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return     # the user changed their mind

                    # save the current contents in the file
                    pathname = fileDialog.GetPath()
                    try:
                        self.tr.save_gdr_data(mask,filename=pathname)
                    except IOError:
                        wx.LogError("Cannot save current data in file '%s'." % pathname)

                        
            if self.data_sel_config['normpass_flag']: 
                default_filename = self.tr.mk_filename_norm_data (mask)

                with wx.FileDialog(self, message="Export AlTiS GDR Dataset as NetCDF file" ,
                       defaultDir=self.data_sel_config['data_dir'], defaultFile=default_filename ,wildcard="NetCDF files (*.nc)|*.nc",
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,) as fileDialog:

                    if fileDialog.ShowModal() == wx.ID_CANCEL:
                        return     # the user changed their mind

                    # save the current contents in the file
                    pathname = fileDialog.GetPath()
                    try:
                        self.tr.save_norm_data(mask,filename=pathname)
                    except IOError:
                        wx.LogError("Cannot save current data in file '%s'." % pathname)
            
        else:
            message = 'No dataset !'
            with wx.MessageDialog(None, message=message, caption='Warning',
                style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR) as save_dataset_dlg:
            
                if save_dataset_dlg.ShowModal() == wx.ID_OK:
                    print('No dataset!')
            
            
    def onQuit(self,event):
        self.data_selection_frame.Close()
        if hasattr(self,'ts_panel'):
            try :
                self.ts_panel.Close()
            except :
                pass
            
        self.Close()
 
    def onUndo(self,event):
        if len(self.common_data.DATA_MASK_SEL) > 1:
            self.common_data.DATA_MASK_SEL.pop()
            self.update_plot()
        
    def update_plot(self,):
        cursor_wait = wx.BusyCursor()

        mask = self.common_data.CYCLE_SEL\
             &  self.common_data.DATA_MASK_SEL[-1]\
             & self.common_data.DATA_MASK_PARAM
        param = self.common_data.param.where(mask)
        lon = self.common_data.lon.where(mask)
        lat = self.common_data.lat.where(mask)
        time = self.common_data.time.where(mask)
        self.plt1.remove()
        self.plt1 = self.ax1.scatter(lon,lat,c=param, marker='+',cmap=self.cm,transform=ccrs.PlateCarree())
        self.plt2.remove()
        self.plt2 = self.ax2.scatter(param,lat,c=param, marker='+',cmap=self.cm ) 
        self.plt3.remove()
        self.plt3 = self.ax3.scatter(lon,param,c=param, marker='+',cmap=self.cm ) 
        self.plt4.remove()
        self.plt4 = self.ax4.scatter(np.array(time),param,c=param, marker='+',cmap=self.cm ) 

#        self.cbar.remove()
        self.cbar.set_cmap(cmap=self.cm)
        self.cbar.set_label(param.attrs['long_name'], rotation=270)
        self.cbar.draw_all()

        self.canvas.draw()
  
    def onHelp(self,event): 
        help=Help_Window()
        help.Show()

    def onSelParam(self,event):

        cursor_wait = wx.BusyCursor()

        self.param = self.comboSelParam.GetValue()
        self.common_data.param_name = self.param
        self.common_data.param = self.tr.data_val[self.param]

        self.common_data.DATA_MASK_PARAM = ~np.isnan(self.common_data.param) &\
                                            ~np.isnan(self.common_data.lon) &\
                                            ~np.isnan(self.common_data.lat) &\
                                            ~np.isnat(self.common_data.time)

        mask = self.common_data.CYCLE_SEL\
             &  self.common_data.DATA_MASK_SEL[-1]\
             & self.common_data.DATA_MASK_PARAM
        
        param = self.common_data.param.where(mask)
        lon = self.common_data.lon.where(mask)
        lat = self.common_data.lat.where(mask)
        time = self.common_data.time.where(mask)

        if (self.data_sel_config['mission'] == self.current_mission) \
            and (self.data_sel_config['track'] == self.current_track):

            self.ax1_zoom = {'x':self.ax1.get_xlim(),'y':self.ax1.get_ylim()}
#            self.plt1.remove()
#            self.plt2.remove()
#            self.plt3.remove()
#            self.plt4.remove()

#        else:
#            self.ax1_zoom = {'x':None,'y':None}
        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        print('Drawing... ',self.param,self.cm,self.groundmap)
        

        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.draw(lon,lat,time,param,mask,self.cm,self.groundmap)

        if (self.data_sel_config['mission'] == self.current_mission) \
            and (self.data_sel_config['track'] == self.current_track):

            self.ax1.set_xlim(self.ax1_zoom['x'])
            self.ax1.set_ylim(self.ax1_zoom['y'])


        self.canvas.draw()
        self.current_mission = self.data_sel_config['mission']
        self.current_track = self.data_sel_config['track']

        
    def onOpen(self,event):
    
        if self.comboKindData.GetValue() != self.ListKindData[0]:
            self.get_env_var()
            self.data_sel_config['data_type'] = self.comboKindData.GetValue()
            self.comboKindData.SetValue(self.ListKindData[0])

            with Load_data_Window(self.data_sel_config) as load_data_args:
                load_data_args.Center()
                load_data_args.Show()
                if load_data_args.ShowModal() == wx.ID_OK:
                    print("ShowModal == wx.ID_OK")
                    self.load_data_process(event,load_data_args.data_sel_config)
                else:
                    print('Cancel')
        
    def load_data_process(self,event,load_data_args):
                        
        self.data_sel_config = load_data_args

        self.progress = wx.ProgressDialog("Opening dataset", "please wait", maximum=100, parent=self, style=wx.PD_SMOOTH|wx.PD_AUTO_HIDE)
        self.progress.Update(10, "Data loading...")
        
        self.current_mission = None
        self.current_track = None
        
        cursor_wait = wx.BusyCursor()

        if self.data_sel_config['normpass_flag']:
            mission=self.data_sel_config['mission']
            kml_file=self.data_sel_config['kml_file']
            filename=self.data_sel_config['normpass_file']
            self.set_env_var()
            
            if (len(filename) == 0) :
                self.progress.Update(100, "Done.")
                self.progress.Destroy()
                return -1

            print('>>>>>:',mission,filename,kml_file)
            try :
                self.tr=Normpass(mission,filename,kml_file=kml_file)
            except Exception:
                message = ('The data file does not suit to the '+mission+' name.\n\n'
                +' - Check the mission name field and the data file.')
                with wx.MessageDialog(None, message=message, caption='Warning',
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR) as save_dataset_dlg:
                
                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print('No dataset!')
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1

#            pdb.set_trace()
            self.data_sel_config['track'] = str(self.tr.data_val.pass_number)
            print('Normpass file has been successfully read.')

            param_name=self.tr.time_hf_name
            data = self.tr.data_val[param_name]
            self.norm_index = np.array(data.coords['norm_index'])
        
        elif self.data_sel_config['gdr_flag']: 
            mission=self.data_sel_config['mission']
            surf_type=self.data_sel_config['surf_type']
            kml_file=self.data_sel_config['kml_file']
            file_list=self.data_sel_config['list_file']
            data_dir=self.data_sel_config['data_dir']
            self.set_env_var()
            
            if (len(file_list) == 0) :
                self.progress.Update(100, "Done.")
                self.progress.Destroy()
                return -1
                
            try:
                self.tr=Track(mission,surf_type,data_dir,file_list,kml_file=kml_file)
            except (Track.InterpolationError, Track.TimeAttMissing, Track.ListFileEmpty) as e:
                message = e.message_gui
                print('>>>>>>>>> ',message)
                with wx.MessageDialog(None, message=message, caption='Error',
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR) as save_dataset_dlg:
                
                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print('No dataset!')
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1
            except (Track.ParamMissing) as e:
                message = e.message_gui
                print('>>>>>>>>> ',message)
                print('Data loading is aborted. No dataset!')
                self.progress.Update(100, "Done.")
                self.progress.Destroy()
                return -1
            except Exception:
                tbe = sys.exc_info()
                print(
                    "Exception in Track class: type %s value %s " % (tbe[0], tbe[1])
                )
                print("Traceback: ")
                print(traceback.print_tb(tbe[2]))
                raise
                message = ('An error has occured during the data loading : \n'
                +' - Check the mission name suitability with the dataset file.\n'
                +' - Check the consol for Warning messages.')
                with wx.MessageDialog(None, message=message, caption='Warning',
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR) as save_dataset_dlg:
                
                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print('No dataset!')
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1
                
            print('GDR files have been successfully read.')

            param_name=self.tr.time_hf_name
            data = self.tr.data_val[param_name]
            self.norm_index = np.array(data.coords['gdr_index'])
            
            
        elif self.data_sel_config['gdr_altis_flag']: 
            mission=self.data_sel_config['mission']
            kml_file=self.data_sel_config['kml_file']
            filename=self.data_sel_config['gdr_altis_file']
            self.set_env_var()
            
            if (len(filename) == 0) :
                self.progress.Update(100, "Done.")
                self.progress.Destroy()
                return -1

            print('>>>>>:',mission,filename,kml_file)
            try:
                self.tr=GDR_altis(mission,filename,kml_file=kml_file)
            except Exception:
                message = ('The data file does not suit to the '+mission+' name.\n\n'
                +' - Check the mission name field and the data file.')
                
                with wx.MessageDialog(None, message=message, caption='Warning',
                    style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR) as save_dataset_dlg:
                
                    if save_dataset_dlg.ShowModal() == wx.ID_OK:
                        print('No dataset!')
                        self.progress.Update(100, "Done.")
                        self.progress.Destroy()
                        return -1
            print('GDR files have been successfully read.')

            param_name=self.tr.time_hf_name
            data = self.tr.data_val[param_name]
            self.norm_index = np.array(data.coords['gdr_index'])
            

        else:
            raise Exception('Error: normpass_flag and gdr_flag')        
        
        
        self.common_data.lon = self.tr.data_val[self.tr.lon_hf_name]
        self.common_data.lat = self.tr.data_val[self.tr.lat_hf_name]
        self.common_data.time = self.tr.data_val[self.tr.time_hf_name]

        self.common_data.tr = self.tr.data_val
        self.common_data.lon_hf_name = self.tr.lon_hf_name
        self.common_data.lat_hf_name = self.tr.lat_hf_name
        self.common_data.time_hf_name = self.tr.time_hf_name

        self.progress.Update(50, "Data reading...")

        self.param_list=list(self.tr.data_val.keys())
        self.param_list.sort()
        
#        param_name='time_20hz'
#        data = self.tr.data_val[param_name]
        self.cycle = np.array(data.coords['cycle'])
        if 'tracks' in data.coords.keys():
            self.tracks = np.array(data.coords['tracks'])
            if self.tracks.min() == self.tracks.max():
                self.data_sel_config['track'] = str(self.tracks.min())
            else :
                self.data_sel_config['track'] = 'Tracks'
            
        else:
            self.tracks = np.empty(len(self.cycle),dtype='int')
            self.tracks.fill(self.data_sel_config['track'])
#            self.data_sel_config['track'] = str(self.tr.pass_number)
            
#        self.norm_index = np.array(data.coords['norm_index'])
        dataset_date=np.array(data.coords['date'],dtype=np.datetime64)
        self.date = [(y,m,d) for y,m,d in zip(pd.DatetimeIndex(dataset_date).year,
                                                pd.DatetimeIndex(dataset_date).month,
                                                pd.DatetimeIndex(dataset_date).day)]
        if self.norm_index.size == 0:
            message = 'The dataset size is null. Check the dataset suitability with the KML file.'
            with wx.MessageDialog(None, message=message, caption='Warning',
                style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR) as save_dataset_dlg:
            
                if save_dataset_dlg.ShowModal() == wx.ID_OK:
                    print('No dataset!')
                    self.progress.Update(100, "Done.")
                    self.progress.Destroy()
                    return -1
            
        self.set_env_var()
        self.progress.Update(50, "Data conditionning...")

        if hasattr(self,"plt1"):
#            delattr(self,'plt1')
            pdb.set_trace()
            self.plt1.remove()
            self.plt2.remove()
            self.plt3.remove()
            self.plt4.remove()
            self.canvas.draw()
        if hasattr(self,"grd_map"):
            self.comboGroundMap.SetValue("Ground Map None")
            self.grd_map.remove()
            self.grd_map = None
            self.canvas.draw()
        if hasattr(self,"rivers"):
            self.checkRiversLakes.SetValue(False)
            self.rivers.remove()
            self.canvas.draw()

        self.initDataSelect(event)
                    
        self.comboSelParam.Clear()
        for param in self.param_list:
            self.comboSelParam.Append(param)


        self.comboSelParam.SetValue(self.param_list[0])
        self.progress.Update(100, "Done.")
        self.progress.Destroy()


    def initDataSelect(self,event):
        self.data_selection_frame.update(self.cycle,self.date,self.tracks)
        self.cycle_mask = self.data_selection_frame.onSelectAll(event)
        self.cycle_mask = np.tile(self.cycle_mask,(len(self.norm_index),1)).T
        self.common_data.CYCLE_SEL = self.cycle_mask
        self.common_data.DATA_MASK_SEL = list()
        self.common_data.DATA_MASK_SEL.append(self.cycle_mask)
        
    def onSelectCycle(self,event):
        print('ok on test')  
        cycle_mask = self.data_selection_frame.getselectcyle()
        cycle_mask = np.tile(cycle_mask,(len(self.norm_index),1)).T
        self.common_data.CYCLE_SEL = cycle_mask
        self.update_plot()
#        self.onSelParam(event)
        
    def onSelectAll(self,event):
        print('ok on Select all')  
        cycle_mask = self.data_selection_frame.onSelectAll(event)
        cycle_mask = np.tile(cycle_mask,(len(self.norm_index),1)).T
        self.common_data.CYCLE_SEL = cycle_mask
        self.update_plot()
#        self.onSelParam(event)

    def get_env_var(self):
        altis_tmp_file = os.path.join(tempfile.gettempdir(),'altis.tmp')

        if os.path.isfile(altis_tmp_file):
            print('altis.tmp trouvé')
            with open(altis_tmp_file,'r') as f:
                try:
                    yaml_data = yaml.load(f)
                except:
                    yaml_data = yaml.load(f, Loader=yaml.FullLoader) # A revoir pour créer un vrai loader

            self.data_sel_config = dict()
            for k in yaml_data.keys():
                self.data_sel_config[k] = yaml_data[k]
            
        else:
            print('altis.tmp non trouvé')
            self.data_sel_config = dict()
            self.data_sel_config['data_type'] = ''
            self.data_sel_config['data_dir'] = ''
            self.data_sel_config['list_file'] = []
            self.data_sel_config['track'] = None
            self.data_sel_config['list_track'] = []
            self.data_sel_config['mission'] = ''
            self.data_sel_config['surf_type'] = ''
            self.data_sel_config['kml_file'] = None
            self.data_sel_config['normpass_flag'] = None
            self.data_sel_config['gdr_flag'] = None
            self.data_sel_config['normpass_file'] = ''
            self.data_sel_config['gdr_altis_flag'] = None
            self.data_sel_config['gdr_altis_file'] = ''
            with open(altis_tmp_file,'w') as f:
                yaml.dump(self.data_sel_config, f, default_flow_style=False)

    def set_env_var(self):
        altis_tmp_file = os.path.join(tempfile.gettempdir(),'altis.tmp')
#        pdb.set_trace()
        with open(altis_tmp_file,'w') as f:
            yaml.dump(self.data_sel_config, f, default_flow_style=False)



def main():
    app = wx.App(redirect = False)
    frame_main = Main_Window()
    frame_main.Show()
    app.MainLoop()

if __name__ == "__main__" :
    main()
