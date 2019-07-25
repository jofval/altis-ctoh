#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Track Class
#
# Created by Fabien Blarel on 2019-04-19. 
# Copyright (c) 2019 Legos/CTOH. All rights reserved.
# ----------------------------------------------------------------------
import pdb
import argparse
import os
import warnings
import re
import sys
import glob
import time
import yaml
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt  
import geopandas as gpd                                                                                                                                                                                                                
from shapely.geometry import shape, Point, Polygon
import pkg_resources
from shutil import copyfile

from utils.tools import __config_load__,update_progress,__regex_file_parser__, fatal_error

from cartopy.io.img_tiles import StamenTerrain
#from cartopy.io.img_tiles import Stamen

#import cartopy.io.img_tiles as cimgt
import cartopy.crs as ccrs
from owslib.wmts import WebMapTileService
from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature,NaturalEarthFeature,COLORS
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from pandas.plotting import register_matplotlib_converters

from flood_indice._version import __version__, __revision__


class Track(object):
    def __init__(self,mission,surf_type,data_directory,file_list,mission_config_file=None,kml_file=None):
        ''' 
            Initialisation de la classe Track:
                - Lecture des données
                - Normalisation des traces (optionel si norm_index existe)
                - Calcul des ranges
        '''
        self.mission = mission
        self.surf_type = surf_type

        # Appel de la fonction "utils" afin de charger les parametres prés définit        
        param_config = __config_load__(mission,mission_config_file)
        self.norm_index_hf_name = param_config['param']['norm_index_hf']
        self.time_hf_name = param_config['param']['time_hf']
        self.time_lf_name = param_config['param']['time_lf']
        self.lon_hf_name = param_config['param']['lon_hf']
        self.lat_hf_name = param_config['param']['lat_hf']

        # Création de la liste de paramétres sans le parametre 'self.time_lf_name'
        # car la fonction np.interp ne peut interpoler un np.dtype('M8[ns])'
        param_list = [param_config['param'][param] for param in param_config['param'].keys()]
        idx = param_list.index(self.time_lf_name)
        param_list.pop(idx)

        # Controle l'homgénéité des données et l'exitance de tous les parametres
        # dans tout les fichiers. Si cela si un ou plusieurs manque le fichier est 
        # rejeté. Revoie une nouvelle liste de fichier conforme pour le tratement.
        file_list = self.__check_file__(data_directory,file_list,param_list)
        
        
        # Calcul de la structure de données normalisée.
        # - gdr_mask : mask gdr de fill_value.
        # - gdr_idx : index gdr vers la structure de données normalisée
        # - norm_index_mask : mask de fill_value dans la structure de données normalisée.
        # Ces parametres sont appliqué pour intégrer chaque trace GDR dans la
        # structure de données de trace normalisée.
        gdr_mask, gdr_idx, norm_index_mask, norm_index_ref = self.__mk_norm_index_struct__(data_directory,file_list)


        # Lecture des fichiers trace et création de la structure.
        data_struct,\
        self.data_attributs,\
        self.struct_dtype,\
        self.cycle,\
        self.date = self.__read_file__(data_directory,\
                                            file_list,\
                                            param_list, norm_index_ref,\
                                            gdr_mask,\
                                            gdr_idx,\
                                            norm_index_mask)


        # Création d'un dictionnaire xarray self.data_val contenant les paramétres et
        # ayant les dimmensions coordonnées définies précédemment.
        self.__mk_data_struct__(data_struct,self.data_attributs,norm_index_ref,param_list,self.cycle,self.date,kml_file)

        # Calcul des hauteurs altimétrique pour les différents retrackers
        self.__surf_height__(surf_type,param_config)

    def __check_file__(self,data_directory,file_list,param_list):
        param_missing = dict()
        file_list_ok = list()
        for idx,filename in enumerate(file_list):
            update_progress(idx/len(file_list), title = 'File checking')
