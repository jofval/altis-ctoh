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

import numpy as np

from matplotlib.widgets import LassoSelector, PolygonSelector, MultiCursor
from matplotlib.path import Path

class DatasetSelection(object):
    """
    Data selected from matplotlib GUI tools
    
    """

    def __init__(self, fig, axes_list,plotfig_cfg,plot_param, cell_mask, alpha_other=0.1):
        self.fig = fig
        self.canvas = fig.canvas
        self.axes = axes_list 
        self.plotfig_cfg = plotfig_cfg
        self.plot_param = plot_param

        self.collections = dict()
        self.fc = dict()
        self.Npts = dict()

        for idx in range(len(self.axes)):
            self.collections[idx] = self.axes[idx].collections[0].get_offsets()
            self.fc[idx] = self.axes[idx].collections[0].get_facecolors()
            self.Npts[idx] = len(self.axes[idx].collections[0].get_offsets())

        self.alpha_other = alpha_other

        self.xys = self.collections

        self.init_selector()
        
        self.cell_mask_index = np.where(cell_mask)
        self.cell_mask_index = np.array([self.cell_mask_index[0],self.cell_mask_index[1]])

        self.array_idx = np.empty(self.cell_mask_index.shape)
        self.array_idx.fill(np.nan)
        
        print('self.cell_mask_index.shape',self.cell_mask_index.shape)
        
#        pdb.set_trace()
        #Récupération de l'axe selectionnées
        #cid : id pour deconnecter l'évenement
        self.canvas.mpl_connect('button_press_event', self.get_axes)
#        self.event_suppr = self.canvas.mpl_connect('key_press_event', self.apply_mask)
        

    def init_selector(self):
        """
        PolygonSelector empèche le sharex de bien marcher dans les scatter plot.
        """
        self.Polysel = dict()
        lineprops = dict(color='r', linestyle='-', linewidth=1, alpha=0.5)
        markerprops = dict(marker='o', markersize=7, mec='k', mfc='k', alpha=0.5)
        for ax_idx,ax in enumerate(self.axes):
            self.Polysel[ax_idx] = PolygonSelector(ax, onselect=self.onselect,\
                useblit=True,lineprops = lineprops, markerprops = markerprops)
        
                    
    #Récuperer l'axe courant
    def get_axes(self, event):
        self.current_axes = event.inaxes

    def onselect(self, verts):

        print('Test_onselect')       

        path = Path(verts)        

        print('self.current_axes',self.current_axes)
        #Recupere l'index de la figure courante
        self.axes_idx = self.axes.index(self.current_axes)
        print('self.axes_idx',self.axes_idx)
        
        self.ind = np.nonzero([path.contains_point(xy) for xy in self.xys[self.axes_idx]])[0]
        print('self.ind.shape',self.ind.shape)
        print('self.ind',self.ind)
        print('self.xys[self.axes_idx].shape',self.xys[self.axes_idx].shape)
        
        self.array_idx[:,0:len(self.ind)] = self.cell_mask_index[:,self.ind] 
        
        self.fc[self.axes_idx][:, -1] = self.alpha_other
        self.fc[self.axes_idx][self.ind, -1] = 1
        self.axes[self.axes_idx].collections[0].set_facecolors(self.fc[self.axes_idx])
        self.canvas.draw_idle()


    def disconnect(self):
        self.Polysel[self.axes_idx].disconnect_events()
        self.fc[self.axes_idx][:, -1] = 1
        self.collection[self.axes_idx].set_facecolors(self.fc[self.axes_idx])
        self.canvas.draw_idle()

def fig_layout(fig):
    ax0 = fig.add_subplot(2,2,1, projection=ccrs.PlateCarree())
#    ax0.autoscale()
    gl = ax0.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=0.5, color='white', alpha=1.0, linestyle='--')
    gl.xlabels_top = True
    gl.ylabels_left = True
    gl.xlabels_bottom = False
    gl.ylabels_right = False
    gl.xlines = True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
        
    ax1 = fig.add_subplot(2,2,2)    #,sharey=ax0)
    ax1.autoscale()
    ax1.grid(True)
    ax2 = fig.add_subplot(2,2,3)    #,sharex=ax0)
    ax2.autoscale()
    ax2.grid(True)
    ax3 = fig.add_subplot(2,2,4)    #,sharey=ax2)
    ax3.autoscale()
    ax3.grid(True)

    return ax0,ax1,ax2,ax3


def fig_draw(fig,axes_list,plotfig_cfg,plot_param):
    ax0,ax1,ax2,ax3 = axes_list
    cm,url,layer,RIVERS_10m = plotfig_cfg
    lon,lat,param,time = plot_param

    # J'ai fait un cmap car c'est le seul moyen pour récupérer les couleur de chaque point avec getfacecolor()
    cmap = plt.cm.get_cmap(cm)
    norm = clr.Normalize(vmin=np.min(param), vmax=np.max(param))

#    plt0 = ax0.scatter(lon,lat,c=param, marker='+',cmap=cm, vmin=np.min(param), vmax=np.max(param), norm=norm,transform=ccrs.PlateCarree())
    plt0 = ax0.scatter(lon,lat,c=cmap(norm(param.data.flatten())), marker='+',transform=ccrs.PlateCarree())
    ax0.add_wmts(url,layer)
    
    ax0.add_feature(RIVERS_10m)

    ax0.plot(x,y,transform=ccrs.PlateCarree())
