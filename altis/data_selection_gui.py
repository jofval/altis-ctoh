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
# Copyright (c) 2019 Legos/CTOH. All rights reserved.
# ----------------------------------------------------------------------

import pdb
import wx
import numpy as np
from altis.common_data import Singleton
from matplotlib.widgets import LassoSelector, PolygonSelector, MultiCursor
from matplotlib.path import Path
import cartopy.crs as ccrs
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import matplotlib as mpl
import matplotlib.cm as mpl_cm
import matplotlib.pyplot as plt
import xarray as xr

class DatasetSelection(object):
    """
    Data selected from matplotlib GUI tools
    
    """

    def __init__(self, fig, plt_list,axes_list, cm, cbar):
        self.fig = fig
        self.canvas = fig.canvas
        self.axes = axes_list 
        self.plt = plt_list
        [self.ax1,self.ax2,self.ax3,self.ax4] = axes_list 
        [self.plt1,self.plt2,self.plt3,self.plt4] = plt_list
        self.collections = dict()
        self.fc = dict()
        self.cm =cm
        self.cbar = cbar
#        for idx in range(len(self.axes)):
#            self.collections[idx] = self.axes[idx].collections[0].get_offsets()
#            self.fc[idx] = self.axes[idx].collections[0].get_facecolors()

        for idx,plt in enumerate(self.plt):
            self.collections[idx] = plt.get_offsets()
            self.fc[idx] = plt.get_facecolors()

        self.xys = self.collections
        self.init_selector()
        
        self.mask_xys = np.ones(self.xys[0].shape[0],dtype='bool')
        
        self.common_data = Singleton()
        self.MASTER_mask = self.common_data.DATA_MASK_SEL[-1]\
                             & self.common_data.DATA_MASK_PARAM\
                             & self.common_data.CYCLE_SEL
                             
        self.mask_output = np.array(self.MASTER_mask)
        self.input_mask_index = np.where(self.MASTER_mask)
        self.input_mask_index = np.array([self.input_mask_index[0],self.input_mask_index[1]])
        
        print('self.MASTER_mask.shape',self.MASTER_mask.shape)
        print('self.input_mask_index.shape',self.input_mask_index.shape)


        def get_axes( event):
            if hasattr(self,'current_axes'):
                pass                
            else:
                self.current_axes = event.inaxes
                print('button_press_event',self.axes.index(self.current_axes))

        def accept(event):
            print('event.key, ',event.key)
            if event.key == "enter":
                self.progress = wx.ProgressDialog("Data Selection Processing ...", "please wait", maximum=100, style=wx.PD_SMOOTH|wx.PD_AUTO_HIDE)
                self.progress.Update(10, "Mask processing...")
                self.axes[self.axes_idx].set_title("      ")
                self.canvas.mpl_disconnect(self.cid_axes)
                self.canvas.mpl_disconnect(self.cid_key)
                self.common_data.DATA_MASK_SEL.append(self.mask_output)
                
                xys_param = self.xys[1][self.mask_xys,0]
                norm = mpl.colors.Normalize(vmin=np.min(xys_param), vmax=np.max(xys_param))
                m = mpl_cm.ScalarMappable(norm=norm, cmap=self.cm)
                col = [list(m.to_rgba(x)) for x in xys_param]
                self.progress.Update(40, "Update plots...")

                for ax in range(len(self.axes)):
                    self.axes[ax].set_title("      ")
                    self.plt[ax].set_facecolors(col)
                    xys_output = self.xys[ax][self.mask_xys,:]
                    self.plt[ax].set_offsets(xys_output)

                self.progress.Update(70, "Update color range...")
                print('selected data...2 xys_output',xys_output.shape)
                    
                self.cbar.set_clim(vmin=np.min(xys_param),vmax=np.max(xys_param))
                self.cbar.draw_all()

                self.canvas.draw()
                self.progress.Update(100, "Update color range...")
                
                print('data_selection DATA_MASK : ',\
                            self.common_data.DATA_MASK_SEL[-1].shape,\
                            np.sum(self.common_data.DATA_MASK_SEL[-1]))
                self.progress.Destroy()
                
            elif event.key == "r":  # revers selection
                self.plot_selection(alpha = 0.01)
            elif event.key == "escape":  # Abort
                print("Aborted selection.")
                if hasattr(self,'axes_idx'):
                    self.axes[self.axes_idx].set_title("      ")
                    self.plot_selection_inside(alpha=1.0)
                self.canvas.mpl_disconnect(self.cid_axes)
                self.canvas.mpl_disconnect(self.cid_key)

        self.cid_axes = self.canvas.mpl_connect('button_press_event', get_axes)
        self.cid_key = self.canvas.mpl_connect("key_press_event", accept)          
        
    def init_selector(self):
        """
        PolygonSelector empèche le sharex de bien marcher dans les scatter plot.
        """
        self.Polysel = []
        lineprops = dict(color='r', linestyle='-', linewidth=1, alpha=0.5)
        markerprops = dict(marker='o', markersize=7, mec='k', mfc='k', alpha=0.5)
        for ax in self.axes:
#            self.Polysel.append(PolygonSelector(ax, onselect=self.onselect,useblit=True,\
#                                   lineprops = lineprops, markerprops = markerprops))
            self.Polysel.append(LassoSelector(ax, onselect=self.onselect,useblit=True))    #,\

    def onselect(self, verts):
    
        path = Path(verts)        

        #Recupere l'index de la figure courante
        self.axes_idx = self.axes.index(self.current_axes)
        print('self.axes_idx',self.axes_idx)
        self.axes[self.axes_idx].set_title("Data selection : 'r' key to reverse,\n'Enter' key to validate, 'Escape' key to aborte. ",color='r',fontweight='bold')
        
        self.ind = np.nonzero([path.contains_point(xy) for xy in self.xys[self.axes_idx]])[0]
        
        print('self.xys[self.axes_idx].shape : ',self.xys[self.axes_idx].shape)
        print('len(self.ind) : ',len(self.ind), np.max(self.ind), np.min(self.ind))
        
        self.select_flag = "inside"
        self.mask_xys[:] = False
        self.mask_xys[self.ind] = True
        for ax in range(len(self.axes)):
            self.fc[ax][:, -1] = 0.01
            self.fc[ax][self.ind, -1] = 1
            self.axes[ax].collections[0].set_facecolors(self.fc[ax])
        self.canvas.draw_idle()
        
#        pdb.set_trace()
        
        self.input_mask_index_sel = self.input_mask_index[:,self.ind]
        self.mask_output [self.input_mask_index[0,:],self.input_mask_index[1,:]] = False 
#        x = xr.DataArray(self.input_mask_index[0], dims=['cycle'])
#        y = xr.DataArray(self.input_mask_index[1], dims=['norm_index'])
####        self.mask_output [x,y] = True
#        for ix,iy in zip(x,y):
#            self.mask_output [ix,iy] = True

        self.mask_output [self.input_mask_index_sel[0,:],self.input_mask_index_sel[1,:]] = True
        self.mask_output = self.mask_output & np.array(self.common_data.DATA_MASK_PARAM & self.common_data.CYCLE_SEL)
        self.disconnect()
                            
    def plot_selection(self,alpha):
            if self.select_flag == "inside":
                self.plot_selection_outside(alpha)
                
                self.mask_xys[:] = True
                self.mask_xys[self.ind] = False

                self.mask_output [self.input_mask_index[0,:],self.input_mask_index[1,:]] = True 
                self.mask_output [self.input_mask_index_sel[0,:],self.input_mask_index_sel[1,:]] = False

                self.mask_output = self.mask_output & np.array(self.common_data.DATA_MASK_PARAM & self.common_data.CYCLE_SEL)
                self.select_flag = "outside"

            elif self.select_flag == "outside":
                self.plot_selection_inside(alpha)

                self.mask_xys[:] = False
                self.mask_xys[self.ind] = True

                self.mask_output [self.input_mask_index[0,:],self.input_mask_index[1,:]] = False
                self.mask_output[self.input_mask_index_sel[0,:],self.input_mask_index_sel[1,:]] = True

                self.mask_output = self.mask_output & np.array(self.common_data.DATA_MASK_PARAM & self.common_data.CYCLE_SEL)
                self.select_flag = "inside"

    def plot_selection_outside(self,alpha):
            for ax in range(len(self.axes)):
                self.fc[ax][:, -1] = 1
                self.fc[ax][self.ind, -1] = alpha
                self.axes[ax].collections[0].set_facecolors(self.fc[ax])
            self.canvas.draw_idle()

    def plot_selection_inside(self,alpha):
            for ax in range(len(self.axes)):
                self.fc[ax][:, -1] = alpha
                self.fc[ax][self.ind, -1] = 1
                self.axes[ax].collections[0].set_facecolors(self.fc[ax])
            self.canvas.draw_idle()

    def disconnect(self):
        for ax in range(len(self.axes)):
            self.Polysel[ax].disconnect_events()