#            with xr.open_dataset(os.path.join(data_directory,filename),decode_times=False) as dataset:
            with xr.open_dataset(os.path.join(data_directory,filename)) as dataset:
                pm = self.__check_param_list_exist__(dataset,param_list)
                if len(pm) > 0:
                    param_missing[filename] = pm
                else:
                    file_list_ok.append(filename)
        update_progress(1.0,title = 'File checking')
        
        if len(param_missing.keys()) > 0:
            print('Parameters missing in some files. They are ignored and not processed : ')
        for k_idx in param_missing.keys():
            print('     >>> ',k_idx,' : ', param_missing[k_idx])

        
        if len(file_list_ok) == 0 :
            raise Exception('None files are conform to the requested parameters')

        return file_list_ok
        

    def __check_param_list_exist__(self,dataset,param_list):
        param_missing = list()
        for param in param_list:
            if not param in dataset.keys():
                param_missing.append(param)
        return param_missing
    
    def __read_param_file__(self,data_directory,filename,param_list):
        data_disk = dict()
#        with xr.open_dataset(os.path.join(data_directory,filename),decode_times=False) as dataset:
        with xr.open_dataset(os.path.join(data_directory,filename)) as dataset:
            cycle = dataset.cycle_number
            date = dataset[self.time_hf_name].data[0,0]
            time_hf = np.array(dataset[self.time_hf_name].data.flatten(),dtype=np.dtype('float64'))
            time_lf = np.array(dataset[self.time_lf_name].data.flatten(),dtype=np.dtype('float64'))
            for param in param_list:
                if len(dataset[param].dims) == 2:
                    data_disk[param] = dataset[param].data.flatten()
                elif len(dataset[param].dims) == 1:
                    data_disk[param] = np.interp(time_hf,time_lf,dataset[param].data)

        return data_disk,cycle,date

    def __data_sort_index__(self,data_struct,norm_index_ref):
            mask = data_struct > -2147483648
            abs_idx = np.where(mask == True)[0]

            match_idx=np.searchsorted(data_struct[mask],norm_index_ref)

            mask_idx = match_idx < data_struct[mask].size
            idx = match_idx[mask_idx]

            data_struct[:data_struct[mask][idx].size] = data_struct[mask][idx]
            mask_fill = ~ (data_struct == norm_index_ref)

            return mask, idx, mask_fill
    
        
    def __sort_norm_index__(self,data_struct,norm_index_ref,cycle):
        mask = dict()
        idx = dict()
        mask_fill = dict()
        for cy_idx in range(len(cycle)):
            update_progress(cy_idx/len(cycle), title = 'Index sorting')

            mask[cy_idx], idx[cy_idx], mask_fill[cy_idx]  = self.__data_sort_index__(data_struct[cy_idx],norm_index_ref)

        update_progress(1., title = 'Index sorting')
            
        return mask,idx,mask_fill
            
    def __mk_norm_index_struct__(self,data_directory,file_list):
        data_disk = dict()
        min_norm_index = []
        max_norm_index = []
        cycle = []
        date = []
        param_missing = dict()
        cy_idx = 0
         # Création d'une structure de type
        for filename in file_list:
            update_progress(cy_idx/len(file_list), title = 'Structure building')
            data_disk_return,cycle_return,date_return = \
                        self.__read_param_file__(data_directory,filename,[self.norm_index_hf_name])
            data_disk[cy_idx] = data_disk_return
            min_norm_index.extend([np.nanmin(data_disk[cy_idx][self.norm_index_hf_name])])
            max_norm_index.extend([np.nanmax(data_disk[cy_idx][self.norm_index_hf_name])])
            cycle.extend([cycle_return])
            date.extend([date_return])
            cy_idx = cy_idx + 1

        update_progress(1., title = 'Structure building')

        min_norm_index = np.array(min_norm_index,dtype=np.dtype('f4'))
        max_norm_index = np.array(max_norm_index,dtype=np.dtype('f4'))
        start_norm_index = np.nanmin(min_norm_index)
        end_norm_index = np.nanmax(max_norm_index)
        
        norm_index_ref = np.arange(start_norm_index,end_norm_index+1)

        # création data_struct
        dim_cycle=len(file_list)
        data_struct=np.empty([dim_cycle,len(norm_index_ref)],dtype=np.dtype('i4'))
        data_struct.fill(np.nan)
        
        for cy_idx,cycle_val in enumerate(cycle):
            if data_disk[cy_idx][self.norm_index_hf_name].size <= data_struct.shape[1] :
                data_struct[cy_idx,:data_disk[cy_idx][self.norm_index_hf_name].size] = data_disk[cy_idx][self.norm_index_hf_name]
            else:
                fatal_error(' GDR time has some duplucated values (cycle number '+str(cycle[cy_idx])+')')

            
        mask, idx, mask_fill = self.__sort_norm_index__(data_struct,norm_index_ref,cycle)
        
        if len(param_missing.keys()) > 0:
            print('   >>>> Warning report: The norm_index is missing for several cycles : ',param_missing.keys())
            print('   >>>> These cycles are ignored <<<< ')

        return mask, idx, mask_fill, norm_index_ref


            
    def __read_file__(self,data_directory,file_list,param_list, norm_index_ref,\
                            gdr_mask,gdr_idx, norm_index_mask):
        '''
         Lecture des fichiers trace est interpolation à 20hz des variables à 1hz.
        '''
        # Création d'une structure de type
