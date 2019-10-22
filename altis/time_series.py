import wx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import MultiCursor

import cartopy.crs as ccrs

from matplotlib.widgets import MultiCursor, Cursor
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as NavigationToolbar
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

from altis.common_data import Singleton

import pdb

class Time_Series_Panel ( wx.Frame ):
    def __init__( self,parent,data_opt):
        super().__init__(parent, title = "AlTiS : Time series",
            style=wx.FRAME_FLOAT_ON_PARENT | wx.DEFAULT_FRAME_STYLE,\
             pos=(10,50),size=(700,700))
        self.common_data = Singleton()
        self.param_name = self.common_data.param_name
        self.data_sel_config = data_opt
        self.InitUI()
        self.Center()
        
    def InitUI(self):
        
        timeseries_panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        self.CanvasPanel(timeseries_panel)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(self.plot_panel, proportion=1, flag=wx.EXPAND|wx.CENTER, border=8)
        vbox.Add(hbox1, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=10)
#        timeseries_panel.SetSizer(vbox)

        self.create_toolbar()
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetStatusText('AlTiS') 
        timeseries_panel.SetSizer(vbox) 
        timeseries_panel.Fit() 

    def create_toolbar(self):
        """
        Create a toolbar
        """
        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize((20,20))
 
        self.btnUpdate = wx.Button(self.toolbar, label='Refresh')
        self.toolbar.AddControl(self.btnUpdate)
        self.toolbar.AddSeparator()
        self.checkMean = wx.CheckBox( self.toolbar, label="Mean")
        self.toolbar.AddControl(self.checkMean, label="Show/Hide Mean" )
        self.toolbar.AddSeparator()
        self.btnCSVexport = wx.Button(self.toolbar, label='Export ...')
        self.toolbar.AddControl(self.btnCSVexport)
        self.toolbar.AddStretchableSpace()
        self.iconHelp = self.mk_iconbar("Help",wx.ART_HELP,"Help on AlTiS")

        self.toolbar.Realize()
        
        self.checkMean.SetValue(True)
        
        self.btnUpdate.Bind(wx.EVT_BUTTON, self.onUpdate)
        self.btnCSVexport.Bind(wx.EVT_BUTTON, self.onCSVexport)
        self.checkMean.Bind(wx.EVT_CHECKBOX, self.onMean)
        
    def mk_iconbar(self,bt_txt,art_id,bt_lg_txt):
    
        ico = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR, (16,16))
        itemTool = self.toolbar.AddTool(wx.ID_ANY, bt_txt, ico, bt_lg_txt)
        return itemTool
    
    def onOnTop(self,event):
        pass
            
    def CanvasPanel(self,panel):
        print('plot_panel')
        self.plot_panel=wx.Panel(panel)
        self.figure = Figure()
        self.ax1 = self.figure.add_subplot(2,2,1)
        self.ax1.set_title('Time Series')
        self.ax1.set_xlabel('Time (YYYY-MM)')
        self.ax1.set_ylabel('Mean')
        self.ax1.autoscale()
        self.ax2 = self.figure.add_subplot(2,2,2)
        self.ax2.set_ylabel('Nber of Sample')
        self.ax2.set_title('Histogramms')
        self.ax2.autoscale()
        self.ax3 = self.figure.add_subplot(2,2,3,sharex=self.ax1)
        self.ax3.set_xlabel('Time (YYYY-MM)')
        self.ax3.autoscale()
        self.ax4 = self.figure.add_subplot(2,2,4)
        self.ax4.set_ylabel('Nber of Sample')
        self.ax4.autoscale()
        self.canvas = FigureCanvas(self.plot_panel, -1, self.figure)
        
        self.list_axes = [self.ax1,self.ax2,self.ax3,self.ax4]
        self.list_axes_coord = [['Time','Param'],['Param','Samp. Nber'],['Time','Std'],['Std','Samp. Nber']]
        self.mpl_toolbar = NavigationToolbar(self.canvas)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        
        vbox.Add(self.mpl_toolbar, proportion=0, flag=wx.CENTER, border=8)
        vbox.Add(self.canvas, proportion=1, flag=wx.EXPAND|wx.CENTER, border=8)

        self.plot_panel.SetSizer(vbox)
        
        self.mouseMoveID = self.figure.canvas.mpl_connect('motion_notify_event',self.onMotion)
        self.param_compute()
        self.draw()
        self.canvas.draw()
        
        self.multi = MultiCursor(self.canvas, (self.ax1, self.ax3), color='black', lw=1)
        
    def onMotion(self, event):
        x = event.x
        y = event.y
        xdata = event.xdata
        ydata = event.ydata
        if event.inaxes in self.list_axes:
            idx = self.list_axes.index(event.inaxes)
            [xlabel,ylabel] = self.list_axes_coord[idx]
            self.statusbar.SetStatusText("AlTiS\t%s : %s, %s : %s" % (xlabel,"{: 10.6f}".format(xdata),ylabel,"{: 10.6f}".format(ydata)))
        else:
            self.statusbar.SetStatusText("AlTiS")
