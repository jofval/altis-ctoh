#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Altimetric Time Series (AlTiS)
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

from track import Track

from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

#-------------------------------------------------------------------------------
# Help window
#-------------------------------------------------------------------------------
class Help_Window(wx.Frame):
    def __init__(self,):        
        super().__init__(None, title = "AlTiS : Help!")

        self.help_panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.TextCtrl(self.help_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH)
        
        help_file = pkg_resources.resource_filename('altis', '../HELP.txt')
        with open(help_file, 'r') as file:
            wx.TextCtrl.SetValue(st1, file.read())
        hbox2.Add(st1, proportion=1, flag=wx.EXPAND)
        vbox.Add(hbox2, proportion=1, flag=wx.LEFT|wx.RIGHT| wx.BOTTOM | wx.EXPAND, border=10)
        
        self.help_panel.SetSizer(vbox)

        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((20,20))
        self.iconHelp = self.mk_iconbar("Help",wx.ART_HELP,"About AlTiS")
        self.toolbar.Realize()
        
        self.Bind(wx.EVT_MENU, self.OnAboutBox, self.iconHelp)
        
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('AlTiS : <version> <creation_date> CTOH') 


    def mk_iconbar(self,bt_txt,art_id,bt_lg_txt):
    
        ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (16,16))
        itemTool = self.toolbar.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool

    def OnAboutBox(self, event):
        
        logo_file = pkg_resources.resource_filename('altis', '../etc/altis_logo.png')        

        description = """AlTiS (Altimetric Time Series) software is a tool for 
        build altimetric time series from GDR (Geographic Data Reccord) files
         suppled by the French Observation Service CTOH 
         (Centre of Topography of the Oceans and the Hydrosphere)."""

        licence = """AlTiS (Altimetric Time Series) software is free software;
        you can redistribute it and/or modify it under the terms of the GNU General 
        Public License as published by the Free Software Foundation; either version 
        3 of the License, or (at your option) any later version.

        AlTiS is distributed in the hope that it will be useful,
        but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
        See the GNU General Public License for more details. You should have
        received a copy of the GNU General Public License along with AlTiS;
        if not, write to the Free Software Foundation, Inc., 59 Temple Place,
        Suite 330, Boston, MA  02111-1307  USA"""


        info = wx.adv.AboutDialogInfo()

        info.SetIcon(wx.Icon(logo_file, wx.BITMAP_TYPE_PNG))
        info.SetName('AlTiS')
        info.SetVersion('<version> <creation_date>')
        info.SetDescription(description)
        info.SetCopyright('2019 - CTOH')
        info.SetWebSite('http://ctoh.legos.obs-mip.fr/applications/land_surfaces/softwares/maps')
        info.SetLicence(licence)
        info.AddDeveloper('CTOH')
        info.AddDocWriter('CTOH')
        info.AddArtist('The CTOH crew')
        info.AddTranslator('CTOH')

        wx.adv.AboutBox(info)

        

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
# Load data window : This window is used to select several parameters in order to 
# dowload the altimetric data.
#-------------------------------------------------------------------------------
class Load_data_Window(wx.Dialog):
    def __init__(self,data_opt):    #,data_opt):
        super().__init__(None,title = "Data Selection")
        self.load_data_panel = wx.Panel(self)
        
        self.data_sel_config = data_opt
        
        sizer = wx.GridBagSizer(10, 15)
