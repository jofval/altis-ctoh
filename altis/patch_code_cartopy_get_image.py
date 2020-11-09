#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------
#
# Cartopy patch issue 
#
#
# Created by Fabien Blarel on 2019-04-19.
# CeCILL Licence 2019 CTOH-LEGOS.
# ----------------------------------------------------------------------



import io
from urllib.request import urlopen, Request
from PIL import Image

##################################################################################
# Patch to solve the issu of user agent
def image_spoof(self, tile): # this function pretends not to be a Python script
    url = self._image_url(tile) # get the url of the street map API
    req = Request(url) # start request
#            req.add_header('User-agent','Anaconda 3') # add user agent to request
    req.add_header('User-agent','CartoPy/0.18.0') # add user agent to request
    print('>>>',tile, url)
    fh = urlopen(req) 
    print('>ok.')
    im_data = io.BytesIO(fh.read()) # get image
    fh.close() # close url
    img = Image.open(im_data) # open image with PIL
    img = img.convert(self.desired_tile_form) # set image format
    return img, self.tileextent(tile), 'lower' # reformat for cartopy
##################################################################################