#        
    def onUpdate(self,event):
#        self.sel_id.disconnect()
        
        self.param_compute()
        self.param_name = self.common_data.param_name
        self.figure.suptitle(self.param_name, fontsize=16)
        
        self.median_sel.remove()
        self.median_plt.remove()
        _ = [b.remove() for b in self.median_bars]
        self.std_plt.remove()
        _ = [b.remove() for b in self.std_bars]

        if self.checkMean.IsChecked():
            self.mean_plt.remove()
            _ = [b.remove() for b in self.mean_bars]
            self.mean_plt, = self.ax1.plot(self.abcisse,self.mean_param,'-+b', label='mean' ,alpha=0.5)
            counts, bins, self.mean_bars = self.ax2.hist(self.mean_param,50,color='b',label='mean',alpha=0.5)

        self.median_plt, = self.ax1.plot(self.abcisse,self.median_param, '.-r',label='median',alpha=0.5)
        self.median_sel, = self.ax1.plot(self.abcisse,self.median_param, 'o',picker=5,alpha=0.0)
        counts, bins, self.median_bars = self.ax2.hist(self.median_param,50, color='r',label='median',alpha=0.5)
        self.std_plt, = self.ax3.plot(self.abcisse,self.std_param,'-+g', label='std' ,alpha=0.5)
        counts, bins, self.std_bars = self.ax4.hist(self.std_param,50,color='g',label='std',alpha=0.5)

        self.ax1.set_ylabel(self.param_name+' ('+self.param_units+')')
        self.ax2.set_xlabel(self.param_name+' ('+self.param_units+')')
        self.ax3.set_ylabel(self.param_name+' ('+self.param_units+')')
        self.ax4.set_xlabel(self.param_name+' ('+self.param_units+')')
        
        self.ax1.relim()
        self.ax2.relim()
        self.ax3.relim()
        self.ax4.relim()
        self.canvas.draw()
 
#        self.sel_id = self.canvas.mpl_connect('pick_event', self.onpick)
        
        
    def onMean(self,even):
        if self.checkMean.IsChecked():
            self.mean_plt, = self.ax1.plot(self.abcisse,self.mean_param,'-+b', label='mean' ,alpha=0.5)
            counts, bins, self.mean_bars = self.ax2.hist(self.mean_param,50,color='b',label='mean',alpha=0.5)
            self.canvas.draw()
        else:
            self.mean_plt.remove()
            _ = [b.remove() for b in self.mean_bars]
            self.canvas.draw()
            
    def param_compute(self,):
        self.mask = self.common_data.CYCLE_SEL\
             &  self.common_data.DATA_MASK_SEL[-1]\
             & self.common_data.DATA_MASK_PARAM
             
