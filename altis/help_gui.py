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
import wx.html
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
from altis._version import __version__,__revision__

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
        
        help_file = pkg_resources.resource_filename('altis', 'HELP.txt')
        with open(help_file, 'r') as file:
            wx.TextCtrl.SetValue(st1, file.read())
#        help_file = pkg_resources.resource_filename('altis', 'HELP.html')
#        print(help_file)
#        helpWin = wx.html.HtmlWindow(self.help_panel, style=wx.NO_BORDER)   #, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH)
#        helpWin.LoadPage('HELP.html')
        
        
        hbox2.Add(st1, proportion=1, flag=wx.EXPAND)
        vbox.Add(hbox2, proportion=1, flag=wx.LEFT|wx.RIGHT| wx.BOTTOM | wx.EXPAND, border=10)
        
        self.help_panel.SetSizer(vbox)

        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((20,20))
        self.iconHelp = self.mk_iconbar("Help",wx.ART_HELP,"About AlTiS")
        self.toolbar.Realize()
        
        self.Bind(wx.EVT_MENU, self.OnAboutBox, self.iconHelp)
        
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText(('AlTiS version : %s, revision : %s CTOH')%(__version__,__revision__))


    def mk_iconbar(self,bt_txt,art_id,bt_lg_txt):
    
        ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (16,16))
        itemTool = self.toolbar.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool

    def OnAboutBox(self, event):
        
        logo_file = pkg_resources.resource_filename('altis', '../etc/altis_logo.png')        

        description = ("AlTiS (Altimetric Time Series) software is a tool to "+
            "build time series from altimetric GDR (Geographic Data Reccord) data "+
            "suppled by the French Observation Service CTOH (Centre of Topography "+
            "of the Oceans and the Hydrosphere).")

        licence = """All of AlTiS the source code is available under the CeCiLL License. What does it means? You have the freedom to:

                    - use the software for any purpose,
                    - change the software to suit your needs,
                    - share the software with your friends and neighbors, and
                    - share the changes you make.

                For more detail, you can refer to the CeCiLL License.

                AlTiS is distributed in the hope that it will be useful,
                but WITHOUT ANY WARRANTY; without even the implied warranty of
                MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE."""
        
        

        info = wx.adv.AboutDialogInfo()

        info.SetIcon(wx.Icon(logo_file, wx.BITMAP_TYPE_PNG))
        info.SetName('AlTiS\n')
        info.SetVersion('Version '+__version__+'\n'+__revision__)
        info.SetDescription(description)
        info.SetCopyright('CeCill FREE SOFTWARE LICENSE - 2019 - CTOH')
        info.SetWebSite('http://ctoh.legos.obs-mip.fr/applications/land_surfaces/softwares/maps', 'AlTiS Web Site')
        info.SetLicence(licence)
        info.AddDeveloper('CTOH')
        #info.AddDocWriter('CTOH')
        #info.AddArtist('The CTOH crew')
        #info.AddTranslator('CTOH')

        wx.adv.AboutBox(info)

