#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Altimetric Time Series (AlTiS)
# Patch to slove to_netcdf issu in the xarray library -> no netcdf4 for windows OS
#
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------

import numpy as np

import netCDF4 as nc
from netCDF4 import default_fillvals as nc_fillval 
from netCDF4 import date2num
import datetime as dt
import os

from altis_utils.tools import (
    __grp_format__,
)

def to_netcdf(filename, dataset):
    """
    To save the xarray dataset into netCDF4 file
    """
    
    with nc.Dataset(filename,'w') as nc_ds:
        for name, val in dataset.dims.items():
            nc_ds.createDimension(name,val)

        for name in dataset.coords.keys():
            if name in nc_ds.variables.keys():
                continue
            if dataset.coords[name].dtype == np.dtype('datetime64[ns]'):
                mask = np.isnan(dataset.coords[name].data)
                idx = np.where(~mask)
                nc_ds.createVariable(name,np.dtype('int64'),dataset.coords[name].dims, fill_value=np.datetime64('NaT'))
                nc_ds.variables[name].setncattr('units', 'seconds since '+str(dataset.coords[name].data[idx[0][0]]))
                nc_ds.variables[name].setncattr('calendar', 'proleptic_gregorian')
                idx = np.where(mask)
                dataset.coords[name].data[idx] = np.datetime64('1970-01-01T00:00:00.0')
                dt = date2num(dataset.coords[name].data.astype('M8[ms]').astype('O'),
                                nc_ds.variables[name].units,
                                calendar=nc_ds.variables[name].calendar)
                nc_ds.variables[name][:] = np.ma.array(dt.data,mask=mask)
            else:
                nc_ds.createVariable(name,dataset.coords[name].dtype,dataset.coords[name].dims)
                nc_ds.variables[name][:]=dataset.coords[name].data
            for attr, val in dataset.coords[name].attrs.items():
                nc_ds.variables[name].setncattr(attr, val)

        for name in dataset.data_vars.keys():
            output_name=__grp_format__(name)

            if dataset.data_vars[name].dtype == np.dtype('datetime64[ns]'):
                mask = np.isnan(dataset.data_vars[name].data)
                idx = np.where(~mask)
                nc_ds.createVariable(output_name,np.dtype('int64'),dataset.data_vars[name].dims, fill_value=np.datetime64('NaT'))
                nc_ds.variables[output_name].setncattr('units', 'seconds since '+str(dataset.data_vars[name].data[idx[0][0],idx[1][0]]))
                nc_ds.variables[output_name].setncattr('long_name', 'Time '+output_name)
                nc_ds.variables[output_name].setncattr('calendar', 'proleptic_gregorian')
                idx = np.where(mask)
                dataset.data_vars[name].data[idx] = np.datetime64('1970-01-01T00:00:00.0')
                dt = date2num(dataset.data_vars[name].data.astype('M8[ms]').astype('O'),
                                nc_ds.variables[output_name].units,
                                calendar=nc_ds.variables[output_name].calendar)
                nc_ds.variables[output_name][:] = np.ma.array(dt.data,mask=mask)
            else:
                nc_ds.createVariable(output_name,dataset.data_vars[name].dtype,dataset.data_vars[name].dims, fill_value=np.nan)
                nc_ds.variables[output_name][:]=dataset.data_vars[name].data
            for attr, val in dataset.data_vars[name].attrs.items():
                if not hasattr(nc_ds.variables[output_name],attr):
                    nc_ds.variables[output_name].setncattr(attr, val)
            nc_ds.variables[output_name].setncattr("coordinates", "date tracks cycle")

            
        for attr, val in dataset.attrs.items():
            nc_ds.setncattr(attr, val)