#        altis_gui,mission_config = self.__config_load__()
        self.__config_load__()
        # Mission
        label_mission = wx.StaticText(self.load_data_panel, label = "Mission")
        sizer.Add(label_mission, pos=(2, 0), flag=wx.LEFT,border=10)
        
        sampleLis = self.altis_gui['mission']
        self.sel_mission = wx.ComboBox(self.load_data_panel,value=self.altis_gui['mission'][0],choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(2, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND)
        
        # Surface Type       
        label_surf_type = wx.StaticText(self.load_data_panel, label= "Surface type")
        sizer.Add(label_surf_type, pos=(3, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        sampleList = self.altis_gui['surface_types']   #['Rivers and Lakes', 'Great Lakes', 'Ocean']
        self.sel_surf_type = wx.ComboBox(self.load_data_panel,value=self.altis_gui['surface_types'][0],choices=sampleList, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_surf_type, pos=(3, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND,border=5)
        
        # KML
#        label_kml = wx.StaticText(self.load_data_panel, label = "KML file")
#        sizer.Add(label_kml, pos=(4, 0), flag=wx.LEFT|wx.TOP, border=10)

        self.chkbox_kml = wx.CheckBox(self.load_data_panel, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(4, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(self.load_data_panel)
        sizer.Add(self.text_ctrl_kml_files, pos=(4, 1), span=(1, 19), flag=wx.TOP|wx.EXPAND,border=5)

        self.kml_filename = self.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(self.load_data_panel, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(4, 20), flag=wx.TOP|wx.RIGHT, border=5)
        self.btn_kml_file.Disable()
        
        # GDR files
        label_gdr = wx.StaticText(self.load_data_panel, label = "Data directory")
        sizer.Add(label_gdr, pos=(5, 0), flag=wx.LEFT|wx.TOP, border=10)

#-------------------------------------------------------------------------------
        self.data_sel_config['data_dir']
        self.text_ctrl_gdr_dir = wx.TextCtrl(self.load_data_panel)
        sizer.Add(self.text_ctrl_gdr_dir, pos=(5, 1), span=(1, 19), flag=wx.TOP|wx.EXPAND,border=5)
        self.gdr_dir = self.data_sel_config['data_dir']
        if not self.gdr_dir == '':
            self.text_ctrl_gdr_dir.SetValue(self.gdr_dir)
        
#-------------------------------------------------------------------------------
       
        self.btn_gdr_files = wx.Button(self.load_data_panel, label='Browse...')
        sizer.Add(self.btn_gdr_files, pos=(5, 20), flag=wx.TOP|wx.RIGHT, border=5)
        
#-------------------------------------------------------------------------------
        label_sel_track = wx.StaticText(self.load_data_panel, label = "Track")
        sizer.Add(label_sel_track, pos=(7, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        
        self.sel_track = wx.ComboBox(self.load_data_panel,value='',choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_track, pos=(7, 1), span=(1, 10), flag=wx.TOP|wx.EXPAND)
        self.sel_track.AppendItems(self.data_sel_config['list_track'])
        if len(self.data_sel_config['list_track']) > 0 :
            self.sel_track.SetValue(self.data_sel_config['list_track'][0])

        self.text_ctrl_nc_files = wx.TextCtrl(self.load_data_panel, style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH)
        sizer.Add(self.text_ctrl_nc_files, pos=(8, 1), span=(10, 19), flag=wx.TOP|wx.EXPAND,border=5)
#-------------------------------------------------------------------------------
        
        # Help button
        self.btn_help = wx.Button(self.load_data_panel, label='Help')
        sizer.Add(self.btn_help, pos=(20, 0), flag=wx.LEFT, border=10)

        # Ok button
        self.btn_ok = wx.Button(self.load_data_panel, label="Ok")
        sizer.Add(self.btn_ok, pos=(20, 19))

        # Ok cancel
        self.btn_cancel = wx.Button(self.load_data_panel, label="Cancel")
        sizer.Add(self.btn_cancel, pos=(20, 20), span=(1, 1),flag=wx.BOTTOM|wx.RIGHT, border=10)
        
        sizer.AddGrowableCol(2)

        self.load_data_panel.SetSizer(sizer)
        sizer.Fit(self)
        
        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.onKMLFile)
        self.btn_gdr_files.Bind(wx.EVT_BUTTON, self.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
        self.sel_track.Bind(wx.EVT_COMBOBOX, self.onLoadFiles)
        self.btn_ok.Bind(wx.EVT_BUTTON, self.onOk)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.onQuit)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.onCheckKML)

    def onCheckKML(self,event):
        if self.chkbox_kml.GetValue():
            self.text_ctrl_kml_files.Enable()
            self.btn_kml_file.Enable()
        else:
            self.text_ctrl_kml_files.Disable()
            self.btn_kml_file.Disable()
    
    
    def onKMLFile(self,event):
         fileDialog = wx.FileDialog(self, "Open KML file", wildcard="KML files (*.kml;*.KML)|*.kml;*.KML",
                       style = wx.FD_FILE_MUST_EXIST) 
         
         if fileDialog.ShowModal() == wx.ID_OK:
             self.kml_filename = fileDialog.GetPath()
             fileDialog.Destroy()
         #Ecriture du pathname et filename du fichier dans le TextCtrl
         self.text_ctrl_kml_files.SetValue(self.kml_filename)
        
    def onGDRFiles(self,event):

#-------------------------------------------------------------------------------
        dirDialog = wx.DirDialog (self, "Altimetric Data directory", "", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dirDialog.ShowModal() == wx.ID_OK:
             self.gdr_dir = dirDialog.GetPath()
             dirDialog.Destroy()

        self.text_ctrl_gdr_dir.SetValue(self.gdr_dir)

        # Selection des fichiers trace
        self.file_struct = __regex_file_parser__(self.sel_mission.GetValue(),self.gdr_dir)

        list_track = np.unique(self.file_struct['track'])
        self.sel_track.Clear()
        for track in list_track:
            self.sel_track.Append(str(track))

        self.sel_track.SetValue(str(list_track[0]))
        
    def onLoadFiles (self,event):
        
        if not hasattr(self,"file_struct"):
            self.file_struct = __regex_file_parser__(self.sel_mission.GetValue(),self.gdr_dir)
            
        track = int(self.sel_track.GetValue())
        mask_file = self.file_struct['track'] == track
        
        self.gdr_filename = self.file_struct['filename'][mask_file].tolist()

        self.text_ctrl_nc_files.SetValue('\n'.join(self.gdr_filename))
        
          
    def onQuit(self,event):
        self.Close()
        
    def onOk(self,event):
#         if (self.kml_filename == '') and (self.gdr_filename == ''):
#            wx.MessageBox('Please assign KML and Altimetric files', 'Error: Missing both KML and Altimetric files', wx.OK | wx.ICON_ERROR)
#            
#         elif (self.kml_filename == '') :
#            wx.MessageBox('Please assign a KML file', 'Error: Missing KML file', wx.OK | wx.ICON_ERROR)
            
        if len(self.gdr_filename) == 0 :
#            wx.MessageBox( 'Missing Altimetric files','Error', wx.OK | wx.ICON_ERROR)
            wx.MessageBox('Download completed', 'Info', wx.OK | wx.ICON_INFORMATION)
#         elif not (os.path.isfile(self.kml_filename)) :
#             wx.MessageBox('The KML file not found', 'Error: KML file not found', wx.OK | wx.ICON_ERROR)
             
#         else :
#            #Creates and fills the dictionary
        self.data_sel_config = dict()
        self.data_sel_config['data_dir'] = self.gdr_dir # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
        self.data_sel_config['list_file'] = self.gdr_filename # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
        self.data_sel_config['track'] = int(self.sel_track.GetValue())
        self.data_sel_config['list_track'] = self.sel_track.GetItems() #int(self.sel_track.GetValue())
        self.data_sel_config['mission'] = self.sel_mission.GetValue()
        self.data_sel_config['surf_type'] = self.sel_surf_type.GetValue()
        if self.chkbox_kml.GetValue():
            self.data_sel_config['kml_file'] = self.kml_filename
        else:
            self.data_sel_config['kml_file'] = None 
        self.Close()


    #safe_load ensures that the function is secured and not deprecated
    def __config_load__(self):
        config_file = pkg_resources.resource_filename('altis', '../etc/altis_config.yml')        
        with open(config_file) as f:
            try:
                self.altis_gui = yaml.safe_load(f)
            except:
                self.altis_gui = yaml.safe_load(f, Loader=yaml.FullLoader)

        config_file = pkg_resources.resource_filename('altis', '../etc/config_mission.yml')        
        with open(config_file) as f:
            try:
                self.mission_config = yaml.safe_load(f)
            except:
                self.mission_config = yaml.safe_load(f, Loader=yaml.FullLoader)
#        return altis_gui,mission_config
        


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
