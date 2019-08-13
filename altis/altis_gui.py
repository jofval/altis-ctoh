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
import wx.adv
import yaml
import os
#import sys
#import matplotlib
import numpy as np
import pandas as pd
import glob
import xarray as xr
import pkg_resources
import re
import pdb
import tempfile

from pandas.plotting import register_matplotlib_converters

from altis_utils.tools import __config_load__,update_progress,__regex_file_parser__

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy.feature import ShapelyFeature,NaturalEarthFeature,COLORS,GSHHSFeature

#try:
#from cartopy.io.img_tiles import StamenTerrain  
#else:
from cartopy.io.img_tiles import Stamen

from altis.track_structure import Track

from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from altis.download_data_gui_2 import Load_data_Window
from altis.help_gui import Help_Window

#-------------------------------------------------------------------------------
# Control window : This window display the list of the cycle dowloaded in memory. 
#    This window is used for the cycle selection.
#-------------------------------------------------------------------------------
class Ctrl_Window(wx.Frame):
    def __init__(self,parent): #,cycle,date):        
        super().__init__(None, title = "AlTiS : Dataset Selection",
            style=wx.STAY_ON_TOP | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX |\
             wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION ,\
             pos=(10,50),size=(200,700))

        self.parent = parent 

        panel = wx.Panel(self)
        self.create_toolbar() 
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.lctrlSelectCycle = wx.ListCtrl(panel, -1, style = wx.LC_REPORT) 
        self.lctrlSelectCycle.InsertColumn(0, 'Cycle', width = 50) 
        self.lctrlSelectCycle.InsertColumn(1, 'Date', wx.LIST_FORMAT_RIGHT, 100) 

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.parent.onSelectCycle, self.lctrlSelectCycle)
        
        box.Add(self.lctrlSelectCycle,1,wx.EXPAND) 
        panel.SetSizer(box) 
        panel.Fit() 
        self.Centre() 

    def update(self,cycle,date):
        self.lctrlSelectCycle.DeleteAllItems()
        index = 0
        for i in zip(cycle,date):
#            print(index,i, 'cycle: {:03d}'.format(i[0]))
#            index = self.list.InsertStringItem(index, '{:03d}'.format(i[0])) 
#            self.list.SetStringItem(index, 1,'{:04d}/{:02d}/{:02d}'.format(i[1][0],i[1][1],i[1][2]) ) 
            index = self.lctrlSelectCycle.InsertItem(index, '{:03d}'.format(i[0])) 
            self.lctrlSelectCycle.SetItem(index, 1,'{:04d}/{:02d}/{:02d}'.format(i[1][0],i[1][1],i[1][2]) ) 
            index += 1  

    def create_toolbar(self):
        """
        Create a toolbar
        """
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((16,16))
 
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
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('AlTiS...') 

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
        self.ax2 = self.figure.add_subplot(2,2,2,sharey=self.ax1)
        self.ax2.set_ylabel('Latitude (deg)')
        self.ax3 = self.figure.add_subplot(2,2,3,sharex=self.ax1)
        self.ax3.set_xlabel('Longitude (deg)')
        self.ax4 = self.figure.add_subplot(2,2,4,sharey=self.ax3)
        self.ax4.set_xlabel('Time (YYYY-MM)')
        self.canvas = FigureCanvas(self.plot_panel, -1, self.figure)
#        plt.ion()

#        self.ax3.autoscale(True,'y',True)
        
        self.mpl_toolbar = NavigationToolbar(self.canvas)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(self.mpl_toolbar, proportion=0, flag=wx.CENTER, border=8)
        vbox.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.CENTER, border=8)
        
#        vbox.Add(hbox1, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=10)
        self.plot_panel.SetSizer(vbox)


    def draw(self,tr,param,mask,cm,groundmap):
        lon = tr.data_val['lon_20hz'].where(mask)
        lat = tr.data_val['lat_20hz'].where(mask)
        param = tr.data_val[param].where(mask)
        time = tr.data_val['time_20hz'].where(mask)


        main_plot_title = 'Mission : '+self.data_sel_config['mission']+' | '+' track number : '+str(self.data_sel_config['track'])
                        
        self.figure.suptitle(main_plot_title, fontsize=16)
        
        register_matplotlib_converters()
        
        if groundmap == 'LandSat':
            altis_cfg = pkg_resources.resource_filename('altis', '../etc/altis_config.yml')
            with open(altis_cfg) as f:
                try:
                    yaml_data = yaml.safe_load(f)
                except:
                    yaml_data = yaml.safe_load(f, Loader=yaml.FullLoader) # A revoir pour créer un vrai loader
            url = yaml_data['wmts']['ground_map']['url']
            layer = yaml_data['wmts']['ground_map']['layer']
        elif groundmap == 'Open Street Map':
