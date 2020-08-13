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

#from altis_utils.tools import __config_load__, update_progress, __regex_file_parser__
from altis._version import __version__, __revision__


# -------------------------------------------------------------------------------
# Help window
# -------------------------------------------------------------------------------
class Help_Window(wx.Frame):
    def __init__(self):
        super().__init__(None, title="AlTiS : Help!", size=(400, 800))
        # wx.Frame.__init__(self, parent, wx.ID_ANY, title="AlTiS : Help!", size=(400,400))
        html_file = pkg_resources.resource_filename("altis", "../etc/HELP.html")
        with open(html_file, "r") as fh:
            html_text = fh.read()
        html = wxHTML(self)

        html.SetPage(html_text)


class wxHTML(wx.html.HtmlWindow):
    def OnLinkClicked(self, link):
        print(link.GetHref())
        if link.GetHref() == "About":
            logo_file = pkg_resources.resource_filename(
                "altis", "../etc/altis_logo.png"
            )

            description = (
                "AlTiS (Altimetric Time Series) software is a tool to "
                + "build time series from altimetric GDR (Geographic Data Reccord) data "
                + "suppled by the French Observation Service CTOH (Centre of Topography "
                + "of the Oceans and the Hydrosphere)."
            )

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
            info.SetName("AlTiS\n")
            info.SetVersion("Version " + __version__ + "\n" + __revision__)
            info.SetDescription(description)
            info.SetCopyright("CeCill FREE SOFTWARE LICENSE - 2019 - CTOH")
            info.SetWebSite(
                "http://ctoh.legos.obs-mip.fr/applications/land_surfaces/softwares/maps",
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

        elif "http://" in link.GetHref():
            webbrowser.open(link.GetHref())