#        with xr.open_dataset(os.path.join(data_directory,file_list[0]),decode_times=False) as dataset:
        with xr.open_dataset(os.path.join(data_directory,file_list[0])) as dataset:
            dtype_list = []
            for param in param_list:
                dtype_list.extend([(param,dataset.variables[param].dtype)])
            struct_dtype = np.dtype(dtype_list)
        
        # création data_struct tableau xarray dans lequel seront chargé les données.
        dim_cycle=len(file_list)
        data_struct=np.empty([dim_cycle, norm_index_ref.size],dtype=struct_dtype)
        data_struct.fill(np.nan)
        data_struct=xr.DataArray(data_struct,dims=['cycle','norm_index'])

        cycle = []
        date = []
        data_attributs = dict()
        cy_idx = 0
        for filename in file_list:
            update_progress(cy_idx/len(file_list), title = 'Track files loading')
            data_disk,cycle_return,date_return = \
                        self.__read_param_file__(data_directory,filename,param_list)

            cycle.extend([cycle_return])
            date.extend([date_return])

            for param in param_list:
                data_struct.data[param][cy_idx,:data_disk[param].size]=data_disk[param]

                size_track = data_struct.data[param][cy_idx,gdr_mask[cy_idx]][gdr_idx[cy_idx]].size
                
                data_struct.data[param][cy_idx,:size_track] =\
                data_struct.data[param][cy_idx,gdr_mask[cy_idx]][gdr_idx[cy_idx]]
                
                
                if data_struct.data.dtype[param] == np.dtype('i4') :
                    data_struct.data[param][cy_idx,norm_index_mask[cy_idx]] = -1
                elif data_struct.data.dtype[param] == np.dtype('M8[ns]') :
                    data_struct.data[param][cy_idx,norm_index_mask[cy_idx]] = None
                else:
                    data_struct.data[param][cy_idx,norm_index_mask[cy_idx]] = np.nan
            cy_idx = cy_idx + 1
            
        dataset.close()                
        update_progress(1.0, title = 'Track files loading')
            
        list_glob_att=['norm_pass_processor_version',
                        'norm_pass_hgid',
                        'norm_pass_CycRef',
                        'norm_pass_MissionRef',
                        'norm_pass_SetCycles',
                        'mean_pass_Def_File',
                        'mean_pass_hgid','pass_number' ]

        for idx in range(len(file_list)):
