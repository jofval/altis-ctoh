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
from altis_utils.tools import med_abs_dev
import warnings
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
        self.checkMean = wx.CheckBox( self.toolbar, label="Mean/Std")
        self.toolbar.AddControl(self.checkMean, label="Show/Hide Mean/Std" )
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

    def onUpdate(self,event):

        self.param_compute()
        self.param_name = self.common_data.param_name
        self.figure.suptitle(self.param_name, fontsize=16)
        
        self.median_sel.remove()
        self.median_plt.remove()
        _ = [b.remove() for b in self.median_bars]
        self.med_abs_dev_plt.remove()
        _ = [b.remove() for b in self.med_abs_dev_bars]

        if self.checkMean.IsChecked():
            self.mean_plt.remove()
            _ = [b.remove() for b in self.mean_bars]
            self.std_plt.remove()
            _ = [b.remove() for b in self.std_bars]
            self.mean_plt, = self.ax1.plot(self.abcisse,self.mean_param,'-+b', label='mean' ,alpha=0.5)
            counts, bins, self.mean_bars = self.ax2.hist(self.mean_param,50,color='b',label='mean',alpha=0.5)

            self.std_plt, = self.ax3.plot(self.abcisse,self.std_param,'-+g', label='std' ,alpha=0.5)
            counts, bins, self.std_bars = self.ax4.hist(self.std_param,50,color='g',label='std',alpha=0.5)

        self.median_plt, = self.ax1.plot(self.abcisse,self.median_param, '.-r',label='median',alpha=0.5)
        self.median_sel, = self.ax1.plot(self.abcisse,self.median_param, 'o',picker=5,alpha=0.0)
        counts, bins, self.median_bars = self.ax2.hist(self.median_param,50, color='r',label='median',alpha=0.5)

        self.med_abs_dev_plt, = self.ax3.plot(self.abcisse,self.med_abs_dev_param,'-+y', label='med_abs_dev' ,alpha=0.5)
        counts, bins, self.med_abs_dev_bars = self.ax4.hist(self.med_abs_dev_param,50,color='y',label='med_abs_dev',alpha=0.5)

        self.ax1.set_ylabel(self.param_name+' ('+self.param_units+')')
        self.ax2.set_xlabel(self.param_name+' ('+self.param_units+')')
        self.ax3.set_ylabel(self.param_name+' ('+self.param_units+')')
        self.ax4.set_xlabel(self.param_name+' ('+self.param_units+')')
        
        self.ax1.relim()
        self.ax2.relim()
        self.ax3.relim()
        self.ax4.relim()
        self.canvas.draw()
 
        
    def onMean(self,even):
        if self.checkMean.IsChecked():
            self.mean_plt, = self.ax1.plot(self.abcisse,self.mean_param,'-+b', label='mean' ,alpha=0.5)
            counts, bins, self.mean_bars = self.ax2.hist(self.mean_param,50,color='b',label='mean',alpha=0.5)
            self.std_plt, = self.ax3.plot(self.abcisse,self.std_param,'-+g', label='std' ,alpha=0.5)
            counts, bins, self.std_bars = self.ax4.hist(self.std_param,50,color='g',label='std',alpha=0.5)
            self.canvas.draw()
        else:
            self.mean_plt.remove()
            self.std_plt.remove()
            _ = [b.remove() for b in self.mean_bars]
            _ = [b.remove() for b in self.std_bars]
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
            self.dim_cycle = 'cycle_index'
        else:
            self.dim_index = 'norm_index'
            self.dim_cycle = 'cycle'
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.median_param = self.common_data.param.where(self.mask).median(dim=self.dim_index)  #,skipna=True)
            self.med_abs_dev_param = med_abs_dev(self.common_data.param.where(self.mask),self.dim_index)  #,skipna=True)
            self.mean_param = self.common_data.param.where(self.mask).mean(dim=self.dim_index)  #,skipna=True)
            self.std_param = self.common_data.param.where(self.mask).std(dim=self.dim_index)    #,skipna=True)
            self.abcisse = np.array(self.common_data.param.coords['date'].where(self.mask.any(axis=1)))
            self.lon_sel = self.common_data.tr[self.common_data.lon_hf_name].where(self.mask)
            self.param_sel = self.common_data.tr[self.common_data.param_name].where(self.mask)
    
            
    def draw(self):
        
        self.figure.suptitle(self.param_name, fontsize=16)

