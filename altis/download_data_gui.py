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
import wx.lib.scrolledpanel
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

 
class Bottom_Bar(wx.Panel):
    def __init__( self, parent ):
        wx.Panel.__init__ ( self, parent )
#-------------------------------------------------------------------------------
#        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        
#        gs = wx.GridBagSizer(2, 11)
#        gs = wx.GridBagSizer(2, 11)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        # Help button
        self.btn_help = wx.Button(self, wx.ID_HELP, label='Help')

        # Ok button
        self.btn_ok = wx.Button(self, wx.ID_OK, label="Ok")

        # Ok cancel
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Cancel")

                
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(self.btn_help,flag=wx.LEFT)
        hbox2.Add(self.btn_ok,flag=wx.LEFT, border=1)
        hbox2.Add(self.btn_cancel,flag=wx.LEFT|wx.BOTTOM, border=1)
        vbox.Add(hbox2,flag=wx.ALIGN_RIGHT|wx.RIGHT, border=1)

        self.SetSizer(vbox)
#        vbox.Fit(self)


#        gs.Add(line, pos=(0, 0), span=(1, 11),flag=wx.EXPAND|wx.BOTTOM, border=10)
#        gs.Add(self.btn_help, pos=(1, 0),flag=wx.EXPAND, border=10)
#        gs.Add(self.btn_ok, pos=(1, 9),flag=wx.EXPAND, border=10)
#        gs.Add(self.btn_cancel, pos=(1, 10),flag=wx.EXPAND, border=10)
#        
#        gs.AddGrowableCol(2)
#        self.SetSizer(gs)
#        gs.Fit(self)

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
#class Load_data_Window(wx.Frame):
    def __init__(self,data_opt):    #,data_opt):
        super().__init__(None,title = "Data Selection",style=wx.RESIZE_BORDER) #,size = wx.GetClientSize()) #wx.DisplaySize())

        self.data_sel_config = data_opt
        
        if self.data_sel_config['data_type'] == 'Normpass':
        
            self.normpass_panel = self.Normpass_Panel()
            self.flag_normpass_panel = True
            self.flag_gdr_panel = False
            self.flag_gdr_altis_panel = False
            
        elif self.data_sel_config['data_type'] == 'GDR Tracks':
        
            self.gdr_panel = self.GDR_Panel()
            self.flag_normpass_panel = False
            self.flag_gdr_panel = True
            self.flag_gdr_altis_panel = False

        elif self.data_sel_config['data_type'] == 'AlTiS GDR':
        
            self.gdr_altis_panel = self.GDR_Altis_Panel()
            self.flag_normpass_panel = False
            self.flag_gdr_panel = False
            self.flag_gdr_altis_panel = True

        self.Show()
        
    def GDR_Altis_Panel(self):
        scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        scroll_panel.SetupScrolling()

        sizer = wx.GridBagSizer(6, 11)

        self.__config_load__()
        Title_panel = wx.StaticText(scroll_panel, label="AlTiS GDR")
        sizer.Add(Title_panel, pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM,
            border=15)

