#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Class of Altimetric Time Series (AlTiS) Software
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

from altis_utils.tools import __config_load__,update_progress,__regex_file_parser__

class GDR_Panel ( wx.Panel ):

    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent )

        sizer = wx.GridBagSizer(10, 20)
#        altis_gui,mission_config = self.__config_load__()
        self.radbox_panel = Radbox_Dataset(self)
        sizer.Add(self.radbox_panel, pos=(1, 1), span=(1, 15), flag=wx.TOP|wx.LEFT|wx.EXPAND,border=10)


        self.Parent.__config_load__()
        # Mission
        label_mission = wx.StaticText(self, label = "Mission")
        sizer.Add(label_mission, pos=(2, 0), flag=wx.LEFT,border=10)
        
        sampleLis = self.Parent.altis_gui['mission']
        self.sel_mission = wx.ComboBox(self,value=self.Parent.altis_gui['mission'][0],choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(2, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND)
        
        # Surface Type       
        label_surf_type = wx.StaticText(self, label= "Surface type")
        sizer.Add(label_surf_type, pos=(3, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        sampleList = self.Parent.altis_gui['surface_types']   #['Rivers and Lakes', 'Great Lakes', 'Ocean']
        self.sel_surf_type = wx.ComboBox(self,value=self.Parent.altis_gui['surface_types'][0],choices=sampleList, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_surf_type, pos=(3, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND,border=5)
        
        # KML
#        label_kml = wx.StaticText(self, label = "KML file")
#        sizer.Add(label_kml, pos=(4, 0), flag=wx.LEFT|wx.TOP, border=10)

        self.chkbox_kml = wx.CheckBox(self, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(4, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_kml_files, pos=(4, 1), span=(1, 19), flag=wx.TOP|wx.EXPAND,border=5)

        self.kml_filename = self.Parent.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(self, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(4, 20), flag=wx.TOP|wx.RIGHT, border=5)
        self.btn_kml_file.Disable()
        
        # GDR files
        label_gdr = wx.StaticText(self, label = "Data directory")
        sizer.Add(label_gdr, pos=(5, 0), flag=wx.LEFT|wx.TOP, border=10)

#-------------------------------------------------------------------------------
        self.Parent.data_sel_config['data_dir']
        self.text_ctrl_gdr_dir = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_gdr_dir, pos=(5, 1), span=(1, 19), flag=wx.TOP|wx.EXPAND,border=5)
        self.gdr_dir = self.Parent.data_sel_config['data_dir']
        if not self.gdr_dir == '':
            self.text_ctrl_gdr_dir.SetValue(self.gdr_dir)
        
#-------------------------------------------------------------------------------
       
        self.btn_gdr_files = wx.Button(self, label='Browse...')
        sizer.Add(self.btn_gdr_files, pos=(5, 20), flag=wx.TOP|wx.RIGHT, border=5)
        
#-------------------------------------------------------------------------------
        label_sel_track = wx.StaticText(self, label = "Track")
        sizer.Add(label_sel_track, pos=(7, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        
        self.sel_track = wx.ComboBox(self,value='',choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_track, pos=(7, 1), span=(1, 10), flag=wx.TOP|wx.EXPAND)
        self.sel_track.AppendItems(self.Parent.data_sel_config['list_track'])
        if len(self.Parent.data_sel_config['list_track']) > 0 :
            self.sel_track.SetValue(self.Parent.data_sel_config['list_track'][0])

        self.text_ctrl_nc_files = wx.TextCtrl(self, style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH)
        sizer.Add(self.text_ctrl_nc_files, pos=(8, 1), span=(10, 19), flag=wx.TOP|wx.EXPAND,border=5)
#-------------------------------------------------------------------------------
        
        # Help button
        self.btn_help = wx.Button(self, label='Help')
        sizer.Add(self.btn_help, pos=(20, 0), flag=wx.LEFT, border=10)

        # Ok button
        self.btn_ok = wx.Button(self, label="Ok")
        sizer.Add(self.btn_ok, pos=(20, 19))

        # Ok cancel
        self.btn_cancel = wx.Button(self, label="Cancel")
        sizer.Add(self.btn_cancel, pos=(20, 20), span=(1, 1),flag=wx.BOTTOM|wx.RIGHT, border=10)
        
        sizer.AddGrowableCol(2)

        self.SetSizer(sizer)
        sizer.Fit(self)
        
        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.Parent.onKMLFile)
        self.btn_gdr_files.Bind(wx.EVT_BUTTON, self.Parent.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
        self.sel_track.Bind(wx.EVT_COMBOBOX, self.Parent.onLoadFiles)
        self.btn_ok.Bind(wx.EVT_BUTTON, self.Parent.onOk)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.Parent.onQuit)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.Parent.onCheckKML)
        
        
        
class Normpass_Panel(wx.Panel):
    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent )


        sizer = wx.GridBagSizer(10, 20)
#        altis_gui,mission_config = self.__config_load__()

        self.radbox_panel = Radbox_Dataset(self)
        sizer.Add(self.radbox_panel, pos=(1, 1), span=(1, 15), flag=wx.TOP|wx.LEFT|wx.EXPAND,border=10)

        self.Parent.__config_load__()
        # Mission
        label_mission = wx.StaticText(self, label = "Mission")
        sizer.Add(label_mission, pos=(2, 0), flag=wx.LEFT,border=10)
        
        sampleLis = self.Parent.altis_gui['mission']
        self.sel_mission = wx.ComboBox(self,value=self.Parent.altis_gui['mission'][0],choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(2, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND)
        

        self.chkbox_kml = wx.CheckBox(self, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(4, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_kml_files, pos=(4, 1), span=(1, 19), flag=wx.TOP|wx.EXPAND,border=5)

        self.kml_filename = self.Parent.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(self, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(4, 20), flag=wx.TOP|wx.RIGHT, border=5)
        self.btn_kml_file.Disable()
        
        # GDR files
        label_gdr = wx.StaticText(self, label = "Normpass file")
        sizer.Add(label_gdr, pos=(5, 0), flag=wx.LEFT|wx.TOP, border=10)

#-------------------------------------------------------------------------------
        
        # Help button
        self.btn_help = wx.Button(self, label='Help')
        sizer.Add(self.btn_help, pos=(20, 0), flag=wx.LEFT, border=10)

        # Ok button
        self.btn_ok = wx.Button(self, label="Ok")
        sizer.Add(self.btn_ok, pos=(20, 19))

        # Ok cancel
        self.btn_cancel = wx.Button(self, label="Cancel")
        sizer.Add(self.btn_cancel, pos=(20, 20), span=(1, 1),flag=wx.BOTTOM|wx.RIGHT, border=10)
        
        sizer.AddGrowableCol(2)

        self.SetSizer(sizer)
        sizer.Fit(self)
        
        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.Parent.onKMLFile)
#        self.btn_gdr_files.Bind(wx.EVT_BUTTON, self.Parent.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
        self.btn_ok.Bind(wx.EVT_BUTTON, self.Parent.onOk)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.Parent.onQuit)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.Parent.onCheckKML)

class Radbox_Dataset(wx.Panel):
    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent )
        
        lblList = ['Normpass          ', 'GDR (from CTOH)'] 
        self.radbox_datafile = wx.RadioBox(self, label="Kind of dataset files",choices = lblList,style=wx.RA_SPECIFY_COLS)
#        sizer.Add(self.radbox_datafile, pos=(1, 1), span=(1, 15), flag=wx.TOP|wx.LEFT|wx.EXPAND,border=10)

        self.radbox_datafile.Bind(wx.EVT_RADIOBOX,self.Parent.Parent.onClickdataset)


#-------------------------------------------------------------------------------
# Load data window : This window is used to select several parameters in order to 
# dowload the altimetric data.
#-------------------------------------------------------------------------------

class Load_data_Window(wx.Dialog):
    def __init__(self,data_opt):    #,data_opt):
        super().__init__(None,title = "Data Selection")
        self.load_data_panel = wx.Panel(self)

        self.data_sel_config = data_opt
        
        sizer = wx.GridBagSizer(10, 20)
#        altis_gui,mission_config = self.__config_load__()
#        lblList = ['Normpass          ', 'GDR (from CTOH)'] 
#        self.radbox_datafile = wx.RadioBox(self, label="Kind of dataset files",choices = lblList,style=wx.RA_SPECIFY_COLS)
#        sizer.Add(self.radbox_datafile, pos=(1, 1), span=(1, 15), flag=wx.TOP|wx.LEFT|wx.EXPAND,border=10)

#        self.radbox_datafile.SetSelection(0)

       # Add gdr panel
        self.gdr_panel = GDR_Panel(self)
        sizer.Add(self.gdr_panel, pos=(1, 0), span=(0, 20), flag=wx.EXPAND|wx.ALL, border=10)
        
        self.normpass_panel = Normpass_Panel(self)
        sizer.Add(self.normpass_panel, pos=(2, 0), span=(0, 20), flag=wx.EXPAND|wx.ALL, border=10)

         # Hide nb and logout button
        self.gdr_panel.Hide()
#        self.normpass_panel.Hide()

        self.load_data_panel.SetSizer(sizer)
        sizer.Fit(self)
        self.Show()
        
#        self.radbox_datafile.Bind(wx.EVT_RADIOBOX,self.onClickdataset)

    def onClickdataset(self,event):
        if self.gdr_panel.IsShown():
            self.gdr_panel.Hide()
#            self.radbox_datafile.Show()
            self.normpass_panel.Show()
            self.Layout()
        else:
            self.normpass_panel.Hide()
#            self.radbox_datafile.Show()
            self.gdr_panel.Show()
            self.Layout()
            


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
        self.file_struct = __regex_file_parser__(self.sel_mission.GetValue(),self.gdr_dir,None)

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
        print('toto')
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

