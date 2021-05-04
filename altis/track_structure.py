#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Track Class
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------
import wx
#import pdb
#import argparse
import os
import warnings
import re
import sys
#import glob
import pathlib
import time
import numpy as np
import xarray as xr
import pandas as pd

import pkg_resources
#from shutil import copyfile

from altis_utils.ellipsoid_tools import (
        ellipsoid_convert)

from altis_utils.tools import (
    __config_load__,
    update_progress,
#    __regex_file_parser__,
#    fatal_error,
    kml_poly_select,
    FileNotFoundError,
)

from altis.to_netcdf import to_netcdf

from altis._version import __version__, __revision__


class GDR_altis(object):

    class Error(Exception):
        pass


    class OutOfAreaError(Error):
        def __init__(self, message):
            super().__init__(message)
            self.message_gui = message

    def __init__(
        self, mission, filename, mission_config_file=None, kml_file=None,
    ):
        """
            Chargement de la structure GDR créer par Altis.
        """
        self.mission = mission

        if mission_config_file is None:
            mission_file_cfg = pkg_resources.resource_filename(
                "altis", "../etc/products_config.yaml"
            )
        else:
            if os.path.isfile(mission_config_file):
                mission_file_cfg = mission_config_file
            else:
                raise Exception("Mission configuration file not found.")

        param_config = __config_load__(mission, mission_config_file)
        filename_pattern = param_config["filename_normpass_pattern"]
        filename_tracks_pattern = param_config["filename_tracks_pattern"]
        self.norm_index_hf_name = param_config["param"]["norm_index_hf"]
        self.time_hf_name = param_config["param"]["time_hf"]
        self.time_lf_name = param_config["param"]["time_lf"]
        self.lon_hf_name = param_config["param"]["lon_hf"]
        self.lat_hf_name = param_config["param"]["lat_hf"]


        altisgdr=False
        with xr.open_dataset(filename) as ds:
            if hasattr(ds,'processor'):
                if ds.processor =='altisgdr':
                    altisgdr=True

        if altisgdr:

            self.data_val = xr.open_dataset(filename)
            cycle = self.data_val.cycle
            lon = self.data_val[self.lon_hf_name].data
            lat = self.data_val[self.lat_hf_name].data

            if kml_file is not None:
                mask_kml = np.zeros(lon.shape, dtype=np.bool)
                for cy_idx, cy in enumerate(cycle):
                    mask_kml[cy_idx, :] = kml_poly_select(
                        kml_file, lon[cy_idx, :], lat[cy_idx, :]
                    )
            else:
                mask_kml = np.ones(lon.shape, dtype=np.bool)
            

            if np.any(mask_kml):
                xr_mask_kml = xr.DataArray(mask_kml, dims=["cycle_index", "gdr_index"])

                for param in list(self.data_val.variables.keys()):
                    if len(self.data_val[param].shape) == 2:
                        self.data_val[param] = self.data_val[param].where(
                            xr_mask_kml, drop=True
                        )
            else:
                message="Out of Aera : None pass goes through the area defined by the KML polygon."
                raise self.OutOfAreaError(message)



            self.data_val.close()
        else:
            raise Exception(
                "The normpass filename is not conform to the filename "
                + "pattern of "
                + mission
                + " mission."
            )

    def mk_filename_gdr_data(self, mask):
        param_name = self.time_hf_name  #'time_20hz'
        data = self.data_val[param_name].where(mask, drop=True)
        cycle = np.array(data.coords["cycle"])
#        norm_index = np.array(data.coords["gdr_index"])

        dataset_date = np.array(data.coords["date"], dtype=np.datetime64)
        date = [
            "{:04d}{:02d}{:02d}".format(y, m, d)
            for y, m, d in zip(
                pd.DatetimeIndex(dataset_date).year,
                pd.DatetimeIndex(dataset_date).month,
                pd.DatetimeIndex(dataset_date).day,
            )
        ]

        startdate = date[0]
        startcycle = "{:03d}".format(cycle[0])
        enddate = date[-1]
        endcycle = "{:03d}".format(cycle[-1])

        if isinstance(self.track_value, str):
            track = self.track_value
        else:
            track = "{:04d}".format(self.track_value.min())

        return (
            "AlTiS_gdrpass_"
            + self.mission
            + "_"
            + track
            + "_"
            + startdate
            + "_"
            + startcycle
            + "_"
            + enddate
            + "_"
            + endcycle
            + ".nc"
        )

    def save_gdr_data(self, mask, filename):

        output_data = self.data_val.where(mask, drop=True)

        param_name = self.time_hf_name  #'time_20hz'
        data = output_data[param_name]
#        cycle = np.array(data.coords["cycle"])
#        norm_index = np.array(data.coords["gdr_index"])

        dataset_date = np.array(data.coords["date"], dtype=np.datetime64)
        date = [
            "{:04d}{:02d}{:02d}".format(y, m, d)
            for y, m, d in zip(
                pd.DatetimeIndex(dataset_date).year,
                pd.DatetimeIndex(dataset_date).month,
                pd.DatetimeIndex(dataset_date).day,
            )
        ]

        startdate = date[0]
#        startcycle = "{:03d}".format(cycle[0])
        enddate = date[-1]