#        icon = wx.StaticBitmap(scroll_panel, bitmap=wx.Bitmap(''))
#        sizer.Add(icon, pos=(0, 4), flag=wx.TOP|wx.RIGHT|wx.ALIGN_RIGHT,
#            border=5)

        line = wx.StaticLine(scroll_panel)
        sizer.Add(line, pos=(1, 0), span=(1, 11),
            flag=wx.EXPAND|wx.BOTTOM, border=10)
        # Mission
        label_mission = wx.StaticText(scroll_panel, label = "Mission")
        sizer.Add(label_mission, pos=(2, 0), flag=wx.LEFT,border=10)
        
        sampleLis = self.altis_gui['mission']
        
        mission = self.data_sel_config['mission'] #None
        if not mission is None:
            last_mission_sel = mission
        else:
            last_mission_sel = self.altis_gui['mission'][0]
        
        self.sel_mission = wx.ComboBox(scroll_panel,value=last_mission_sel,choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(2, 1), span=(1, 5), flag=wx.LEFT|wx.EXPAND)
        

        self.chkbox_kml = wx.CheckBox(scroll_panel, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(3, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_kml_files, pos=(3, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.kml_filename = self.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(scroll_panel, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(3, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_kml_file.Disable()
        
        # NORMPASS files
        label_gdr = wx.StaticText(scroll_panel, label = "AlTiS GDR file")
        sizer.Add(label_gdr, pos=(4, 0), flag=wx.LEFT|wx.TOP, border=10)

        self.text_ctrl_gdr_altis_files = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_gdr_altis_files, pos=(4, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.gdr_altis_filename = self.data_sel_config['gdr_altis_file'] #None
        if not self.gdr_altis_filename is None:
            self.text_ctrl_gdr_altis_files.SetValue(self.gdr_altis_filename)

        self.btn_normpass_file = wx.Button(scroll_panel, label='Browse...') 
        sizer.Add(self.btn_normpass_file, pos=(4, 10), flag=wx.TOP|wx.RIGHT, border=10)

#-------------------------------------------------------------------------------        
        self.chkbox_cfgfile = wx.CheckBox(scroll_panel, label="Config file")
        sizer.Add(self.chkbox_cfgfile, pos=(5, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_cfgfile = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_cfgfile, pos=(5, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.cfgfile_filename = self.data_sel_config['cfg_file'] #None
        if not self.cfgfile_filename is None:
            self.text_ctrl_cfgfile.SetValue(self.cfgfile_filename)
        self.text_ctrl_cfgfile.Disable()
        
        self.btn_cfgfile = wx.Button(scroll_panel, label='Browse...') 
        sizer.Add(self.btn_cfgfile, pos=(5, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_cfgfile.Disable()
#-------------------------------------------------------------------------------        
#        
        line = wx.StaticLine(scroll_panel)
        sizer.Add(line, pos=(6, 0), span=(1, 11),
            flag=wx.EXPAND|wx.BOTTOM, border=10)
            
        self.bottom_bar_panel=Bottom_Bar(scroll_panel)
        sizer.Add(self.bottom_bar_panel, pos=(7, 8), span=(1, 3) ,border=10)
        
        sizer.AddGrowableCol(2)

        scroll_panel.SetSizer(sizer)
        sizer.Fit(self)
        
        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.onKMLFile)
        self.btn_normpass_file.Bind(wx.EVT_BUTTON, self.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
#        self.btn_ok.Bind(wx.EVT_BUTTON, self.onOk)
#        self.btn_cancel.Bind(wx.EVT_BUTTON, self.onQuit)
        self.chkbox_cfgfile.Bind(wx.EVT_CHECKBOX, self.onCheckCFGFILE)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.onCheckKML)
        self.btn_cfgfile.Bind(wx.EVT_BUTTON, self.onCFGfile)

    def Normpass_Panel( self):
        scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        scroll_panel.SetupScrolling()

        sizer = wx.GridBagSizer(8, 11)

        self.__config_load__()
        
        Title_panel = wx.StaticText(scroll_panel, label="Normpass")
        sizer.Add(Title_panel, pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM,
            border=15)

#        icon = wx.StaticBitmap(scroll_panel, bitmap=wx.Bitmap(''))
#        sizer.Add(icon, pos=(0, 4), flag=wx.TOP|wx.RIGHT|wx.ALIGN_RIGHT,
#            border=5)

        line = wx.StaticLine(scroll_panel)
        sizer.Add(line, pos=(1, 0), span=(1, 11),
            flag=wx.EXPAND|wx.BOTTOM, border=10)
            
        # Mission
        label_mission = wx.StaticText(scroll_panel, label = "Mission")
        sizer.Add(label_mission, pos=(2, 0), flag=wx.LEFT,border=10)
        
        sampleLis = self.altis_gui['mission']
        mission = self.data_sel_config['mission'] #None
        if not mission is None:
            last_mission_sel = mission
        else:
            last_mission_sel = self.altis_gui['mission'][0]
        self.sel_mission = wx.ComboBox(scroll_panel,value=last_mission_sel,choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(2, 1), span=(1, 5), flag=wx.LEFT|wx.EXPAND,border=10)
        

        self.chkbox_kml = wx.CheckBox(scroll_panel, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(3, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_kml_files, pos=(3, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.kml_filename = self.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(scroll_panel, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(3, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_kml_file.Disable()
        
        # NORMPASS files
        label_gdr = wx.StaticText(scroll_panel, label = "Normpass file")
        sizer.Add(label_gdr, pos=(4, 0), flag=wx.LEFT|wx.TOP, border=10)

        self.text_ctrl_normpass_files = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_normpass_files, pos=(4, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)
 
        self.normpass_filename = self.data_sel_config['normpass_file'] #None
        if not self.normpass_filename is None:
            self.text_ctrl_normpass_files.SetValue(self.normpass_filename)

        self.btn_normpass_file = wx.Button(scroll_panel, label='Browse...') 
        sizer.Add(self.btn_normpass_file, pos=(4, 10), flag=wx.TOP|wx.RIGHT, border=10)

#-------------------------------------------------------------------------------        
        self.chkbox_cfgfile = wx.CheckBox(scroll_panel, label="Config file")
        sizer.Add(self.chkbox_cfgfile, pos=(5, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_cfgfile = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_cfgfile, pos=(5, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.cfgfile_filename = self.data_sel_config['cfg_file'] #None
        if not self.cfgfile_filename is None:
            self.text_ctrl_cfgfile.SetValue(self.cfgfile_filename)
        self.text_ctrl_cfgfile.Disable()
        
        self.btn_cfgfile = wx.Button(scroll_panel, label='Browse...') 
        sizer.Add(self.btn_cfgfile, pos=(5, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_cfgfile.Disable()
#-------------------------------------------------------------------------------        
        

#-------------------------------------------------------------------------------
        line = wx.StaticLine(scroll_panel)
        sizer.Add(line, pos=(6, 0), span=(1, 11),
            flag=wx.EXPAND|wx.BOTTOM, border=10)
            
        self.bottom_bar_panel=Bottom_Bar(scroll_panel)
        sizer.Add(self.bottom_bar_panel, pos=(7, 8), span=(1, 3) ,border=10)
        
        sizer.AddGrowableCol(2)

        scroll_panel.SetSizer(sizer)
        sizer.Fit(self)

        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.onKMLFile)
        self.btn_normpass_file.Bind(wx.EVT_BUTTON, self.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
#        self.btn_ok.Bind(wx.EVT_BUTTON, self.onOk)
#        self.btn_cancel.Bind(wx.EVT_BUTTON, self.onQuit)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.onCheckKML)
        self.chkbox_cfgfile.Bind(wx.EVT_CHECKBOX, self.onCheckCFGFILE)
        self.btn_cfgfile.Bind(wx.EVT_BUTTON, self.onCFGfile)


    def GDR_Panel(self):
        scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        scroll_panel.SetupScrolling()

        sizer = wx.GridBagSizer(14,20)

        self.__config_load__()
        
        Title_panel = wx.StaticText(scroll_panel, label="GDR Tracks")
        sizer.Add(Title_panel, pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM,
            border=15)

#        icon = wx.StaticBitmap(scroll_panel, bitmap=wx.Bitmap(''))
#        sizer.Add(icon, pos=(0, 4), flag=wx.TOP|wx.RIGHT|wx.ALIGN_RIGHT,
#            border=5)

        line = wx.StaticLine(scroll_panel)
        sizer.Add(line, pos=(1, 0), span=(1, 11),
            flag=wx.EXPAND|wx.BOTTOM, border=10)
        # Mission
        label_mission = wx.StaticText(scroll_panel, label = "Mission")
        sizer.Add(label_mission, pos=(2, 0), flag=wx.TOP|wx.LEFT,border=10)
        
        sampleLis = self.altis_gui['mission']
        mission = self.data_sel_config['mission'] #None
        if not mission is None:
            last_mission_sel = mission
        else:
            last_mission_sel = self.altis_gui['mission'][0]
        self.sel_mission = wx.ComboBox(scroll_panel,value=last_mission_sel,choices=sampleLis, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_mission, pos=(2, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND,border=10)
        
        # Surface Type       
        label_surf_type = wx.StaticText(scroll_panel, label= "Surface type")
        sizer.Add(label_surf_type, pos=(3, 0), span=(1, 1), flag=wx.LEFT|wx.TOP, border=10)
        
        sampleList = self.altis_gui['surface_types']   #['Rivers and Lakes', 'Great Lakes', 'Ocean']
        self.sel_surf_type = wx.ComboBox(scroll_panel, value=self.altis_gui['surface_types'][0],choices=sampleList, style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_surf_type, pos=(3, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND,border=10)
        
        self.chkbox_kml = wx.CheckBox(scroll_panel, label="KML file")
        sizer.Add(self.chkbox_kml, pos=(4, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_kml_files = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_kml_files, pos=(4, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.kml_filename = self.data_sel_config['kml_file'] #None
        if not self.kml_filename is None:
            self.text_ctrl_kml_files.SetValue(self.kml_filename)
        self.text_ctrl_kml_files.Disable()
        
        self.btn_kml_file = wx.Button(scroll_panel, label='Browse...') 
        sizer.Add(self.btn_kml_file, pos=(4, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_kml_file.Disable()
#        
        # GDR files
        label_gdr = wx.StaticText(scroll_panel, label = "Data directory")
        sizer.Add(label_gdr, pos=(5, 0), flag=wx.LEFT|wx.TOP, border=10)

#-------------------------------------------------------------------------------
        self.data_sel_config['data_dir']
        self.text_ctrl_gdr_dir = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_gdr_dir, pos=(5, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)
        self.gdr_dir = self.data_sel_config['data_dir']
        if not self.gdr_dir == '':
            self.text_ctrl_gdr_dir.SetValue(self.gdr_dir)
        
#-------------------------------------------------------------------------------
       
        self.btn_gdr_files = wx.Button(scroll_panel, label='Browse...')
        sizer.Add(self.btn_gdr_files, pos=(5, 10), flag=wx.TOP|wx.RIGHT, border=10)
        
##-------------------------------------------------------------------------------
        label_sel_track = wx.StaticText(scroll_panel, label = "Track")
        sizer.Add(label_sel_track, pos=(6, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.sel_track = wx.ComboBox(scroll_panel,value='',choices=[], style=wx.CB_DROPDOWN | wx.CB_SORT | wx.TE_READONLY)
        sizer.Add(self.sel_track, pos=(6, 1), span=(1, 5), flag=wx.TOP|wx.EXPAND,border=10)
        self.sel_track.AppendItems(self.data_sel_config['list_track'])
        if len(self.data_sel_config['list_track']) > 0 :
            self.sel_track.SetValue(self.data_sel_config['list_track'][0])

        self.text_ctrl_nc_files = wx.TextCtrl(scroll_panel, style = wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH)
        sizer.Add(self.text_ctrl_nc_files, pos=(7, 1), span=(10, 9), flag=wx.TOP|wx.EXPAND,border=10)



#-------------------------------------------------------------------------------        
        self.chkbox_cfgfile = wx.CheckBox(scroll_panel, label="Config file")
        sizer.Add(self.chkbox_cfgfile, pos=(18, 0), flag=wx.LEFT|wx.TOP, border=10)
        
        self.text_ctrl_cfgfile = wx.TextCtrl(scroll_panel)
        sizer.Add(self.text_ctrl_cfgfile, pos=(18, 1), span=(1, 9), flag=wx.TOP|wx.EXPAND,border=10)

        self.cfgfile_filename = self.data_sel_config['cfg_file'] #None
        if not self.cfgfile_filename is None:
            self.text_ctrl_cfgfile.SetValue(self.cfgfile_filename)
        self.text_ctrl_cfgfile.Disable()
        
        self.btn_cfgfile = wx.Button(scroll_panel, label='Browse...') 
        sizer.Add(self.btn_cfgfile, pos=(18, 10), flag=wx.TOP|wx.RIGHT, border=10)
        self.btn_cfgfile.Disable()
#-------------------------------------------------------------------------------        

##-------------------------------------------------------------------------------
        line = wx.StaticLine(scroll_panel)
        sizer.Add(line, pos=(19, 0), span=(1, 11),
            flag=wx.EXPAND|wx.BOTTOM, border=10)
            
        self.bottom_bar_panel=Bottom_Bar(scroll_panel)
        sizer.Add(self.bottom_bar_panel, pos=(20, 8), span=(1, 3) ,border=10)
        
        
#        sizer.AddGrowableCol(2)
        scroll_panel.SetSizer(sizer)
        sizer.Fit(self)

        #Binds functions to appropriate buttons
        self.btn_kml_file.Bind(wx.EVT_BUTTON, self.onKMLFile)
        self.btn_gdr_files.Bind(wx.EVT_BUTTON, self.onGDRFiles)
#        self.btn_load.Bind(wx.EVT_BUTTON, self.onSelFiles)
        self.sel_track.Bind(wx.EVT_COMBOBOX, self.onLoadFiles)
#        self.btn_ok.Bind(wx.EVT_BUTTON, self.onOk)
#        self.btn_cancel.Bind(wx.EVT_BUTTON, self.onQuit)
        self.chkbox_kml.Bind(wx.EVT_CHECKBOX, self.onCheckKML)
        self.chkbox_cfgfile.Bind(wx.EVT_CHECKBOX, self.onCheckCFGFILE)
        self.btn_cfgfile.Bind(wx.EVT_BUTTON, self.onCFGfile)

                
    def onCheckKML(self,event):
        if self.flag_normpass_panel:
            self.check_ctrl_kml(self.normpass_panel)
        elif self.flag_gdr_altis_panel:
            self.check_ctrl_kml(self.gdr_altis_panel)
        elif self.flag_gdr_panel:
            self.check_ctrl_kml(self.gdr_panel)

    def check_ctrl_kml(self,panel):
        if self.chkbox_kml.GetValue():
            self.text_ctrl_kml_files.Enable()
            self.btn_kml_file.Enable()
        else:
            self.text_ctrl_kml_files.Disable()
            self.btn_kml_file.Disable()

    def onCheckCFGFILE(self,event):
        if self.flag_normpass_panel:
            self.check_cfgfile(self.normpass_panel)
        elif self.flag_gdr_altis_panel:
            self.check_cfgfile(self.gdr_altis_panel)
        elif self.flag_gdr_panel:
            self.check_cfgfile(self.gdr_panel)

    def check_cfgfile(self,panel):
        if self.chkbox_cfgfile.GetValue():
            self.text_ctrl_cfgfile.Enable()
            self.btn_cfgfile.Enable()
        else:
            self.text_ctrl_cfgfile.Disable()
            self.btn_cfgfile.Disable()
    
#-------------------------------------------------------------------------------
    
    def onKMLFile(self,event):
        if self.text_ctrl_kml_files.GetValue() != '':
            directory = self.text_ctrl_kml_files.GetValue()
            directory = os.sep.join(directory.split(os.sep)[:-1])
        else: 
            directory = ''
        self.kml_filename = self.kml_dialog_txtctrl(self.text_ctrl_kml_files,directory)


    def kml_dialog_txtctrl(self,text_ctrl,directory):
         fileDialog = wx.FileDialog(self, "Open KML file",
                                    defaultDir=directory, 
                                    wildcard="KML files (*.kml;*.KML)|*.kml;*.KML",
                       style = wx.FD_FILE_MUST_EXIST) 
         
         if fileDialog.ShowModal() == wx.ID_OK:
             kml_filename = fileDialog.GetPath()
             fileDialog.Destroy()
         #Ecriture du pathname et filename du fichier dans le TextCtrl
         text_ctrl.SetValue(kml_filename)
         
         return kml_filename
#-------------------------------------------------------------------------------

    def onCFGfile(self,event):
        if self.text_ctrl_cfgfile.GetValue() != '':
            directory = self.text_ctrl_cfgfile.GetValue()
            directory = os.sep.join(directory.split(os.sep)[:-1])
        else: 
            directory = ''
        self.kml_filename = self.cfgfile_dialog_txtctrl(self.text_ctrl_cfgfile,directory)

    def cfgfile_dialog_txtctrl(self,text_ctrl,directory):
         fileDialog = wx.FileDialog(self, "Select your configuration file.",
                                    defaultDir=directory, 
                                    wildcard="YAML files (*.YML)|*.yml",
                       style = wx.FD_FILE_MUST_EXIST) 
         
         if fileDialog.ShowModal() == wx.ID_OK:
             cfgfile_filename = fileDialog.GetPath()
             fileDialog.Destroy()
         #Ecriture du pathname et filename du fichier dans le TextCtrl
         text_ctrl.SetValue(cfgfile_filename)
         
    
#-------------------------------------------------------------------------------
                
    def onGDRFiles(self,event):

#        if self.normpass_panel.IsShown():
        if self.flag_normpass_panel:
            if self.text_ctrl_normpass_files.GetValue() != '':
                directory = self.text_ctrl_normpass_files.GetValue()
                directory = os.sep.join(directory.split(os.sep)[:-1])
            else: 
                directory = ''
                
            fileDialog = wx.FileDialog(self, "Open Normpass file",
                                defaultDir=directory,
                                wildcard="nc files (*.nc;*.NC)|*.nc;*.NC",
                                style = wx.FD_FILE_MUST_EXIST) 
             
             
            if fileDialog.ShowModal() == wx.ID_OK:
                self.normpass_filename = fileDialog.GetPath()
                fileDialog.Destroy()
                #Ecriture du pathname et filename du fichier dans le TextCtrl

            self.text_ctrl_normpass_files.SetValue(self.normpass_filename)
#        elif self.gdr_altis_panel.IsShown():
        elif self.flag_gdr_altis_panel:

            if self.text_ctrl_gdr_altis_files.GetValue() != '':
                directory = self.text_ctrl_gdr_altis_files.GetValue()
                directory = os.sep.join(directory.split(os.sep)[:-1])
            else: 
                directory = ''

            fileDialog = wx.FileDialog(self, "Open AlTiS GDR file",
                                    defaultDir=directory,
                                    wildcard="nc files (AlTiS*.nc;AlTiS*.NC)|*.nc;*.NC",
                                    style = wx.FD_FILE_MUST_EXIST) 

            if fileDialog.ShowModal() == wx.ID_OK:
             self.gdr_altis_filename = fileDialog.GetPath()
             fileDialog.Destroy()
            #Ecriture du pathname et filename du fichier dans le TextCtrl
            self.text_ctrl_gdr_altis_files.SetValue(self.gdr_altis_filename)
#        elif self.gdr_panel.IsShown():
        elif self.flag_gdr_panel:

            if self.text_ctrl_gdr_dir.GetValue() != '':
                directory = self.text_ctrl_gdr_dir.GetValue()
#                directory = os.sep.join(directory.split(os.sep)[:-1])
            else: 
                directory = ''

            dirDialog = wx.DirDialog (self, "Altimetric Data directory", directory, style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

            if dirDialog.ShowModal() == wx.ID_OK:
                 self.gdr_dir = dirDialog.GetPath()
                 dirDialog.Destroy()

            self.text_ctrl_gdr_dir.SetValue(self.gdr_dir)

            # Selection des fichiers trace
            self.file_struct = __regex_file_parser__(self.sel_mission.GetValue(),self.gdr_dir,None)

            list_track = np.unique(self.file_struct['track'])
            self.sel_track.Clear()
            self.sel_track.Append('All-tracks')
            for track in list_track:
                self.sel_track.Append(str(track))

            self.sel_track.SetValue(str(list_track[0]))
             

        
    def onLoadFiles (self,event):
        
        if not hasattr(self,"file_struct"):
            print('self.text_ctrl_gdr_dir.GetValue()',self.text_ctrl_gdr_dir.GetValue())
            print('self.sel_mission.GetValue()',self.sel_mission.GetValue())
            self.gdr_dir = self.text_ctrl_gdr_dir.GetValue()
            self.file_struct = __regex_file_parser__(self.sel_mission.GetValue(),self.gdr_dir,None)
            
        if self.sel_track.GetValue() == 'All-tracks':
            mask_file = np.ones(len(self.file_struct['track']),dtype='bool')
        else:
            track = int(self.sel_track.GetValue())
            mask_file = self.file_struct['track'] == track
        
        self.gdr_filename = self.file_struct['filename'][mask_file].tolist()

        self.text_ctrl_nc_files.SetValue('\n'.join(self.gdr_filename))
        
          
    def onQuit(self,event):
#        self.Close()
        self.Destroy()
                
    def onOk(self,event):
#        self.data_sel_config = dict()
#        if self.normpass_panel.IsShown():
        if self.flag_normpass_panel:
            self.data_sel_config['normpass_flag'] = True
            self.data_sel_config['gdr_flag'] = False
            self.data_sel_config['gdr_altis_flag'] = False
            self.data_sel_config['normpass_file'] = self.text_ctrl_normpass_files.GetValue()    #self.normpass_filename # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
            self.data_sel_config['mission'] = self.sel_mission.GetValue()
            if self.chkbox_kml.GetValue():
                self.data_sel_config['kml_file'] = self.text_ctrl_kml_files.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['kml_file'] = None 
            if self.chkbox_cfgfile.GetValue():
                self.data_sel_config['cfg_file'] = self.text_ctrl_cfgfile.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['cfg_file'] = None 
#            self.Close()
            event.Skip()            
#        elif self.gdr_altis_panel.IsShown():
        elif self.flag_gdr_altis_panel:
#            if len(self.gdr_altis_filename) == 0 :
#                wx.MessageBox('Download completed', 'Info', wx.OK | wx.ICON_INFORMATION)
            self.data_sel_config['normpass_flag'] = False
            self.data_sel_config['gdr_flag'] = False
            self.data_sel_config['gdr_altis_flag'] = True
            self.data_sel_config['gdr_altis_file'] = self.text_ctrl_gdr_altis_files.GetValue()    #self.gdr_altis_filename # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
            self.data_sel_config['mission'] = self.sel_mission.GetValue()
            if self.chkbox_kml.GetValue():
                self.data_sel_config['kml_file'] = self.text_ctrl_kml_files.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['kml_file'] = None 
            if self.chkbox_cfgfile.GetValue():
                self.data_sel_config['cfg_file'] = self.text_ctrl_cfgfile.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['cfg_file'] = None 
#            self.Close()
            event.Skip()            
#        elif self.gdr_panel.IsShown():
        elif self.flag_gdr_panel:
            if len(self.gdr_filename) == 0 :
                wx.MessageBox('Download completed', 'Info', wx.OK | wx.ICON_INFORMATION)
            self.data_sel_config['normpass_flag'] = False
            self.data_sel_config['gdr_flag'] = True
            self.data_sel_config['gdr_altis_flag'] = False
            self.data_sel_config['data_dir'] = self.gdr_dir # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
            self.data_sel_config['list_file'] = self.gdr_filename # wx.TextCtrl.GetValue(self.text_ctrl_nc_files)
            self.data_sel_config['track'] = self.sel_track.GetValue() #int(self.gdr_panel.sel_track.GetValue())
            self.data_sel_config['list_track'] = self.sel_track.GetItems() #int(self.sel_track.GetValue())
            self.data_sel_config['mission'] = self.sel_mission.GetValue()
            self.data_sel_config['surf_type'] = self.sel_surf_type.GetValue()
            if self.chkbox_kml.GetValue():
                self.data_sel_config['kml_file'] = self.text_ctrl_kml_files.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['kml_file'] = None 
            if self.chkbox_cfgfile.GetValue():
                self.data_sel_config['cfg_file'] = self.text_ctrl_cfgfile.GetValue()  #self.kml_filename
            else:
                self.data_sel_config['cfg_file'] = None 
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