#        if len(np.unique(self.median_param.coords['tracks'].data)) > 1 :
#            for t in np.unique(self.median_param.coords['tracks'].data):
#                idx_t = np.where(self.median_param.coords['tracks'].data == t)
#                self.mean_plt, = self.ax1.plot(self.abcisse[idx_t],self.mean_param[idx_t],'-+', label='mean' ,alpha=0.5)
#                self.median_plt, = self.ax1.plot(self.abcisse[idx_t],self.median_param[idx_t], '.-',label='median',alpha=0.5)
#                self.median_sel, = self.ax1.plot(self.abcisse[idx_t],self.median_param[idx_t], 'o', picker=5,alpha=0.0) 
#                self.ax1.legend((self.mean_plt,self.median_plt),('mean','median'))
#        
#        else:

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
        self.med_abs_dev_plt, = self.ax3.plot(self.abcisse,self.med_abs_dev_param,'-+y', label='med_abs_dev' ,alpha=0.5)
        self.ax3.legend()
        self.ax3.set_ylabel(self.param_name+' ('+self.param_units+')')
        self.ax3.grid(True)

        counts, bins, self.std_bars = self.ax4.hist(self.std_param,50,color='g',label='std',alpha=0.5)
        counts, bins, self.med_abs_dev_bars = self.ax4.hist(self.med_abs_dev_param,50,color='y',label='med_abs_dev',alpha=0.5)
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
        
        export_param_list = list_param
        
        list_param = self.export_control_dialog(export_param_list)
        print (list_param)
        
        if list_param is None:
            return
        
        mask_cycle = np.any(mask,axis=1).data
        
        array = list()
        header_csvfile = list()
        array.append(np.array(self.common_data.param.coords['cycle'].where(mask.any(axis=1)),dtype='int')[mask_cycle])
        if 'tracks' in self.common_data.param.coords._names:
            array.append(np.array(self.common_data.param.coords['tracks'].where(mask.any(axis=1)),dtype='int')[mask_cycle])
        else:
            array.append([int(self.data_sel_config['track'])]*len(self.common_data.param.coords['cycle'])[mask_cycle])
        array.append(np.array(pd.Series(self.common_data.param.coords['date'].where(mask.any(axis=1))).dt.strftime("%Y-%m-%d"))[mask_cycle])
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for param in list_param_coord:
                array.append(self.common_data.tr[param].where(mask).mean(dim=self.dim_index).data[mask_cycle])
                header_csvfile.extend([param+'_mean (deg)'])

            for param in list_param:
                if not 'units' in self.common_data.tr[param].attrs.keys():
                    self.common_data.tr[param].attrs['units']='None'
                array.append(self.common_data.tr[param].where(mask).median(dim=self.dim_index).data[mask_cycle])
                array.append(med_abs_dev(self.common_data.tr[param].where(mask),self.dim_index).data[mask_cycle])
                array.append(self.common_data.tr[param].where(mask).mean(dim=self.dim_index).data[mask_cycle])
                array.append(self.common_data.tr[param].where(mask).std(dim=self.dim_index).data[mask_cycle])
                header_csvfile.extend([param+'_median ('+self.common_data.tr[param].units+')',\
                                        param+'_med_abs_dev ('+self.common_data.tr[param].units+')',\
                                        param+'_mean ('+self.common_data.tr[param].units+')',\
                                        param+'_std ('+self.common_data.tr[param].units+')'])
      
        array.append(np.sum(mask,axis=1).data[mask_cycle])
        array = pd.DataFrame(array).T
        header_csvfile = ['Cycle number','Track number','date (Year-Month-Day)'] + header_csvfile + ['number of sample']

        if self.data_sel_config['track'] == 'Tracks':
            default_filaname = "AlTiS_TimeSeries_"+self.data_sel_config['mission']+"_Tracks"
        else:        
            default_filaname = "AlTiS_TimeSeries_"+self.data_sel_config['mission']+"_{:04d}".format(int(self.data_sel_config['track']))
        
        latpos = self.common_data.lat.where(mask).mean(dim=self.dim_index).mean(dim=self.dim_cycle)
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


    def export_control_dialog(self, export_param_list):
        """
            Appel de la fenetre de dialogue pour la selection dee paramétres à exporter dans les fichiers CSV.
        """
        with Export_param_sel_Window(export_param_list) as param_output_diag:
             param_output_diag.Center()
             param_output_diag.Show()
             if param_output_diag.ShowModal() == wx.ID_OK:
                 print("ShowModal == wx.ID_OK")
                 return param_output_diag.param_sel
             else:
                 return None
                 print('Cancel')
        

    def onpick(self,event):

        if event.artist!=self.median_sel: return True

        N = len(event.ind)
        if not N: return True
        
        figi = plt.figure()
        print('event.ind',event.ind) #self.common_data.param.coords['cycle']
        
        for subplotnum, dataind in enumerate(event.ind):
            ax = figi.add_subplot(N,1,subplotnum+1)
            ax.plot(self.lon_sel[dataind],self.param_sel[dataind],'.')
            ax.set_title('Cycle number : %04d,\nMedian value = %1.3f, Mean value = %1.3f, Std = %1.3f '%(int(self.common_data.param.cycle[dataind].data)
,self.median_param[dataind],self.mean_param[dataind],self.std_param[dataind]))
            ax.set_ylabel(self.param_name+' ('+self.param_units+')')
            ax.set_xlabel('Longitude (deg)')
            ax.grid()
        #            ax.text(0.05, 0.9, 'mu=%1.3f\nsigma=%1.3f'%(mean_H_param[dataind], std_H_param[dataind]),
        #                    transform=ax.transAxes, va='top')
        #            ax.set_ylim(-0.5, 1.5)
        figi.show()
        return True