#            tiler = StamenTerrain()
            tiler = Stamen('terrain-background')
        elif groundmap == "Ground Map None":
            pass            

        RIVERS_10m =NaturalEarthFeature('physical','rivers_lake_centerlines', '10m', edgecolor=COLORS['water'],facecolor='none')
        coaste = GSHHSFeature(scale='auto', levels=[1,2,3,4],edgecolor="red")
        
        self.plt1 = self.ax1.scatter(lon,lat,c=param, marker='+',cmap=cm,transform=ccrs.PlateCarree())

        if groundmap == 'LandSat':
#            tiler = Stamen('terrain-background')
#            self.ax1.add_image(tiler,10)
            self.ax1.add_wmts(url,layer)
        elif groundmap == 'Open Street Map':
            self.ax1.add_image(tiler,6)
        elif groundmap == "Ground Map None":
            print(groundmap)
        
        self.ax1.add_feature(RIVERS_10m)
        self.ax1.add_feature(coaste)
        
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
        plt2 = self.ax2.scatter(param,lat,c=param, marker='+',cmap=cm ) 
        self.ax2.grid(True)
        plt3 = self.ax3.scatter(lon,param,c=param, marker='+',cmap=cm ) 
        self.ax3.grid(True)
        self.ax3.set_ylabel(param.attrs['long_name'])
        self.ax3.set_xlabel('Longitude (deg)')
        plt4 = self.ax4.scatter(np.array(time),param,c=param, marker='+',cmap=cm ) 
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

    def create_toolbar(self):
        """
        Create a toolbar
        """
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((20,20))
 
        self.iconQuit = self.mk_iconbar("Quit",wx.ART_QUIT,"Quit AlTiS")

        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()

        self.iconOpen = self.mk_iconbar("Open",wx.ART_FILE_OPEN,"Load Altimetry Dataset")
        self.toolbar.AddStretchableSpace()
        self.comboSelParam = wx.ComboBox( self.toolbar, value = "Select_parameter", choices = [],size=(200,30))
        self.toolbar.AddControl(self.comboSelParam, label="Select a paramter" )
        self.toolbar.AddStretchableSpace()
        self.iconSave = self.mk_iconbar("Save",wx.ART_FILE_SAVE,"Save Altimetry Dataset")
        
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()

        self.btnSelectData = wx.Button(self.toolbar, label="Dataset Selection")
        self.toolbar.AddControl(self.btnSelectData)
        self.toolbar.AddStretchableSpace()
        self.iconUndo = self.mk_iconbar("Undo",wx.ART_UNDO,"Undo")
        self.iconRedo = self.mk_iconbar("Redo",wx.ART_REDO,"Redo")

        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()

        self.comboColorMap = wx.ComboBox( self.toolbar, value = "jet", choices = ["jet","hsv","ocean","terrain","coolwarm","RdBu","viridis"])
        self.toolbar.AddControl(self.comboColorMap, label="Color palet" )
        self.comboGroundMap = wx.ComboBox( self.toolbar, value = "Ground Map None", choices = ["Ground Map None","LandSat","Open Street Map"])
        self.toolbar.AddControl(self.comboGroundMap, label="Ground Map")

        self.toolbar.AddStretchableSpace()

        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()

        self.btnHoocking = wx.Button(self.toolbar, label="Hoocking correction")
        self.toolbar.AddControl(self.btnHoocking )
        self.btnColAnalysis = wx.Button(self.toolbar, label="Collinear Analysis")
        self.toolbar.AddControl(self.btnColAnalysis)
        self.btnTimeSeries = wx.Button(self.toolbar, label="Time Series")
        self.toolbar.AddControl(self.btnTimeSeries)

        self.toolbar.AddStretchableSpace()

        self.toolbar.AddSeparator()  


        self.toolbar.AddStretchableSpace()
        self.iconHelp = self.mk_iconbar("Help",wx.ART_HELP,"Help on AlTiS")

        self.toolbar.Realize()


        self.Bind(wx.EVT_MENU, self.onQuit,         self.iconQuit)
        self.Bind(wx.EVT_MENU, self.onOpen,         self.iconOpen)
        self.Bind(wx.EVT_COMBOBOX, self.onSelParam,     self.comboSelParam)
        self.Bind(wx.EVT_MENU, self.onSave,         self.iconSave)
        self.Bind(wx.EVT_MENU, self.onSelectData,   self.btnSelectData)
        self.Bind(wx.EVT_MENU, self.onHoocking,     self.btnHoocking)
        self.Bind(wx.EVT_MENU, self.onColAnalysis,  self.btnColAnalysis)
        self.Bind(wx.EVT_MENU, self.onTimeSeries,   self.btnTimeSeries)
        self.Bind(wx.EVT_MENU, self.onUndo,         self.iconUndo)
        self.Bind(wx.EVT_MENU, self.onRedo,         self.iconRedo)
        self.Bind(wx.EVT_COMBOBOX, self.onColorMap,     self.comboColorMap)
        self.Bind(wx.EVT_COMBOBOX, self.onGroundMap,    self.comboGroundMap)
        self.Bind(wx.EVT_MENU, self.onHelp,         self.iconHelp)


    def mk_iconbar(self,bt_txt,art_id,bt_lg_txt):
    
        ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (20,20))
        itemTool = self.toolbar.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool

    def onHoocking(self,event): pass
    def onColAnalysis(self,event): pass
    def onTimeSeries(self,event): pass

    def onColorMap(self,event):
        if hasattr(self,"plt1"):
            self.ax1_zoom = {'x':self.ax1.get_xlim(),'y':self.ax1.get_ylim()}
        else:
            self.ax1_zoom = {'x':None,'y':None}
        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        self.param = self.comboSelParam.GetValue()
        print(self.cm)
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.draw(self.tr,self.param,self.data_mask,self.cm,self.groundmap)
        self.ax1.set_xlim(self.ax1_zoom['x'])
        self.ax1.set_ylim(self.ax1_zoom['y'])
        self.canvas.draw()
        print('done')


    def onGroundMap(self,event):
        if hasattr(self,"plt1"):
            self.ax1_zoom = {'x':self.ax1.get_xlim(),'y':self.ax1.get_ylim()}
        else:
            self.ax1_zoom = {'x':None,'y':None}
        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        self.param = self.comboSelParam.GetValue()
        print(self.groundmap)
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.draw(self.tr,self.param,self.data_mask,self.cm,self.groundmap)
        self.ax1.set_xlim(self.ax1_zoom['x'])
        self.ax1.set_ylim(self.ax1_zoom['y'])
        self.canvas.draw()
        print('done')
    

    def onSelectData(self,event):
        pass
        
    def onSave(self,event):
        if hasattr(self,"tr"):
            directory = os.getcwd()
            message = 'Save the dataset?'
            with  wx.DirDialog(None, message='Choose dataset a directory', 
                defaultPath=directory, style=wx.DD_DEFAULT_STYLE) as dataset_dir:
            
                if dataset_dir.ShowModal() == wx.ID_OK:
                    self.tr.save_norm_data(dataset_dir.GetPath())
        else:
            message = 'No dataset !'
            with wx.MessageDialog(None, message=message, caption='Warning',
                style=wx.OK | wx.OK_DEFAULT | wx.ICON_ERROR) as save_dataset_dlg:
            
                if save_dataset_dlg.ShowModal() == wx.ID_OK:
                    print('No dataset!')
            
            
    def onRefresh(self,event):
        pass
    def onQuit(self,event):
        self.data_selection_frame.Close()
        self.Close()
 
    def onUndo(self,event):
        pass
 
    def onRedo(self,event):
        pass
 
    def onHelp(self,event): 
        help=Help_Window()
        help.Show()

    def onSelParam(self,event):
        if hasattr(self,"plt1"):
            self.ax1_zoom = {'x':self.ax1.get_xlim(),'y':self.ax1.get_ylim()}
        else:
            self.ax1_zoom = {'x':None,'y':None}
        self.cm = self.comboColorMap.GetValue()
        self.groundmap = self.comboGroundMap.GetValue()
        self.param = self.comboSelParam.GetValue()
        print('Drawing... ',self.param,self.cm,self.groundmap)
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        self.draw(self.tr,self.param,self.data_mask,self.cm,self.groundmap)
        self.ax1.set_xlim(self.ax1_zoom['x'])
        self.ax1.set_ylim(self.ax1_zoom['y'])
        self.canvas.draw()
    
    def onOpen(self,event):
    
        self.get_env_var()
    
        with Load_data_Window(self.data_sel_config) as load_data_args:
            load_data_args.Center()
            load_data_args.Show()
            if load_data_args.ShowModal() == wx.ID_OK:
                print("ShowModal")
