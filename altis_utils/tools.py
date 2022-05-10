#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Module of tools for AlTiS.
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
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
from shapely.geometry import shape, Point, Polygon
import fiona
import xarray as xr



# --------------------------------------------------------------------------
# Compute the median absolute deviation of the data along the given axis.
#
# https://github.com/scipy/scipy/blob/v1.3.3/scipy/stats/stats.py#L2658
# "Median absolute deviation" https://en.wikipedia.org/wiki/Median_absolute_deviation
# --------------------------------------------------------------------------
# 2020/04/22 | F. BLAREL   | Creation
# --------------------------------------------------------------------------
def med_abs_dev(vec, dim_label, scale=1.4826):
    mask_nan = np.isnan(vec.median(dim=dim_label))
    med_abs_diff = np.abs(vec - vec.median(dim=dim_label)).median(dim=dim_label)
    med_abs_diff[mask_nan] = np.nan
    return scale * med_abs_diff


def kml_poly_select(filename, lon_mean, lat_mean):
    """
       Selection des données contenues à l'intérieur du polygone défini dans le fichier kml
    """
    fiona.supported_drivers['KML']='rw'
    poly_obj_file = fiona.open(filename,'r',driver='KML')

    obj_dim = len(poly_obj_file)
    if obj_dim == 0:
        print("[KML/ShapeFile] Polynom Object file not valid! Is empty.")
        exit(-1)
    if obj_dim > 1:
        print(f"[KML/ShapeFile] Polynom Object file contains several "+
                f"Object Items : {obj_dim} found.")
    
    polygon = None
    for poly_str in poly_obj_file:
        if "geometry" not in poly_str.keys():
            print("[KML/ShapeFile] Polygon structure id"+poly_str['id']+" not correct : "
                    "\"geometry\" field is missing!")
            continue
        if "Polygon" != poly_str["geometry"]["type"]:
            print("[KML/ShapeFile] Polygon structure id"+poly_str['id']+" not correct : "
                    "\"geometry type\" field value is not \"Polygon\"."
                    "Value found : "+poly_str["geometry"]["type"])
            continue
        if "coordinates" not in poly_str["geometry"].keys():
            print("[KML/ShapeFile] Polygon structure id"+poly_str['id']+" not correct : "
                    "\"coordinate\" field is missing.")
            continue
        polys = poly_str["geometry"]["coordinates"]
        if len(polys) == 0:
            print("[KML/ShapeFile] Polygon structure id"+poly_str['id']+" not correct : "
                    "\"coordinate\" field is empty.")
            continue

        if polygon is None:
            polygon = Polygon(polys[0])
        else:
            polygon.union(Polygon(polys[0]))

        for poly in polys[1:]:
            polygon.union(Polygon(poly))
    
    poly_obj_file.close()

    if polygon is None:
        print("[KML/ShapeFile] Polygon is empty : None is returned")


    mask = [
        Point(lon, lat).within(polygon)
        for lon, lat in zip(lon_mean, lat_mean)
    ]

    return mask


def fatal_error(msg):
    """Print a message and exit"""
    logging.error(msg)
    print("\n>>>>> FATAL ERROR %s ... exiting\n" % msg)
    sys.exit(-1)


# ---------------------------------------------------------------------------------------------------------------------------------
# update_progress() : Displays or updates a console progress bar
## Accepts a float between 0 and 1. Any int will be converted to a float.
## A value under 0 represents a 'halt'.
## A value at 1 or bigger represents 100%
def update_progress(progress, title=""):
    barLength = 20  # Modify this to change the length of the progress bar
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
    block = int(round(barLength * progress))
    text = "\r[{0}] Percent: [{1}] {2}% {3}".format(
        title,
        "#" * block + "-" * (barLength - block),
        "{:4.1f}".format(progress * 100),
        status,
    )
    sys.stdout.write(text)
    sys.stdout.flush()


def __read_cfg_file__(mission_config_file):
    """
        lecture des parametres de la mission
    """
    if mission_config_file is None:
        mission_file_cfg = pkg_resources.resource_filename(
            "altis", "../etc/products_config.yml"
        )
    else:
        if os.path.isfile(mission_config_file):
            mission_file_cfg = mission_config_file
        else:
            raise Exception("Mission configuration file not found.")

    with open(mission_file_cfg) as f:
        #        try:
        #            yaml_data = yaml.load(f)
        #        except:
        yaml_data = yaml.load(
            f, Loader=yaml.FullLoader
        )  # A revoir pour créer un vrai loader
    return yaml_data


def __config_load__(mission, mission_config_file):
    """
        lecture et selection des parametres de la mission
    """
    yaml_data = __read_cfg_file__(mission_config_file)

    if mission in yaml_data.keys():
        return yaml_data[mission]
    else:
        raise Exception(mission, " mission is not already configurated.")

class Error(Exception):
        pass


class FilenameNotConformError(Error):
    def __init__(self, message):
        super().__init__(message)
        self.message_gui = message

def __regex_file_parser__(mission, directory, mission_config_file):
    config_mission = __config_load__(mission, mission_config_file)
    filename_pattern = re.compile(r'{}'.format(config_mission["filename_pattern"]))

    file_list = glob.glob(os.path.join(directory, "*.nc"))
    file_list.sort()
    file_list = [filename.split(os.path.sep)[-1] for filename in file_list]

    track = []
    cycle = []
    file_list_bad_regex = []
    file_list_ok_regex = []
    for idx, filename in enumerate(file_list):
        match = filename_pattern.match( filename)
        if match is None:
            file_list_bad_regex.extend([filename])
        else:
            track.append(int(match.group("track")))
            cycle.append(int(match.group("cycle")))
            file_list_ok_regex.extend([filename])

    #    if track.count(None) > 0:
    if len(file_list_bad_regex) == len(file_list):
        message = (
            "The GDR files are not for "+mission+" product. "
            +"It seems to be files of another product. Check "
            +"the chosen mission is conformed to the selected files."
            +" Files can't be load."
        )
        print("altis_utils.tools.FilenameNotConformError : ",message)
        raise FilenameNotConformError(message)
    #        else:
    #            raise Exception('Some filenames are not conform to the filename '\
    #                            +'pattern of '+mission+' mission and could not '\
    #                            +'be load : \n',file_list_bad_regex)
    else:
        file_list = file_list_ok_regex
        track = np.array(track, dtype=np.int)
        cycle = np.array(cycle, dtype=np.int)
        list_track = np.unique(track)
        print(
            str(len(file_list))
            + " Files found for "
            + mission
            + " mission:\n"
            + "    - Tracks : ",
            list_track,
        )

        dtype_file_struct = [
            ("track", np.dtype("i4")),
            ("cycle", np.dtype("i4")),
            ("filename", np.dtype("U" + str(len(file_list[0])))),
        ]
        file_struct = np.empty(len(file_list), dtype=dtype_file_struct)

        file_struct["track"] = track
        file_struct["cycle"] = cycle
        file_struct["filename"] = file_list
        return file_struct
        
        
        
def __grp_format__(name):
    """
        formate le nom de la variable si nom est complosé avec groupe
    """
    if '/' in name:
        return '_'.join(name.split('/')[1:])
    else:
        return name