#        endcycle = "{:03d}".format(cycle[-1])
        #
        #        dataset_merge.attrs['Conventions']='CF-1.6'
        #        dataset_merge.attrs['creation_date'] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
        output_data.attrs["AlTiS_creation_date"] = time.strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
        output_data.attrs["start_date"] = startdate
        output_data.attrs["end_date"] = enddate
        #        self.data_val.attrs[''] =

        #        dataset_merge.attrs['title']='Level 3 product : Normalized dataset of radar altimetric parameters for the '+self.mission+' mission.'
        #        dataset_merge.attrs['institutions'] = "CTOH, LEGOS (UMR5566), Universite de Toulouse, CNES, CNRS, IRD, UPS, Toulouse, France"
        #        dataset_merge.attrs['contact'] = "ctoh_products@legos.obs-mip.fr"
        #        dataset_merge.attrs['processing_facility'] = "CTOH, LEGOS (UMR5566)"
        #        dataset_merge.attrs['source'] = 'Altimetric data (GDR) from CTOH data base'
        #        dataset_merge.attrs['doi'] = "10.6096/CTOH_NORM_PASS_2019_01"
        #        dataset_merge.attrs['Doc_ref'] = "BLAREL, Fabien, FRAPPART, Frédéric, LEGRÉSY, Benoît, et al. Altimetry backscattering signatures at Ku and S bands over land and ice sheets. In : Remote Sensing for Agriculture, Ecosystems, and Hydrology XVII. International Society for Optics and Photonics, 2015."
        #        dataset_merge.attrs['processor_version'] = 'Version : '+__version__+' Revision : '+__revision__  #??? | Data generation date : ???"
        #        dataset_merge.attrs['hgid'] = __revision__
        #        dataset_merge.attrs['start_date'] = startdate
        #        dataset_merge.attrs['end_date'] = enddate
        #        dataset_merge.attrs['lat_min'] = np.min(lat)
        #        dataset_merge.attrs['lat_max'] = np.max(lat)
        #        dataset_merge.attrs['lon_min'] = np.min(lon)
        #        dataset_merge.attrs['lon_max'] = np.max(lon)

        #        if 'global' in self.data_attributs.keys():
        #            for att in self.data_attributs['global'].keys():
        #                dataset_merge.attrs[att] = self.data_attributs['global'][att]

        #        track=int(self.data_attributs['global']['pass_number'])
#        track = self.data_val.pass_number

        print("AlTiS GDR pass file created :  " + filename)
        to_netcdf(pathlib.PurePath(filename), output_data) 

        #if sys.platform.startswith('linux'):
        #    output_data.to_netcdf(filename)
        #elif sys.platform.startswith('win'):
        #    output_data.to_netcdf(pathlib.PurePath(filename), format="NETCDF3_64BIT", engine="scipy")
            
#        output_data.to_netcdf(filename)
#        output_data.to_netcdf(filename, format="NETCDF4_CLASSIC")
#        output_data.to_netcdf(pathlib.PurePath(filename), format="NETCDF3_64BIT", engine="scipy")
        output_data.close()


class Normpass(object):
    def __init__(
        self, mission, filename, mission_config_file=None, kml_file=None,
    ):
        """
            Chargement de la trace normalisée.
        """
        self.mission = mission

        if mission_config_file is None:
            mission_file_cfg = pkg_resources.resource_filename(
                "altis", "../etc/products_config.yaml"
            )
        else:
            if os.path.isfile(mission_config_file):
                mission_file_cfg = mission_config_file
            else:
                raise Exception("Mission configuration file not found.")

        param_config = __config_load__(mission, mission_config_file)
        filename_pattern = param_config["filename_normpass_pattern"]
        self.norm_index_hf_name = param_config["param"]["norm_index_hf"]
        self.time_hf_name = param_config["param"]["time_hf"]
        self.time_lf_name = param_config["param"]["time_lf"]
        self.lon_hf_name = param_config["param"]["lon_hf"]
        self.lat_hf_name = param_config["param"]["lat_hf"]

        if not os.path.isfile(filename):
            message = ("File not found !\n\n- %s") % (filename)
            print(message)
            raise FileNotFoundError(message)

        match = re.search(filename_pattern, filename)
        if match:
            self.data_val = xr.open_dataset(filename)
            self.data_val.pass_number
            lon_mean = self.data_val.lon.data
            lat_mean = self.data_val.lat.data
            if kml_file is not None:
                mask_kml = kml_poly_select(kml_file, lon_mean, lat_mean)
            else:
                mask_kml = np.ones(lon_mean.shape, dtype=np.bool)
            data_val = self.data_val.where(
                self.data_val.norm_index[mask_kml], drop=True
            )
            self.data_val = data_val
            self.data_val.close()
        else:
            raise Exception(
                "The normpass filename is not conform to the filename "
                + "pattern of "
                + mission
                + " mission."
            )

    def mk_filename_norm_data(self, mask):

        param_name = self.time_hf_name  #'time_20hz'
        data = self.data_val[param_name].where(mask, drop=True)
        cycle = np.array(data.coords["cycle"])