#        median_param = self.common_data.param.where(mask).median(dim='cycle')
#        mean_param = self.common_data.param.where(mask).mean(dim='cycle')
#        std_param = self.common_data.param.where(mask).std(dim='cycle')
#        mean_lon = self.common_data.lon.where(mask).mean(dim='cycle')
#        mean_lat = self.common_data.lat.where(mask).mean(dim='cycle')
#    
        if self.common_data.param.units is None:
            self.param_units = ''
        else:
            self.param_units = self.common_data.param.units
        
        if 'gdr_index' in self.common_data.param.dims:
            self.dim_index = 'gdr_index'
        else:
            self.dim_index = 'norm_index'
        
        self.median_param = self.common_data.param.where(self.mask).median(dim=self.dim_index)  #,skipna=True)
        self.mean_param = self.common_data.param.where(self.mask).mean(dim=self.dim_index)  #,skipna=True)
        self.std_param = self.common_data.param.where(self.mask).std(dim=self.dim_index)    #,skipna=True)
        self.abcisse = np.array(self.common_data.param.coords['date'].where(self.mask.any(axis=1)))
        self.lon_sel = self.common_data.tr[self.common_data.lon_hf_name].where(self.mask)
        self.param_sel = self.common_data.tr[self.common_data.param_name].where(self.mask)
    
    
            
    def draw(self):
        
        self.figure.suptitle(self.param_name, fontsize=16)
        
        self.mean_plt, = self.ax1.plot(self.abcisse,self.mean_param,'-+b', label='mean' ,alpha=0.5)
        self.median_plt, = self.ax1.plot(self.abcisse,self.median_param, '.-r',label='median',alpha=0.5)
        self.median_sel, = self.ax1.plot(self.abcisse,self.median_param, 'o', picker=5,alpha=0.0) 
        self.ax1.legend((self.mean_plt,self.median_plt),('mean','median'))
        
        self.ax1.set_ylabel(self.param_name+' ('+self.param_units+')')
        self.ax1.grid(True)

        counts, bins, self.mean_bars = self.ax2.hist(self.mean_param,50,color='b',label='mean',alpha=0.5)
        counts, bins, self.median_bars = self.ax2.hist(self.median_param,50, color='r',label='median',alpha=0.5)
        self.ax2.legend()
        self.ax2.set_xlabel(self.param_name+' ('+self.param_units+')')
        self.ax2.grid(True)

        self.std_plt, = self.ax3.plot(self.abcisse,self.std_param,'-+g', label='std' ,alpha=0.5)
        self.ax3.legend()
        self.ax3.set_ylabel(self.param_name+' ('+self.param_units+')')
        self.ax3.grid(True)

        counts, bins, self.std_bars = self.ax4.hist(self.std_param,50,color='g',label='std',alpha=0.5)
        self.ax4.legend()
        self.ax4.set_xlabel(self.param_name+' ('+self.param_units+')')
        self.ax4.grid(True)

        self.canvas.mpl_connect('pick_event', self.onpick)

    def onCSVexport(self,event):
        
        mask = self.common_data.CYCLE_SEL\
             &  self.common_data.DATA_MASK_SEL[-1]\
             & self.common_data.DATA_MASK_PARAM
             
        list_param = list(self.common_data.tr.keys())
        list_param.remove(self.common_data.time_hf_name)
        list_param.remove(self.common_data.lon_hf_name)
        list_param.remove(self.common_data.lat_hf_name)
        
        list_param_coord = [self.common_data.lon_hf_name, self.common_data.lat_hf_name]
        
        array = list()
        header_csvfile = list()
        array.append(np.array(pd.Series(self.common_data.param.coords['date'].where(mask.any(axis=1))).dt.strftime("%Y-%m-%d")))

        for param in list_param_coord:
            array.append(self.common_data.tr[param].where(mask).mean(dim=self.dim_index).data)
            header_csvfile.extend([param+'_mean'])

        for param in list_param:
            array.append(self.common_data.tr[param].where(mask).median(dim=self.dim_index).data)
            array.append(self.common_data.tr[param].where(mask).mean(dim=self.dim_index).data)
            array.append(self.common_data.tr[param].where(mask).std(dim=self.dim_index).data)
            header_csvfile.extend([param+'_median',param+'_mean',param+'_std'])
      
        array.append(np.sum(mask,axis=1).data)
        array = pd.DataFrame(array).T
        header_csvfile = ['date'] + header_csvfile + ['number of sample']

        default_filaname = "AlTiS_TimeSeries_"+self.data_sel_config['mission']+"_{:04d}".format(self.data_sel_config['track'])
        
        latpos = self.common_data.lat.where(mask).mean(dim=self.dim_index).mean(dim='cycle')
        if latpos >= 0.0:
            latpos_flag = 'N{:04d}'.format(int(latpos*100))
        else:
            latpos_flag = 'S{:04d}'.format(int(latpos*-100))
        

        with wx.FileDialog(self, message="Export Time Series as CSV file" ,
           defaultDir=self.data_sel_config['data_dir'], defaultFile=default_filaname+'_'+latpos_flag ,wildcard="CSV files (*.csv)|*.csv",
           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,) as fileDialog:


            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # save the current contents in the file
            pathname = fileDialog.GetPath()
            try:
                array.to_csv(pathname, header=header_csvfile)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    def onpick(self,event):

        if event.artist!=self.median_sel: return True

        N = len(event.ind)
        if not N: return True
        
        figi = plt.figure()
        print('event.ind',event.ind)
        for subplotnum, dataind in enumerate(event.ind):
            ax = figi.add_subplot(N,1,subplotnum+1)
            ax.plot(self.lon_sel[dataind],self.param_sel[dataind],'.')
            ax.set_title('Cycle number : %04d,\nMedian value = %1.3f, Mean value = %1.3f, Std = %1.3f '%(dataind,self.median_param[dataind],self.mean_param[dataind],self.std_param[dataind]))
            ax.set_ylabel(self.param_name+' ('+self.param_units+')')
            ax.set_xlabel('Longitude (deg)')
            ax.grid()
        #            ax.text(0.05, 0.9, 'mu=%1.3f\nsigma=%1.3f'%(mean_H_param[dataind], std_H_param[dataind]),
        #                    transform=ax.transAxes, va='top')
        #            ax.set_ylim(-0.5, 1.5)
        figi.show()
        return True

            