#            elif load_data_args.ShowModal() == wx.ID_CANCEL:
#                print('Canceled.')
#                load_data_args.Close()
#                return -1
                
        self.data_sel_config = load_data_args.data_sel_config

        self.progress = wx.ProgressDialog("Opening dataset", "please wait", maximum=100, parent=self, style=wx.PD_SMOOTH|wx.PD_AUTO_HIDE)
        self.progress.Update(10, "Data loading...")
        
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
        
        self.tr=Track(mission,surf_type,data_dir,file_list,kml_file)
        
        self.progress.Update(50, "Data reading...")

        self.param_list=list(self.tr.data_val.keys())
        self.param_list.sort()
        
        param_name='time_20hz'
        data = self.tr.data_val[param_name]
        self.cycle = np.array(data.coords['cycle'])
        self.norm_index = np.array(data.coords['norm_index'])
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
            
        
        
        self.progress.Update(50, "Data conditionning...")

        self.initDataSelect(event)
        if hasattr(self,"plt1"):
            delattr(self,'plt1')
                    
        self.comboSelParam.Clear()
        for param in self.param_list:
            self.comboSelParam.Append(param)

        self.comboSelParam.SetValue(self.param_list[0])
        self.progress.Update(100, "Done.")
        self.progress.Destroy()



    def initDataSelect(self,event):
        self.data_selection_frame.update(self.cycle,self.date)
        self.cycle_mask = self.data_selection_frame.onSelectAll(event)
        self.cell_mask = np.tile(self.cycle_mask,(len(self.norm_index),1)).T
        self.data_mask = self.cell_mask
        
    def onSelectCycle(self,event):
        print('ok on test')  
        cycle_mask = self.data_selection_frame.getselectcyle()
        cycle_mask = np.tile(cycle_mask,(len(self.norm_index),1)).T
        print('cycle_mask',cycle_mask.shape,cycle_mask)
        self.data_mask = self.cell_mask & cycle_mask
        print('self.data_mask',self.data_mask)
        self.onSelParam(event)
        
    def onSelectAll(self,event):
        print('ok on Select all')  
        cycle_mask = self.data_selection_frame.onSelectAll(event)
        cycle_mask = np.tile(cycle_mask,(len(self.norm_index),1)).T
        print('cycle_mask',cycle_mask.shape,cycle_mask)
        self.data_mask = self.cell_mask & cycle_mask
        print('self.data_mask',self.data_mask)
        self.onSelParam(event)

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
            self.data_sel_config['data_dir'] = yaml_data['data_dir']
            self.data_sel_config['list_file'] = yaml_data['list_file']
            self.data_sel_config['track'] = yaml_data['track']
            self.data_sel_config['list_track'] = yaml_data['list_track']
            self.data_sel_config['mission'] = yaml_data['mission']
            self.data_sel_config['surf_type'] = yaml_data['surf_type']
            self.data_sel_config['kml_file'] = yaml_data['kml_file']
            
        else:
            print('altis.tmp non trouvé')
            self.data_sel_config = dict()
            self.data_sel_config['data_dir'] = ''
            self.data_sel_config['list_file'] = []
            self.data_sel_config['track'] = None
            self.data_sel_config['list_track'] = []
            self.data_sel_config['mission'] = ''
            self.data_sel_config['surf_type'] = ''
            self.data_sel_config['kml_file'] = None
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