#        norm_index = np.array(data.coords["norm_index"])
#        lon = np.array(data.coords["lon"])
#        lat = np.array(data.coords["lat"])

        dataset_date = np.array(data.coords["date"], dtype=np.datetime64)
        date = [
            "{:04d}{:02d}{:02d}".format(y, m, d)
            for y, m, d in zip(
                pd.DatetimeIndex(dataset_date).year,
                pd.DatetimeIndex(dataset_date).month,
                pd.DatetimeIndex(dataset_date).day,
            )
        ]

        startdate = date[0]
        startcycle = "{:03d}".format(cycle[0])
        enddate = date[-1]
        endcycle = "{:03d}".format(cycle[-1])

        if isinstance(self.track_value, str):
            track = self.track_value
        else:
            track = "{:04d}".format(self.track_value.min())

        return (
            "AlTiS_normpass_"
            + self.mission
            + "_"
            + track
            + "_"
            + startdate
            + "_"
            + startcycle
            + "_"
            + enddate
            + "_"
            + endcycle
            + ".nc"
        )

    def save_norm_data(self, mask, filename):
        
        data_val = self.data_val.where(mask, drop=True)

        param_name = self.time_hf_name  #'time_20hz'
        data = data_val[param_name]
#        cycle = np.array(data.coords["cycle"])
#        norm_index = np.array(data.coords["norm_index"])
        lon = np.array(data.coords["lon"])
        lat = np.array(data.coords["lat"])

        dataset_date = np.array(data.coords["date"], dtype=np.datetime64)
        date = [
            "{:04d}{:02d}{:02d}".format(y, m, d)
            for y, m, d in zip(
                pd.DatetimeIndex(dataset_date).year,
                pd.DatetimeIndex(dataset_date).month,
                pd.DatetimeIndex(dataset_date).day,
            )
        ]

        startdate = date[0]
#        startcycle = "{:03d}".format(cycle[0])
        enddate = date[-1]
#        endcycle = "{:03d}".format(cycle[-1])
        #
        #        dataset_merge.attrs['Conventions']='CF-1.6'
        #        dataset_merge.attrs['creation_date'] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
        data_val.attrs["AlTiS_creation_date"] = time.strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
        data_val.attrs["start_date"] = startdate
        data_val.attrs["end_date"] = enddate
        data_val.attrs["lat_min"] = np.min(lat)
        data_val.attrs["lat_max"] = np.max(lat)
        data_val.attrs["lon_min"] = np.min(lon)
        data_val.attrs["lon_max"] = np.max(lon)
        #        self.data_val.attrs[''] =

        print("Normpass file created :  " + filename)
        to_netcdf(pathlib.PurePath(filename), data_val) 

#        if sys.platform.startswith('linux'):
#            data_val.to_netcdf(filename)
#        elif sys.platform.startswith('win'):
#            data_val.to_netcdf(pathlib.PurePath(filename), format="NETCDF3_64BIT", engine="scipy")

#        data_val.to_netcdf(filename)
#        data_val.to_netcdf(filename, format="NETCDF4_CLASSIC")
#        data_val.to_netcdf(pathlib.PurePath(filename), format="NETCDF3_64BIT", engine="scipy")
        data_val.close()