#def plot_time_series(tr,mask):
#    cm='hsv'

#    lon = tr.data_val['lon_20hz'].where(mask).mean(dim='cycle')
#    lat = tr.data_val['lat_20hz'].where(mask).mean(dim='cycle')
#    
#    abcisse = lon
#    
#    param = tr.data_val['ice1_ku_SurfHeight_alti'].where(mask).mean(dim='cycle')
#    std_param = tr.data_val['ice1_ku_SurfHeight_alti'].where(mask).std(dim='cycle')
#    fig = plt.figure()
#    ax1 = fig.add_subplot(7,1,1)
#    ax1.set_title('Mean parameter along the normalized track')
#    plt1 = ax1.scatter(abcisse,param,c=param, marker='+',cmap=cm ) 
#    ax1.set_ylabel('Surface height (m)')
#    ax1.grid()
#    ax2 = fig.add_subplot(7,1,2,sharex=ax1)
#    plt2 = ax2.scatter(abcisse,std_param,c=std_param, marker='+',cmap=cm ) 
#    ax2.set_ylabel('Std Surface height (m)')
#    ax2.grid()
#    
#    param = 10.0*np.log10(np.power(10.0,tr.data_val['ice_sig0_20hz_ku']/10.).where(mask).mean(dim='cycle'))
#    std_param = 10.0*np.log10(np.power(10.0,tr.data_val['ice_sig0_20hz_ku']/10.).where(mask).std(dim='cycle'))
#    ax3 = fig.add_subplot(7,1,3,sharex=ax1)
#    plt3 = ax3.scatter(abcisse,param,c=param, marker='+',cmap=cm ) 
#    ax3.set_ylabel('Sig0 (dB)')
#    ax3.grid()
#    ax4 = fig.add_subplot(7,1,4,sharex=ax1)
#    plt4 = ax4.scatter(abcisse,std_param,c=std_param, marker='+',cmap=cm ) 
#    ax4.set_ylabel('Std Sig0 (dB)')
#    ax4.grid()

#    param = tr.data_val['peakiness_20hz_ku'].where(mask).mean(dim='cycle')
#    std_param = tr.data_val['peakiness_20hz_ku'].where(mask).std(dim='cycle')
#    ax5 = fig.add_subplot(7,1,5,sharex=ax1)
#    plt5 = ax5.scatter(abcisse,param,c=param, marker='+',cmap=cm ) 
#    ax5.set_ylabel('Peakiness')
#    ax5.grid()
#    ax6 = fig.add_subplot(7,1,6,sharex=ax1)
#    plt6 = ax6.scatter(abcisse,std_param,c=std_param, marker='+',cmap=cm ) 
#    ax6.set_ylabel('Std Peakiness')
#    ax6.grid()

