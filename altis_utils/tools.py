#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Module of tools for AlTiS.
#
# Created by Fabien Blarel on 2019-04-19. 
# Copyright (c) 2019 Legos/CTOH. All rights reserved.
# ----------------------------------------------------------------------
import pdb
import os
import re
import sys
import glob
import yaml
import numpy as np
import pkg_resources
import logging, sys
import geopandas as gpd 
from shapely.geometry import shape, Point, Polygon
import xarray as xr


class Error(Exception):
    pass

class FileNotFoundError(Error):
    def __init__(self,message):
        super().__init__(message)
        self.message_gui = message

#--------------------------------------------------------------------------
# Computation of stand absolute deviation (deviation in L1 norm) of a
# variable
#
#--------------------------------------------------------------------------
# 2014/04/04 | F. FRAPPART   | Creation 
#--------------------------------------------------------------------------
def std_abs_dev(vec,dim_label):
    sum_abs_diff = np.abs(vec-vec.median(dim=dim_label)).sum(dim=dim_label)
    N = len(vec.coords[dim_label])
    return (1/N)*sum_abs_diff


def kml_poly_select(kml_file,lon_mean,lat_mean):
    '''
       Selection des données contenues à l'intérieur du polygone défini dans le fichier kml
    '''
    
    gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
    polys = gpd.read_file(kml_file, driver='KML')
    poly = polys.loc[polys['Name'] ==  polys['Name'][0]]

    mask = [Point(lon,lat).within(poly.loc[0, 'geometry']) for lon,lat in zip(lon_mean,lat_mean)]
    
    return mask


def fatal_error(msg):
    """Print a message and exit"""
    logging.error(msg)
    print('\n>>>>> FATAL ERROR %s ... exiting\n' % msg)
    sys.exit(-1)

#---------------------------------------------------------------------------------------------------------------------------------       
# update_progress() : Displays or updates a console progress bar
    ## Accepts a float between 0 and 1. Any int will be converted to a float.
    ## A value under 0 represents a 'halt'.
    ## A value at 1 or bigger represents 100%
def update_progress(progress, title = ''):
    barLength = 20 # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float               \r\n"
    if progress < 0:
        progress = 0
        status = "Halt...                \r\n"
    if progress >= 1:
        progress = 1
        status = "Done.             \r\n"
    block = int(round(barLength*progress))
    text = "\r[{0}] Percent: [{1}] {2}% {3}".format(title, "#"*block + "-"*(barLength-block), "{:4.1f}".format(progress*100), status)
    sys.stdout.write(text)
    sys.stdout.flush()


def __config_load__(mission,mission_config_file):
    '''
        lecture des parametres de la mission
    '''
    if mission_config_file is None:
        mission_file_cfg = pkg_resources.resource_filename('altis', '../etc/config_mission.yml')
    else:
        if os.path.isfile(mission_config_file):
            mission_file_cfg = mission_config_file
        else:
            raise Exception('Mission configuration file not found.')
        
    with open(mission_file_cfg) as f:
        try:
            yaml_data = yaml.load(f)
        except:
            yaml_data = yaml.load(f, Loader=yaml.FullLoader) # A revoir pour créer un vrai loader

    if mission in yaml_data.keys():
        return yaml_data[mission]
    else:
        raise Exception(mission, ' mission is not already configurated.')


def __regex_file_parser__(mission,directory,mission_config_file):
    config_mission = __config_load__(mission,mission_config_file)
    filename_pattern = config_mission['filename_pattern']
    track_pattern = config_mission['track_pattern']
    cycle_pattern = config_mission['cycle_pattern']
    
    file_list=glob.glob(os.path.join(directory,'*.nc'))
    file_list.sort()
    file_list=[ filename.split(os.path.sep)[-1] for filename in file_list ]
    
    track=[]
    cycle=[]
    file_list_bad_regex=[]
    file_list_ok_regex=[]
    for idx,filename in enumerate(file_list):
        match = re.search(filename_pattern, filename)
        if match :
            match = re.search(track_pattern, filename)
            track.extend([int(match.group(2))])
            match = re.search(cycle_pattern, filename)
            cycle.extend([int(match.group(2))])
            file_list_ok_regex.extend([filename])
        else:
#            track.extend([None])
#            cycle.extend([None])
            file_list_bad_regex.extend([filename])
    
    
#    if track.count(None) > 0:
    if len(file_list_bad_regex) == len(file_list):
        message = ('The filenames are not conform to the filename '\
                        +'pattern of '+mission+' mission. None file '\
                        'could not be load.')
        print(message)
        raise FileNotFoundError(message)
#        else:
#            raise Exception('Some filenames are not conform to the filename '\
#                            +'pattern of '+mission+' mission and could not '\
#                            +'be load : \n',file_list_bad_regex)
    else:
        file_list = file_list_ok_regex
        track = np.array(track,dtype=np.int)
        cycle = np.array(cycle,dtype=np.int)
        list_track = np.unique(track)
        print(str(len(file_list))+' Files found for '+mission+' mission:\n'\
                +'    - Tracks : ',list_track)
    
        dtype_file_struct = ([('track', np.dtype('i4')),\
                                ('cycle', np.dtype('i4')),\
                                ('filename',np.dtype('U'+str(len(file_list[0]))))])
        file_struct = np.empty(len(file_list),dtype = dtype_file_struct)
        
        file_struct['track'] = track
        file_struct['cycle'] = cycle
        file_struct['filename'] = file_list
        return file_struct