class Track(object):
    class Error(Exception):
        pass

    class InterpolationError(Error):
        def __init__(self, message):
            super().__init__(message)
            self.message_gui = message

    class ParamMissing(Error):
        def __init__(self, message):
            super().__init__(message)
            self.message_gui = message

    class TimeAttMissing(Error):
        def __init__(self, message):
            super().__init__(message)
            self.message_gui = message

    class ListFileEmpty(Error):
        def __init__(self, message):
            super().__init__(message)
            self.message_gui = message

    class SurfaceHeightError(Error):
        def __init__(self, message):
            super().__init__(message)
            self.message_gui = message

    class OutOfAreaError(Error):
        def __init__(self, message):
            super().__init__(message)
            self.message_gui = message

    def __init__(
        self,
        mission,
        surf_type,
        data_directory,
        file_list,
        mission_config_file=None,
        kml_file=None,
    ):
        """ 
            Initialisation de la classe Track:
                - Lecture des données
                - Normalisation des traces (optionel si norm_index existe)
                - Calcul des ranges
        """
        self.mission = mission
        self.surf_type = surf_type

        if mission_config_file is None:
            mission_file_cfg = pkg_resources.resource_filename(
                "altis", "../etc/products_config.yaml"
            )
        else:
            if os.path.isfile(mission_config_file):
                mission_file_cfg = mission_config_file
            else:
                raise Exception("Mission configuration file not found.")

        # Appel de la fonction "utils" afin de charger les parametres prés définit
        param_config = __config_load__(mission, mission_config_file)
        #        self.norm_index_hf_name = param_config['param']['norm_index_hf']
        self.time_hf_name = param_config["param"]["time_hf"]
        self.time_lf_name = param_config["param"]["time_lf"]
        self.lon_hf_name = param_config["param"]["lon_hf"]
        self.lat_hf_name = param_config["param"]["lat_hf"]

        # on récupére les informations de dimmenssion.
        # pour les missions en une dimension.
        if "dim_hf" in param_config.keys():
            self.dim_hf = param_config["dim_hf"]
            self.dim_lf = param_config["dim_lf"]
        else:
            self.dim_hf = None
            self.dim_lf = None

        # Création de la liste de paramétres sans le parametre 'self.time_lf_name'
        # car la fonction np.interp ne peut interpoler un np.dtype('M8[ns])'
        param_list = [
            param_config["param"][param] for param in param_config["param"].keys()
        ]
        if "None" in param_list:
            param_list.remove("None")
        idx = param_list.index(self.time_lf_name)
        param_list.pop(idx)

        # Controle l'homgénéité des données et l'exitance de tous les parametres
        # dans tout les fichiers. Si cela si un ou plusieurs manque le fichier est
        # rejeté. Revoie une nouvelle liste de fichier conforme pour le tratement.
        file_list = self.__check_file__(data_directory, file_list, param_list)

        if len(file_list) == 0:
            mission_file_cfg = pkg_resources.resource_filename(
                "altis", "../etc/products_config.yaml"
            )
            message = (
                "[Error] None files have all valid parameters for AlTiS.\n\n"
                + "You have to custom your configuration to load those "
                + "kind of GDR files. Just edit the configuration file "
                + "of AlTiS : \n\t - %s\n\n"
                + " The GDR files loading is aborted."
            ) % (mission_file_cfg)
            print(message)
            raise self.ListFileEmpty(message)

        # Calcul de la structure de données.
        norm_index_ref = self.__mk_norm_index_struct__(data_directory, file_list)

        # Lecture des fichiers trace et création de la structure.
        (
            data_struct,
            self.data_attributs,
            self.struct_dtype,
            self.cycle,
            self.date,
            self.tracks,
        ) = self.__read_file__(data_directory, file_list, param_list, norm_index_ref)

        # Création d'un dictionnaire xarray self.data_val contenant les paramétres et
        # ayant les dimmensions coordonnées définies précédemment.
        self.__mk_data_struct__(
            data_struct,
            self.data_attributs,
            norm_index_ref,
            param_list,
            self.cycle,
            self.date,
            kml_file,
            self.tracks,
        )

        # correction d'éllipsoide si différente de WGS84
        if param_config["ellipsoid"] == "WGS84":
            print("Reference ellipsoid is ok :"+ param_config["ellipsoid"])
        else:
            print("Reference ellipsoid is not WGS84 :"+ param_config["ellipsoid"])
            print("The coordinates (lon/lat) and the altitude of the satellite are converted to the reference ellipsoid WGS84.")
            self.__ellipsoid_corr__(param_config)

        # Calcul des hauteurs altimétrique pour les différents retrackers
        try:
            self.__surf_height__(surf_type, param_config)
        except self.SurfaceHeightError as e:
            message = e.message_gui
            print(message)
            raise self.SurfaceHeightError(message)

    def __check_file__(self, data_directory, file_list, param_list):
        param_missing = dict()
        file_list_ok = list()
        for idx, filename in enumerate(file_list):
            update_progress(idx / len(file_list), title="File checking")

            try:
                with xr.open_dataset(os.path.join(data_directory, filename)) as dataset:

                    pm = self.__check_param_list_exist__(dataset, param_list)
                    if len(pm) > 0:
                        param_missing[filename] = pm
                    else:
                        file_list_ok.append(filename)
            except ValueError:
                message = (
                    "[Error] Time values not conform to CF-1.6 convention.\n"
                    + "Several attibutes of the Time variable (i.e : _Fillvalues, "
                    + "units, ...) miss in the GDR file. "
                    + "\n\nCheck this file : "
                    + "\n\n- Filename : \n%s\n\n\n"
                    + " The GDR files loading is Aborted."
                ) % (filename)
                print(message)
                raise self.TimeAttMissing(message)

        update_progress(1.0, title="File checking")

        if len(param_missing.keys()) > 0:
            message = (
                "Parameters missing in some files. \n\n"
                + "\tThey will be ignored and not processed : \n\n"
            )
            for k_idx in param_missing.keys():
                message = (
                    message + "-" + k_idx + " : " + str(param_missing[k_idx]) + "\n"
                )

            with wx.MessageDialog(
                None,
                message=message,
                caption="Warning !",
                style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION,
            ) as save_dataset_dlg:

                if save_dataset_dlg.ShowModal() == wx.ID_CANCEL:
                    raise self.ParamMissing(message)

                if save_dataset_dlg.ShowModal() == wx.ID_OK:
                    save_dataset_dlg.Destroy
                    return file_list_ok

        if len(file_list_ok) == 0:
            raise Exception("None files are conform to the requested parameters")

        return file_list_ok

    def __check_param_list_exist__(self, dataset, param_list):
        param_missing = list()
        for param in param_list:
            if param not in dataset.keys():
                param_missing.append(param)
        return param_missing

    def __read_param_file__(self, data_directory, filename, param_list):
        data_disk = dict()
        with xr.open_dataset(os.path.join(data_directory, filename)) as dataset:
            if hasattr(dataset, "sub_cycle_number"):
                cycle = int(dataset.sub_cycle_number)
            else:
                cycle = dataset.cycle_number
            track = dataset.pass_number
            try:
                mask = np.isnat(dataset[self.time_hf_name].data)
            except ValueError:
                message = (
                    "[Error] Time values not conform to CF-1.6 convention.\n"
                    + "Several attibutes of the Time variable (i.e : _Fillvalues, "
                    + "units, ...) miss in the GDR file. "
                    + "\n\nCheck this file : "
                    + "\n\n- Parameter : %s \n\n- Mission : %s "
                    + "\n- Pass number : %s \n- Cycle number : %s "
                    + "\n\n- Filename : \n%s\n\n\n"
                    + " The GDR files loading is Aborted."
                ) % (
                    self.time_hf_name,
                    dataset.mission_name,
                    str(dataset.pass_number),
                    str(dataset.cycle_number),
                    filename,
                )
                print(message)
                raise self.TimeAttMissing(message)
            date = dataset[self.time_hf_name].data[~mask][0]
            time_hf = np.array(
                dataset[self.time_hf_name].data.flatten(), dtype=np.dtype("float64")
            )
            time_lf = np.array(
                dataset[self.time_lf_name].data.flatten(), dtype=np.dtype("float64")
            )
            for param in param_list:
                if len(dataset[param].dims) == 2:
                    data_disk[param] = dataset[param].data.flatten()
                elif len(dataset[param].dims) == 1:
                    if (dataset[param].dims[0] == self.dim_lf) | (self.dim_lf is None):
                        try:
                            data_disk[param] = np.interp(
                                time_hf, time_lf, dataset[param].data
                            )
                        except ValueError:
                            message = (
                                "[Error] Interpolation : GDR file not "
                                + "conform.\n\nCheck this file : "
                                + "\n\n- Parameter : %s \n\n- Mission : %s "
                                + "\n- Pass number : %s \n- Cycle number : %s "
                                + "\n\n- Filename : \n%s\n\n\n"
                                + " The GDR files loading is Aborted."
                            ) % (
                                param,
                                dataset.mission_name,
                                str(dataset.pass_number),
                                str(dataset.cycle_number),
                                filename,
                            )
                            print(message)
                            raise self.InterpolationError(message)
                    else:
                        data_disk[param] = dataset[param].data

        return data_disk, cycle, date, track

    def __data_sort_index__(self, data_struct, norm_index_ref):
        mask = data_struct > -2147483648