#    ax7 = fig.add_subplot(7,1,7,sharex=ax1)
#    plt7 = ax7.scatter(abcisse,std_param.coords['count'],c=std_param.coords['count'], marker='+',cmap=cm ) 
#    ax7.set_xlabel('lon')
#    ax7.set_ylabel('Count')
#    ax7.grid()
#    multi_normpass = MultiCursor(fig.canvas, (ax1, ax2, ax3, ax4, ax5, ax6, ax7), color='r', lw=1)
#    
##-------------------------------------------------------------------------------

#    H_param = tr.data_val['ice1_ku_SurfHeight_alti'].where(mask).data

#    Lon = tr.data_val['lon_20hz'].where(mask).data

#    mean_H_param = tr.data_val['ice1_ku_SurfHeight_alti'].where(mask).mean(dim='norm_index')
#    std_H_param = tr.data_val['ice1_ku_SurfHeight_alti'].where(mask).std(dim='norm_index')

##    pdb.set_trace()
##-------------------------------------------------------------------------------


#    def onpick(event):

#        if event.artist!=line: return True

#        N = len(event.ind)
#        if not N: return True


#        figi = plt.figure()
#        print('event.ind',event.ind)
#        for subplotnum, dataind in enumerate(event.ind):
#            ax = figi.add_subplot(N,1,subplotnum+1)
#            ax.plot(Lon[dataind],H_param[dataind],'.')
#            ax.set_title('Cycle number : %04d,\nMean value = %1.3f, Std = %1.3f '%(dataind,mean_H_param[dataind], std_H_param[dataind]))
#            ax.set_ylabel('Surface height (m)')
#            ax.set_xlabel('Longitude (deg)')
#            ax.grid()
##            ax.text(0.05, 0.9, 'mu=%1.3f\nsigma=%1.3f'%(mean_H_param[dataind], std_H_param[dataind]),
##                    transform=ax.transAxes, va='top')
##            ax.set_ylim(-0.5, 1.5)
#        figi.show()
#        return True


#    param = tr.data_val['ice1_ku_SurfHeight_alti'].where(mask).mean(dim='norm_index')
#    std_param = tr.data_val['ice1_ku_SurfHeight_alti'].where(mask).std(dim='norm_index')
#    abcisse = np.array(param.coords['date'].where(mask.any(axis=1)))

#    fig = plt.figure()
#    ax1 = fig.add_subplot(2,2,1)
#    ax1.set_title('Surface height Time series')
#    
##    line, = ax1.plot(abcisse,param, '+', picker=5)  # 5 points tolerance


#    plt1 = ax1.scatter(abcisse,param,c=param, marker='+',cmap=cm ) 
#    line, = ax1.plot(abcisse,param, '+', picker=5)  # 5 points tolerance
#    ax1.set_ylabel('Surface height (m)')
#    ax1.grid()
#    
#    vmin = np.min(param)
#    vmax = np.max(param)
#    ax2 = fig.add_subplot(2,2,2)
#    ax2.set_title('histo')
#    plt2 = ax2.hist(param,50)
##    n, bins, patches = ax2.hist(np.array(param),50, (vmin,vmax), normed=True, histtype='bar')
##    cm = plt.cm.get_cmap(cm)
##    bin_centers = 0.5 * (bins[:-1] + bins[1:])
##    # scale values to interval [0,1]
##    col = bin_centers - min(bin_centers)
##    col /= max(col)
##    
##    for c, p in zip(col, patches):
##        ax2.setp(p, 'facecolor', cm(c))

#    ax2.set_xlabel('Surface height (m)')
#    ax2.grid()
#    ax3 = fig.add_subplot(2,2,3,sharex=ax1)
#    ax3.set_title('Std Time series')
#    plt3 = ax3.scatter(abcisse,std_param,c=std_param, marker='+',cmap=cm ) 
#    ax3.set_ylabel('Std Surface height (m)')
#    ax3.set_xlabel('Time date')
#    ax3.grid()

#    vmin = np.min(std_param)
#    vmax = np.max(std_param)
#    ax4 = fig.add_subplot(2,2,4)
#    ax4.set_title('histo')
#    plt4 = ax4.hist(std_param,50)
#    ax4.set_xlabel('Std Surface height (m)')
#    ax4.grid()
#    
#    multi = MultiCursor(fig.canvas, (ax1, ax3), color='r', lw=1)
#    
#    
#    fig.canvas.mpl_connect('pick_event', onpick)
#    
#    plt.show()