#            with xr.open_dataset(os.path.join(data_directory,file_list[idx])) as dataset:
#            dataset = xr.open_dataset(os.path.join(data_directory,file_list[idx]),decode_times=False)
            dataset = xr.open_dataset(os.path.join(data_directory,file_list[idx]))
            if list_glob_att[0] in dataset.attrs.keys():
                break
            dataset.close()

        if idx < (len(file_list)-1):
            data_attributs['global']={}        
            for glob_att in list_glob_att:
                data_attributs['global'][glob_att]=dataset.attrs[glob_att]
        else:
            print('Warning : None global attribut found for normpass in the GDR files.')
            data_attributs['global']={}        
            data_attributs['global']['pass_number']=dataset.attrs['pass_number']



        for param in struct_dtype.names:
            data_attributs[param]={}
            if 'units' in dataset[param].attrs:
                data_attributs[param]['units']=dataset[param].attrs['units']
            else:
                data_attributs[param]['units']=''
            
            if 'standard_name' in dataset[param].attrs:
                data_attributs[param]['standard_name']=dataset[param].attrs['standard_name']
            else:
                data_attributs[param]['standard_name']=''
                
            if 'long_name' in dataset[param].attrs:
                data_attributs[param]['long_name']=dataset[param].attrs['long_name']
            else:
                data_attributs[param]['long_name']=''
            
            if 'comment' in dataset[param].attrs:
                data_attributs[param]['comment']=dataset[param].attrs['comment']
            else:
                data_attributs[param]['comment']=''


        return data_struct,data_attributs,struct_dtype,cycle,date

    def __mk_data_struct__(self,data_struct,data_attributs,norm_index_ref,param_list,cycle,date,kml_file):
        '''
            Création d'un dictionnaire xarray self.data_val contenant les paramétres et
            ayant les dimmensions coordonnées définies précédemment.
        '''

        # Création des dimensions coordonnées de la nouvelle table xarray self.data_val
        # calcul d'un masque (mask) pour selectionner les cellules de la trace
        # normanlisée non vide.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("ignore") # On n'affiche pas les warnings
