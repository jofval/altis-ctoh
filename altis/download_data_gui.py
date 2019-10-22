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

        sizer = wx.GridBagSizer(20, 15)
        y_pos = 0
#        altis_gui,mission_config = self.__config_load__()
        self.radbox_panel = Radbox_Dataset(self)
        sizer.Add(self.radbox_panel, pos=(y_pos, 0), span=(1, 19), flag=wx.TOP|wx.LEFT|wx.EXPAND,border=10)   #|wx.EXPAND,border=10)

        self.Parent.__config_load__()
        # Mission
        label_mission = wx.StaticText(self, label = "Mission")
        sizer.Add(label_mission, pos=(y_pos+1, 0), flag=wx.TOP|wx.LEFT,border=10)
        
        sampleLis = self.Parent.altis_gui['mission']
        mission = self.Parent.data_sel_config['mission'] #None
        if not mission is None:
            last_mission_sel = mission
        else:
            last_mission_sel = self.Parent.altis_gui['mission'][0]
        self.sel_mission = wx.ComboBox(self,value=last_mission_sel,choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(y_pos+1, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND,border=10)
        
        # Surface Type       
        label_surf_type = wx.StaticText(self, label= "Surface type")
        sizer.Add(label_surf_type, pos=(y_pos+2, 0), span=(1, 1), flag=wx.LEFT|wx.TOP, border=10)
        
        sampleList = self.Parent.altis_gui['surface_types']   #['Rivers and Lakes', 'Great Lakes', 'Ocean']
        self.sel_surf_type = wx.ComboBox(self,value=self.Parent.altis_gui['surface_types'][0],choices=sampleList, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_surf_type, pos=(y_pos+2, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND,border=10)
        
        self.chkbox_kml = wx.CheckBox(self, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(y_pos+3, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_kml_files, pos=(y_pos+3, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.kml_filename = self.Parent.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(self, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(y_pos+3, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_kml_file.Disable()
        
        # GDR files
        label_gdr = wx.StaticText(self, label = "Data directory")
        sizer.Add(label_gdr, pos=(y_pos+4, 0), flag=wx.LEFT|wx.TOP, border=10)

#-------------------------------------------------------------------------------
        self.Parent.data_sel_config['data_dir']
        self.text_ctrl_gdr_dir = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_gdr_dir, pos=(y_pos+4, 1), span=(1, 8), flag=wx.TOP|wx.EXPAND,border=10)
        self.gdr_dir = self.Parent.data_sel_config['data_dir']
        if not self.gdr_dir == '':
            self.text_ctrl_gdr_dir.SetValue(self.gdr_dir)
        
#-------------------------------------------------------------------------------
       
        self.btn_gdr_files = wx.Button(self, label='Browse...')
        sizer.Add(self.btn_gdr_files, pos=(y_pos+4, 10), flag=wx.TOP|wx.RIGHT, border=10)
        
#-------------------------------------------------------------------------------
        label_sel_track = wx.StaticText(self, label = "Track")
        sizer.Add(label_sel_track, pos=(y_pos+5, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        
        self.sel_track = wx.ComboBox(self,value='',choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_track, pos=(y_pos+5, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND,border=10)
        self.sel_track.AppendItems(self.Parent.data_sel_config['list_track'])
        if len(self.Parent.data_sel_config['list_track']) > 0 :
            self.sel_track.SetValue(self.Parent.data_sel_config['list_track'][0])

        self.text_ctrl_nc_files = wx.TextCtrl(self, style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH)
        sizer.Add(self.text_ctrl_nc_files, pos=(y_pos+6, 1), span=(10, 13), flag=wx.TOP|wx.EXPAND,border=10)
#-------------------------------------------------------------------------------
        self.bottom_bar_panel=Bottom_Bar(self)
        sizer.Add(self.bottom_bar_panel, pos=(y_pos+17, 0), span=(1, 15) ,border=10)
        
        
        sizer.AddGrowableCol(2)

        self.SetSizer(sizer)
        sizer.Fit(self)
        
        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.Parent.onKMLFile)
        self.btn_gdr_files.Bind(wx.EVT_BUTTON, self.Parent.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
        self.sel_track.Bind(wx.EVT_COMBOBOX, self.Parent.onLoadFiles)
#        self.btn_ok.Bind(wx.EVT_BUTTON, self.Parent.onOk)
#        self.btn_cancel.Bind(wx.EVT_BUTTON, self.Parent.onQuit)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.Parent.onCheckKML)
        
        
        
class Normpass_Panel(wx.Panel):
    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent )


        sizer = wx.GridBagSizer(20, 15)
#        altis_gui,mission_config = self.__config_load__()
        y_pos = -1
        self.radbox_panel = Radbox_Dataset(self)
        sizer.Add(self.radbox_panel, pos=(y_pos+1, 0), span=(1, 9), flag=wx.TOP|wx.LEFT|wx.EXPAND,border=10)


        self.Parent.__config_load__()
        # Mission
        label_mission = wx.StaticText(self, label = "Mission")
        sizer.Add(label_mission, pos=(y_pos+2, 0), flag=wx.LEFT,border=10)
        
        sampleLis = self.Parent.altis_gui['mission']
        mission = self.Parent.data_sel_config['mission'] #None
        if not mission is None:
            last_mission_sel = mission
        else:
            last_mission_sel = self.Parent.altis_gui['mission'][0]
        self.sel_mission = wx.ComboBox(self,value=last_mission_sel,choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(y_pos+2, 1), span=(1, 5), flag=wx.LEFT|wx.EXPAND,border=10)
        

        self.chkbox_kml = wx.CheckBox(self, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(y_pos+3, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_kml_files, pos=(y_pos+3, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.kml_filename = self.Parent.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(self, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(y_pos+3, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_kml_file.Disable()
        
        # NORMPASS files
        label_gdr = wx.StaticText(self, label = "Normpass file")
        sizer.Add(label_gdr, pos=(y_pos+4, 0), flag=wx.LEFT|wx.TOP, border=10)

        self.text_ctrl_normpass_files = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_normpass_files, pos=(y_pos+4, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)
 
        self.normpass_filename = self.Parent.data_sel_config['normpass_file'] #None
        if not self.normpass_filename is None:
            self.text_ctrl_normpass_files.SetValue(self.normpass_filename)

        self.btn_normpass_file = wx.Button(self, label='Browse...') 
        sizer.Add(self.btn_normpass_file, pos=(y_pos+4, 10), flag=wx.TOP|wx.RIGHT, border=10)
        

#-------------------------------------------------------------------------------
        self.bottom_bar_panel=Bottom_Bar(self)
        sizer.Add(self.bottom_bar_panel, pos=(y_pos+19, 0), span=(1, 9) ,border=10)
        
        sizer.AddGrowableCol(2)

        self.SetSizer(sizer)
        sizer.Fit(self)
        
        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.Parent.onKMLFile)
        self.btn_normpass_file.Bind(wx.EVT_BUTTON, self.Parent.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
#        self.btn_ok.Bind(wx.EVT_BUTTON, self.Parent.onOk)
#        self.btn_cancel.Bind(wx.EVT_BUTTON, self.Parent.onQuit)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.Parent.onCheckKML)


class GDR_Altis_Panel(wx.Panel):
    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent )


        sizer = wx.GridBagSizer(20, 15)
#        altis_gui,mission_config = self.__config_load__()
        y_pos = -1
        self.radbox_panel = Radbox_Dataset(self)
        sizer.Add(self.radbox_panel, pos=(y_pos+1, 0), span=(1, 9), flag=wx.TOP|wx.LEFT|wx.EXPAND,border=10)

#        line = wx.StaticLine(self)
#        sizer.Add(line, pos=(2, 0), span=(2, 20),flag=wx.EXPAND|wx.BOTTOM, border=10)


        self.Parent.__config_load__()
        # Mission
        label_mission = wx.StaticText(self, label = "Mission")
        sizer.Add(label_mission, pos=(y_pos+3, 0), flag=wx.LEFT,border=10)
        
        sampleLis = self.Parent.altis_gui['mission']
        
        mission = self.Parent.data_sel_config['mission'] #None
        if not mission is None:
            last_mission_sel = mission
        else:
            last_mission_sel = self.Parent.altis_gui['mission'][0]
        
        self.sel_mission = wx.ComboBox(self,value=last_mission_sel,choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(y_pos+3, 1), span=(1, 5), flag=wx.LEFT|wx.EXPAND)
        

        self.chkbox_kml = wx.CheckBox(self, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(y_pos+4, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_kml_files, pos=(y_pos+4, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.kml_filename = self.Parent.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(self, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(y_pos+4, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_kml_file.Disable()
        
        # NORMPASS files
        label_gdr = wx.StaticText(self, label = "AlTiS GDR file")
        sizer.Add(label_gdr, pos=(y_pos+5, 0), flag=wx.LEFT|wx.TOP, border=10)

        self.text_ctrl_gdr_altis_files = wx.TextCtrl(self)
        sizer.Add(self.text_ctrl_gdr_altis_files, pos=(y_pos+5, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.gdr_altis_filename = self.Parent.data_sel_config['gdr_altis_file'] #None
        if not self.gdr_altis_filename is None:
            self.text_ctrl_gdr_altis_files.SetValue(self.gdr_altis_filename)

        self.btn_normpass_file = wx.Button(self, label='Browse...') 
        sizer.Add(self.btn_normpass_file, pos=(y_pos+5, 10), flag=wx.TOP|wx.RIGHT, border=10)
        
        
        self.bottom_bar_panel=Bottom_Bar(self)
        sizer.Add(self.bottom_bar_panel, pos=(y_pos+19, 0), span=(0, 9) ,border=10)
        
        sizer.AddGrowableCol(2)

        self.SetSizer(sizer)
        sizer.Fit(self)
        
        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.Parent.onKMLFile)
        self.btn_normpass_file.Bind(wx.EVT_BUTTON, self.Parent.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
#        self.btn_ok.Bind(wx.EVT_BUTTON, self.Parent.onOk)
#        self.btn_cancel.Bind(wx.EVT_BUTTON, self.Parent.onQuit)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.Parent.onCheckKML)



class Bottom_Bar(wx.Panel):
    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent )
#-------------------------------------------------------------------------------
#        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        
        gs = wx.GridBagSizer(2, 15)
        # Help button
        self.btn_help = wx.Button(self, wx.ID_HELP, label='Help')

        # Ok button
        self.btn_ok = wx.Button(self, wx.ID_OK, label="Ok")

        # Ok cancel
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Cancel")

        line = wx.StaticLine(self)
        gs.Add(line, pos=(0, 0), span=(1, 15),flag=wx.EXPAND|wx.BOTTOM, border=10)
        gs.Add(self.btn_help, pos=(1, 0),flag=wx.EXPAND, border=10)
        gs.Add(self.btn_ok, pos=(1, 14),flag=wx.EXPAND, border=10)
        gs.Add(self.btn_cancel, pos=(1, 15),flag=wx.EXPAND, border=10)
        
        self.SetSizer(gs)
        gs.Fit(self)

        #Binds functions to appropriate buttons
        self.btn_ok.Bind(wx.EVT_BUTTON, self.Parent.Parent.onOk)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.Parent.Parent.onQuit)


class Radbox_Dataset(wx.Panel):
    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent )
        
        lblList = ['Normpass        ', 'AlTiS GDR           ', 'GDR Tracks        '] 
        self.radbox_datafile = wx.RadioBox(self, label="Kind of dataset",choices = lblList,style=wx.RA_SPECIFY_COLS)

        self.radbox_datafile.Bind(wx.EVT_RADIOBOX,self.Parent.Parent.onClickdataset)


#-------------------------------------------------------------------------------
# Load data window : This window is used to select several parameters in order to 
# dowload the altimetric data.
#-------------------------------------------------------------------------------

class Load_data_Window(wx.Dialog):
    def __init__(self,data_opt):    #,data_opt):
        super().__init__(None,title = "Data Selection") #,size = wx.GetClientSize()) #wx.DisplaySize())
        self.load_data_panel = wx.Panel(self)

        self.data_sel_config = data_opt
        
        sizer = wx.GridBagSizer(20, 10)

       # Add gdr panel
        self.gdr_panel = GDR_Panel(self)
        sizer.Add(self.gdr_panel, pos=(1, 0), flag=wx.EXPAND|wx.ALL, border=10)

         # Hide nb and logout button
        self.gdr_panel.Hide()

       # Add gdr panel
        self.gdr_altis_panel = GDR_Altis_Panel(self)
        sizer.Add(self.gdr_altis_panel, pos=(2, 0), flag=wx.EXPAND|wx.ALL, border=10)

         # Hide nb and logout button
        self.gdr_altis_panel.Hide()
        
        self.normpass_panel = Normpass_Panel(self)
        sizer.Add(self.normpass_panel, pos=(0, 0), flag=wx.EXPAND|wx.ALL, border=10)


        self.load_data_panel.SetSizer(sizer)
        sizer.Fit(self)
        self.Show()
        
    def onClickdataset(self,event):
        if self.normpass_panel.IsShown():
            if self.normpass_panel.radbox_panel.radbox_datafile.GetSelection() == 0 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.normpass_panel.Show()
                self.gdr_altis_panel.Hide()
                self.gdr_panel.Hide()
                self.Layout()
            elif self.normpass_panel.radbox_panel.radbox_datafile.GetSelection() == 1 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.normpass_panel.Hide()
                self.gdr_altis_panel.Show()
                self.gdr_panel.Hide()
                self.Layout()
            elif self.normpass_panel.radbox_panel.radbox_datafile.GetSelection() == 2 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.normpass_panel.Hide()
                self.gdr_altis_panel.Hide()
                self.gdr_panel.Show()
                self.Layout()
            
        elif self.gdr_altis_panel.IsShown():
            if self.gdr_altis_panel.radbox_panel.radbox_datafile.GetSelection() == 0 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.normpass_panel.Show()
                self.gdr_altis_panel.Hide()
                self.gdr_panel.Hide()
                self.Layout()
            elif self.gdr_altis_panel.radbox_panel.radbox_datafile.GetSelection() == 1 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.normpass_panel.Hide()
                self.gdr_altis_panel.Show()
                self.gdr_panel.Hide()
                self.Layout()
            elif self.gdr_altis_panel.radbox_panel.radbox_datafile.GetSelection() == 2 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.normpass_panel.Hide()
                self.gdr_altis_panel.Hide()
                self.gdr_panel.Show()
                self.Layout()

        elif self.gdr_panel.IsShown():
            if self.gdr_panel.radbox_panel.radbox_datafile.GetSelection() == 0 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(0)
                self.normpass_panel.Show()
                self.gdr_altis_panel.Hide()
                self.gdr_panel.Hide()
                self.Layout()
            elif self.gdr_panel.radbox_panel.radbox_datafile.GetSelection() == 1 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(1)
                self.normpass_panel.Hide()
                self.gdr_altis_panel.Show()
                self.gdr_panel.Hide()
                self.Layout()
            elif self.gdr_panel.radbox_panel.radbox_datafile.GetSelection() == 2 :
                self.normpass_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.gdr_altis_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.gdr_panel.radbox_panel.radbox_datafile.SetSelection(2)
                self.normpass_panel.Hide()
                self.gdr_altis_panel.Hide()
                self.gdr_panel.Show()
                self.Layout()
            
            
    def onCheckKML(self,event):
        if self.normpass_panel.IsShown():
            self.check_ctrl_kml(self.normpass_panel)
        elif self.gdr_altis_panel.IsShown():
            self.check_ctrl_kml(self.gdr_altis_panel)
        elif self.gdr_panel.IsShown():
            self.check_ctrl_kml(self.gdr_panel)

    def check_ctrl_kml(self,panel):
        if panel.chkbox_kml.GetValue():
            panel.text_ctrl_kml_files.Enable()
            panel.btn_kml_file.Enable()
        else:
            panel.text_ctrl_kml_files.Disable()
            panel.btn_kml_file.Disable()
    
    
    def onKMLFile(self,event):
#         fileDialog = wx.FileDialog(self, "Open KML file", wildcard="KML files (*.kml;*.KML)|*.kml;*.KML",
#                       style = wx.FD_FILE_MUST_EXIST) 
#         
#         if fileDialog.ShowModal() == wx.ID_OK:
#             self.kml_filename = fileDialog.GetPath()
#             fileDialog.Destroy()
#         #Ecriture du pathname et filename du fichier dans le TextCtrl
#         self.text_ctrl_kml_files.SetValue(self.kml_filename)
        if self.normpass_panel.IsShown():
            self.kml_filename = self.kml_dialog_txtctrl(self.normpass_panel.text_ctrl_kml_files)
        elif self.gdr_altis_panel.IsShown():
            self.kml_filename = self.kml_dialog_txtctrl(self.gdr_altis_panel.text_ctrl_kml_files)
        if self.gdr_panel.IsShown():
            self.kml_filename = self.kml_dialog_txtctrl(self.gdr_panel.text_ctrl_kml_files)


    def kml_dialog_txtctrl(self,text_ctrl):
         fileDialog = wx.FileDialog(self, "Open KML file", wildcard="KML files (*.kml;*.KML)|*.kml;*.KML",
                       style = wx.FD_FILE_MUST_EXIST) 
         
         if fileDialog.ShowModal() == wx.ID_OK:
             kml_filename = fileDialog.GetPath()
             fileDialog.Destroy()
         #Ecriture du pathname et filename du fichier dans le TextCtrl
         text_ctrl.SetValue(kml_filename)
         
         return kml_filename

#-------------------------------------------------------------------------------
                
    def onGDRFiles(self,event):

        if self.normpass_panel.IsShown():
             fileDialog = wx.FileDialog(self, "Open Normpass file", wildcard="nc files (*.nc;*.NC)|*.nc;*.NC",
                           style = wx.FD_FILE_MUST_EXIST) 
             
             if fileDialog.ShowModal() == wx.ID_OK:
                 self.normpass_filename = fileDialog.GetPath()
                 fileDialog.Destroy()
             #Ecriture du pathname et filename du fichier dans le TextCtrl
             self.normpass_panel.text_ctrl_normpass_files.SetValue(self.normpass_filename)
        elif self.gdr_altis_panel.IsShown():
             fileDialog = wx.FileDialog(self, "Open AlTiS GDR file", wildcard="nc files (AlTiS*.nc;AlTiS*.NC)|*.nc;*.NC",
                           style = wx.FD_FILE_MUST_EXIST) 
             
             if fileDialog.ShowModal() == wx.ID_OK:
                 self.gdr_altis_filename = fileDialog.GetPath()
                 fileDialog.Destroy()
             #Ecriture du pathname et filename du fichier dans le TextCtrl
             self.gdr_altis_panel.text_ctrl_gdr_altis_files.SetValue(self.gdr_altis_filename)
        elif self.gdr_panel.IsShown():
            dirDialog = wx.DirDialog (self, "Altimetric Data directory", "", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

            if dirDialog.ShowModal() == wx.ID_OK:
                 self.gdr_dir = dirDialog.GetPath()
                 dirDialog.Destroy()

            self.gdr_panel.text_ctrl_gdr_dir.SetValue(self.gdr_dir)

            # Selection des fichiers trace
            self.file_struct = __regex_file_parser__(self.gdr_panel.sel_mission.GetValue(),self.gdr_dir,None)

            list_track = np.unique(self.file_struct['track'])
            self.gdr_panel.sel_track.Clear()
            self.gdr_panel.sel_track.Append('All-tracks')
            for track in list_track:
                self.gdr_panel.sel_track.Append(str(track))

            self.gdr_panel.sel_track.SetValue(str(list_track[0]))
             

        
    def onLoadFiles (self,event):
        
        if not hasattr(self,"file_struct"):
            print('self.gdr_panel.text_ctrl_gdr_dir.GetValue()',self.gdr_panel.text_ctrl_gdr_dir.GetValue())
            print('self.gdr_panel.sel_mission.GetValue()',self.gdr_panel.sel_mission.GetValue())
            self.gdr_dir = self.gdr_panel.text_ctrl_gdr_dir.GetValue()
            self.file_struct = __regex_file_parser__(self.gdr_panel.sel_mission.GetValue(),self.gdr_dir,None)
            
        if self.gdr_panel.sel_track.GetValue() == 'All-tracks':
            mask_file = np.ones(len(self.file_struct['track']),dtype='bool')
        else:
            track = int(self.gdr_panel.sel_track.GetValue())
            mask_file = self.file_struct['track'] == track
        
        self.gdr_filename = self.file_struct['filename'][mask_file].tolist()

        self.gdr_panel.text_ctrl_nc_files.SetValue('\n'.join(self.gdr_filename))
        
          
    def onQuit(self,event):
#        self.Close()
        self.Destroy()
                
    def onOk(self,event):
#        self.data_sel_config = dict()
        if self.normpass_panel.IsShown():
            self.data_sel_config['normpass_flag'] = True
            self.data_sel_config['gdr_flag'] = False
            self.data_sel_config['gdr_altis_flag'] = False
            self.data_sel_config['normpass_file'] = self.normpass_panel.text_ctrl_normpass_files.GetValue()    #self.normpass_filename # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
            self.data_sel_config['mission'] = self.normpass_panel.sel_mission.GetValue()
            if self.normpass_panel.chkbox_kml.GetValue():
                self.data_sel_config['kml_file'] = self.normpass_panel.text_ctrl_kml_files.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['kml_file'] = None 
#            self.Close()
            event.Skip()            
        elif self.gdr_altis_panel.IsShown():
#            if len(self.gdr_altis_filename) == 0 :
#                wx.MessageBox('Download completed', 'Info', wx.OK | wx.ICON_INFORMATION)
            self.data_sel_config['normpass_flag'] = False
            self.data_sel_config['gdr_flag'] = False
            self.data_sel_config['gdr_altis_flag'] = True
            self.data_sel_config['gdr_altis_file'] = self.gdr_altis_panel.text_ctrl_gdr_altis_files.GetValue()    #self.gdr_altis_filename # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
            self.data_sel_config['mission'] = self.gdr_altis_panel.sel_mission.GetValue()
            if self.gdr_altis_panel.chkbox_kml.GetValue():
                self.data_sel_config['kml_file'] = self.gdr_altis_panel.text_ctrl_kml_files.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['kml_file'] = None 
#            self.Close()
            event.Skip()            
        elif self.gdr_panel.IsShown():
            if len(self.gdr_filename) == 0 :
                wx.MessageBox('Download completed', 'Info', wx.OK | wx.ICON_INFORMATION)
            self.data_sel_config['normpass_flag'] = False
            self.data_sel_config['gdr_flag'] = True
            self.data_sel_config['gdr_altis_flag'] = False
            self.data_sel_config['data_dir'] = self.gdr_dir # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
            self.data_sel_config['list_file'] = self.gdr_filename # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
            self.data_sel_config['track'] = self.gdr_panel.sel_track.GetValue() #int(self.gdr_panel.sel_track.GetValue())
            self.data_sel_config['list_track'] = self.gdr_panel.sel_track.GetItems() #int(self.sel_track.GetValue())
            self.data_sel_config['mission'] = self.gdr_panel.sel_mission.GetValue()
            self.data_sel_config['surf_type'] = self.gdr_panel.sel_surf_type.GetValue()
            if self.gdr_panel.chkbox_kml.GetValue():
                self.data_sel_config['kml_file'] = self.gdr_panel.text_ctrl_kml_files.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['kml_file'] = None 
#            self.Close()
            event.Skip()            

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