class Export_param_sel_Window(wx.Dialog):
    def __init__(self,param_sel_default):    #,data_opt):
        super().__init__(None,title = "Export Parameters Selection",style=wx.RESIZE_BORDER) #,size = wx.GetClientSize()) #wx.DisplaySize())

        self.param_sel = param_sel_default

        self.IU_Panel()

        self.Show()
        
    def IU_Panel(self):
        scroll_panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        scroll_panel.SetupScrolling()

        sizer = wx.GridBagSizer(6, 15)
        
        self.checked_param = {}
        sb = wx.StaticBox(scroll_panel, label="Default Parameters")
        boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)

        for p in ['Cycle number','Track number','date (Year-Month-Day)', 'lon', 'lat','number of sample']:
            boxsizer.Add(wx.StaticText(scroll_panel, label=p),
                flag=wx.LEFT|wx.TOP, border=5) 

        sizer.Add(boxsizer, pos=(1, 0), span=(1, 5),
            flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT , border=10)        
        

        sb = wx.StaticBox(scroll_panel, label="Parameters")
        boxsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)

        for p in self.param_sel:
            self.checked_param[p]=wx.CheckBox(scroll_panel, label=p)
            boxsizer.Add(self.checked_param[p],
                flag=wx.LEFT|wx.TOP, border=5)
            
            if 'SurfHeight' in p:
                self.checked_param[p].SetValue(True)

        sizer.Add(boxsizer, pos=(2, 0), span=(1, 5),
            flag=wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT , border=10)        
        
        btn_help = wx.Button(scroll_panel, label='Help')
        sizer.Add(btn_help, pos=(7, 0), flag=wx.LEFT, border=10)

        btn_ok = wx.Button(scroll_panel, wx.ID_OK, label="Ok")
        sizer.Add(btn_ok, pos=(7, 3))

        btn_cancel = wx.Button(scroll_panel, wx.ID_CANCEL, label="Cancel")
        sizer.Add(btn_cancel, pos=(7, 4), span=(1, 1),
            flag=wx.BOTTOM|wx.RIGHT, border=10)
        
        
        for p in self.checked_param.keys():
            self.checked_param[p].Bind(wx.EVT_CHECKBOX, self.update_checked_param_list)
        
        self.param_sel = []
        for p in self.checked_param.keys():
            if self.checked_param[p].IsChecked():
                self.param_sel.append(p)
        
        sizer.AddGrowableCol(2)

        scroll_panel.SetSizer(sizer)
        sizer.Fit(self)
        
        
    def update_checked_param_list(self,event):
        self.param_sel = []
        for p in self.checked_param.keys():
            if self.checked_param[p].IsChecked():
                self.param_sel.append(p)
                
        
        
        
    
 