#            warnings.simplefilter("default") # On affiche les warnings
            # convertion des longitudes 0<lon<360. en -180<lon<180.
            data_struct.data[self.lon_hf_name] = \
                            np.where(data_struct.data[self.lon_hf_name] > 180.0,\
                            data_struct.data[self.lon_hf_name]-360.0,\
                            data_struct.data[self.lon_hf_name])

        lon_mean = np.nanmean(data_struct.data[self.lon_hf_name],axis=0)
        lat_mean = np.nanmean(data_struct.data[self.lat_hf_name],axis=0)
        count = np.sum(~np.isnan(data_struct.data[self.lon_hf_name]),axis=0)
        mask_count = ~(count==0)
        if not kml_file is None:
            mask_kml = self.__kml_poly_select__(kml_file,lon_mean,lat_mean)
        else:
            mask_kml = np.ones(mask_count.shape,dtype=np.bool)

        mask = mask_count & mask_kml
        
        # Création d'un dictionnaire xarray self.data_val contenant les paramétres et
        # ayant les dimmensions coordonnées définies précédemment.
        self.data_val={}
        for param in param_list:
            if not param in [self.norm_index_hf_name]:
                self.data_val[param] = xr.DataArray(data_struct.data[param][:,mask],
                                    coords={'cycle' : cycle, 
                                    'norm_index' : norm_index_ref[mask] ,
                                    'date' : ('cycle',date),
                                    'lon' : ('norm_index',lon_mean[mask]),
                                    'lat' : ('norm_index',lat_mean[mask]),
                                    'count' : ('norm_index',count[mask]) },
                                    dims=['cycle','norm_index'])
                if not data_attributs[param]['units'] == '':
                    self.data_val[param].attrs['units']=data_attributs[param]['units']
                self.data_val[param].attrs['standard_name']=data_attributs[param]['standard_name']
                self.data_val[param].attrs['long_name']=data_attributs[param]['long_name']
                self.data_val[param].attrs['comment']=data_attributs[param]['comment']
                
    def __surf_height__(self,surf_type,param_config):
        '''
            Calcul des hauteurs altimétrique pour les différents retrackers
        '''
        
        if surf_type == 'RiversLakes':
            for band in param_config['band']:
                for retracker in param_config['retracker']:
                    param_name = retracker+'_'+band+'_'+'SurfHeight_alti'
                    self.data_val[param_name] = \
                        self.data_val[param_config['param']['alt_hf']]\
                            -self.data_val[param_config['param'][retracker+'_range_'+band]]\
                            -self.data_val[param_config['param']['model_wet_tropo_corr']]\
                            -self.data_val[param_config['param']['model_dry_tropo_corr']]\
                            -self.data_val[param_config['param']['solid_earth_tide']]\
                            -self.data_val[param_config['param']['geoid']]\
                            -self.data_val[param_config['param']['iono_corr_gim_'+band]]\
                            -self.data_val[param_config['param']['pole_tide']]   

                    self.data_val[param_name].attrs['units']='meters'
                    self.data_val[param_name].attrs['standard_name']='surface_height'
                    self.data_val[param_name].attrs['long_name']=str(param_config['freq'])+' Hz '+band+' band surface height ('+retracker+' retracking)'
                    self.data_val[param_name].attrs['comment']='Altimetric Surfurce Height = '+param_config['param']['alt_hf']\
                    +' - '+param_config['param'][retracker+'_range_'+band]+' - '+param_config['param']['model_wet_tropo_corr']\
                    +' - '+param_config['param']['model_dry_tropo_corr']+' - '+param_config['param']['solid_earth_tide']\
                    +' - '+param_config['param']['geoid']+' - '+param_config['param']['iono_corr_gim_'+band]\
                    +' - '+param_config['param']['pole_tide']
                
        else:
            raise Exception('Surface_type not already defined : ',surf_type)

    def __kml_poly_select__(self,kml_file,lon_mean,lat_mean):
        '''
           Selection des données contenues à l'intérieur du polygone défini dans le fichier kml
        '''
        
        gpd.io.file.fiona.drvsupport.supported_drivers['KML'] = 'rw'
        polys = gpd.read_file(kml_file, driver='KML')
        poly = polys.loc[polys['Name'] ==  polys['Name'][0]]

        mask = [Point(lon,lat).within(poly.loc[0, 'geometry']) for lon,lat in zip(lon_mean,lat_mean)]
        
        return mask

    def save_norm_data(self,directory):
        dataset_merge=xr.merge([self.data_val])

        param_name=self.time_hf_name    #'time_20hz'
        data = self.data_val[param_name]
        cycle = np.array(data.coords['cycle'])
        norm_index = np.array(data.coords['norm_index'])
        lon = np.array(data.coords['lon'])
        lat = np.array(data.coords['lat'])

        dataset_date=np.array(data.coords['date'],dtype=np.datetime64)
        date = ['{:04d}{:02d}{:02d}'.format(y,m,d) for y,m,d in zip(pd.DatetimeIndex(dataset_date).year,
                                                pd.DatetimeIndex(dataset_date).month,
                                                pd.DatetimeIndex(dataset_date).day)]
        
        startdate = date[0]
        startcycle = '{:03d}'.format(cycle[0])
        enddate = date[-1]
        endcycle = '{:03d}'.format(cycle[-1])
        
        dataset_merge.attrs['Conventions']='CF-1.6'
        dataset_merge.attrs['creation_date'] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
        dataset_merge.attrs['title']='Level 3 product : Normalized dataset of radar altimetric parameters for the '+self.mission+' mission.'
        dataset_merge.attrs['institutions'] = "CTOH, LEGOS (UMR5566), Universite de Toulouse, CNES, CNRS, IRD, UPS, Toulouse, France"
        dataset_merge.attrs['contact'] = "ctoh_products@legos.obs-mip.fr"
        dataset_merge.attrs['processing_facility'] = "CTOH, LEGOS (UMR5566)"
        dataset_merge.attrs['source'] = 'Altimetric data from CTOH data base'
        dataset_merge.attrs['doi'] = "10.6096/CTOH_NORM_PASS_2019_01"
        dataset_merge.attrs['Doc_ref'] = "BLAREL, Fabien, FRAPPART, Frédéric, LEGRÉSY, Benoît, et al. Altimetry backscattering signatures at Ku and S bands over land and ice sheets. In : Remote Sensing for Agriculture, Ecosystems, and Hydrology XVII. International Society for Optics and Photonics, 2015."
        dataset_merge.attrs['processor_version'] = 'Version : '+__version__+' Revision : '+__revision__  #??? | Data generation date : ???"
        dataset_merge.attrs['hgid'] = __revision__
        dataset_merge.attrs['start_date'] = startdate 
        dataset_merge.attrs['end_date'] = enddate
        dataset_merge.attrs['lat_min'] = np.min(lat)
        dataset_merge.attrs['lat_max'] = np.max(lat)
        dataset_merge.attrs['lon_min'] = np.min(lon)
        dataset_merge.attrs['lon_max'] = np.max(lon)

        if 'global' in self.data_attributs.keys():
            for att in self.data_attributs['global'].keys():
                dataset_merge.attrs[att] = self.data_attributs['global'][att]

        track=int(self.data_attributs['global']['pass_number'])
        dataset_merge.to_netcdf(os.path.join(directory,'normpass_dataset_'+self.mission+'_{:04d}'.format(track)+'_'+startdate+'_'+startcycle+'_'+enddate+'_'+endcycle+'.nc'),format='NETCDF4_CLASSIC') 
        
                    
                
