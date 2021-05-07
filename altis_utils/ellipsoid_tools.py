#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Ellipsoid tools. To convert coordinates (lon/lat) using different
# ellipsoid.
#
# module load python/3.7
# source activate gui_py37
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------
import numpy as np
import pkg_resources


def get_ellipsoid_params():
    """
    return the a and b ellipsoid parameters
    """
    ellipsoid_dict = {}
    ellipse_params_file = pkg_resources.resource_filename(
           "altis", "../etc/ellipse_a_b.txt")
    with open(ellipse_params_file, "r") as id_file:
        for line in id_file:
            code_ellipse, ellipse_name_type, a, b = line.split()
            ellipsoid_dict[code_ellipse] = dict()
            ellipsoid_dict[code_ellipse]['a'] = float(a)
            ellipsoid_dict[code_ellipse]['b'] = float(b)

    return ellipsoid_dict


def ecef2lla(ellipse_type, x, y, z):
    """
    
    convert earth-centered earth-fixed (ECEF) to latitude, longitude, altitude

    """
    ellipsoid_dict = get_ellipsoid_params()

    a = ellipsoid_dict[ellipse_type]['a']
    b = ellipsoid_dict[ellipse_type]['b']

    e = np.sqrt(1.0 - (b / a) ** 2.0)

    b = np.sqrt((a ** 2.) * (1. - (e ** 2)))
    ep = np.sqrt(((a ** 2.) - (b ** 2.)) / (b ** 2.))
    p = np.sqrt((x ** 2.) + (y ** 2.))
    th = np.arctan2(a * z, b * p)
    xlon = np.arctan2(y, x)
    xlat = np.arctan2(
        z + (ep ** 2.0) * b * (np.sin(th) ** 3.),
        (p - (e ** 2.0) * a * (np.cos(th) ** 3.)),
    )
    N = a / np.sqrt(1. - (e ** 2.0) * (np.sin(xlat) ** 2.))
    xh = p / (np.cos(xlat)) - N

    xlon = xlon * 180.0 / np.pi
    # pas utile Altis a besoin d'un -180.0 < lon < 180. cartopy
#    xlon = np.where(xlon < 0.0, xlon + 360.0, xlon)
    xlat = xlat * 180 / np.pi

    return xlon, xlat, xh


def lla2ecef(ellipse_type, xlon, xlat, xh):
    """
    convert latitude, longitude, altitude to earth-centered earth-fixed (ECEF) 
    """

    ellipsoid_dict = get_ellipsoid_params()

    a = ellipsoid_dict[ellipse_type]['a']
    b = ellipsoid_dict[ellipse_type]['b']

    d2r = np.pi / 180.0
    e = np.sqrt(1.0 - ((b / a) ** 2.0))

    xlon = np.where(xlon < 0.0, xlon + 360.0, xlon)

    xlon = xlon * d2r
    xlat = xlat * d2r
    N = a / np.sqrt(1.0 - (e ** 2.0) * (np.sin(xlat) ** 2.0))
    x = (N + xh) * np.cos(xlat) * np.cos(xlon)
    y = (N + xh) * np.cos(xlat) * np.sin(xlon)
    z = (N * (1.0 - (e ** 2.0)) + xh) * np.sin(xlat)

    return x, y, z

def ellipsoid_convert(xlon,xlat,xh,ellip_in, ellip_out):
    """
        conversion de coordonnées xlon,xlat, xh (alti) ayant pour ellipsoid de référence ellip_in
        en  coordonnées xlon,xlat, xh (alti) avec une autre ellipsoide de référence ellip_out
    """
    [x, y, z] = lla2ecef (ellip_in, xlon, xlat, xh)
    [xlon, xlat, xh] = ecef2lla (ellip_out, x, y, z)

    return xlon, xlat, xh