#        abs_idx = np.where(mask == True)[0]

        match_idx = np.searchsorted(data_struct[mask], norm_index_ref)

        mask_idx = match_idx < data_struct[mask].size
        idx = match_idx[mask_idx]

        data_struct[: data_struct[mask][idx].size] = data_struct[mask][idx]
        mask_fill = ~(data_struct == norm_index_ref)

        return mask, idx, mask_fill

    def __sort_norm_index__(self, data_struct, norm_index_ref, cycle):
        mask = dict()
        idx = dict()
        mask_fill = dict()
        for cy_idx in range(len(cycle)):
            update_progress(cy_idx / len(cycle), title="Index sorting")

            mask[cy_idx], idx[cy_idx], mask_fill[cy_idx] = self.__data_sort_index__(
                data_struct[cy_idx], norm_index_ref
            )

        update_progress(1.0, title="Index sorting")

        return mask, idx, mask_fill

    def __mk_norm_index_struct__(self, data_directory, file_list):
        data_disk = dict()
        along_track_size_index = []
        cycle = []
        date = []
#        param_missing = dict()
        cy_idx = 0
        # Création d'une structure de type
        for filename in file_list:
            update_progress(cy_idx / len(file_list), title="Structure building")
            (
                data_disk_return,
                cycle_return,
                date_return,
                track_return,
            ) = self.__read_param_file__(data_directory, filename, [self.time_hf_name])
            data_disk[cy_idx] = data_disk_return
            along_track_size_index.extend([len(data_disk[cy_idx][self.time_hf_name])])
            cycle.extend([cycle_return])
            date.extend([date_return])
            cy_idx = cy_idx + 1

        update_progress(1.0, title="Structure building")

        start_norm_index = 0
        end_norm_index = np.nanmax(along_track_size_index)

        norm_index_ref = np.arange(start_norm_index, end_norm_index + 1)
        return norm_index_ref

    def __read_file__(
        self, data_directory, file_list, param_list, norm_index_ref
    ):  # ,\
        #                            gdr_mask,gdr_idx, norm_index_mask):
        """
         Lecture des fichiers trace est interpolation à 20hz des variables à 1hz.
        """
        # Création d'une structure de type
        #        with xr.open_dataset(os.path.join(data_directory,file_list[0]),decode_times=False) as dataset:
        with xr.open_dataset(os.path.join(data_directory, file_list[0])) as dataset:
            dtype_list = []
            for param in param_list:
                dtype_list.extend([(param, dataset.variables[param].dtype)])
            struct_dtype = np.dtype(dtype_list)

        # création data_struct tableau xarray dans lequel seront chargé les données.
        dim_cycle = len(file_list)
        data_struct = np.empty([dim_cycle, norm_index_ref.size], dtype=struct_dtype)
        data_struct.fill(np.nan)
        data_struct = xr.DataArray(data_struct, dims=["cycle_index", "gdr_index"])

        tracks = []
        cycle = []
        date = []
        data_attributs = dict()
        cy_idx = 0

        for filename in file_list:
            update_progress(cy_idx / len(file_list), title="Track files loading")
            (
                data_disk,
                cycle_return,
                date_return,
                track_return,
            ) = self.__read_param_file__(data_directory, filename, param_list)

            tracks.extend([int(track_return)])
            cycle.extend([cycle_return])
            date.extend([date_return])

            for param in param_list:
                data_struct.data[param][cy_idx, : data_disk[param].size] = data_disk[
                    param
                ]

            cy_idx = cy_idx + 1

        dataset.close()
        update_progress(1.0, title="Track files loading")

        dataset = xr.open_dataset(os.path.join(data_directory, file_list[0]))
        data_attributs["global"] = {}
        data_attributs["global"]["pass_number"] = dataset.attrs["pass_number"]
        for param in struct_dtype.names:
            data_attributs[param] = {}
            if "units" in dataset[param].attrs:
                data_attributs[param]["units"] = dataset[param].attrs["units"]
            else:
                data_attributs[param]["units"] = ""

            if "standard_name" in dataset[param].attrs:
                data_attributs[param]["standard_name"] = dataset[param].attrs[
                    "standard_name"
                ]
            else:
                data_attributs[param]["standard_name"] = ""

            if "long_name" in dataset[param].attrs:
                data_attributs[param]["long_name"] = dataset[param].attrs["long_name"]
            else:
                data_attributs[param]["long_name"] = ""

            if "comment" in dataset[param].attrs:
                data_attributs[param]["comment"] = dataset[param].attrs["comment"]
            else:
                data_attributs[param]["comment"] = ""

        return data_struct, data_attributs, struct_dtype, cycle, date, tracks

    def __mk_data_struct__(
        self,
        data_struct,
        data_attributs,
        norm_index_ref,
        param_list,
        cycle,
        date,
        kml_file,
        tracks,
    ):
        """
            Création d'un dictionnaire xarray self.data_val contenant les paramétres et
            ayant les dimmensions coordonnées définies précédemment.
        """

        # Création des dimensions coordonnées de la nouvelle table xarray self.data_val
        # calcul d'un masque (mask) pour selectionner les cellules de la trace
        # normanlisée non vide.
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("ignore")  # On n'affiche pas les warnings
            #            warnings.simplefilter("default") # On affiche les warnings
            # convertion des longitudes 0<lon<360. en -180<lon<180.
            data_struct.data[self.lon_hf_name] = np.where(
                data_struct.data[self.lon_hf_name] > 180.0,
                data_struct.data[self.lon_hf_name] - 360.0,
                data_struct.data[self.lon_hf_name],
            )

        cycle_index = list()
        mask = np.zeros(data_struct.shape, dtype=np.bool)
        if kml_file is not None:
            for cy_idx, cy in enumerate(cycle):
                update_progress(cy_idx / len(cycle), title="Mask selection processing")

                mask_nan = ~np.isnan(data_struct.data[self.lon_hf_name][cy_idx, :])
                mask_kml = kml_poly_select(
                    kml_file,
                    data_struct.data[self.lon_hf_name][cy_idx, :],
                    data_struct.data[self.lat_hf_name][cy_idx, :],
                )
                mask[cy_idx, :] = mask_nan & mask_kml
                cycle_index.append(cy_idx)
            update_progress(1.0, title="Mask selection processing")
        else:
            for cy_idx, cy in enumerate(cycle):
                mask_nan = ~np.isnan(data_struct.data[self.lon_hf_name][cy_idx, :])
                mask[cy_idx, :] = mask_nan
                cycle_index.append(cy_idx)

        if np.any(mask):
            xr_mask = xr.DataArray(mask, dims=["cycle_index", "gdr_index"])

            # Création d'un dictionnaire xarray self.data_val contenant les paramètres et
            # ayant les dimmensions coordonnées définies précédemment.
            self.data_val = {}
            
            for param in param_list:

                self.data_val[param] = xr.DataArray(
                    data_struct.data[param],
                    coords={
                        "cycle_index": cycle_index,
                        "tracks": ("cycle_index", tracks),
                        "cycle": ("cycle_index", cycle),
                        "date": ("cycle_index", date),
                        "gdr_index": np.arange(data_struct.shape[1]),
                    },
                    dims=["cycle_index", "gdr_index"],
                )
                if not data_attributs[param]["units"] == "":
                    self.data_val[param].attrs["units"] = data_attributs[param]["units"]
                self.data_val[param].attrs["standard_name"] = data_attributs[param][
                    "standard_name"
                ]
                self.data_val[param].attrs["long_name"] = data_attributs[param]["long_name"]
                self.data_val[param].attrs["comment"] = data_attributs[param]["comment"]

            for param in param_list:
                #            print(param,self.data_val[param].shape,xr_mask.shape)
                #            pdb.set_trace()
                self.data_val[param] = self.data_val[param].where(xr_mask, drop=True)
        else:
            message="Out of Aera : None pass goes through the area defined by the KML polygon."
