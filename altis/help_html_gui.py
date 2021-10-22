#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Help class
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------
import wx
import wx.adv
import wx.html
#import yaml
#import os

# import sys
# import matplotlib
#import numpy as np
#import pandas as pd
#import glob
#import xarray as xr
import pkg_resources
#import re
#import pdb
#import tempfile
import webbrowser
import datetime


#from altis_utils.tools import __config_load__, update_progress, __regex_file_parser__
from altis._version import __version__, __revision__


# -------------------------------------------------------------------------------
# Help window
# -------------------------------------------------------------------------------
class Help_Window(wx.Frame):
    def OnAboutBox(self):
        logo_file = pkg_resources.resource_filename(
            "altis", "../etc/altis_logo.png"
        )
#        licence_file = pkg_resources.resource_filename(
#            "altis", "../etc/Licence_CeCILL_V2.1-en.txt"
#        )
        licence_file = pkg_resources.resource_filename(
            "altis", "LICENSE"
        )

        with open(licence_file,'r') as fs:
            text_file=fs.read()

        description = (
            "AlTiS (Altimetric Time Series) software is a tool to "
            + "build time series from altimetric GDR (Geographic Data Reccord) data "
            + "suppled by the French Observation Service CTOH (Centre of Topography "
            + "of the Oceans and the Hydrosphere)."
        )

        licence = text_file
        info = wx.adv.AboutDialogInfo()

        info.SetIcon(wx.Icon(logo_file, wx.BITMAP_TYPE_PNG))
        info.SetName("AlTiS")
        info.SetVersion("Version " + __version__ + "\n" + __revision__)
        info.SetDescription(description)
        current_date = datetime.date.today()
        year = current_date.year
        info.SetCopyright("\n\n\nCeCill FREE SOFTWARE LICENSE, 2019-"+str(year)+", CTOH\n\n"
                          +"  IDDN Certification : IDDN.FR.010.0121234.000.R.X.2020.041.30000\n\n\n")
        info.SetWebSite(
            "http://ctoh.legos.obs-mip.fr/applications/land_surfaces/softwares/altis",
            "AlTiS Web Site",
        )

        info.SetLicence(licence)
        #            info.AddDeveloper(""" Fabien Blarel, blarel@legos.obs-mip.fr
        #
        #                         with the contributions of:
        #                          - Denis Blumstien
        #                          - Frederic Frappart
        #                          - Fernando Nino
        #                          -
        #                          -
        #                                     """)

        # info.AddDocWriter('CTOH')
        # info.AddArtist('The CTOH crew')
        # info.AddTranslator('CTOH')

        wx.adv.AboutBox(info)