#    plt1 = ax1.scatter(param,lat,c=param, marker='+',cmap=cm, vmin=np.min(param), vmax=np.max(param), norm=norm) 
#    plt2 = ax2.scatter(lon,param,c=param, marker='+',cmap=cm, vmin=np.min(param), vmax=np.max(param), norm=norm) 
#    plt3 = ax3.scatter(np.array(time),param,c=param, marker='+',cmap=cm, vmin=np.min(param), vmax=np.max(param), norm=norm) 
    plt1 = ax1.scatter(param,lat,c=cmap(norm(param.data.flatten())), marker='+') 
    plt2 = ax2.scatter(lon,param,c=cmap(norm(param.data.flatten())), marker='+') 
    plt3 = ax3.scatter(np.array(time),param,c=cmap(norm(param.data.flatten())), marker='+') 
    cbar = fig.colorbar(plt0, ax=[ax1,ax3], orientation='vertical')

#    pdb.set_trace()
#    cbar = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=[ax1,ax3],orientation='vertical')
        
#    cbar.set_label(param.attrs['long_name'], rotation=270)
 
    return plt0,plt1,plt2,plt3

if __name__ == '__main__':

    import matplotlib.colors as clr
    import matplotlib.pyplot as plt
    from matplotlib.cm import ScalarMappable
    from matplotlib.colorbar import ColorbarBase
    from track import Track

#    from cartopy.io.img_tiles import Stamen
    from utils.tools import __config_load__,update_progress,__regex_file_parser__
    
    import geopandas as gpd 
    
    #import cartopy.io.img_tiles as cimgt
    import cartopy.crs as ccrs
    from owslib.wmts import WebMapTileService
    from cartopy.io.shapereader import Reader
    from cartopy.feature import ShapelyFeature,NaturalEarthFeature,COLORS
    import cartopy.feature as cfeature
    import cartopy.io.img_tiles as cimgt
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    from pandas.plotting import register_matplotlib_converters
    import pkg_resources
    import yaml

    # Performance GUI
    # Line segment simplification and Using the fast style
    import matplotlib.style as mplstyle
    import matplotlib as mpl
    mplstyle.use('fast')
    mpl.rcParams['path.simplify'] = True
    mpl.rcParams['path.simplify_threshold'] = 1.0
    mpl.rcParams['agg.path.chunksize'] = 10000
   
    mission = 'j2D'
    data_directory = '/local/hdd/MAPS_DATA/j2D'
#    data_directory = '/home/blarel/DATA/j2D'
    track = 102
    surf_type = 'RiversLakes'
    kml_file = '/home/ctoh/blarel/prog/AlTiS_Software/prototype_GUI/102_j2D_Mississip.kml'
#    kml_file = '/home/blarel/prog/102_j2D_Mississip.kml'

    # Selection des fichiers trace
    file_struct = __regex_file_parser__(mission,data_directory)
    mask_file = file_struct['track'] == track
    file_list = file_struct['filename'][mask_file]
    
    # création de l'objet Track.
    tr=Track(mission,surf_type,data_directory,file_list,kml_file)


    # Lecture polygone contenu dans le fichier kml
    gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
    polys = gpd.read_file(kml_file, driver='KML')
    poly = polys.loc[polys['Name'] ==  polys['Name'][0]]
    x,y = poly['geometry'][0].exterior.xy

    altis_cfg = pkg_resources.resource_filename('altis', '../etc/altis_config.yml')
    with open(altis_cfg) as f:
        try:
            yaml_data = yaml.load(f)
        except:
            yaml_data = yaml.load(f, Loader=yaml.FullLoader) # A revoir pour créer un vrai loader
    url = yaml_data['wmts']['ground_map']['url']
    layer = yaml_data['wmts']['ground_map']['layer']
    
    RIVERS_10m =NaturalEarthFeature('physical','rivers_lake_centerlines', '10m', edgecolor=COLORS['water'],facecolor='none')

    lon = tr.data_val['lon_20hz']
    lat = tr.data_val['lat_20hz']
    param = tr.data_val['ice1_ku_Surf-Height_alti']
    time = tr.data_val['time_20hz']

    register_matplotlib_converters()
    
#        tiler = StamenTerrain()
#    tiler = Stamen('terrain-background',style='toner-labels')   # desired_tile_form='RGBA')
# Figure 1    
#    cm='viridis' #'hsv'
    cm='hsv'

    plt.ion() # Mode interactif pour fonctionner sous ipython. Cela ne fonctionne pas en ligne de commande : 'python data_selection_gui.py'
    fig = plt.figure()
    ax0,ax1,ax2,ax3 = fig_layout(fig)
    
    axes_list =[ax0,ax1,ax2,ax3]
    plotfig_cfg = [cm,url,layer,RIVERS_10m]
    plot_param = [lon,lat,param,time]
    
    plt0,plt1,plt2,plt3=fig_draw(fig,axes_list,plotfig_cfg,plot_param)
    
    cycle_mask = np.ones([param.shape[1]],dtype=np.dtype('bool'))
    cell_mask = np.ones(param.shape,dtype=np.dtype('bool'))
    
    
    print('param.shape',param.shape)
    print('lon.shape',lon.shape)
    print('lat.shape',lat.shape)
    
    mask_param = np.isnan(param)
    mask_lon = np.isnan(lon)
    mask_lat = np.isnan(lat)
#    mask_time = np.isnan(np.array(time))
#    
    cell_mask = ~mask_param & ~mask_lon & ~mask_lat
    
    print('plt0.get_facecolors().shape',plt0.get_facecolors().shape)
    
    
#    pdb.set_trace()
    selector = DatasetSelection(fig,axes_list,plotfig_cfg,plot_param,cell_mask)