#            print(message)
            raise self.OutOfAreaError(message)


    def __ellipsoid_corr__(self, param_config):
        """
        concersion d'ellipsoide.
        """


        shape_array = self.data_val[param_config["param"]["lon_hf"]].data.shape
        
        # correction ellipsoide pour le geoid 
        lon = self.data_val[param_config["param"]["lon_hf"]].data.reshape(-1)
        lat = self.data_val[param_config["param"]["lat_hf"]].data.reshape(-1)
        geoid = self.data_val[param_config["param"]["geoid"]].data.reshape(-1)
        [lon, lat, geoid] = ellipsoid_convert (lon,lat,geoid,param_config["ellipsoid"],"WGS84")
 
        # correction ellipsoide pour alt_sat
        lon = self.data_val[param_config["param"]["lon_hf"]].data.reshape(-1)
        lat = self.data_val[param_config["param"]["lat_hf"]].data.reshape(-1)
        alt_sat = self.data_val[param_config["param"]["alt_hf"]].data.reshape(-1)
        [lon, lat, alt_sat] = ellipsoid_convert (lon,lat,alt_sat,param_config["ellipsoid"],"WGS84")
        
        lon = np.where(lon>180.0, lon-180.0,lon)

        self.data_val[param_config["param"]["lon_hf"]].data = lon.reshape(shape_array)
        self.data_val[param_config["param"]["lat_hf"]].data = lat.reshape(shape_array)
        self.data_val[param_config["param"]["geoid"]].data = geoid.reshape(shape_array)
        self.data_val[param_config["param"]["alt_hf"]].data = alt_sat.reshape(shape_array)
        



    def __surf_height__(self, surf_type, param_config):
        """
            Calcul des hauteurs altimétrique pour les différents retrackers
        """

        if surf_type == "RiversLakes":
            #            try:

            for band in param_config["band"]:
                for retracker in param_config["retracker"]:
                    
                    if not (retracker + "_range_" + band in param_config["param"].keys()):
                        continue

                    param_name = retracker + "_" + band + "_" + "SurfHeight_alti"
                    # initialisation du nouveau paramétre dans la structure xarray
                    self.data_val[param_name] = (
                        self.data_val[param_config["param"]["alt_hf"]] * np.nan
                    )

                    cycles = (
                        self.data_val[param_config["param"]["alt_hf"]]
                        .coords["cycle_index"]
                        .data
                    )

                    if (band == "ku") or (band == "ka"):
                        for cy_idx, cy in enumerate(cycles):
                            update_progress(
                                cy_idx / len(self.cycle),
                                title=surf_type + " | Surface height : " + param_name,
                            )
                            self.data_val[param_name][cy_idx, :] = (
                                self.data_val[param_config["param"]["alt_hf"]][cy_idx, :]
                                - self.data_val[
                                    param_config["param"][retracker + "_range_" + band]
                                ][cy_idx, :]
                                - self.data_val[
                                    param_config["param"]["model_wet_tropo_corr"]
                                ][cy_idx, :]
                                - self.data_val[
                                    param_config["param"]["model_dry_tropo_corr"]
                                ][cy_idx, :]
                                - self.data_val[param_config["param"]["solid_earth_tide"]][
                                    cy_idx, :
                                ]
                                - self.data_val[param_config["param"]["geoid"]][cy_idx, :]
                                - self.data_val[
                                    param_config["param"]["iono_corr_gim_" + band]
                                ][cy_idx, :]
                                - self.data_val[param_config["param"]["pole_tide"]][
                                    cy_idx, :
                                ]
                            )
                    elif (band == "c"):
                        for cy_idx, cy in enumerate(cycles):
                            update_progress(
                                cy_idx / len(self.cycle),
                                title=surf_type + " | Surface height : " + param_name,
                            )
                            if "alt_hf_"+ band in param_config["param"].keys():
                                alt_sat_label = "alt_hf_"+ band
                            else:
                                alt_sat_label = "alt_hf"

                            self.data_val[param_name][cy_idx, :] = (
                                self.data_val[param_config["param"][alt_sat_label]][cy_idx, :]
                                - self.data_val[
                                    param_config["param"][retracker + "_range_" + band]
                                ][cy_idx, :]
                                - self.data_val[
                                    param_config["param"]["model_wet_tropo_corr"]
                                ][cy_idx, :]
                                - self.data_val[
                                    param_config["param"]["model_dry_tropo_corr"]
                                ][cy_idx, :]
                                - self.data_val[param_config["param"]["solid_earth_tide"]][
                                    cy_idx, :
                                ]
                                - self.data_val[param_config["param"]["geoid"]][cy_idx, :]
                                - self.data_val[param_config["param"]["pole_tide"]][
                                    cy_idx, :
                                ]
                            )
 

                    update_progress(
                        1.0, title=surf_type + " | Surface height : " + param_name
                    )
                    self.data_val[param_name].attrs["units"] = "meters"
                    self.data_val[param_name].attrs["standard_name"] = "surface_height"
                    self.data_val[param_name].attrs["long_name"] = (
                        str(param_config["freq"])
                        + " Hz "
                        + band
                        + " band surface height ("
                        + retracker
                        + " retracking)"
                    )
                    if (band == "ku") or (band == "ka"):
                        self.data_val[param_name].attrs["comment"] = (
                            "Altimetric Surfurce Height = "
                            + param_config["param"]["alt_hf"]
                            + " - "
                            + param_config["param"][retracker + "_range_" + band]
                            + " - "
                            + param_config["param"]["model_wet_tropo_corr"]
                            + " - "
                            + param_config["param"]["model_dry_tropo_corr"]
                            + " - "
                            + param_config["param"]["solid_earth_tide"]
                            + " - "
                            + param_config["param"]["geoid"]
                            + " - "
                            + param_config["param"]["iono_corr_gim_" + band]
                            + " - "
                            + param_config["param"]["pole_tide"]
                        )
                    elif (band == "c"):
                        if "alt_hf_"+ band in param_config["param"].keys():
                            alt_sat_label = "alt_hf_"+ band
                        else:
                            alt_sat_label = "alt_hf"

                        self.data_val[param_name].attrs["comment"] = (
                            "Altimetric Surfurce Height = "
                            + param_config["param"][alt_sat_label]
                            + " - "
                            + param_config["param"][retracker + "_range_" + band]
                            + " - "
                            + param_config["param"]["model_wet_tropo_corr"]
                            + " - "
                            + param_config["param"]["model_dry_tropo_corr"]
                            + " - "
                            + param_config["param"]["solid_earth_tide"]
                            + " - "
                            + param_config["param"]["geoid"]
                            + " - "
                            + param_config["param"]["pole_tide"]
                        )
 
            #            except KeyError as k:
        #                message= (('They is KeyError issue : \n '+
        #                           '\t- %s\n\n'+
        #                           'In order to compute the "%s" '+
        #                           'surface height the key parametre '+
        #                           '%s is needed. Check your configuration file!'  )%(str(k),surf_type,str(k),))
        #                print('test : ',message)
        #                raise self.SurfaceHeightError(message)

        elif surf_type == "None":
            pass
        else:
            raise Exception("Surface_type not already defined : ", surf_type)

    def mk_filename_gdr_data(self, mask):

        param_name = self.time_hf_name  #'time_20hz'
        data = self.data_val[param_name].where(mask, drop=True)
        cycle = np.array(data.coords["cycle"])
        #norm_index = np.array(data.coords["gdr_index"])
        #        lon = np.array(data.coords['lon'])
        #        lat = np.array(data.coords['lat'])

        dataset_date = np.array(data.coords["date"], dtype=np.datetime64)
        date = [
            "{:04d}{:02d}{:02d}".format(y, m, d)
            for y, m, d in zip(
                pd.DatetimeIndex(dataset_date).year,
                pd.DatetimeIndex(dataset_date).month,
                pd.DatetimeIndex(dataset_date).day,
            )
        ]

        startdate = date[0]
        startcycle = "{:03d}".format(cycle[0])
        enddate = date[-1]
        endcycle = "{:03d}".format(cycle[-1])

        #        if min(self.tracks) == max(self.tracks):
        #            track = '{:04d}'.format(min(self.tracks))
        #        else:
        #            track = 'Tracks'
        if isinstance(self.track_value, str):
            track = self.track_value
        else:
            track = "{:04d}".format(self.track_value.min())

        return (
            "AlTiS_gdrpass_"
            + self.mission
            + "_"
            + track
            + "_"
            + startdate
            + "_"
            + startcycle
            + "_"
            + enddate
            + "_"
            + endcycle
            + ".nc"
        )

    def save_gdr_data(self, mask, filename):

        backup_copy = self.data_val.copy()
        for param in backup_copy.keys():
            backup_copy[param] = backup_copy[param].where(mask, drop=True)

        dataset_merge = xr.merge([backup_copy])

        param_name = self.time_hf_name  #'time_20hz'
        data = self.data_val[param_name]