def main():

    parser = argparse.ArgumentParser(description="Merge GDR data into normpass structure (CTOH Level 3 product).",epilog="contact : blarel@legos.obs-mip.fr")
    parser.add_argument("-v", "--version", action="version", version='Version : '+__version__+';\nRevision : '+__revision__)

    subparsers = parser.add_subparsers(help='Choose a command')
    mk_normpassfile_parser = subparsers.add_parser('mkfile', help='Command argument to generate normpass files. See "mkfile" help for more options informations.')
    mk_normpassfile_parser.add_argument("mission", type=str, choices=['j1E','j2D','j3Ds','ers2.c.v1','envisat.v21','saral.s'], help="Altimetric Mission name")
    mk_normpassfile_parser.add_argument("track", type=int, help="Track number")
    mk_normpassfile_parser.add_argument("input_dir", type=str, help="Input GDR data path directory.")
    mk_normpassfile_parser.add_argument("output_dir", type=str, help="Output data path directory.")
    mk_normpassfile_parser.add_argument("-type", default=None, type=str, choices=['Ocean','Coastal','RiversLakes','GreatLakes'],\
                    help="As function of the kind of analysis, the right surface height is computed (for allowed and informed experts only, all abus will crash the program).")
    mk_normpassfile_parser.add_argument("-cfg","--config_file", type=str, default=None, help='Take the user configuration mission file to generate the normpass file (This file is generated by "config" command argument).')

    mk_cfgfile_parser = subparsers.add_parser('config', help='Command argument to generate configuration mission file template (for allowed and informed experts only, all abus will crash the program).')
    mk_cfgfile_parser.add_argument("config", action='store_true', default=False, help="To generate configuration mission file template (for allowed and informed experts only, all abus will crash the program).")

    args = parser.parse_args()

    if hasattr(args,'config'):
        if args.config :
            print('\nA configuration mission file is generated (normpass_cfg.yml). Modify the needing parameters and use the -cfg option to generate your own normpass files.\n')
            mission_file_cfg = pkg_resources.resource_filename('altis', '../etc/config_mission.yml')
            cwd = os.getcwd()
    #        print(cwd)
            copyfile(mission_file_cfg, cwd+'/normpass_cfg.yml')
            sys.exit(-1)
        
        


    mission = args.mission      #'j2D'
    track = args.track          #102
    data_directory = args.input_dir   #'/calcul/pc-blarel/MAPS_DATA'
    surf_type = args.type      #'RiversLakes'
    kml_file = None #args.kml_file

    mission_config_file = args.config_file

    if not args.output_dir is None:
        output_directory=args.output_dir

    
    if not os.path.isdir(data_directory):
        raise Exception('Input GDR data path directory not found : It does not exists. > '+data_directory+' <')
    
    
    # Selection des fichiers trace
    file_struct = __regex_file_parser__(mission,data_directory,mission_config_file)
    mask_file = file_struct['track'] == track
    file_list = file_struct['filename'][mask_file]
    
    if len(file_list) == 0:
        fatal_error('None files are found for the pass number : '+str(track))
