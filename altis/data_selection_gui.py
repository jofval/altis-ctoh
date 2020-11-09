#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# DatasetSelection Class
#
# This class build a mask selection of the altimetric dataset from 
# matplotlib collection 
#
# Created by Fabien Blarel on 2019-04-19. 
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------

#import pdb
import wx
import numpy as np
from altis.common_data import Singleton
from matplotlib.widgets import LassoSelector    #, PolygonSelector, MultiCursor
from matplotlib.path import Path
#import cartopy.crs as ccrs
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
#import matplotlib as mpl
#import matplotlib.cm as mpl_cm
#import matplotlib.pyplot as plt
#import xarray as xr


class DatasetSelection(object):
    """
        Graphical data selection class
    """

    def __init__(self, main_panel, fig, plt_list,axes_list, select_text_info,DEBUG=True):
        """
            Initialisation
        """
        self.main_panel = main_panel
        self.main_panel.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))
        self.fig = fig
        self.canvas = fig.canvas
        self.axes = axes_list 
        self.plt = plt_list
        [self.ax1,self.ax2,self.ax3,self.ax4] = axes_list 
        [self.plt1,self.plt2,self.plt3,self.plt4] = plt_list
        self.collections = dict()
        self.fc = dict()
        self.debug = DEBUG
        self.select_text_info = select_text_info

        for idx,plt in enumerate(self.plt):
            self.collections[idx] = plt.get_offsets()
            self.fc[idx] = plt.get_facecolors()

        self.xys = self.collections
        self.init_selector()
        
        self.mask_xys = np.ones(self.xys[0].shape[0],dtype='bool')
        
        self.common_data = Singleton()
        self.MASTER_mask = self.common_data.DATA_MASK_SEL[-1]\
                             & self.common_data.DATA_MASK_PARAM #\
#                             & self.common_data.CYCLE_SEL

        self.mask_output = np.ones(self.MASTER_mask.shape,dtype='bool')
        self.input_mask_index = np.where(self.mask_output)
        self.input_mask_index = np.array([self.input_mask_index[0],self.input_mask_index[1]])
        
#        if self.debug:
#            print('self.MASTER_mask.shape',self.MASTER_mask.shape)
#            print('self.input_mask_index.shape',self.input_mask_index.shape)
#            print('self.mask_xys.shape',self.mask_xys.shape)
#            print('np.sum(self.xys.mask)',np.sum(self.xys[0].mask))

        def get_axes(event):
            """
                catch axes action
            """
            if hasattr(self,'current_axes'):
                pass                
            else:
                self.current_axes = event.inaxes
#                if self.debug:
#                    print('button_press_event',self.axes.index(self.current_axes))

        def accept(event):
            """
                key event action
            """
            cursor_wait = wx.BusyCursor()
#            print('event.key, ',event.key)
            if (event.key == "enter")or(event.key == "v"):
                self.progress = wx.ProgressDialog("Data Selection Processing ...", "please wait", maximum=100, style=wx.PD_SMOOTH|wx.PD_AUTO_HIDE)
                self.progress.Update(10, "Mask processing...")
                self.axes[self.axes_idx].set_title(" ")
                self.canvas.mpl_disconnect(self.cid_axes)
                self.canvas.mpl_disconnect(self.cid_key)
                self.mask_output = self.mask_output & np.array(self.MASTER_mask)
                self.progress.Update(60, "Mask processing...")
                self.common_data.DATA_MASK_SEL.append(self.mask_output)
                
                self.progress.Destroy()
                self.select_text_info.set_text('Press refresh ...')
                self.canvas.draw_idle()
                self.main_panel.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
                                
            elif event.key == "r":  # revers selection
                self.plot_selection(alpha=0.01)
            elif event.key == "escape":  # Abort
                if hasattr(self,'axes_idx'):
                    self.axes[self.axes_idx].set_title("      ")
                    self.plot_selection_inside(alpha=1.0)
                self.canvas.mpl_disconnect(self.cid_axes)
                self.canvas.mpl_disconnect(self.cid_key)
                self.select_text_info.set_text('')
                self.main_panel.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            del cursor_wait

        self.cid_axes = self.canvas.mpl_connect('button_press_event', get_axes)
        self.cid_key = self.canvas.mpl_connect("key_press_event", accept)          
        
    def init_selector(self):
        """
            Matplotlib graphical selector Initialisation 
        """
        self.Polysel = []
        #lineprops = dict(color='r', linestyle='-', linewidth=1, alpha=0.5)
        #markerprops = dict(marker='o', markersize=7, mec='k', mfc='k', alpha=0.5)
        for ax in self.axes:
            # PolygonSelector empèche le sharex de bien marcher dans les scatter plot.
            #            self.Polysel.append(PolygonSelector(ax, onselect=self.onselect,useblit=True,\
            # lineprops = lineprops, markerprops = markerprops))
            self.Polysel.append(LassoSelector(ax, onselect=self.onselect,useblit=True))    #,\

    def onselect(self, verts):
        """
            selection action
        """
        cursor_wait = wx.BusyCursor()
    
        path = Path(verts)

        #Recupere l'index de la figure courante
        self.axes_idx = self.axes.index(self.current_axes)
        if self.debug:
            print('self.axes_idx',self.axes_idx)
        self.axes[self.axes_idx].set_title("Data selection : 'r' key to reverse,\n'Enter' (or 'v') key to validate, 'Escape' key to abort. ",color='r',fontweight='bold')
        
        self.ind = np.nonzero([path.contains_point(xy) for xy in self.xys[self.axes_idx]])[0]
        