#        cycle = np.array(data.coords["cycle"])
#        norm_index = np.array(data.coords["gdr_index"])
        #        lon = np.array(data.coords['lon'])
        #        lat = np.array(data.coords['lat'])

        dataset_date = np.array(data.coords["date"], dtype=np.datetime64)
        date = [
            "{:04d}{:02d}{:02d}".format(y, m, d)
            for y, m, d in zip(
                pd.DatetimeIndex(dataset_date).year,
                pd.DatetimeIndex(dataset_date).month,
                pd.DatetimeIndex(dataset_date).day,
            )
        ]

        startdate = date[0]
#        startcycle = "{:03d}".format(cycle[0])
        enddate = date[-1]
#        endcycle = "{:03d}".format(cycle[-1])

        dataset_merge.attrs["Conventions"] = "CF-1.6"
        dataset_merge.attrs["creation_date"] = time.strftime("%Y-%m-%d %H:%M:%S %Z")
        dataset_merge.attrs[
            "title"
        ] = "Radar altimetric parameters dataset for AlTiS Software."
        dataset_merge.attrs[
            "institutions"
        ] = "CTOH, LEGOS (UMR5566), Universite de Toulouse, CNES, CNRS, IRD, UPS, Toulouse, France"
        dataset_merge.attrs["contact"] = "ctoh_products@legos.obs-mip.fr"
        dataset_merge.attrs["processing_facility"] = "CTOH, LEGOS (UMR5566)"
        dataset_merge.attrs["source"] = "Altimetric data from CTOH data base"
        dataset_merge.attrs["doi"] = ""
        dataset_merge.attrs["Doc_ref"] = ""
        dataset_merge.attrs["processor_version"] = (
            "Version : " + __version__ + " Revision : " + __revision__
        )  # ??? | Data generation date : ???"
        dataset_merge.attrs["hgid"] = __revision__
        dataset_merge.attrs["start_date"] = startdate
        dataset_merge.attrs["end_date"] = enddate
        dataset_merge.attrs["mission"] = self.mission
        dataset_merge.attrs["processor"] = "altisgdr"
        

        if "global" in self.data_attributs.keys():
            for att in self.data_attributs["global"].keys():
                dataset_merge.attrs[att] = self.data_attributs["global"][att]

        if min(self.tracks) == max(self.tracks):
            dataset_merge.attrs["pass_number"] = min(self.tracks)
        else:
            dataset_merge.attrs["pass_number"] = -1
        #            track = 'Tracks'

        print("AlTiS GDR pass file created :  " + filename)
        to_netcdf(pathlib.PurePath(filename), dataset_merge)
        
#        if sys.platform.startswith('linux'):
#            dataset_merge.to_netcdf(filename)
#        elif sys.platform.startswith('win'):
#            dataset_merge.to_netcdf(pathlib.PurePath(filename), format="NETCDF3_64BIT", engine="scipy")

    #        dataset_merge.to_netcdf(filename, format="NETCDF4_CLASSIC")
        
        dataset_merge.close()
        
        