#        raise Exception('None files are found for the pass number :', track)
    
    # création de l'objet Track.
    tr=Track(mission,surf_type,data_directory,file_list,mission_config_file,kml_file)

    tr.save_norm_data(output_directory) 

    if not kml_file is None:
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
        tiler = Stamen('terrain-background')
    # Figure 1    
    #    cm='viridis' #'hsv'
        cm='hsv'
        fig = plt.figure()

        ax0 = fig.add_subplot(2,2,1, projection=ccrs.PlateCarree())
        plt0 = ax0.scatter(lon,lat,c=param, marker='+',cmap=cm,transform=ccrs.PlateCarree())
        
        if args.sat_img :
            ax0.add_wmts(url,layer)
        else : 
            ax0.add_image(tiler,10)
        
        ax0.add_feature(RIVERS_10m)

        if not args.kml_file is None:
            ax0.plot(x,y,transform=ccrs.PlateCarree())
        gl = ax0.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                          linewidth=0.5, color='white', alpha=1.0, linestyle='--')
        gl.xlabels_top = True
        gl.ylabels_left = True
        gl.xlabels_bottom = False
        gl.ylabels_right = False
        gl.xlines = True
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
            
        ax1 = fig.add_subplot(2,2,2,sharey=ax0)
        plt1 = ax1.scatter(param,lat,c=param, marker='+',cmap=cm ) 
        ax1.grid()
        ax2 = fig.add_subplot(2,2,3,sharex=ax0)
        plt2 = ax2.scatter(lon,param,c=param, marker='+',cmap=cm ) 
        ax2.grid()
        ax3 = fig.add_subplot(2,2,4,sharey=ax2)
        plt3 = ax3.scatter(np.array(time),param,c=param, marker='+',cmap=cm ) 
        ax3.grid()
        cbar = fig.colorbar(plt0, ax=[ax1,ax3],orientation='vertical')
        cbar.set_label(param.attrs['long_name'], rotation=270)

    #    plt.show()
        
    # Figure 2
        lon = tr.data_val['lon_20hz'].mean(dim='cycle')
        lat = tr.data_val['lat_20hz'].mean(dim='cycle')
        
        abcisse = lat
        
        param = tr.data_val['ice1_ku_Surf-Height_alti'].mean(dim='cycle')
        std_param = tr.data_val['ice1_ku_Surf-Height_alti'].std(dim='cycle')
        fig = plt.figure()
        ax1 = fig.add_subplot(7,1,1)
        ax1.set_title('Mean parameter along the normalized track')
        plt1 = ax1.scatter(abcisse,param,c=param, marker='+',cmap=cm ) 
        ax1.set_ylabel('Surface height (m)')
        ax1.grid()
        ax2 = fig.add_subplot(7,1,2)
        plt2 = ax2.scatter(abcisse,std_param,c=std_param, marker='+',cmap=cm ) 
        ax2.set_ylabel('Std Surface height (m)')
        ax2.grid()
        
        param = 10.0*np.log10(np.power(10.0,tr.data_val['ice_sig0_20hz_ku']/10.).mean(dim='cycle'))
        std_param = 10.0*np.log10(np.power(10.0,tr.data_val['ice_sig0_20hz_ku']/10.).std(dim='cycle'))
        ax3 = fig.add_subplot(7,1,3)
        plt3 = ax3.scatter(abcisse,param,c=param, marker='+',cmap=cm ) 
        ax3.set_ylabel('Sig0 (dB)')
        ax3.grid()
        ax4 = fig.add_subplot(7,1,4)
        plt4 = ax4.scatter(abcisse,std_param,c=std_param, marker='+',cmap=cm ) 
        ax4.set_ylabel('Sig0 (dB)')
        ax4.grid()

        param = tr.data_val['peakiness_20hz_ku'].mean(dim='cycle')
        std_param = tr.data_val['peakiness_20hz_ku'].std(dim='cycle')
        ax5 = fig.add_subplot(7,1,5)
        plt5 = ax5.scatter(abcisse,param,c=param, marker='+',cmap=cm ) 
        ax5.set_ylabel('Peakiness')
        ax5.grid()
        ax6 = fig.add_subplot(7,1,6)
        plt6 = ax6.scatter(abcisse,std_param,c=std_param, marker='+',cmap=cm ) 
        ax6.set_ylabel('Std Peakiness')
        ax6.grid()

        ax7 = fig.add_subplot(7,1,7)
        plt7 = ax7.scatter(abcisse,std_param.coords['count'],c=std_param.coords['count'], marker='+',cmap=cm ) 
        ax7.set_xlabel('lat')
        ax7.set_ylabel('Count')
        ax7.grid()
        

    # Figure 3
        raw_data = tr.data_val['ice1_ku_Surf-Height_alti'].T
        mean_time = tr.data_val['time_20hz'][:,0]   #.mean(dim='norm_index')
        
        param = tr.data_val['ice1_ku_Surf-Height_alti'].median(dim='norm_index')
    #    ecart_abs_median_param = np.sum(np.abs(tr.data_val['ice1_ku_Surf-Height_alti'] - tr.data_val['ice1_ku_Surf-Height_alti'].median(dim='norm_index'))) / np.
        std_param = tr.data_val['ice1_ku_Surf-Height_alti'].std(dim='norm_index')
        abcisse = np.array(param.coords['date'])


        fig = plt.figure()
        ax1 = fig.add_subplot(2,2,1)
        ax1.set_title('Surface height Time series')
    #    pdb.set_trace()
    #    ax1.boxplot(np.array(raw_data), positions=np.array(mean_time,dtype='f8'), notch=False, widths=2.5)
        plt1 = ax1.scatter(abcisse,param,c=param, marker='+',cmap=cm ) 
        ax1.set_ylabel('Surface height (m)')
        ax1.grid()
        
        vmin = np.min(param)
        vmax = np.max(param)
        ax2 = fig.add_subplot(2,2,2)
        ax2.set_title('histo')
        plt2 = ax2.hist(param,50)
        ax2.set_xlabel('Surface height (m)')
        ax2.grid()
        ax3 = fig.add_subplot(2,1,2)
        ax3.set_title('Std Time series')
        plt3 = ax3.scatter(abcisse,std_param,c=std_param, marker='+',cmap=cm ) 
        ax3.set_ylabel('Std Surface height (m)')
        ax3.set_xlabel('Time date')
        ax3.grid()
        
        plt.show()
    
    
if __name__ == '__main__':
    main()