#        if self.debug:
#            print('self.xys[self.axes_idx].shape : ',self.xys[self.axes_idx].shape)
#            print('len(self.ind) : ',len(self.ind), np.max(self.ind), np.min(self.ind))
        
        self.select_flag = "inside"
        self.mask_xys[:] = False
        self.mask_xys[self.ind] = True
        
        self.ind_not_sel=np.where(self.mask_xys == False)[0]
        
        cursor_wait = wx.BusyCursor()
        for ax in range(len(self.axes)):
            self.fc[ax][:, -1] = 0.05
            self.fc[ax][self.ind, -1] = 1
            self.axes[ax].collections[0].set_facecolors(self.fc[ax])
        self.canvas.draw_idle()
        
        self.input_mask_index_sel = self.input_mask_index[:,self.ind]
        #self.input_mask_index_not_sel = self.input_mask_index[:,self.ind_not_sel]
        
        # on récupère le numéro d'index des cycles selectionnés
        self.idx_cy_sel = np.unique(self.input_mask_index_sel[0,:])

        # on récupère le numéro d'index des cycles non selectionnés 
        # mais visible dans la fenétre graphique
        #self.idx_cy_not_sel = np.unique(self.input_mask_index_not_sel[0,:])

        # on initilalise à True par défaut le mask_ouput
        self.mask_output[self.input_mask_index[0,:],self.input_mask_index[1,:]] = True
        
        # on initialise à False que les cycles qui ont été selectionnés
        self.mask_output[self.idx_cy_sel,:] = False
        # on initialise à False que les cycles qui n'ont pas été selectionnés
        #self.mask_output [self.idx_cy_not_sel,:] = False
        
        # on met uniquement à True les points à l'intérieure de la selection graphique des cycles selectionnés
        self.mask_output[self.input_mask_index_sel[0,:],self.input_mask_index_sel[1,:]] = True

#        pdb.set_trace()
        del cursor_wait
        self.disconnect()
                            
    def plot_selection(self,alpha):
        """
            inside/outside mask selection managment 
        """
        if self.select_flag == "inside":
            self.plot_selection_outside(alpha)
            
            self.mask_xys[:] = True
            self.mask_xys[self.ind] = False

#                self.mask_output [self.input_mask_index[0,:],self.input_mask_index[1,:]] = True 
#                self.mask_output [self.input_mask_index_sel[0,:],self.input_mask_index_sel[1,:]] = False

            # on initialise à False que les cycles qui ont été selectionnés
            self.mask_output[self.idx_cy_sel,:] = True
            
            # on met uniquement à True les points à l'intérieure de la selection graphique des cycles selectionnés
            self.mask_output[self.input_mask_index_sel[0,:],self.input_mask_index_sel[1,:]] = False

#                self.mask_output = self.mask_output & np.array(self.common_data.DATA_MASK_PARAM & self.common_data.CYCLE_SEL)
            self.select_flag = "outside"

        elif self.select_flag == "outside":
            self.plot_selection_inside(alpha)

            self.mask_xys[:] = False
            self.mask_xys[self.ind] = True

#                self.mask_output [self.input_mask_index[0,:],self.input_mask_index[1,:]] = False
#                self.mask_output[self.input_mask_index_sel[0,:],self.input_mask_index_sel[1,:]] = True

            # on initialise à False que les cycles qui ont été selectionnés
            self.mask_output[self.idx_cy_sel,:] = False
            
            # on met uniquement à True les points à l'intérieure de la selection graphique des cycles selectionnés
            self.mask_output[self.input_mask_index_sel[0,:],self.input_mask_index_sel[1,:]] = True

#                self.mask_output = self.mask_output & np.array(self.common_data.DATA_MASK_PARAM & self.common_data.CYCLE_SEL)
            self.select_flag = "inside"

    def plot_selection_outside(self,alpha):
        """
            matplotlib variable and plot managment
        """
        for ax in range(len(self.axes)):
            self.fc[ax][:, -1] = 1
            self.fc[ax][self.ind, -1] = alpha
            self.axes[ax].collections[0].set_facecolors(self.fc[ax])
        self.canvas.draw_idle()

    def plot_selection_inside(self,alpha):
        """
            matplotlib variable and plot managment
        """
        for ax in range(len(self.axes)):
            self.fc[ax][:, -1] = alpha
            self.fc[ax][self.ind, -1] = 1
            self.axes[ax].collections[0].set_facecolors(self.fc[ax])
        self.canvas.draw_idle()

    def disconnect(self):
        """
            Matplotlib selector disconnect
        """
        for ax in range(len(self.axes)):
            self.Polysel[ax].disconnect_events()
